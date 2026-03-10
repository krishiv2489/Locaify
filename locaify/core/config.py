from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from platformdirs import user_config_dir

if sys.version_info >= (3, 11):
    pass
else:
    pass


def _get_config_dir() -> Path:
    import os

    override = os.environ.get("LOCAIFY_CONFIG_DIR")
    if override:
        return Path(override)
    return Path(user_config_dir("locaify"))


def _get_config_path() -> Path:
    return _get_config_dir() / "config.toml"


@dataclass
class PlayerConfig:
    volume: int = 80
    suffle: bool = False
    repeat_mode: str = "none"
    audio_backend: str = "auto"
