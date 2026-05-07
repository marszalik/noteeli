"""Thin async wrapper around the Paddle Billing REST API."""
from __future__ import annotations

import httpx

from app.core.config import Settings


class PaddleClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.paddle_api_key
        self._price_id = settings.paddle_price_id
        base = (
            "https://api.paddle.com"
            if settings.paddle_environment == "live"
            else "https://sandbox-api.paddle.com"
        )
        self._base = base
        self._portal_base = (
            "https://customer.paddle.com"
            if settings.paddle_environment == "live"
            else "https://sandbox-customer.paddle.com"
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def create_checkout_url(
        self,
        customer_email: str,
        success_url: str,
        customer_id: str | None = None,
    ) -> str:
        """Create a Paddle transaction and return the hosted checkout URL.

        Tries with a custom success_url first.  If Paddle rejects the domain
        (transaction_checkout_url_domain_is_not_approved) it retries without
        the custom URL so the user at least reaches the Paddle checkout page.
        Add the app domain to Paddle's Approved Domains to get the full
        success-URL redirect back into the app.
        """
        payload: dict = {
            "items": [{"price_id": self._price_id, "quantity": 1}],
            "checkout": {"url": success_url},
        }
        if customer_id:
            payload["customer_id"] = customer_id
        else:
            payload["customer"] = {"email": customer_email}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base}/transactions",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            if resp.status_code == 400:
                body = resp.json()
                if body.get("error", {}).get("code") == "transaction_checkout_url_domain_is_not_approved":
                    # Retry without custom success URL — Paddle will use
                    # the Default Payment Link domain instead.
                    payload.pop("checkout", None)
                    resp = await client.post(
                        f"{self._base}/transactions",
                        headers=self._headers(),
                        json=payload,
                        timeout=15,
                    )
            resp.raise_for_status()
            data = resp.json()

        return data["data"]["checkout"]["url"]

    async def get_customer_portal_url(self, paddle_customer_id: str) -> str:
        """Get a one-time-auth customer portal URL."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base}/customers/{paddle_customer_id}/auth-token",
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            token = resp.json()["data"]["token"]

        return f"{self._portal_base}/?token={token}"
