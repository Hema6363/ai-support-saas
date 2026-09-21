import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ai.document_parser import document_parser
from app.db.session import SessionLocal
from app.crud import document as crud_doc


def test_text_cleaning_and_chunking():
    sample_text = """
    # Customer Service Guide
    
    This is the first paragraph with important information about billing.
    
    This is the second paragraph with details about cancellation.
    
    This is the third paragraph with details about upgrades.
    """
    cleaned = document_parser.clean_text(sample_text)
    assert "# Customer Service Guide" in cleaned
    assert "\n\n\n" not in cleaned

    chunks = document_parser.split_into_chunks(cleaned)
    assert len(chunks) >= 1
    for c in chunks:
        assert len(c["text"]) > 0
        assert "chunk_index" in c


def test_document_crud_lifecycle():
    db = SessionLocal()
    try:
        doc = crud_doc.create_document(
            db=db,
            tenant_id=1,
            owner_id=1,
            filename="test_guide.txt",
            original_filename="User_Guide.txt",
            file_path="uploads/tenant_1/test_guide.txt",
            file_type="text/plain",
            file_size=1024,
            status="PENDING",
        )
        assert doc.id is not None
        assert doc.status == "PENDING"

        # Update status
        updated = crud_doc.update_document_status(
            db=db,
            document_id=doc.id,
            tenant_id=1,
            status="PROCESSED",
            chunk_count=5,
        )
        assert updated is not None
        assert updated.status == "PROCESSED"
        assert updated.chunk_count == 5

        # Delete
        success = crud_doc.delete_document(db=db, document_id=doc.id, tenant_id=1)
        assert success is True
    finally:
        db.close()
