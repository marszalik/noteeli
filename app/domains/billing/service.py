"""Billing service — subscription lifecycle logic."""
from __future__ import annotations

from app.core.config import Settings
from app.domains.billing.repository import BillingRepository
from app.domains.billing.paddle_client import PaddleClient


class BillingService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._repo = BillingRepository(settings)
        self._paddle = PaddleClient(settings)

    # ── User management ──────────────────────────────────────────────────

    def get_or_create_user(self, google_id: str, email: str) -> int:
        return self._repo.get_or_create_user(google_id, email)

    def is_subscription_active(self, user_id: int) -> bool:
        return self._repo.is_subscription_active(user_id)

    def get_subscription(self, user_id: int) -> dict | None:
        return self._repo.get_subscription(user_id)

    # ── Webhook event handlers ────────────────────────────────────────────

    def handle_webhook_event(self, event_type: str, data: dict) -> None:
        """Process a single Paddle Billing webhook event."""
        customer_id: str | None = data.get("customer_id")
        sub_id: str | None = data.get("id")
        status: str = data.get("status", "")
        period_end: str | None = data.get("next_billed_at") or data.get("current_billing_period", {}).get("ends_at")

        # Map Paddle status names to our internal ones.
        STATUS_MAP = {
            "active":   "active",
            "trialing": "trialing",
            "past_due": "past_due",
            "paused":   "paused",
            "canceled": "canceled",
        }
        internal_status = STATUS_MAP.get(status, status)

        if event_type in (
            "subscription.activated",
            "subscription.updated",
            "subscription.canceled",
            "subscription.paused",
            "subscription.resumed",
        ):
            if not sub_id or not customer_id:
                return

            user = self._repo.get_user_by_paddle_customer_id(customer_id)
            if user is None:
                # Customer not yet linked — can happen if checkout was
                # completed before the user visited the app. Skip silently;
                # the next login will re-check via the API if needed.
                return

            user_id: int = user["id"]
            self._repo.upsert_subscription(user_id, sub_id, internal_status, period_end)

    # ── Checkout / portal ─────────────────────────────────────────────────

    async def create_checkout_url(
        self, user_id: int, email: str, success_url: str
    ) -> str:
        paddle_customer_id = self._repo.get_paddle_customer_id(user_id)
        url = await self._paddle.create_checkout_url(
            customer_email=email,
            success_url=success_url,
            customer_id=paddle_customer_id,
        )
        return url

    async def get_portal_url(self, user_id: int) -> str | None:
        paddle_customer_id = self._repo.get_paddle_customer_id(user_id)
        if not paddle_customer_id:
            return None
        return await self._paddle.get_customer_portal_url(paddle_customer_id)

    def link_paddle_customer(self, user_id: int, paddle_customer_id: str) -> None:
        self._repo.set_paddle_customer_id(user_id, paddle_customer_id)
