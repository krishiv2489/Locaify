from pathlib import Path

from locaify.core.models import (
    PlaybackState,
    Playlist,
    RepeatMode,
    ScanProgress,
    Track,
)


def make_track(**kwargs) -> Track:
    defaults = {
        "id": 1,
        "path": Path("/music/test.mp3"),
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "duration": 185.0,
    }
    defaults.update(kwargs)
    return Track(**defaults)


def test_track_creation():
    track = make_track()
    assert track.title == "Test Song"
    assert track.artist == "Test Artist"
    assert track.duration == 185.0


def test_track_duration_formatted():
    track = make_track(duration=185.0)
    assert track.duration_formatted == "3:05"


def test_track_duration_formatted_under_one_minute():
    track = make_track(duration=45.0)
    assert track.duration_formatted == "0:45"


def test_track_display_title_falls_back_to_filename():
    track = make_track(title="", path=Path("/music/my_song.mp3"))
    assert track.display_title == "my_song"


def test_track_display_artist_falls_back():
    track = make_track(artist="")
    assert track.display_artist == "Unknown Artist"


def test_track_display_album_falls_back():
    track = make_track(album="")
    assert track.display_album == "Unknown Album"


def test_playlist_track_count():
    tracks = [make_track(id=i, title=f"Track {i}") for i in range(5)]
    playlist = Playlist(id="abc-123", name="My Playlist", tracks=tracks)
    assert playlist.track_count == 5


def test_playlist_total_duration_formatted():
    tracks = [make_track(duration=60.0) for _ in range(3)]
    playlist = Playlist(id="abc-123", name="Test", tracks=tracks)
    assert playlist.total_duration == 180.0
    assert playlist.total_duration_formatted == "3:00"


def test_playlist_total_duration_hours():
    tracks = [make_track(duration=1800.0) for _ in range(3)]
    playlist = Playlist(id="abc-123", name="Long", tracks=tracks)
    assert playlist.total_duration_formatted == "1:30:00"


def test_scan_progress_percentage():
    progress = ScanProgress(scanned=50, total=200, current_path=Path("/music/song.mp3"))
    assert progress.percentage == 25.0


def test_scan_progress_zero_total():
    progress = ScanProgress(scanned=0, total=0, current_path=Path("/music/song.mp3"))
    assert progress.percentage == 0.0


def test_playback_state_enum():
    assert PlaybackState.PLAYING != PlaybackState.PAUSED
    assert PlaybackState.STOPPED != PlaybackState.PLAYING


def test_repeat_mode_enum():
    assert RepeatMode.NONE != RepeatMode.ONE
    assert RepeatMode.ONE != RepeatMode.ALL
