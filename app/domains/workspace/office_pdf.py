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
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

from app.core.config import Settings

logger = logging.getLogger(__name__)

CONVERTIBLE_SUFFIXES = {".pptx", ".ppt", ".odp", ".docx", ".doc", ".odt", ".xlsx", ".xls", ".ods"}
CACHE_DIR_NAME = "office-pdf-cache"
CACHE_MAX_FILES = 200
CONVERT_TIMEOUT_SECONDS = 120

# Portable LibreOffice, fetched by the app itself when no system install
# exists: an AppImage unpacked with `--appimage-extract` (no FUSE, no
# root) under <data_dir>/libreoffice. LibreItalia publishes the official
# AppImages under stable, unversioned names.
PORTABLE_DIR_NAME = "libreoffice"
PORTABLE_APPIMAGE_URL = "https://appimages.libreitalia.org/LibreOffice-still.basic-x86_64.AppImage"
PORTABLE_APPIMAGE_NAME = "LibreOffice.AppImage"
PORTABLE_RUNNER = Path("squashfs-root") / "AppRun"
PORTABLE_MIN_BYTES = 50 * 1024 * 1024


class OfficeConversionError(Exception):
    """LibreOffice is present but the conversion did not produce a PDF."""


class OfficePdfConverter:
    _lock = threading.Lock()
    _install_lock = threading.Lock()

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._executable: str | None | bool = False  # False = not looked up yet
        self._install: dict = {"state": "idle", "received": 0, "total": 0, "error": ""}
        self._install_thread: threading.Thread | None = None

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
        portable = self.portable_runner
        if portable.is_file() and os.access(portable, os.X_OK):
            return str(portable)
        return None

    def kind(self) -> str | None:
        """'portable' for the app-fetched AppImage, 'system' for anything
        else that works, None when there is no converter."""
        exe = self.executable()
        if exe is None:
            return None
        return "portable" if Path(exe) == self.portable_runner else "system"

    # ── portable install ────────────────────────────────────────────

    @property
    def portable_dir(self) -> Path:
        return Path(self.settings.data_dir) / PORTABLE_DIR_NAME

    @property
    def portable_runner(self) -> Path:
        return self.portable_dir / PORTABLE_RUNNER

    @staticmethod
    def portable_supported() -> bool:
        return sys.platform.startswith("linux") and platform.machine() in ("x86_64", "AMD64")

    def install_status(self) -> dict:
        return {**self._install, "available": self.available(), "kind": self.kind(),
                "portable_supported": self.portable_supported()}

    def start_portable_install(self) -> dict:
        """Kick off the download + unpack in a background thread (no-op
        when one is already running or a converter already exists)."""
        if self.available():
            return self.install_status()
        if not self.portable_supported():
            self._install = {"state": "error", "received": 0, "total": 0,
                             "error": "Portable LibreOffice is only available for Linux x86_64."}
            return self.install_status()
        with self._install_lock:
            if self._install_thread and self._install_thread.is_alive():
                return self.install_status()
            self._install = {"state": "downloading", "received": 0, "total": 0, "error": ""}
            self._install_thread = threading.Thread(target=self._run_portable_install, daemon=True)
            self._install_thread.start()
        return self.install_status()

    def _run_portable_install(self) -> None:
        try:
            self.portable_dir.mkdir(parents=True, exist_ok=True)
            appimage = self.portable_dir / PORTABLE_APPIMAGE_NAME
            self._download(PORTABLE_APPIMAGE_URL, appimage)
            if appimage.stat().st_size < PORTABLE_MIN_BYTES:
                raise OfficeConversionError("The downloaded file is too small to be LibreOffice.")
            self._install["state"] = "extracting"
            self._extract(appimage)
            if not self.portable_runner.is_file():
                raise OfficeConversionError("The AppImage did not unpack into squashfs-root/AppRun.")
            appimage.unlink(missing_ok=True)  # the unpacked tree is what runs
            self._executable = False  # re-detect
            self._install = {"state": "ready", "received": 0, "total": 0, "error": ""}
            logger.info("Portable LibreOffice installed at %s", self.portable_runner)
        except Exception as exc:  # noqa: BLE001 — surfaced to the UI
            logger.warning("Portable LibreOffice install failed: %s", exc)
            self._install = {"state": "error", "received": 0, "total": 0, "error": str(exc)}

    def _download(self, url: str, target: Path) -> None:
        request = urllib.request.Request(url, headers={"User-Agent": "Noteeli"})
        with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            self._install["total"] = total
            received = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                received += len(chunk)
                self._install["received"] = received

    def _extract(self, appimage: Path) -> None:
        appimage.chmod(appimage.stat().st_mode | 0o755)
        shutil.rmtree(self.portable_dir / "squashfs-root", ignore_errors=True)
        completed = subprocess.run(
            [str(appimage), "--appimage-extract"],
            cwd=str(self.portable_dir),
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()[-400:]
            raise OfficeConversionError(f"Unpacking the AppImage failed (exit {completed.returncode}). {detail}")

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
