from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import pytest

from locaify.core.database import Database
from locaify.core.models import Track


# kwargs allow you to pass as many args as you like, but it gives the function in dict type
# this test function creates a track or returns a default Track object if fields are empty.
def make_track(**kwargs) -> Track:
    defaults = {
        "id": 0,
        "path": Path("/music/test.mp3"),
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "duration": 185.0,
        "date_added": datetime.now(),
    }
    defaults.update(kwargs)
    return Track(**defaults)


# this func creates a tmp .db file just for the test purpose
@pytest.fixture
def db(tmp_path: Path) -> Generator[Database, None, None]:
    database = Database(tmp_path / "test.db")
    database.connect()
    yield database
    database.disconnect()


# this func checks if there is no .db file, and we try to connect then will the .connect() method create one
def test_connect_creates_database_file(tmp_path: Path) -> None:
    db_path = tmp_path / "library.db"
    with Database(db_path) as _:
        assert db_path.exists()


# checks if the insert track func returns an id
def test_insert_track_returns_id(db: Database) -> None:
    track = make_track()
    track_id = db.insert_track(track)
    assert track_id > 0


# tests if the duplicate path safety thing works or not
def test_insert_same_track_twice_no_duplicate(db: Database) -> None:
    track = make_track()
    db.insert_track(track)
    db.insert_track(track)
    assert db.get_track_count() == 1


# tests if there is no tracks in the db then will it return an empty list
def test_get_all_tracks_empty(db: Database) -> None:
    assert db.get_all_tracks() == []


# tests if the get_all_track works properly
def test_get_all_tracks_returns_inserted(db: Database) -> None:
    db.insert_track(make_track(title="Song A", artist="Artist A"))
    db.insert_track(make_track(title="Song B", artist="Artist B", path=Path("/music/b.mp3")))
    tracks = db.get_all_tracks()
    assert len(tracks) == 2


# tests if the get_track_by_id returns id
def test_get_track_by_id(db: Database) -> None:
    track_id = db.insert_track(make_track(title="Find Me"))
    result = db.get_track_by_id(track_id)
    assert result is not None
    assert result.title == "Find Me"


# tests if it returns None if there is not matching ID in db tables
def test_get_track_by_id_not_found(db: Database) -> None:
    result = db.get_track_by_id(9999)
    assert result is None


def test_track_path_survives_round_trip(db: Database) -> None:
    path = Path("/home/krishiv/Music/queen/bohemian.mp3")
    track_id = db.insert_track(make_track(path=path))
    result = db.get_track_by_id(track_id)
    assert result.path == path


# tests if we search by the title it works or not
def test_search_tracks_finds_by_title(db: Database) -> None:
    db.insert_track(make_track(title="Bohemian Rhapsody", artist="Queen"))
    db.insert_track(
        make_track(
            title="Stairway to Heaven", artist="Led Zeppelin", path=Path("/music/stairway.mp3")
        )
    )
    results = db.search_tracks("bohemian")
    assert len(results) == 1
    assert results[0].title == "Bohemian Rhapsody"


# tests if we search by the artist it still works or not
def test_search_tracks_finds_by_artist(db: Database) -> None:
    db.insert_track(make_track(title="Bohemian Rhapsody", artist="Queen"))
    results = db.search_tracks("queen")
    assert len(results) == 1


# tests if the empty search return get_all_track
def test_search_empty_query_returns_all(db: Database) -> None:
    db.insert_track(make_track(title="Song A"))
    db.insert_track(make_track(title="Song B", path=Path("/music/b.mp3")))
    assert len(db.search_tracks("")) == 2


# tests if the record_play method inserts the track into history table
def test_record_play_inserts_history(db: Database) -> None:
    track_id = db.insert_track(make_track())
    db.record_play(track_id)
    assert db.get_history_count() == 1


# tests if the play_count increment works
def test_record_play_increments_play_count(db: Database) -> None:
    track_id = db.insert_track(make_track())
    db.record_play(track_id)
    db.record_play(track_id)
    track = db.get_track_by_id(track_id)
    assert track.play_count == 2


# tests if the history returns in the most recent order or not
def test_get_history_returns_most_recent_first(db: Database) -> None:
    track_a_id = db.insert_track(make_track(title="First", path=Path("/music/a.mp3")))
    track_b_id = db.insert_track(make_track(title="Second", path=Path("/music/b.mp3")))
    db.record_play(track_a_id)
    db.record_play(track_b_id)
    history = db.get_history()
    assert history[0].title == "Second"
    assert history[1].title == "First"


# tests if the deletee track works
def test_delete_track_removes_from_library(db: Database) -> None:
    track_id = db.insert_track(make_track())
    db.delete_track(track_id)
    assert db.get_track_by_id(track_id) is None
    assert db.get_track_count() == 0


# tests if the exit dunder method closes the db
def test_context_manager_closes_connection(tmp_path: Path) -> None:
    db_path = tmp_path / "library.db"
    with Database(db_path) as _:
        db.insert_track(make_track())
    assert db._conn is None
