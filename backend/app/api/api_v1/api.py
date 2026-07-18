from fastapi import APIRouter

from backend.app.api.api_v1.endpoints import health, auth

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(auth.router, prefix="/api/v1")
