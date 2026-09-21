from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationDetail,
    ConversationUpdate,
)
from app.schemas.message import MessageOut
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationOut])
def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_conv.list_conversations(
        db, tenant_id=current_user.tenant_id, user_id=None, skip=skip, limit=limit
    )


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_conv.create_conversation(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        title=body.title,
        document_id=body.document_id,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = crud_conv.get_conversation(
        db, conversation_id=conversation_id, tenant_id=current_user.tenant_id
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = crud_msg.list_messages(
        db, conversation_id=conversation_id, tenant_id=current_user.tenant_id
    )

    return ConversationDetail(
        id=conv.id,
        tenant_id=conv.tenant_id,
        user_id=conv.user_id,
        document_id=conv.document_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageOut.model_validate(m) for m in messages],
    )


@router.patch("/{conversation_id}", response_model=ConversationOut)
def update_conversation(
    conversation_id: int,
    body: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = crud_conv.get_conversation(
        db, conversation_id=conversation_id, tenant_id=current_user.tenant_id
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.title:
        conv = crud_conv.update_conversation_title(
            db, conversation_id=conversation_id, tenant_id=current_user.tenant_id, title=body.title
        )
    return conv


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = crud_conv.delete_conversation(
        db, conversation_id=conversation_id, tenant_id=current_user.tenant_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}
