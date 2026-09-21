import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.document import DocumentOut, DocumentReindexResponse
from app.crud import document as crud_doc
from app.core.config import settings
from app.ai.document_parser import document_parser
from app.ai.embeddings import embedding_service
from app.ai.vector_store import vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".json", ".log"}


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
@router.post("/upload/", response_model=DocumentOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 2. Read content and validate size
    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_file_size_mb} MB",
        )

    # 3. Store file locally
    tenant_upload_dir = os.path.join(settings.upload_dir, f"tenant_{current_user.tenant_id}")
    os.makedirs(tenant_upload_dir, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(tenant_upload_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(content)

    # 4. Create document record in database
    doc = crud_doc.create_document(
        db=db,
        tenant_id=current_user.tenant_id,
        owner_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename or "document.txt",
        file_path=file_path,
        file_type=file.content_type or "text/plain",
        file_size=len(content),
        status="PROCESSING",
    )

    # 5. Extract text, chunk, embed, and index in ChromaDB
    try:
        raw_text = document_parser.extract_text(file_path, doc.file_type)
        if not raw_text.strip():
            crud_doc.update_document_status(
                db, doc.id, current_user.tenant_id, status="FAILED", error_message="Extracted text was empty"
            )
            raise HTTPException(status_code=400, detail="Document contains no readable text")

        chunks = document_parser.split_into_chunks(raw_text)
        if not chunks:
            crud_doc.update_document_status(
                db, doc.id, current_user.tenant_id, status="FAILED", error_message="Could not split document into chunks"
            )
            raise HTTPException(status_code=400, detail="Could not create document chunks")

        # Generate embeddings
        chunk_texts = [c["text"] for c in chunks]
        embeddings = await embedding_service.aembed_documents(chunk_texts)

        chunk_ids = [f"t{current_user.tenant_id}_d{doc.id}_c{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "tenant_id": current_user.tenant_id,
                "document_id": doc.id,
                "filename": doc.original_filename,
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ]

        # Add to vector store
        await vector_store.aadd_chunks(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas,
        )

        doc = crud_doc.update_document_status(
            db, doc.id, current_user.tenant_id, status="PROCESSED", chunk_count=len(chunks)
        )
        return doc

    except Exception as e:
        logger.error(f"Error processing document {doc.id}: {e}")
        crud_doc.update_document_status(
            db, doc.id, current_user.tenant_id, status="FAILED", error_message=str(e)[:500]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {str(e)}",
        )


@router.get("", response_model=List[DocumentOut])
@router.get("/", response_model=List[DocumentOut], include_in_schema=False)
def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_doc.list_documents(db, tenant_id=current_user.tenant_id, skip=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = crud_doc.get_document(db, document_id=document_id, tenant_id=current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = crud_doc.get_document(db, document_id=document_id, tenant_id=current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Remove vector chunks from ChromaDB
    await vector_store.adelete_document_chunks(
        tenant_id=current_user.tenant_id, document_id=document_id
    )

    # 2. Remove file from disk
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Could not remove local file {doc.file_path}: {e}")

    # 3. Delete database record
    crud_doc.delete_document(db, document_id=document_id, tenant_id=current_user.tenant_id)
    return {"status": "success", "message": f"Document {document_id} deleted successfully"}


@router.post("/{document_id}/reindex", response_model=DocumentReindexResponse)
async def reindex_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = crud_doc.get_document(db, document_id=document_id, tenant_id=current_user.tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=400, detail="Original document file not found on disk")

    try:
        # Clear existing chunks
        await vector_store.adelete_document_chunks(
            tenant_id=current_user.tenant_id, document_id=document_id
        )

        raw_text = document_parser.extract_text(doc.file_path, doc.file_type)
        chunks = document_parser.split_into_chunks(raw_text)
        chunk_texts = [c["text"] for c in chunks]
        embeddings = await embedding_service.aembed_documents(chunk_texts)

        chunk_ids = [f"t{current_user.tenant_id}_d{doc.id}_c{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "tenant_id": current_user.tenant_id,
                "document_id": doc.id,
                "filename": doc.original_filename,
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ]

        await vector_store.aadd_chunks(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas,
        )

        crud_doc.update_document_status(
            db, doc.id, current_user.tenant_id, status="PROCESSED", chunk_count=len(chunks)
        )

        return {
            "document_id": doc.id,
            "filename": doc.original_filename,
            "status": "PROCESSED",
            "chunk_count": len(chunks),
            "message": "Document re-indexed successfully",
        }
    except Exception as e:
        logger.error(f"Error reindexing doc {doc.id}: {e}")
        crud_doc.update_document_status(
            db, doc.id, current_user.tenant_id, status="FAILED", error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")
