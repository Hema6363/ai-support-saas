from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    health,
    auth,
    documents,
    chat,
    conversations,
    tickets,
    analytics,
    payments,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(auth.router, prefix="/api/v1")
api_router.include_router(documents.router, prefix="/api/v1")
api_router.include_router(chat.router, prefix="/api/v1")
api_router.include_router(conversations.router, prefix="/api/v1")
api_router.include_router(tickets.router, prefix="/api/v1")
api_router.include_router(analytics.router, prefix="/api/v1")
api_router.include_router(payments.router, prefix="/api/v1")
