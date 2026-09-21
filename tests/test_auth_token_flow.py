import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.crud import user as crud_user
from app.crud import tenant as crud_tenant
from app.core.security import get_password_hash

client = TestClient(app)


def test_auth_token_required_on_unauthenticated_request():
    """Verify that document endpoints strictly reject requests without token with 401."""
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Authentication token required"

    upload_resp = client.post("/api/v1/documents/upload")
    assert upload_resp.status_code == 401
    assert upload_resp.json().get("detail") == "Authentication token required"


def test_auth_token_invalid_or_expired():
    """Verify that invalid bearer tokens are rejected with 401."""
    headers = {"Authorization": "Bearer completely.invalid.jwt.token"}
    resp = client.get("/api/v1/documents", headers=headers)
    assert resp.status_code == 401
    assert "Invalid" in resp.json().get("detail")


def test_complete_auth_token_flow_and_knowledge_base():
    """Verify end-to-end token issuance, authenticated document ingestion, and refresh flow."""
    db = SessionLocal()
    try:
        # 1. Register & Login
        email = "kb_test_admin@acmesaas.com"
        password = "SecurePassword123!"
        
        # Check if user already exists
        existing = crud_user.get_user_by_email(db, email=email)
        if not existing:
            reg_resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": "KB Tester",
                    "company_name": "Acme Knowledge Corp",
                },
            )
            assert reg_resp.status_code == 201

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Authenticated GET /documents
        get_docs = client.get("/api/v1/documents", headers=headers)
        assert get_docs.status_code == 200
        initial_docs = get_docs.json()
        assert isinstance(initial_docs, list)

        # 3. Authenticated POST /documents/upload (Simulating Load Sample Policy)
        sample_policy = (
            "Acme Cloud Support Service Level Policy:\n"
            "1. Standard support hours are 9am to 6pm EST.\n"
            "2. Enterprise customers receive 1-hour critical response SLAs.\n"
            "3. Refunds are allowed within 14 days of purchase."
        )
        files = {
            "file": (
                "acme_saas_support_policy.txt",
                sample_policy.encode("utf-8"),
                "text/plain",
            )
        }
        upload_resp = client.post("/api/v1/documents/upload", headers=headers, files=files)
        assert upload_resp.status_code == 201
        doc_data = upload_resp.json()
        assert doc_data["status"] == "PROCESSED"
        assert doc_data["chunk_count"] > 0
        doc_id = doc_data["id"]

        # 4. Verify Document is in Indexed Documents list
        list_after = client.get("/api/v1/documents", headers=headers)
        assert list_after.status_code == 200
        docs_after = list_after.json()
        assert any(d["id"] == doc_id for d in docs_after)

        # 5. Token Refresh: Exchange refresh token for a new access token
        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        new_access_token = new_tokens["access_token"]
        assert new_access_token != access_token

        # 6. Verify New Token can perform Document Operations (Reindex & Delete)
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        reindex_resp = client.post(f"/api/v1/documents/{doc_id}/reindex", headers=new_headers)
        assert reindex_resp.status_code == 200
        assert reindex_resp.json()["status"] == "PROCESSED"

        # 7. Multi-Tenant Isolation: Create Tenant B and ensure Tenant A's doc is not returned
        tenant_b_email = "tenant_b_user@othercompany.com"
        existing_b = crud_user.get_user_by_email(db, email=tenant_b_email)
        if not existing_b:
            client.post(
                "/api/v1/auth/register",
                json={
                    "email": tenant_b_email,
                    "password": password,
                    "company_name": "Competitor Org B",
                },
            )
        login_b = client.post(
            "/api/v1/auth/login",
            json={"email": tenant_b_email, "password": password},
        )
        token_b = login_b.json()["access_token"]
        docs_b_resp = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token_b}"})
        assert docs_b_resp.status_code == 200
        docs_b = docs_b_resp.json()
        assert not any(d["id"] == doc_id for d in docs_b)

        # Cleanup test document
        del_resp = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
        assert del_resp.status_code == 200

    finally:
        db.close()
