from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://ai_support:changeme@127.0.0.1:5432/ai_support"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_host: str = "0.0.0.0"
    frontend_port: int = 3000

    # ChromaDB & Ollama Configuration
    chromadb_url: str = "http://127.0.0.1:8001"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"

    # Security & Auth
    secret_key: str = "7c1e2d9f5b6a4c8e3f1d9a7b2c6e8f4a1d3b5c7e9f2a4b6c8d1e3f5a7b9c2d4"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Ingestion & Uploads
    max_file_size_mb: int = 25
    upload_dir: str = "uploads"

    # RAG Settings
    rag_top_k: int = 4
    rag_similarity_threshold: float = 0.35
    rag_history_messages: int = 6

    # Optional Integrations
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    notification_webhook_url: str = ""

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
