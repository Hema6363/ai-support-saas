from fastapi import FastAPI

from backend.app.api.api_v1.api import api_router

app = FastAPI(title="AI Support SaaS Backend")

app.include_router(api_router)

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
