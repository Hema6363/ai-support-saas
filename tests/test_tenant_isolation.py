import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.crud import tenant as crud_tenant
from app.crud import document as crud_doc
from app.crud import conversation as crud_conv
from app.ai.vector_store import vector_store
from app.ai.embeddings import embedding_service


def test_strict_multi_tenant_vector_isolation():
    """Verify that vector searches for Tenant A NEVER return chunks belonging to Tenant B."""
    tenant_a_id = 8881
    tenant_b_id = 8882

    # Clean previous
    vector_store.delete_document_chunks(tenant_id=tenant_a_id, document_id=1)
    vector_store.delete_document_chunks(tenant_id=tenant_b_id, document_id=2)

    # 1. Add secret document chunk for Tenant A
    doc_a_text = "Tenant A Confidential Revenue is $50 Million and CEO secret PIN is 9876."
    emb_a = embedding_service.embed_text(doc_a_text)
    vector_store.add_chunks(
        ids=[f"t{tenant_a_id}_d1_c0"],
        embeddings=[emb_a],
        documents=[doc_a_text],
        metadatas=[{"tenant_id": tenant_a_id, "document_id": 1, "filename": "secret_a.txt"}],
    )

    # 2. Add public document chunk for Tenant B
    doc_b_text = "Tenant B standard refund policy allows 14 days returns."
    emb_b = embedding_service.embed_text(doc_b_text)
    vector_store.add_chunks(
        ids=[f"t{tenant_b_id}_d2_c0"],
        embeddings=[emb_b],
        documents=[doc_b_text],
        metadatas=[{"tenant_id": tenant_b_id, "document_id": 2, "filename": "policy_b.txt"}],
    )

    # 3. Query as Tenant B asking for confidential revenue/PIN
    query_emb = embedding_service.embed_text("What is the confidential revenue or secret PIN?")
    results_for_b = vector_store.query(query_embedding=query_emb, tenant_id=tenant_b_id, n_results=5)

    # Verify: Tenant B query MUST NOT return Tenant A's document
    for r in results_for_b:
        assert r["metadata"].get("tenant_id") == tenant_b_id
        assert "Tenant A" not in r["content"]
        assert "9876" not in r["content"]

    # 4. Query as Tenant A asking for secret PIN
    results_for_a = vector_store.query(query_embedding=query_emb, tenant_id=tenant_a_id, n_results=5)
    assert len(results_for_a) > 0
    assert results_for_a[0]["metadata"].get("tenant_id") == tenant_a_id
    assert "9876" in results_for_a[0]["content"]

    # Cleanup
    vector_store.delete_document_chunks(tenant_id=tenant_a_id, document_id=1)
    vector_store.delete_document_chunks(tenant_id=tenant_b_id, document_id=2)
