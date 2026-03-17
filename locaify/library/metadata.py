from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from locaify.core.models import Track

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac"}  # type: ignore


def read_metadata(path: Path) -> Track:
    # this func will take path and then apply the right helper function to extract all the details
    suffix = path.suffix.lower()

    dispatch = {
        ".mp3": _read_mp3,
        ".flac": _read_flac,
        ".ogg": _read_ogg,
        ".m4a": _read_mp4,
        ".aac": _read_mp4,  # same MP4 containerz
        ".wav": _read_wav,
    }

    reader = dispatch.get(suffix)

    if reader is None:
        raise ValueError(f"Unsupported format: {suffix}")

    try:
        return reader(path)
    except Exception:
        #         fallback option so that the ui doesn't crash
        from locaify.core.models import Track

        return Track(
            id=0,
            path=path,
            title=path.stem,
            artist="Unknown Artist",
            album="Unknown Album",
            file_format=suffix.lstrip("."),
            duration=0.0,
        )


def _read_mp3(path: Path) -> Track:
    from mutagen.mp3 import MP3

    from locaify.core.models import Track

    audio = MP3(path)
    tags = audio.tags

    def get(key):
        if tags and key in tags:
            return tags[key]
        return None

    return Track(
        id=0,
        path=path,
        title=_safe_str(get("TIT2")) or path.stem,
        artist=_safe_str(get("TPE1")) or "Unknown Artist",
        album=_safe_str(get("TALB")) or "Unknown Album",
        album_artist=_safe_str(get("TPE2")),
        duration=audio.info.length,
        genre=_safe_str(get("TCON")),
        track_number=_safe_int(get("TRCK")),
        disc_number=_safe_int(get("TPOS")),
        year=_safe_int(get("TDRC")) or _safe_int(get("TYER")),
        file_format="mp3",
        has_album_cover=_has_cover_art(audio),
    )


def _read_flac(path: Path) -> Track:
    from mutagen.flac import FLAC

    from locaify.core.models import Track

    audio = FLAC(path)

    def get(key):
        return audio.get(key)

    return Track(
        id=0,
        path=path,
        title=_safe_str(get("title")) or path.stem,
        artist=_safe_str(get("artist")) or "Unknown Artist",
        album=_safe_str(get("album")) or "Unknown Album",
        album_artist=_safe_str(get("albumartist")),
        duration=audio.info.length,
        genre=_safe_str(get("genre")),
        track_number=_safe_int(get("tracknumber")),
        disc_number=_safe_int(get("discnumber")),
        year=_safe_int(get("date")),
        file_format="flac",
        has_album_cover=_has_cover_art(audio),
    )


def _read_ogg(path: Path) -> Track:
    from mutagen.oggvorbis import OggVorbis

    from locaify.core.models import Track

    audio = OggVorbis(path)

    def get(key):
        return audio.get(key)

    return Track(
        id=0,
        path=path,
        title=_safe_str(get("title")) or path.stem,
        artist=_safe_str(get("artist")) or "Unknown Artist",
        album=_safe_str(get("album")) or "Unknown Album",
        album_artist=_safe_str(get("albumartist")),
        duration=audio.info.length,
        genre=_safe_str(get("genre")),
        track_number=_safe_int(get("tracknumber")),
        disc_number=_safe_int(get("discnumber")),
        year=_safe_int(get("date")),
        file_format="ogg",
        has_album_cover=False,
    )


def _read_mp4(path: Path) -> Track:
    from mutagen.mp4 import MP4

    from locaify.core.models import Track

    audio = MP4(path)

    def get(key):
        return audio.get(key)

    return Track(
        # \xa9 -> escape code for: ©
        # so iTunes stores the name of the song as @nam and artist name as @art
        # But we use escape code instead of hardcore...
        id=0,
        path=path,
        title=_safe_str(get("\xa9nam")) or path.stem,
        artist=_safe_str(get("\xa9ART")) or "Unknown Artist",
        album=_safe_str(get("\xa9alb")) or "Unknown Album",
        album_artist=_safe_str(get("aART")),
        duration=audio.info.length,
        genre=_safe_str(get("\xa9gen")),
        track_number=_safe_int(get("trkn")),
        disc_number=_safe_int(get("disk")),
        year=_safe_int(get("\xa9day")),
        file_format="mp4",
        has_album_cover=False,
    )


def _read_wav(path: Path) -> Track:
    from mutagen.wave import WAVE

    from locaify.core.models import Track

    audio = WAVE(path)
    tags = audio.tags

    def get(key):
        if tags and key in tags:
            return tags[key]
        return None

    return Track(
        id=0,
        path=path,
        title=_safe_str(get("TIT2")) or path.stem,
        artist=_safe_str(get("TPE1")) or "Unknown Artist",
        album=_safe_str(get("TALB")) or "Unknown Album",
        album_artist=_safe_str(get("TPE2")),
        duration=audio.info.length,
        genre=_safe_str(get("TCON")),
        track_number=_safe_int(get("TRCK")),
        disc_number=_safe_int(get("TPOS")),
        year=_safe_int(get("TDRC")) or _safe_int(get("TYER")),
        file_format="wav",
        has_album_cover=_has_cover_art(audio),
    )


def _safe_str(value) -> str:
    if value is None:
        return ""

    try:
        if hasattr(value, "text"):
            return str(value.text[0]).strip()
        if isinstance(value, list):
            return str(value[0]).strip() if value else ""
        return str(value).strip()
    except Exception:
        return ""


def _safe_int(value) -> int:
    raw = _safe_str(value)

    try:
        return int(raw.split("/")[0])
    except (ValueError, IndexError):
        return 0


def _has_cover_art(audio) -> bool:
    try:
        if hasattr(audio, "tags") and audio.tags:
            if any(k.startswith("APIC") for k in audio.tags.keys()):
                return True

        if hasattr(audio, "pictures"):
            return len(audio.pictures) > 0

        if "covr" in audio:
            return True

    except Exception:
        pass

    return False
