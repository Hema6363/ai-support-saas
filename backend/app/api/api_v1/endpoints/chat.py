import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.message import ChatMessageRequest, ChatMessageResponse, CitationOut, MessageOut
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg
from app.ai.rag import rag_pipeline
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(
    req: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty",
        )

    # 1. Resolve or create conversation
    if req.conversation_id:
        conversation = crud_conv.get_conversation(
            db, conversation_id=req.conversation_id, tenant_id=current_user.tenant_id
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        title = req.message[:50].strip()
        if len(req.message) > 50:
            title += "..."
        conversation = crud_conv.create_conversation(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            title=title,
            document_id=req.document_id,
        )

    # 2. Store user message in database
    user_msg = crud_msg.create_message(
        db=db,
        tenant_id=current_user.tenant_id,
        conversation_id=conversation.id,
        role="user",
        content=req.message,
        sender_id=current_user.id,
    )

    # 3. Retrieve recent conversation history for context window
    history_records = crud_msg.list_messages(
        db,
        conversation_id=conversation.id,
        tenant_id=current_user.tenant_id,
        limit=settings.rag_history_messages,
    )
    # Convert to standard format excluding the latest user message which will be passed as current question
    conversation_history: List[Dict[str, str]] = []
    for h in history_records[:-1]:
        conversation_history.append({"role": h.role, "content": h.content})

    # 4. Execute local Ollama RAG pipeline
    try:
        rag_result = await rag_pipeline.arun(
            question=req.message,
            tenant_id=current_user.tenant_id,
            conversation_history=conversation_history,
            document_id=req.document_id or conversation.document_id,
        )
    except Exception as e:
        logger.error(f"RAG processing failed: {e}")
        # Fallback graceful response
        rag_result = {
            "answer": "I apologize, but I am currently having trouble accessing the local AI knowledge service. Please try again or open a support ticket.",
            "citations": [],
            "latency_ms": 0,
            "suggest_escalation": True,
        }

    # 5. Store AI assistant message
    citations_json = json.dumps(rag_result.get("citations", []))
    asst_msg = crud_msg.create_message(
        db=db,
        tenant_id=current_user.tenant_id,
        conversation_id=conversation.id,
        role="assistant",
        content=rag_result["answer"],
        sender_id=None,
        citations=citations_json,
        latency_ms=rag_result.get("latency_ms", 0),
    )

    citations_out = [
        CitationOut(
            document_id=c.get("document_id"),
            filename=c.get("filename", "Document"),
            chunk_index=c.get("chunk_index", 0),
            snippet=c.get("snippet", ""),
            distance=c.get("distance", 0.0),
        )
        for c in rag_result.get("citations", [])
    ]

    return ChatMessageResponse(
        conversation_id=conversation.id,
        user_message=MessageOut.model_validate(user_msg),
        assistant_message=MessageOut.model_validate(asst_msg),
        citations=citations_out,
        suggest_escalation=rag_result.get("suggest_escalation", False),
        latency_ms=rag_result.get("latency_ms", 0),
    )
