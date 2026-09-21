from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal, get_db
from app.ai.ollama_client import ollama_client
from app.core.config import settings
import httpx

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # 1. Database check
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # 2. ChromaDB check
    chroma_status = "ok"
    try:
        with httpx.Client(base_url=settings.chromadb_url, timeout=2.0) as client:
            resp = client.get("/api/v2/heartbeat")
            if resp.status_code != 200:
                chroma_status = f"HTTP {resp.status_code}"
    except Exception as e:
        chroma_status = f"unreachable: {str(e)}"

    # 3. Ollama check
    ollama_info = ollama_client.check_health()

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "AI Customer Support SaaS API",
        "database": db_status,
        "chromadb": chroma_status,
        "ollama": ollama_info,
    }
