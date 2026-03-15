from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from locaify.core.models import Track

SUPPORTED_EXTENTIONS = {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac"}  # type: ignore


def read_metadata(path: Path) -> Track:
    # this func will take path and then apply the right helper function to extract all the details
    pass


def _read_mp3():
    pass


def _read_flac():
    pass


def _read_ogg():
    pass


def _read_mp4():
    pass


def _read_wav():
    pass


def _safe_str():
    pass


def _safe_int():
    pass


def _has_cover_art():
    pass
