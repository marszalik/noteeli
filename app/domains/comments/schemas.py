"""Pydantic models for the review-comments API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CommentStatus = Literal["open", "resolved"]


class Comment(BaseModel):
    id: str
    status: CommentStatus = "open"
    created: str = ""
    text: str = ""


class CommentsDocument(BaseModel):
    """Everything the panel needs: the comments plus where they live."""

    document: str                      # workspace path of the commented note
    comments_path: str                 # sibling `<stem>_comments.md`
    exists: bool = False               # False → no comments file on disk (yet)
    comments: list[Comment] = Field(default_factory=list)


class CreateCommentRequest(BaseModel):
    path: str                          # the note, not the comments file
    text: str = Field(min_length=1, max_length=20_000)
    # Optional client-chosen id so the editor can mark the range before
    # the round-trip completes. Must match `c_<6-12 hex>`; the server
    # generates one when omitted.
    id: str | None = Field(default=None, pattern=r"^c_[0-9a-f]{6,12}$")


class UpdateCommentRequest(BaseModel):
    path: str
    text: str | None = Field(default=None, max_length=20_000)
    status: CommentStatus | None = None
