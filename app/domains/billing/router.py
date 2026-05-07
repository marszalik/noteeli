"""Billing routes.

Public routes:
    GET  /subscribe          — paywall / subscribe page (must be logged in)
    POST /billing/checkout   — create Paddle checkout session → redirect
    GET  /billing/portal     — Paddle customer portal → redirect
    GET  /billing/success    — post-checkout landing page → workspace
    POST /webhooks/paddle    — Paddle Billing webhook (no auth)
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.templates import render_template
from app.domains.auth.service import AuthService
from app.domains.billing.service import BillingService
from app.domains.billing.webhook import verify_signature

logger = logging.getLogger(__name__)
router = APIRouter(tags=["billing"])


def _billing_service() -> BillingService:
    return BillingService(get_settings())


def _auth_service() -> AuthService:
    return AuthService(get_settings())


# ── Subscribe / paywall ───────────────────────────────────────────────────


@router.get("/subscribe", name="subscribe_page")
async def subscribe_page(request: Request):
    user = _auth_service().get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    # Already subscribed → go to workspace.
    user_id = user.get("db_id")
    if user_id and _billing_service().is_subscription_active(user_id):
        return RedirectResponse(url=request.url_for("workspace_page"), status_code=303)

    settings = get_settings()
    return render_template(
        "domains/billing/views/subscribe.mako",
        request,
        user_email=user.get("email", ""),
        paddle_client_token=settings.paddle_client_token,
        paddle_price_id=settings.paddle_price_id,
        paddle_environment=settings.paddle_environment,
        success_url=str(request.url_for("billing_success")),
    )


# ── Checkout ──────────────────────────────────────────────────────────────


@router.post("/billing/checkout", name="billing_checkout")
async def billing_checkout(request: Request):
    user = _auth_service().get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Login required.")

    settings = get_settings()
    if not settings.paddle_api_key or not settings.paddle_price_id:
        raise HTTPException(status_code=503, detail="Billing not configured.")

    user_id = user.get("db_id")
    email = user.get("email", "")
    success_url = str(request.url_for("billing_success"))

    try:
        checkout_url = await _billing_service().create_checkout_url(
            user_id=user_id,
            email=email,
            success_url=success_url,
        )
    except Exception as exc:
        logger.exception("Paddle checkout error: %s", exc)
        raise HTTPException(status_code=502, detail="Could not start checkout. Please try again.")

    return RedirectResponse(url=checkout_url, status_code=303)


# ── Customer portal ───────────────────────────────────────────────────────


@router.get("/billing/portal", name="billing_portal")
async def billing_portal(request: Request):
    user = _auth_service().get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Login required.")

    portal_url = await _billing_service().get_portal_url(user.get("db_id"))
    if portal_url is None:
        # No Paddle customer yet — send to subscribe page.
        return RedirectResponse(url=request.url_for("subscribe_page"), status_code=303)

    return RedirectResponse(url=portal_url, status_code=303)


# ── Post-checkout landing ─────────────────────────────────────────────────


@router.get("/billing/success", name="billing_success")
async def billing_success(request: Request):
    """Paddle redirects here after a successful checkout.

    Paddle processes the payment asynchronously — the webhook may arrive
    a few seconds after the redirect. We refresh the subscription flag
    in the session on the next workspace load anyway, so just redirect.
    """
    # Mark subscription_active optimistically so the first workspace load
    # doesn't bounce the user back to /subscribe.
    user = request.session.get("user", {})
    user["subscription_active"] = True
    request.session["user"] = user
    return RedirectResponse(url=request.url_for("workspace_page"), status_code=303)


# ── Paddle webhook ────────────────────────────────────────────────────────


@router.post("/webhooks/paddle", name="billing_webhook")
async def billing_webhook(request: Request):
    """Receive and process Paddle Billing webhook events.

    Raw body must be read before any parsing so signature verification
    works correctly.
    """
    raw_body = await request.body()
    signature = request.headers.get("Paddle-Signature", "")
    settings = get_settings()

    if not verify_signature(settings.paddle_webhook_secret, raw_body, signature):
        logger.warning("Invalid Paddle webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON.")

    event_type: str = payload.get("event_type", "")
    data: dict = payload.get("data", {})

    logger.info("Paddle webhook: %s", event_type)

    svc = _billing_service()

    # Link paddle_customer_id to our user if not yet done.
    customer_id = data.get("customer_id")
    if customer_id:
        user = svc._repo.get_user_by_paddle_customer_id(customer_id)
        if user is None:
            # Try to resolve via email from the customer object.
            # (Paddle includes customer.email in some event payloads.)
            customer_email = (
                data.get("customer", {}).get("email")
                or payload.get("customer", {}).get("email")
            )
            if customer_email:
                with svc._repo._connect() as conn:
                    row = conn.execute(
                        "SELECT id FROM users WHERE email = ?", (customer_email,)
                    ).fetchone()
                    if row:
                        svc.link_paddle_customer(row["id"], customer_id)

    svc.handle_webhook_event(event_type, data)

    return {"ok": True}
