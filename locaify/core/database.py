from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from locaify.core.models import Track

# here we write the whole sturcture of the db anf this way it is cleaner
# TABLES:- tracks, playlists, history
# Then we also create a VIRTUAL TABLE to create indexing for fts5([full text search 5] which is better then just running the raw loops) for searching
_SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL DEFAULT '',
    artist TEXT NOT NULL DEFAULT '',
    duration FLOAT NOT NULL DEFAULT 0.0,
    album TEXT NOT NULL DEFAULT '',
    album_artist TEXT NOT NULL DEFAULT '',
    track_number INTEGER,
    disc_number INTEGER,
    year INTEGER,
    genre TEXT,
    file_format TEXT NOT NULL DEFAULT '',
    has_album_cover INTEGER NOT NULL DEFAULT 0,
    play_count INTEGER NOT NULL DEFAULT 0,
    has_liked INTEGER NOT NULL DEFAULT 0,
    date_added TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS tracks_fts USING fts5(
    title,
    artist,
    album,
    content = tracks,
    content_rowid = id
);

CREATE TRIGGER IF NOT EXISTS tracks_ai
    AFTER INSERT ON tracks BEGIN
        INSERT INTO tracks_fts(rowid, title, artist, album)
        VALUES(new.id, new.title, new.artist, new.album);
    END;

CREATE TRIGGER IF NOT EXISTS tracks_ad
    AFTER DELETE  ON tracks BEGIN
        INSERT INTO tracks_fts(tracks_fts, rowid, title, artist, album)
        VALUES('delete', old.id, old.title, old.artist, old.album);
    END;

CREATE TABLE IF NOT EXISTS history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    played_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS playlists(
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS playlists_tracks(
    playlist_id TEXT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, track_id)
);
"""


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def __enter__(
        self,
    ) -> Database:  # this is a special dunder method which is like on_mount(not excatly but close...) so it ensures that when this class is init it  also initialises the connection btw the db
        self.connect()
        return self

    def __exit__(
        self, exc_type, exc_val, exc_tb
    ) -> None:  # no matter what this will ensure that the connection is closed to ensure the integrity of the db contents
        self.disconnect()

    def connect(self):
        pass

    def disconnect(self):
        pass

    def insert_track(self, track: Track):
        # scanner will identify the tracks from a folder and then this function will be called thus it should take the title, artist, album, playlist and path from track dataclass
        pass

    def get_all_tracks(self):
        pass

    def get_track_by_id(self, track_id: int):
        # id -> int or even str
        pass

    def search_tracks(self, query: str):
        # will need a str so that fts5 could search it to database
        pass

    def record_play(self, track_id: int):
        # we will calculate how much of the track is heard by using datetime.now and monotime() and all and then in database we will append a str(title / id) and a float(duration) and the playlist
        pass

    def get_history(self, limit: int):
        pass


def _track_to_row(track: Track) -> tuple:
    return (
        str(track.path),
        track.title,
        track.artist,
        track.duration,
        track.track_number,
        track.track_title,
        track.genre,
        track.album_artist,
        track.album,
        track.id,
        track.disc_number,
        track.year,
        track.file_format,
    )
