"""Tests for the configuration system."""

from __future__ import annotations

from collections.abc import Generator
import os
from pathlib import Path

import pytest

from locaify.core.config import (
    LocaifyConfig,
    load_config,
    save_config,
)


@pytest.fixture
def config_dir(tmp_path: Path) -> Generator[Path, None, None]:
    config_path = tmp_path / "locaify"
    os.environ["LOCAIFY_CONFIG_DIR"] = str(config_path)
    yield config_path
    del os.environ["LOCAIFY_CONFIG_DIR"]


def test_load_config_creates_file_on_first_run(config_dir: Path) -> None:
    config = load_config()
    assert (config_dir / "config.toml").exists()
    assert isinstance(config, LocaifyConfig)


def test_load_config_returns_defaults_on_first_run(config_dir: Path) -> None:
    config = load_config()
    assert config.ui.theme == "catppuccin"
    assert config.player.volume == 80
    assert config.player.shuffle is False
    assert config.library.root_dirs == []


def test_save_and_reload_config(config_dir: Path) -> None:
    config = load_config()
    config.player.volume = 95
    config.ui.theme = "dracula"
    save_config(config)

    reloaded = load_config()
    assert reloaded.player.volume == 95
    assert reloaded.ui.theme == "dracula"


def test_save_creates_directory_if_missing(tmp_path: Path) -> None:
    deep_path = tmp_path / "a" / "b" / "c" / "locaify"
    os.environ["LOCAIFY_CONFIG_DIR"] = str(deep_path)
    config = LocaifyConfig()
    save_config(config)
    assert (deep_path / "config.toml").exists()
    del os.environ["LOCAIFY_CONFIG_DIR"]


def test_missing_keys_use_defaults(config_dir: Path) -> None:
    (config_dir).mkdir(parents=True, exist_ok=True)
    (config_dir / "config.toml").write_text("[player]\nvolume = 50\n")

    config = load_config()
    assert config.player.volume == 50
    assert config.ui.theme == "catppuccin"
    assert config.player.shuffle is False


def test_volume_is_saved_correctly(config_dir: Path) -> None:
    config = load_config()
    config.player.volume = 42
    save_config(config)

    reloaded = load_config()
    assert reloaded.player.volume == 42


def test_library_directories_saved(config_dir: Path) -> None:
    config = load_config()
    config.library.root_dirs = ["/home/krishiv/Music", "/home/krishiv/Downloads"]
    save_config(config)

    reloaded = load_config()
    assert "/home/krishiv/Music" in reloaded.library.root_dirs
    assert len(reloaded.library.root_dirs) == 2
