from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.document import Document
from app.models.message import Message
from app.crud import tenant as crud_tenant
from app.schemas.payment import (
    SubscriptionPlanOut,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    SubscriptionStatusOut,
)
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/plans", response_model=List[SubscriptionPlanOut])
def get_plans():
    return payment_service.get_plans()


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    req: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        res = payment_service.create_checkout_session(
            tenant_id=current_user.tenant_id,
            plan_id=req.plan_id,
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscription-status", response_model=SubscriptionStatusOut)
def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant = crud_tenant.get_tenant(db, current_user.tenant_id)
    plan_info = payment_service.get_plan(tenant.plan if tenant else "starter") or payment_service.get_plans()[0]

    docs_count = db.query(Document).filter(Document.tenant_id == current_user.tenant_id).count()
    queries_count = (
        db.query(Message)
        .filter(Message.tenant_id == current_user.tenant_id, Message.role == "assistant")
        .count()
    )

    return SubscriptionStatusOut(
        tenant_id=current_user.tenant_id,
        plan=tenant.plan if tenant else "starter",
        status="active" if (tenant and tenant.is_active) else "inactive",
        documents_used=docs_count,
        documents_limit=plan_info.get("max_documents", 5),
        queries_used=queries_count,
        queries_limit=plan_info.get("max_queries_per_month", 500),
        is_active=tenant.is_active if tenant else True,
    )


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        res = payment_service.handle_webhook_event(payload, stripe_signature)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
