"""Tests for the library scanner."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import wave

import pytest

from locaify.core.database import Database
from locaify.core.models import ScanProgress
from locaify.library.scanner import get_audio_files, scan_directory

# these test the helper functions


def make_wav(path: Path) -> None:
    """Write a minimal valid WAV file to path using stdlib only."""
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(44100)
        f.writeframes(b"\x00\x00" * 4410)  # 0.1 seconds of silence


@pytest.fixture
def db(tmp_path: Path) -> Generator[Database, None, None]:
    """Connected Database instance pointing at a temp file."""
    database = Database(tmp_path / "test.db")
    database.connect()
    yield database
    database.disconnect()


@pytest.fixture
def music_dir(tmp_path: Path) -> Path:
    """A temp directory pre-populated with a small fake music library."""
    root = tmp_path / "Music"
    root.mkdir()

    # Artist A — two albums
    (root / "Artist A" / "Album 1").mkdir(parents=True)
    (root / "Artist A" / "Album 2").mkdir(parents=True)
    make_wav(root / "Artist A" / "Album 1" / "track01.wav")
    make_wav(root / "Artist A" / "Album 1" / "track02.wav")
    make_wav(root / "Artist A" / "Album 2" / "track01.wav")

    # Artist B — one album
    (root / "Artist B" / "Album 1").mkdir(parents=True)
    make_wav(root / "Artist B" / "Album 1" / "track01.wav")
    make_wav(root / "Artist B" / "Album 1" / "track02.wav")

    return root


# get_audio_files


def test_get_audio_files_finds_all_wavs(music_dir: Path) -> None:
    files = get_audio_files(music_dir)
    assert len(files) == 5


def test_get_audio_files_returns_absolute_paths(music_dir: Path) -> None:
    files = get_audio_files(music_dir)
    for f in files:
        assert f.is_absolute(), f"{f} is not absolute"


def test_get_audio_files_returns_sorted(music_dir: Path) -> None:
    files = get_audio_files(music_dir)
    assert files == sorted(files)


def test_get_audio_files_empty_dir(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert get_audio_files(empty) == []


def test_get_audio_files_ignores_non_audio(tmp_path: Path) -> None:
    root = tmp_path / "mixed"
    root.mkdir()
    make_wav(root / "song.wav")
    (root / "cover.jpg").write_bytes(b"fake image")
    (root / "info.txt").write_text("liner notes")
    (root / "thumbs.db").write_bytes(b"windows junk")

    files = get_audio_files(root)
    assert len(files) == 1
    assert files[0].name == "song.wav"


def test_get_audio_files_skips_hidden_directories(tmp_path: Path) -> None:
    root = tmp_path / "Music"
    root.mkdir()
    make_wav(root / "visible.wav")

    # Hidden directory — should be skipped entirely
    hidden = root / ".cache"
    hidden.mkdir()
    make_wav(hidden / "cached.wav")

    files = get_audio_files(root)
    assert len(files) == 1
    assert files[0].name == "visible.wav"


def test_get_audio_files_finds_nested_deeply(tmp_path: Path) -> None:
    # Artist / Year / Album / Disc / track.wav — 4 levels deep
    deep = tmp_path / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    make_wav(deep / "song.wav")
    files = get_audio_files(tmp_path)
    assert len(files) == 1


#  scan_directory


def test_scan_directory_yields_progress(music_dir: Path, db: Database) -> None:
    progress_updates = list(scan_directory(music_dir, db))
    assert len(progress_updates) == 5  # one yield per file


def test_scan_directory_progress_is_scan_progress_type(music_dir: Path, db: Database) -> None:
    for progress in scan_directory(music_dir, db):
        assert isinstance(progress, ScanProgress)


def test_scan_directory_final_progress_is_complete(music_dir: Path, db: Database) -> None:
    updates = list(scan_directory(music_dir, db))
    final = updates[-1]
    assert final.scanned == final.total
    assert final.total == 5


def test_scan_directory_inserts_tracks_into_db(music_dir: Path, db: Database) -> None:
    list(scan_directory(music_dir, db))  # exhaust the generator
    assert db.get_track_count() == 5


def test_scan_directory_empty_dir_yields_nothing(tmp_path: Path, db: Database) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    updates = list(scan_directory(empty, db))
    assert updates == []


def test_scan_directory_rescanning_does_not_duplicate(music_dir: Path, db: Database) -> None:
    list(scan_directory(music_dir, db))
    list(scan_directory(music_dir, db))  # scan again
    # INSERT OR IGNORE means duplicates are silently skipped
    assert db.get_track_count() == 5


#
def test_scan_directory_progress_scanned_increments(music_dir: Path, db: Database) -> None:
    updates = list(scan_directory(music_dir, db))
    scanned_values = [u.scanned for u in updates]
    # Each update should have a higher scanned count than the previous
    assert scanned_values == sorted(scanned_values)
    assert scanned_values[-1] == 5


# test if the starting value of error is 0 so if there are no errors then error == 0
def test_scan_directory_errors_start_at_zero(music_dir: Path, db: Database) -> None:
    # All files are valid WAVs so errors should be 0 throughout
    for progress in scan_directory(music_dir, db):
        assert progress.errors == 0
