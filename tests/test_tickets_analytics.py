import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.crud import ticket as crud_ticket
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg


def test_ticket_creation_and_status_transitions():
    db = SessionLocal()
    try:
        conv = crud_conv.create_conversation(db, tenant_id=1, user_id=1, title="Billing Problem")
        assert conv.id is not None

        ticket = crud_ticket.create_ticket(
            db=db,
            tenant_id=1,
            user_id=1,
            title="Escalated: Billing Problem",
            description="Customer unable to update credit card details.",
            priority="high",
            conversation_id=conv.id,
        )
        assert ticket.id is not None
        assert ticket.status == "open"
        assert ticket.is_resolved is False

        # In progress
        updated = crud_ticket.update_ticket(
            db=db,
            ticket_id=ticket.id,
            tenant_id=1,
            status="in_progress",
        )
        assert updated.status == "in_progress"
        assert updated.is_resolved is False

        # Resolved
        resolved = crud_ticket.update_ticket(
            db=db,
            ticket_id=ticket.id,
            tenant_id=1,
            status="resolved",
        )
        assert resolved.status == "resolved"
        assert resolved.is_resolved is True
    finally:
        db.close()
