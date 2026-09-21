import logging
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class IntegrationsService:
    def __init__(self):
        self.webhook_url = settings.notification_webhook_url

    async def notify_ticket_escalated(
        self,
        ticket_id: int,
        tenant_id: int,
        title: str,
        description: str,
        priority: str,
    ) -> Dict[str, Any]:
        """Dispatch notification to configured webhook / Slack / Email endpoint."""
        payload = {
            "event": "ticket.escalated",
            "ticket_id": ticket_id,
            "tenant_id": tenant_id,
            "title": title,
            "description": description,
            "priority": priority,
        }

        if self.webhook_url:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(self.webhook_url, json=payload)
                    logger.info(f"Webhook notification sent for ticket {ticket_id}: HTTP {resp.status_code}")
                    return {"status": "dispatched", "status_code": resp.status_code}
            except Exception as e:
                logger.warning(f"Failed to dispatch ticket webhook: {e}")
                return {"status": "failed", "error": str(e)}

        # Default log fallback
        logger.info(f"[INTEGRATIONS] Ticket #{ticket_id} escalated for Tenant {tenant_id} ('{title}', Priority: {priority})")
        return {"status": "logged", "message": "Notification logged (no external webhook configured)"}


integrations_service = IntegrationsService()
