import sys
from pathlib import Path

# Ensure backend directory is in sys.path so 'app' package imports work cleanly from any CWD
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings


app = FastAPI(
    title="AI Customer Support SaaS API",
    version="1.0.0",
    description="Multi-tenant SME AI Customer Support Platform powered by local Ollama (Llama 3.1 & nomic-embed-text) and ChromaDB.",
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


app.include_router(api_router)


@app.get("/", tags=["root"])
def root():
    return {
        "message": "AI Customer Support SaaS API is active.",
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
    }


@app.get("/health", tags=["health"])
def root_health():
    return {"status": "ok"}