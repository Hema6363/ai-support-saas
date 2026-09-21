import pytest
import sys
import os
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.db.session import SessionLocal
from app.crud import user as crud_user
from app.crud import tenant as crud_tenant
from app.crud import document as crud_doc
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg
from app.crud import ticket as crud_ticket
from app.core.security import get_password_hash, create_access_token
from app.ai.document_parser import document_parser
from app.ai.embeddings import embedding_service
from app.ai.vector_store import vector_store
from app.ai.rag import rag_pipeline
from app.schemas.ticket import TicketCreate


def test_full_critical_path_end_to_end():
    db = SessionLocal()
    try:
        # 1. Register new organization (Tenant) & Admin User
        company_name = f"E2E Enterprise Testing Corp"
        tenant = crud_tenant.create_tenant(db, name=company_name)
        assert tenant.id is not None
        assert tenant.name == company_name

        user_email = f"admin_e2e_{tenant.id}@e2etest.com"
        hashed_pwd = get_password_hash("SuperSecret123!")
        user = crud_user.create_user(
            db,
            email=user_email,
            hashed_password=hashed_pwd,
            tenant_id=tenant.id,
            full_name="E2E Administrator",
            role="admin",
        )
        assert user.id is not None
        assert user.tenant_id == tenant.id

        # 2. Issue JWT Token
        token, exp = create_access_token(subject=user.id, tenant_id=tenant.id)
        assert isinstance(token, str)

        # 3. Create and Ingest a Knowledge Base Document
        doc_content = (
            "Acme Cloud Support SLA Guideline:\n"
            "Critical Severity Level 1 incidents have a guaranteed 15-minute response SLA.\n"
            "Customers on the Enterprise tier have dedicated account managers assigned."
        )
        doc = crud_doc.create_document(
            db,
            tenant_id=tenant.id,
            owner_id=user.id,
            filename="sla_policy_e2e.txt",
            original_filename="sla_policy_e2e.txt",
            file_type="text/plain",
            file_size=len(doc_content.encode("utf-8")),
            file_path="uploads/mock_sla.txt",
        )
        assert doc.id is not None

        chunks = document_parser.split_into_chunks(doc_content)
        assert len(chunks) > 0

        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_documents(chunk_texts)
        assert len(embeddings) == len(chunks)

        chunk_ids = [f"t{tenant.id}_d{doc.id}_c{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "tenant_id": tenant.id,
                "document_id": doc.id,
                "filename": doc.filename,
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ]

        vector_store.add_chunks(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas,
        )

        crud_doc.update_document_status(
            db,
            tenant_id=tenant.id,
            document_id=doc.id,
            status="PROCESSED",
            chunk_count=len(chunks),
        )

        # 4. RAG Query via local Ollama
        query = "What is the guaranteed response SLA for Critical Level 1 incidents?"
        rag_res = rag_pipeline.run(
            question=query,
            tenant_id=tenant.id,
            document_id=doc.id,
        )

        assert "answer" in rag_res
        assert len(rag_res["citations"]) > 0
        assert "15" in rag_res["answer"] or "minute" in rag_res["answer"] or "15-minute" in rag_res["answer"]

        # 5. Create Conversation & Log Messages
        conv = crud_conv.create_conversation(
            db,
            tenant_id=tenant.id,
            user_id=user.id,
            title="SLA Inquiry",
            document_id=doc.id,
        )
        assert conv.id is not None

        user_msg = crud_msg.create_message(
            db,
            conversation_id=conv.id,
            tenant_id=tenant.id,
            sender_id=user.id,
            role="user",
            content=query,
        )
        assert user_msg.id is not None

        ai_msg = crud_msg.create_message(
            db,
            conversation_id=conv.id,
            tenant_id=tenant.id,
            role="assistant",
            content=rag_res["answer"],
            latency_ms=rag_res["latency_ms"],
        )
        assert ai_msg.id is not None

        # 6. Escalate / Create Ticket
        ticket = crud_ticket.create_ticket(
            db,
            tenant_id=tenant.id,
            user_id=user.id,
            title="SLA Review Request",
            description="User requested confirmation of 15-minute SLA terms.",
            priority="high",
            conversation_id=conv.id,
        )
        assert ticket.id is not None
        assert ticket.status == "open"
        assert ticket.priority == "high"

        # 7. Multi-Tenant Isolation Check (Tenant B cannot read Tenant A's doc or ticket)
        tenant_b = crud_tenant.create_tenant(db, name="Separate Org B")
        doc_b_query = crud_doc.list_documents(db, tenant_id=tenant_b.id)
        assert not any(d.id == doc.id for d in doc_b_query)

        # Cleanup test vector chunks
        vector_store.delete_document_chunks(tenant_id=tenant.id, document_id=doc.id)

    finally:
        db.close()
