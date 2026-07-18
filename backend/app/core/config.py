from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    chromadb_url: str
    ollama_url: str

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
