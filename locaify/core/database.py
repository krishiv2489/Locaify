from pathlib import Path

from locaify.core.models import (
    Track,
)


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path

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
