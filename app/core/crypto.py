"""Symmetric encryption helpers for at-rest secrets.

Used for SFTP passwords and any other credential we must persist. The
key is derived from NOTEELI_SESSION_SECRET — same source of truth, no
separate key to manage. Rotating session_secret invalidates encrypted
secrets (acceptable: users re-enter passwords on next connect).

Format: Fernet (HMAC-SHA256 + AES-128-CBC + base64). Tokens are stored
as plain ASCII strings in the SQLite DB.
"""
from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


@lru_cache
def _key() -> bytes:
    secret = get_settings().session_secret or "change-me-in-production"
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a plaintext secret. Empty / None returns ''."""
    if not plaintext:
        return ""
    return Fernet(_key()).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt. If the value isn't a valid Fernet token (e.g. legacy
    plaintext from before encryption rolled out, or wrong key after a
    secret rotation), return empty string — caller will treat it as
    "no stored password" and prompt the user."""
    if not ciphertext:
        return ""
    try:
        return Fernet(_key()).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeDecodeError):
        return ""


def is_encrypted(value: str) -> bool:
    """Heuristic: Fernet tokens start with 'gAAAAA' and are URL-safe b64."""
    return bool(value) and value.startswith("gAAAAA")
