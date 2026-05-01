"""Application package for Noteeli."""
from __future__ import annotations

import tomllib
from pathlib import Path


def _read_version() -> str:
    """Read the project version straight from pyproject.toml.

    Cheap (one file read at import time) and avoids importlib.metadata,
    which only works once the package is properly installed."""
    try:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        with pyproject.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "0.0.0+unknown"


__version__ = _read_version()
