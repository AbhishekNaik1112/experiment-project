"""Read OKF bundle files from a directory or a zip. Shared by ingest and validate."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BundleEntry:
    rel_path: str
    text: str


def read_dir(dir_path: str) -> tuple[str, list[BundleEntry]]:
    """Return (bundle_name, entries) for every .md under dir_path. Raises ValueError if not a dir."""
    root = Path(dir_path)
    if not root.is_dir():
        raise ValueError(f"not a directory: {dir_path}")
    entries = [
        BundleEntry(p.relative_to(root).as_posix(), p.read_text(encoding="utf-8"))
        for p in sorted(root.rglob("*.md"))
    ]
    return root.name, entries


def read_zip(data: bytes) -> list[BundleEntry]:
    entries: list[BundleEntry] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith("/") or not name.lower().endswith(".md"):
                continue
            entries.append(BundleEntry(name, zf.read(name).decode("utf-8")))
    return entries
