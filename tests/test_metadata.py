"""Tests for the metadata reader."""

from __future__ import annotations

from pathlib import Path
import wave

import pytest

from locaify.library.metadata import (
    SUPPORTED_EXTENSIONS,
    _safe_int,
    _safe_str,
    read_metadata,
)

# ── _safe_str tests ──────────────────────────────────────────────────────────


def test_safe_str_none_returns_empty():
    assert _safe_str(None) == ""


def test_safe_str_plain_string():
    assert _safe_str("hello") == "hello"


def test_safe_str_strips_whitespace():
    assert _safe_str("  hello  ") == "hello"


def test_safe_str_list_takes_first():
    assert _safe_str(["Queen", "David Bowie"]) == "Queen"


def test_safe_str_empty_list_returns_empty():
    assert _safe_str([]) == ""


def test_safe_str_exception_returns_empty():
    # object with broken __str__ — safe_str must not crash
    class Broken:
        def __str__(self):
            raise RuntimeError("broken")

    assert _safe_str(Broken()) == ""


# ── _safe_int tests ──────────────────────────────────────────────────────────


def test_safe_int_plain_number_string():
    assert _safe_int("5") == 5


def test_safe_int_track_slash_total():
    # "3/12" → 3
    assert _safe_int("3/12") == 3


def test_safe_int_none_returns_zero():
    assert _safe_int(None) == 0


def test_safe_int_empty_string_returns_zero():
    assert _safe_int("") == 0


def test_safe_int_non_numeric_returns_zero():
    assert _safe_int("banana") == 0


# ── SUPPORTED_EXTENSIONS ─────────────────────────────────────────────────────


def test_supported_extensions_contains_expected():
    assert ".mp3" in SUPPORTED_EXTENSIONS
    assert ".flac" in SUPPORTED_EXTENSIONS
    assert ".ogg" in SUPPORTED_EXTENSIONS
    assert ".wav" in SUPPORTED_EXTENSIONS
    assert ".m4a" in SUPPORTED_EXTENSIONS
    assert ".aac" in SUPPORTED_EXTENSIONS


def test_supported_extensions_excludes_junk():
    assert ".txt" not in SUPPORTED_EXTENSIONS
    assert ".jpg" not in SUPPORTED_EXTENSIONS
    assert ".pdf" not in SUPPORTED_EXTENSIONS


# ── read_metadata: unsupported format ────────────────────────────────────────


def test_read_metadata_unsupported_format_raises(tmp_path: Path):
    fake = tmp_path / "file.xyz"
    fake.write_bytes(b"not audio")
    with pytest.raises(ValueError, match="Unsupported format"):
        read_metadata(fake)


# ── read_metadata: fallback on corrupted file ────────────────────────────────


def test_read_metadata_corrupt_file_returns_fallback(tmp_path: Path):
    # A file with .mp3 extension but garbage bytes — mutagen will fail
    bad_mp3 = tmp_path / "corrupt.mp3"
    bad_mp3.write_bytes(b"this is not valid mp3 data at all")

    track = read_metadata(bad_mp3)

    # Should not raise — should return a fallback Track
    assert track.title == "corrupt"  # falls back to path.stem
    assert track.artist == "Unknown Artist"
    assert track.duration == 0.0
    assert track.file_format == "mp3"


# ── read_metadata: real WAV file (stdlib — no external deps needed) ──────────


def _make_wav(path: Path) -> None:
    """Create a minimal valid WAV file using Python's stdlib wave module."""
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)  # mono
        f.setsampwidth(2)  # 16-bit
        f.setframerate(44100)  # CD quality sample rate
        f.writeframes(b"\x00\x00" * 4410)


def test_read_metadata_wav_returns_track(tmp_path: Path):
    wav_path = tmp_path / "silence.wav"
    _make_wav(wav_path)

    track = read_metadata(wav_path)

    assert track.path == wav_path
    assert track.file_format == "wav"
    assert track.duration > 0.0
    assert track.title == "silence"  # no tags → falls back to filename
    assert track.artist == "Unknown Artist"


def test_read_metadata_wav_id_is_zero(tmp_path: Path):
    wav_path = tmp_path / "silence.wav"
    _make_wav(wav_path)

    track = read_metadata(wav_path)
    # id=0 is the placeholder — real id comes from the database on insert
    assert track.id == 0


def test_read_metadata_wav_has_album_cover_is_bool(tmp_path: Path):
    wav_path = tmp_path / "silence.wav"
    _make_wav(wav_path)

    track = read_metadata(wav_path)
    assert isinstance(track.has_album_cover, bool)
