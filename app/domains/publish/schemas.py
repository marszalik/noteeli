"""Schemas for the public-publish feature."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PublishedItem(BaseModel):
    """A file or folder that has been published as a read-only public
    page on the same Noteeli instance."""

    id: int
    kind: Literal["file", "directory"]
    path: str
    slug: str
    created_at: str
    public_url: str  # absolute path on this instance, e.g. "/12/my-notes"
    # Who published it, so the public page can render with that person's
    # theme/font/language. Empty for rows predating the column — those
    # fall back to the global preferences. Never sent to public visitors:
    # the public sidebar uses PublicNavItem, which carries no identity.
    user_key: str = ""


class PublishedItemsResponse(BaseModel):
    items: list[PublishedItem]


class PublicNavItem(BaseModel):
    """Public-safe projection of a published item for the shared-page
    sidebar nav. Deliberately carries NO filesystem path — only the
    display name (basename) and where the public page lives."""

    name: str
    kind: Literal["file", "directory"]
    public_url: str


class PublicNavResponse(BaseModel):
    items: list[PublicNavItem]


class PublishRequest(BaseModel):
    path: str
    # kind is inferred server-side from the actual filesystem state, but
    # the client passes a hint for sanity-checking.
    kind: Literal["file", "directory"] | None = None
