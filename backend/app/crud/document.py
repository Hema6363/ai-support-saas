from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import Document


def get_document(db: Session, document_id: int, tenant_id: int) -> Optional[Document]:
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.tenant_id == tenant_id)
        .first()
    )


def list_documents(
    db: Session, tenant_id: int, skip: int = 0, limit: int = 100
) -> List[Document]:
    return (
        db.query(Document)
        .filter(Document.tenant_id == tenant_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_document(
    db: Session,
    tenant_id: int,
    owner_id: int,
    filename: str,
    original_filename: str,
    file_path: str,
    file_type: str,
    file_size: int,
    chunk_count: int = 0,
    status: str = "PENDING",
) -> Document:
    doc = Document(
        tenant_id=tenant_id,
        owner_id=owner_id,
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        chunk_count=chunk_count,
        status=status,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document_status(
    db: Session,
    document_id: int,
    tenant_id: int,
    status: str,
    chunk_count: Optional[int] = None,
    error_message: Optional[str] = None,
) -> Optional[Document]:
    doc = get_document(db, document_id, tenant_id)
    if doc:
        doc.status = status
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if error_message is not None:
            doc.error_message = error_message
        db.add(doc)
        db.commit()
        db.refresh(doc)
    return doc


def delete_document(db: Session, document_id: int, tenant_id: int) -> bool:
    doc = get_document(db, document_id, tenant_id)
    if doc:
        db.delete(doc)
        db.commit()
        return True
    return False
