import pytest
import sys
import os

# Ensure backend modules are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from app.db.session import SessionLocal
from app.crud import user as crud_user
from app.crud import tenant as crud_tenant


def test_password_hashing():
    raw_pass = "SuperSecretPassword123"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_decoding():
    user_id = 42
    tenant_id = 7
    token, exp = create_access_token(subject=user_id, tenant_id=tenant_id)
    assert isinstance(token, str)
    assert exp > 0

    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == str(user_id)
    assert payload.get("tenant_id") == tenant_id
    assert payload.get("type") == "access"


def test_user_and_tenant_creation():
    db = SessionLocal()
    try:
        tenant = crud_tenant.create_tenant(db, name="Test Unit Corp")
        assert tenant.id is not None
        assert tenant.name == "Test Unit Corp"

        user = crud_user.create_user(
            db,
            email=f"unit_test_{tenant.id}@example.com",
            hashed_password=get_password_hash("testpass"),
            tenant_id=tenant.id,
            full_name="Unit Tester",
        )
        assert user.id is not None
        assert user.tenant_id == tenant.id
        assert user.email.startswith("unit_test_")

        found = crud_user.get_user(db, user.id)
        assert found is not None
        assert found.email == user.email
    finally:
        db.close()
