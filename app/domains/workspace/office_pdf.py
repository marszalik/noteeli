"""Faithful office previews via LibreOffice.

python-pptx can only pull text and pictures out of a deck; the result is
a column of white cards that looks nothing like the slides. When a
LibreOffice binary is around, a .pptx is instead converted to PDF
(`soffice --headless --convert-to pdf`) and shown in the browser's PDF
viewer — layout, fonts, backgrounds, charts and all. Without LibreOffice
the text cards remain as the fallback, so nothing is lost on machines
that never install it.

Conversions are cached under <data_dir>/office-pdf-cache keyed by the
file's content hash: re-opening a deck costs one stat, and an edited
deck is converted again. LibreOffice dislikes running twice at once
(profile locks), so conversions are serialised with a lock and run with
a private user profile.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from app.core.config import Settings

CONVERTIBLE_SUFFIXES = {".pptx", ".ppt", ".odp", ".docx", ".doc", ".odt", ".xlsx", ".xls", ".ods"}
CACHE_DIR_NAME = "office-pdf-cache"
CACHE_MAX_FILES = 200
CONVERT_TIMEOUT_SECONDS = 120


class OfficeConversionError(Exception):
    """LibreOffice is present but the conversion did not produce a PDF."""


class OfficePdfConverter:
    _lock = threading.Lock()

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._executable: str | None | bool = False  # False = not looked up yet

    # ── availability ────────────────────────────────────────────────

    def executable(self) -> str | None:
        if self._executable is False:
            self._executable = self._find_executable()
        return self._executable  # type: ignore[return-value]

    def available(self) -> bool:
        return self.executable() is not None

    def _find_executable(self) -> str | None:
        configured = (self.settings.office_converter or "").strip()
        if configured.lower() in ("off", "none", "0", "false"):
            return None
        if configured:
            path = Path(configured).expanduser()
            if path.is_file():
                return str(path)
            return shutil.which(configured)
        for candidate in ("soffice", "libreoffice"):
            found = shutil.which(candidate)
            if found:
                return found
        for candidate in ("/usr/lib/libreoffice/program/soffice", "/opt/libreoffice/program/soffice",
                          "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
            if Path(candidate).is_file():
                return candidate
        return None

    # ── conversion ──────────────────────────────────────────────────

    @property
    def cache_dir(self) -> Path:
        return Path(self.settings.data_dir) / CACHE_DIR_NAME

    def convert_to_pdf(self, data: bytes, suffix: str) -> Path:
        """Return a cached PDF rendering of `data` (an office file with
        extension `suffix`), converting it first when needed."""
        exe = self.executable()
        if exe is None:
            raise OfficeConversionError("No LibreOffice executable is available.")
        suffix = suffix.lower() if suffix.startswith(".") else f".{suffix.lower()}"
        key = hashlib.sha256(data).hexdigest()[:40]
        cache_dir = self.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        target = cache_dir / f"{key}.pdf"
        if target.is_file():
            target.touch()  # LRU bookkeeping
            return target

        with self._lock:
            if target.is_file():
                return target
            with tempfile.TemporaryDirectory(prefix="noteeli-office-") as tmp:
                work = Path(tmp)
                source = work / f"{key}{suffix}"
                source.write_bytes(data)
                profile = work / "profile"
                command = [
                    exe,
                    "--headless",
                    "--norestore",
                    "--nologo",
                    "--nolockcheck",
                    f"-env:UserInstallation={profile.as_uri()}",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(work),
                    str(source),
                ]
                try:
                    completed = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=CONVERT_TIMEOUT_SECONDS,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise OfficeConversionError(f"LibreOffice failed to run: {exc}") from exc
                produced = work / f"{key}.pdf"
                if completed.returncode != 0 or not produced.is_file():
                    detail = (completed.stderr or completed.stdout or "").strip()[-400:]
                    raise OfficeConversionError(
                        f"LibreOffice did not produce a PDF (exit {completed.returncode}). {detail}"
                    )
                shutil.move(str(produced), str(target))
            self._prune(cache_dir)
        return target

    @staticmethod
    def _prune(cache_dir: Path) -> None:
        pdfs = sorted(cache_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime)
        for stale in pdfs[: max(0, len(pdfs) - CACHE_MAX_FILES)]:
            try:
                stale.unlink()
            except OSError:
                pass
