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


class PublishedItemsResponse(BaseModel):
    items: list[PublishedItem]


class PublishRequest(BaseModel):
    path: str
    # kind is inferred server-side from the actual filesystem state, but
    # the client passes a hint for sanity-checking.
    kind: Literal["file", "directory"] | None = None
