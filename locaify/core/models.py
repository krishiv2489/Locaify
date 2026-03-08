"""
This is the file where all the variable and all are define and it will be used to call and used as a common across the entire app
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class RepeatMode(Enum):
    NONE = auto()
    ONCE = auto()
    ALL = auto()


class PlaybackState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    LOADING = auto()
    ERROR = auto()


@dataclass
class Track:
    id: int
    path: Path
    title: str
    artist: str
    duration: float
    album: str
    album_artist: str = ""
    track_number: int | None = None
    disc_number: int | None = None
    year: int | None = None
    genre: str | None = None
    file_format: str = ""
    has_album_cover: bool = False
    play_count: int = 0
    has_liked: bool = False
    date_added: datetime = field(default_factory=datetime.now)


@property
def display_title(self) -> str:
    return self.title if self.title.strip() else self.path.stem


@property
def display_artist(self) -> str:
    return self.artist if self.artist.strip() else "Unknown Artist"


@property
def display_album(self) -> str:
    return self.album if self.album.strip() else "Unknown Album"


@property
def duration_formatted(self) -> str:
    min = int(self.duration // 60)
    sec = int(self.duration % 60)
    return f"{min}:{sec:02d}"


@dataclass
class Playlist:
    """
    Stored as a JSON file at:
    ~/.config/locaify/playlists/{id}.json
    """

    id: str
    name: str
    tracks: list[Track] = field(default_factory=list)
    date_created: datetime = field(default_factory=datetime.now)
    date_modified: datetime = field(default_factory=datetime.now)

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def total_duration(self) -> float:
        return sum(t.duration for t in self.tracks)

    @property
    def total_duration_formatted(self) -> str:
        total = int(self.total_duration)
        hours = total // 3600
        min = (total % 3600) // 60
        sec = total % 60
        if hours > 0:
            return f"{hours}:{min:02d}:{sec:02d}"
        return f"{min}:{sec:02d}"


@dataclass
class ScanProgress:
    scanned: int
    total: int
    current_path: Path
    errors: int = 0

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.scanned / self.total) * 100
