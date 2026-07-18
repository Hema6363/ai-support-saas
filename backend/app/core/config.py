from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    chromadb_url: str
    ollama_url: str
    secret_key: str = "CHANGE_ME_REPLACE_IN_ENV"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
