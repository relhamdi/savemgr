from pathlib import Path

import pytest

from savemgr.models.game import Game, GameSource


@pytest.fixture
def app_dir(tmp_path: Path) -> Path:
    """Temporary application directory for each test."""
    return tmp_path


@pytest.fixture
def sample_game() -> Game:
    """A sample game with sources for all platforms."""
    return Game(
        slug="celeste",
        name="Celeste",
        sources=GameSource(
            windows=[
                "%LOCALAPPDATA%\\Celeste\\Saves",
                "%LOCALAPPDATA%\\Celeste\\Backups",
            ],
            linux=["$HOME/.local/share/Celeste/Saves"],
            macos=["$HOME/Library/Application Support/Celeste/Saves"],
        ),
    )
