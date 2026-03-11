from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import sys

from platformdirs import user_config_dir

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


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
    shuffle: bool = False
    repeat_mode: str = "none"
    audio_backend: str = "auto"


@dataclass
class LibraryConfig:
    root_dirs: list[str] = field(default_factory=list)
    watch_for_changes: bool = True


@dataclass
class UIConfig:
    theme: str = "catppuccin"
    show_album_art: bool = True
    art_width: int = 20
    show_visualizer: bool = True


@dataclass
class IntegrationsConfig:
    lastfm_enabled: bool = False
    lastfm_username: str = ""
    lyrics_enabled: bool = True
    notifications_enabled: bool = False


@dataclass
class LocaifyConfig:
    player: PlayerConfig = field(default_factory=PlayerConfig)
    library: LibraryConfig = field(default_factory=LibraryConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)


def _dict_to_config(data: dict) -> LocaifyConfig:
    player_data = data.get(
        "player", {}
    )  # this makes sure that if the player doesnt exist then it makes it empty dict and not throw error
    library_data = data.get("library", {})
    ui_data = data.get("ui", {})
    integrations_data = data.get("integrations", {})

    return LocaifyConfig(
        player=PlayerConfig(
            volume=int(
                player_data.get("volume", 80)
            ),  # dictionary.get(key, default_if_missing) thus 80 is default fall back option... if volume is empty
            shuffle=bool(player_data.get("shuffle", False)),
            repeat_mode=str(player_data.get("repeat_mode", "none")),
            audio_backend=str(player_data.get("audio_backend", "auto")),
        ),
        library=LibraryConfig(
            root_dirs=list(library_data.get("root_dirs", [])),
            watch_for_changes=bool(library_data.get("watch_for_changes", True)),
        ),
        ui=UIConfig(
            theme=str(ui_data.get("theme", "catppuccin")),
            show_album_art=bool(ui_data.get("show_album_art", True)),
            art_width=int(ui_data.get("art_width", 20)),
            show_visualizer=bool(ui_data.get("show_visualizer", False)),
        ),
        integrations=IntegrationsConfig(
            lastfm_enabled=bool(integrations_data.get("lastfm_enabled", False)),
            lastfm_username=str(integrations_data.get("lastfm_username", "")),
            lyrics_enabled=bool(integrations_data.get("lyrics_enabled", True)),
            notifications_enabled=bool(integrations_data.get("notifications_enabled", False)),
        ),
    )


def load_config() -> LocaifyConfig:
    config_path = _get_config_path()

    if not config_path.exists():
        config = LocaifyConfig()
        save_config(config)
        return config

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    return _dict_to_config(data)


def save_config(config: LocaifyConfig) -> None:
    config_dir = _get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = _get_config_path()
    data = asdict(config)

    with config_path.open("wb") as f:
        tomli_w.dump(data, f)
