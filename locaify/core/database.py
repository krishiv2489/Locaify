from __future__ import annotations

from datetime import datetime
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

    def __enter__(self) -> Database:
        # this is a special dunder method which is like on_mount(not excatly but close...) so it ensures that when this class is init it  also initialises the connection btw the db
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # no matter what this will ensure that the connection is closed to ensure the integrity of the db contents
        self.disconnect()

    def connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row  # this makes every row behave like a dict...
        self._conn.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")
        self._create_tables()

    def disconnect(self):
        if self._conn is not None:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def _create_tables(self) -> None:
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    @property
    def _cursor(self) -> sqlite3.Cursor:
        if self._conn is None:
            raise RuntimeError("Database is not connected. Use 'with Database(path) as db'.")
        return self._conn.cursor()

    def _row_to_track(self, row: sqlite3.Row) -> Track:
        from locaify.core.models import Track

        return Track(
            id=row["id"],
            path=Path(row["path"]),
            title=row["title"],
            artist=row["artist"],
            duration=row["duration"],
            album=row["album"],
            album_artist=row["album_artist"],
            track_number=row["track_number"],
            disc_number=row["disc_number"],
            year=row["year"],
            genre=row["genre"],
            file_format=row["file_format"],
            has_album_cover=bool(row["has_album_cover"]),
            play_count=row["play_count"],
            has_liked=bool(row["has_liked"]),
            date_added=datetime.fromisoformat(row["date_added"]),
        )

    def insert_track(self, track: Track) -> int:
        # scanner will identify the tracks from a folder and then this function will be called thus it should take the title, artist, album, playlist and path from track dataclass
        cursor = self._cursor
        cursor.execute(
            """
            INSERT OR IGNORE INTO tracks(
                path, title, artist, album, album_artist,
                duration, track_number, disc_number, year, genre,
                file_format, has_album_cover, play_count, has_liked, date_added
            )
            VALUES (
                    ?,?,?,?,?,
                    ?,?,?,?,?,
                    ?,?,?,?,?
                   )
                    """,
            (
                str(track.path),
                track.title,
                track.artist,
                track.album,
                track.album_artist,
                track.duration,
                track.track_number,
                track.disc_number,
                track.year,
                track.genre,
                track.file_format,
                int(track.has_album_cover),
                track.play_count,
                int(track.has_liked),
                track.date_added.isoformat(),
            ),
        )
        self._conn.commit()

        if cursor.lastrowid:
            return cursor.lastrowid

        existing = self._cursor
        existing.execute("SELECT id FROM tracks WHERE path = ?", (str(track.path),))
        row = existing.fetchone()
        return row["id"] if row else -1

    def get_all_tracks(self) -> list[Track]:
        cursor = self._cursor
        cursor.execute("SELECT * FROM tracks ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE")
        return [self._row_to_track(row) for row in cursor.fetchall()]

    def get_track_by_id(self, track_id: int) -> list[Track]:
        # id -> int or even str
        cursor = self._cursor
        cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
        row = cursor.fetchone()
        return self._row_to_track(row) if row else None

    def search_tracks(self, query: str) -> list[Track]:
        # will need a str so that fts5 could search it to database
        if not query.strip():
            return self.get_all_tracks()

        fts_query = f"{query.strip()}*"
        cursor = self._cursor
        cursor.execute(
            "SELECT tracks.* FROM tracks_fts JOIN tracks ON tracks.id = tracks_fts.rowid WHERE tracks_fts MATCH ? ORDER BY rank",
            (fts_query,),
        )
        rows = cursor.fetchall()

        if rows:
            return [self._row_to_track(row) for row in rows]

        # Now like search so that in edge cases if the fts search fails there is a fallback
        like_query = f"%{query.strip()}%"
        cursor.execute(
            "SELECT * FROM tracks WHERE title LIKE ? OR album LIKE ? OR artist LIKE ? ORDER BY artist COLLATE NOCASE",
            (like_query,),
        )

        return [self._row_to_track(row) for row in cursor.fetchall()]

    def record_play(self, track_id: int) -> None:
        # we will calculate how much of the track is heard by using datetime.now and monotime() and all and then in database we will append a str(title / id) and a float(duration) and the playlist
        cursor = self._cursor
        cursor.execute(
            "INSERT INTO history (track_id, played_at) VALUES(?,?)",
            (track_id, datetime.now().isoformat()),
        )
        self.update_play_count(track_id)
        self._conn.commit()

    def get_history(self, limit: int = 50):
        cursor = self._cursor
        cursor.execute(
            "SELECT tracks.* FROM history JOIN tracks on history.track_id = tracks.id ORDER BY history.played_at DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_track(row) for row in cursor.fetchall()]

    def get_history_count(self) -> int:
        cursor = self._cursor
        cursor.execute("SELECT COUNT(*) FROM history")
        return cursor.fetchone()[0]

    def get_track_count(self) -> int:
        cursor = self._cursor
        cursor.execute("SELECT COUNT(*) FROM tracks")
        count = cursor.fetchone()
        return count[0]

    def update_play_count(self, track_id: int) -> None:
        cursor = self._cursor
        cursor.execute("UPDATE tracks SET play_count = play_count + 1 WHERE id = ?", (track_id,))
        self._conn.commit()

    def delete_track(self, track_id: int) -> None:
        self._cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
        self._conn.commit()
