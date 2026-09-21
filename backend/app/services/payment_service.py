import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

PLANS = [
    {
        "id": "starter",
        "name": "Starter (Free)",
        "price_monthly": 0,
        "currency": "USD",
        "max_documents": 5,
        "max_queries_per_month": 500,
        "features": [
            "Up to 5 Knowledge Base Documents",
            "500 AI Chat Responses / mo",
            "Local Ollama Llama 3.1 & nomic-embed",
            "Basic Support Ticketing",
            "Standard Analytics",
        ],
    },
    {
        "id": "pro",
        "name": "Professional",
        "price_monthly": 49,
        "currency": "USD",
        "max_documents": 50,
        "max_queries_per_month": 5000,
        "features": [
            "Up to 50 Knowledge Base Documents",
            "5,000 AI Chat Responses / mo",
            "Priority Local AI Generation",
            "Advanced Multi-Tenant Isolation",
            "Auto-Ticket Escalation & Webhooks",
            "Full Analytics Dashboard",
        ],
    },
    {
        "id": "enterprise",
        "name": "Enterprise SME",
        "price_monthly": 199,
        "currency": "USD",
        "max_documents": 500,
        "max_queries_per_month": 50000,
        "features": [
            "Unlimited Knowledge Base Documents",
            "50,000 AI Chat Responses / mo",
            "Custom System Prompts & SLA",
            "Dedicated Slack/Email Integration",
            "Exportable Compliance Reports",
            "24/7 Priority Support",
        ],
    },
]


class PaymentService:
    def __init__(self):
        self.stripe_key = settings.stripe_secret_key
        self.webhook_secret = settings.stripe_webhook_secret

    def get_plans(self) -> List[Dict[str, Any]]:
        return PLANS

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        for p in PLANS:
            if p["id"] == plan_id:
                return p
        return None

    def create_checkout_session(
        self,
        tenant_id: int,
        plan_id: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session or a simulated sandbox session if API key is not configured."""
        plan = self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Unknown plan {plan_id}")

        if self.stripe_key:
            try:
                # Real Stripe integration
                import stripe  # type: ignore
                stripe.api_key = self.stripe_key
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{
                        "price_data": {
                            "currency": plan["currency"].lower(),
                            "product_data": {"name": f"AI SaaS {plan['name']} Plan"},
                            "unit_amount": plan["price_monthly"] * 100,
                            "recurring": {"interval": "month"},
                        },
                        "quantity": 1,
                    }],
                    mode="subscription",
                    success_url=success_url or f"http://localhost:3000/settings?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=cancel_url or "http://localhost:3000/settings",
                    metadata={"tenant_id": str(tenant_id), "plan_id": plan_id},
                )
                return {
                    "checkout_url": session.url,
                    "session_id": session.id,
                    "mode": "live_stripe",
                }
            except Exception as e:
                logger.error(f"Stripe session creation error: {e}")
                # Fallback to sandbox simulation
                pass

        # Sandbox / Mock checkout
        return {
            "checkout_url": f"http://localhost:3000/settings?sandbox_upgrade={plan_id}&tenant={tenant_id}",
            "session_id": f"sandbox_sess_{tenant_id}_{plan_id}",
            "mode": "sandbox_simulated",
        }

    def handle_webhook_event(self, payload: bytes, sig_header: Optional[str]) -> Dict[str, Any]:
        """Verify and process incoming Stripe webhook events."""
        if not self.webhook_secret or not self.stripe_key:
            return {"status": "skipped", "message": "Stripe webhook not configured"}

        try:
            import stripe  # type: ignore
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
            return {"status": "received", "type": event.get("type")}
        except Exception as e:
            logger.error(f"Stripe webhook verification error: {e}")
            raise


payment_service = PaymentService()
