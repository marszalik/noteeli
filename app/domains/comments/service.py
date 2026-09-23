"""Review comments on a Markdown note.

The note itself stays a plain document: a commented range is fenced by
two HTML comments, `<!--comment:c_a7f3d2:start-->` … `<!--comment:c_a7f3d2:end-->`,
which every Markdown renderer ignores. The comment bodies live next to the
note in `<stem>_comments.md`, itself ordinary Markdown:

    ---
    document: article.md
    ---
    ## c_a7f3d2
    status: open
    created: 2026-09-23T20:41:00+02:00

    Is this sentence too absolute?

One `## <id>` section per comment, `key: value` metadata lines directly
under the heading, then the free-text body. The file is meant to be read
by humans and by an AI assistant alongside the note ("read article.md and
article_comments.md, propose one minimal change per open comment").

Ids are stable random tokens, never sequence numbers, so deleting one
comment never renumbers the others. Display numbers are the UI's job.
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime

from app.domains.comments.schemas import Comment, CommentsDocument
from app.domains.workspace.service import (
    DocumentNotFoundError,
    InvalidPathError,
    WorkspaceService,
)
from app.domains.workspace.storage import StorageBackend

COMMENT_ID_RE = re.compile(r"^c_[0-9a-f]{6,12}$")
COMMENTS_SUFFIX = "_comments.md"
MARKER_RE = re.compile(r"<!--comment:(c_[0-9a-f]{6,12}):(start|end)-->")

_HEADING_RE = re.compile(r"^##\s+(c_[0-9a-f]{6,12})\s*$")
_META_RE = re.compile(r"^([a-z][a-z_]*):\s*(.*)$")
_METADATA_KEYS = ("status", "created")


class CommentError(Exception):
    """Base error for comment operations."""


class CommentNotFoundError(CommentError):
    """The comments file has no section with that id."""


class CommentAlreadyExistsError(CommentError):
    """A client-supplied id collides with an existing comment."""


def comments_path_for(document_path: str) -> str:
    """`notes/article.md` → `notes/article_comments.md`."""
    directory, _, name = document_path.rpartition("/")
    stem = name[:-3] if name.lower().endswith(".md") else name
    target = f"{stem}{COMMENTS_SUFFIX}"
    return f"{directory}/{target}" if directory else target


def is_comments_file(path: str) -> bool:
    return path.lower().endswith(COMMENTS_SUFFIX)


def new_comment_id() -> str:
    return f"c_{secrets.token_hex(3)}"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_comments(text: str) -> tuple[str, list[Comment]]:
    """Return (document, comments) from a comments file body.

    Tolerant by design: unknown metadata keys are kept as body text,
    a missing frontmatter is fine, and prose before the first `## c_…`
    heading is ignored.
    """
    document = ""
    lines = text.splitlines()
    index = 0
    if lines and lines[0].strip() == "---":
        index = 1
        while index < len(lines) and lines[index].strip() != "---":
            match = _META_RE.match(lines[index].strip())
            if match and match.group(1) == "document":
                document = match.group(2).strip()
            index += 1
        index += 1  # closing fence

    comments: list[Comment] = []
    current: Comment | None = None
    body: list[str] = []
    in_meta = False

    def flush() -> None:
        if current is not None:
            current.text = "\n".join(body).strip("\n").strip()
            comments.append(current)

    for line in lines[index:]:
        heading = _HEADING_RE.match(line)
        if heading:
            flush()
            current = Comment(id=heading.group(1))
            body = []
            in_meta = True
            continue
        if current is None:
            continue
        if in_meta:
            meta = _META_RE.match(line.strip())
            if meta and meta.group(1) in _METADATA_KEYS:
                key, value = meta.group(1), meta.group(2).strip()
                if key == "status":
                    current.status = "resolved" if value == "resolved" else "open"
                elif key == "created":
                    current.created = value
                continue
            in_meta = False
            if not line.strip():
                continue  # the blank line separating metadata from body
        body.append(line)
    flush()
    return document, comments


def serialize_comments(document: str, comments: list[Comment]) -> str:
    out = ["---", f"document: {document}", "---"]
    for comment in comments:
        out.append(f"## {comment.id}")
        out.append(f"status: {comment.status}")
        if comment.created:
            out.append(f"created: {comment.created}")
        out.append("")
        if comment.text:
            out.append(comment.text.strip("\n"))
            out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def strip_markers(markdown: str) -> str:
    """Remove every range marker (for renderers that must not see them)."""
    return MARKER_RE.sub("", markdown)


class CommentsService:
    def __init__(self, workspace: WorkspaceService) -> None:
        self.workspace = workspace

    # ── read ────────────────────────────────────────────────────────

    def list_comments(self, document_path: str) -> CommentsDocument:
        backend = self.workspace.get_backend()
        doc_rel = self._resolve_document(document_path, backend)
        comments_rel = comments_path_for(doc_rel)
        if not backend.is_file(comments_rel):
            return CommentsDocument(document=doc_rel, comments_path=comments_rel)
        _, comments = parse_comments(backend.read_text(comments_rel))
        return CommentsDocument(
            document=doc_rel, comments_path=comments_rel, exists=True, comments=comments
        )

    # ── write ───────────────────────────────────────────────────────

    def add_comment(self, document_path: str, text: str, comment_id: str | None = None) -> CommentsDocument:
        self.workspace.block_if_demo()
        backend = self.workspace.get_backend()
        doc_rel = self._resolve_document(document_path, backend)
        current = self.list_comments(doc_rel)
        if comment_id is not None and not COMMENT_ID_RE.match(comment_id):
            raise CommentError("Invalid comment id.")
        if comment_id is None:
            comment_id = new_comment_id()
            while any(c.id == comment_id for c in current.comments):
                comment_id = new_comment_id()
        elif any(c.id == comment_id for c in current.comments):
            raise CommentAlreadyExistsError(f"Comment {comment_id} already exists.")
        current.comments.append(
            Comment(id=comment_id, status="open", created=now_iso(), text=text.strip())
        )
        return self._write(doc_rel, current, backend)

    def update_comment(
        self,
        document_path: str,
        comment_id: str,
        *,
        text: str | None = None,
        status: str | None = None,
    ) -> CommentsDocument:
        self.workspace.block_if_demo()
        backend = self.workspace.get_backend()
        doc_rel = self._resolve_document(document_path, backend)
        current = self.list_comments(doc_rel)
        target = self._find(current, comment_id)
        if text is not None:
            target.text = text.strip()
        if status is not None:
            target.status = "resolved" if status == "resolved" else "open"
        return self._write(doc_rel, current, backend)

    def delete_comment(self, document_path: str, comment_id: str) -> CommentsDocument:
        self.workspace.block_if_demo()
        backend = self.workspace.get_backend()
        doc_rel = self._resolve_document(document_path, backend)
        current = self.list_comments(doc_rel)
        self._find(current, comment_id)
        current.comments = [c for c in current.comments if c.id != comment_id]
        return self._write(doc_rel, current, backend)

    # ── internals ───────────────────────────────────────────────────

    def _resolve_document(self, document_path: str, backend: StorageBackend) -> str:
        rel = self.workspace.resolve_relative_path(document_path, backend)
        if not backend.is_file(rel):
            raise DocumentNotFoundError("Document does not exist.")
        if not rel.lower().endswith(".md"):
            raise InvalidPathError("Comments are only supported on Markdown notes.")
        if is_comments_file(rel):
            raise InvalidPathError("A comments file cannot itself be commented.")
        return rel

    @staticmethod
    def _find(current: CommentsDocument, comment_id: str) -> Comment:
        for comment in current.comments:
            if comment.id == comment_id:
                return comment
        raise CommentNotFoundError(f"Comment {comment_id} not found.")

    def _write(self, doc_rel: str, current: CommentsDocument, backend: StorageBackend) -> CommentsDocument:
        comments_rel = current.comments_path
        if not current.comments:
            # Last comment gone → drop the sidecar instead of leaving an
            # empty shell next to the note.
            if backend.is_file(comments_rel):
                backend.delete(comments_rel)
            return CommentsDocument(document=doc_rel, comments_path=comments_rel, exists=False)
        document_name = doc_rel.rsplit("/", 1)[-1]
        backend.write_text(comments_rel, serialize_comments(document_name, current.comments))
        return CommentsDocument(
            document=doc_rel, comments_path=comments_rel, exists=True, comments=current.comments
        )
