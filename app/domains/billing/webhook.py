"""Paddle Billing webhook signature verification.

Paddle sends:
    Paddle-Signature: ts=1749290400;h1=<hex-digest>

Signed payload = f"{ts}:{raw_body_utf8}"
Algorithm      = HMAC-SHA256(webhook_secret, signed_payload)
"""
from __future__ import annotations

import hashlib
import hmac
import time


def verify_signature(
    secret: str,
    raw_body: bytes,
    header: str,
    max_age_seconds: int = 300,
) -> bool:
    """Return True if the Paddle-Signature header is valid."""
    if not secret or not header:
        return False

    parts = {}
    for part in header.split(";"):
        if "=" in part:
            k, _, v = part.partition("=")
            parts[k.strip()] = v.strip()

    ts = parts.get("ts")
    h1 = parts.get("h1")
    if not ts or not h1:
        return False

    # Replay-attack guard.
    try:
        if abs(time.time() - int(ts)) > max_age_seconds:
            return False
    except ValueError:
        return False

    signed = f"{ts}:{raw_body.decode('utf-8')}"
    expected = hmac.new(
        secret.encode("utf-8"),
        signed.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, h1)
