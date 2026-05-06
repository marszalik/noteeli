"""Service layer for the public-publish feature.

Lets the user expose a single file or a whole folder under a stable
public URL on the same Noteeli instance — read-only, no auth, no
mutation. Everything else (write actions, the rest of the file tree)
remains hidden behind the regular auth flow.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.core.config import Settings, get_settings
from app.domains.publish.repository import PublishedItemsRepository
from app.domains.publish.schemas import PublishedItem


class PublishError(Exception):
    """Base class for publish-domain errors."""


class PublishedItemNotFoundError(PublishError):
    pass


class PublishedItemAlreadyExistsError(PublishError):
    pass


class PublishService:
    def __init__(
        self,
        settings: Settings | None = None,
        repository: PublishedItemsRepository | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.repository = repository or PublishedItemsRepository(self.settings)

    # ── Slug generation ──────────────────────────────────────────

    @staticmethod
    def slugify(value: str) -> str:
        """Convert an arbitrary file/folder name into a URL-safe slug.

        - drops the file extension
        - normalises diacritics (Polish ł → l, ą → a, etc.)
        - keeps only [a-z0-9-]
        - falls back to "item" for empty results
        """
        # Strip a single trailing extension (.md, .png, …) — keep dots in
        # the middle of the name in case someone uses them on purpose.
        stem = Path(value).stem if "." in value else value
        # ASCII-fold common diacritics by stripping combining marks.
        import unicodedata

        normalized = unicodedata.normalize("NFKD", stem)
        ascii_only = "".join(
            ch for ch in normalized if not unicodedata.combining(ch)
        )
        # Manual map for letters that NFKD doesn't decompose (Ł, Ø, …)
        ascii_only = (
            ascii_only
            .replace("ł", "l").replace("Ł", "L")
            .replace("ø", "o").replace("Ø", "O")
            .replace("đ", "d").replace("Đ", "D")
        )
        lowered = ascii_only.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
        return slug or "item"

    # ── Public reads ─────────────────────────────────────────────

    def list_published(self) -> list[PublishedItem]:
        rows = self.repository.list_all()
        return [self._row_to_item(row) for row in rows]

    def find_by_id(self, item_id: int) -> PublishedItem:
        row = self.repository.find_by_id(item_id)
        if row is None:
            raise PublishedItemNotFoundError(
                f"Published item #{item_id} does not exist."
            )
        return self._row_to_item(row)

    def find_by_path(self, path: str) -> PublishedItem | None:
        row = self.repository.find_by_path(path)
        return self._row_to_item(row) if row is not None else None

    def published_paths(self) -> dict[str, int]:
        """Map of path → item id for every published entry. The frontend
        uses this to render a globe badge on the matching tree rows."""
        return {row["path"]: row["id"] for row in self.repository.list_all()}

    # ── Mutations ────────────────────────────────────────────────

    def publish(self, kind: str, path: str) -> PublishedItem:
        existing = self.repository.find_by_path(path)
        if existing is not None:
            raise PublishedItemAlreadyExistsError(
                f"'{path}' is already published as #{existing['id']}."
            )

        if kind not in ("file", "directory"):
            raise PublishError(f"Invalid kind: {kind!r}")

        # Use the basename to generate a slug — the server can match on
        # the id, the slug is purely cosmetic.
        basename = Path(path).name or "item"
        slug = self.slugify(basename)
        item_id = self.repository.insert(kind, path, slug)
        return PublishedItem(
            id=item_id,
            kind=kind,
            path=path,
            slug=slug,
            created_at="",  # populated by the row read on next list
            public_url=self._public_url(item_id, slug),
        )

    def unpublish(self, item_id: int) -> None:
        deleted = self.repository.delete_by_id(item_id)
        if deleted == 0:
            raise PublishedItemNotFoundError(
                f"Published item #{item_id} does not exist."
            )

    def cleanup_for_removed_path(self, path: str) -> int:
        """Remove publish entries whose target was renamed or deleted."""
        return self.repository.delete_by_path_prefix(path)

    # ── Path scoping ─────────────────────────────────────────────

    @staticmethod
    def is_in_scope(item: PublishedItem, requested_path: str) -> bool:
        """A request to view a file inside a published item must stay
        inside the published path. Files have a single allowed path
        (the file itself); directories allow any descendant."""
        if not requested_path:
            return item.kind == "directory" or requested_path == item.path
        # Normalise — strip leading slashes, collapse double slashes.
        clean = "/".join(part for part in requested_path.split("/") if part)
        if item.kind == "file":
            return clean == item.path
        # Directory: descendant or self.
        if clean == item.path:
            return True
        prefix = item.path + "/"
        return clean.startswith(prefix)

    # ── Internal helpers ─────────────────────────────────────────

    def _row_to_item(self, row) -> PublishedItem:
        slug = row["slug"]
        return PublishedItem(
            id=row["id"],
            kind=row["kind"],
            path=row["path"],
            slug=slug,
            created_at=row["created_at"],
            public_url=self._public_url(row["id"], slug),
        )

    def _public_url(self, item_id: int, slug: str) -> str:
        return f"/{item_id}/{slug}"
