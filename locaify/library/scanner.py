from __future__ import annotations

from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

from locaify.library.metadata import SUPPORTED_EXTENSIONS, read_metadata

if TYPE_CHECKING:
    from locaify.core.database import Database
    from locaify.core.models import ScanProgress


def get_audio_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for path in root.rglob("*"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return sorted(files)


def scan_directory(
    root: Path, db: Database, max_worker: int = 4
) -> Generator[
    ScanProgress, None, None
]:  # Generator syntax --> Generator[YieldType, SendType, ReturnType]
    from locaify.core.models import ScanProgress

    audio_files = get_audio_files(root)
    total = len(audio_files)

    if total == 0:
        return
    scanned = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=max_worker) as executor:
        future_to_path = {executor.submit(read_metadata, path): path for path in audio_files}

        for future in as_completed(future_to_path):
            path = future_to_path[future]

            try:
                track = future.result()
                db.insert_track(track)

            except Exception:
                errors += 1

            scanned += 1

            yield ScanProgress(
                scanned=scanned,
                total=total,
                current_path=path,
                errors=errors,
            )
