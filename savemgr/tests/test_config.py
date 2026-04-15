import pytest

from savemgr.core.config import (
    add_game,
    get_game,
    load_games,
    remove_game,
    set_game_locked,
)
from savemgr.models.game import Game, GameSource


def test_add_and_load_game(app_dir, sample_game):
    add_game(app_dir, sample_game)
    games = load_games(app_dir)
    assert "celeste" in games
    assert games["celeste"].name == "Celeste"


def test_load_games_empty(app_dir):
    games = load_games(app_dir)
    assert games == {}


def test_get_game(app_dir, sample_game):
    add_game(app_dir, sample_game)
    game = get_game(app_dir, "celeste")
    assert game.slug == "celeste"


def test_get_game_not_found(app_dir):
    with pytest.raises(KeyError):
        get_game(app_dir, "unknown")


def test_remove_game(app_dir, sample_game):
    add_game(app_dir, sample_game)
    remove_game(app_dir, "celeste")
    games = load_games(app_dir)
    assert "celeste" not in games


def test_remove_game_not_found(app_dir):
    with pytest.raises(KeyError):
        remove_game(app_dir, "unknown")


def test_add_game_preserves_existing(app_dir, sample_game):
    other = Game(slug="witcher3", name="The Witcher 3", sources=GameSource())
    add_game(app_dir, sample_game)
    add_game(app_dir, other)
    games = load_games(app_dir)
    assert len(games) == 2


def test_sources_roundtrip(app_dir, sample_game):
    add_game(app_dir, sample_game)
    game = get_game(app_dir, "celeste")
    assert game.sources.windows == sample_game.sources.windows
    assert game.sources.linux == sample_game.sources.linux
    assert game.sources.macos == sample_game.sources.macos


def test_add_game_overwrites_existing(app_dir, sample_game):
    """Adding a game with an existing slug should overwrite it."""
    add_game(app_dir, sample_game)
    updated = Game(slug="celeste", name="Celeste Updated", sources=GameSource())
    add_game(app_dir, updated)
    game = get_game(app_dir, "celeste")
    assert game.name == "Celeste Updated"


def test_load_games_preserves_all_sources(app_dir, sample_game):
    """All platform sources should survive a write/read roundtrip."""
    add_game(app_dir, sample_game)
    game = get_game(app_dir, "celeste")
    assert len(game.sources.windows) == 2
    assert len(game.sources.linux) == 1
    assert len(game.sources.macos) == 1


def test_set_game_locked(app_dir, sample_game):
    """set_game_locked should persist the locked state."""
    add_game(app_dir, sample_game)
    set_game_locked(app_dir, "celeste", locked=True)
    game = get_game(app_dir, "celeste")
    assert game.locked is True


def test_set_game_unlocked(app_dir, sample_game):
    """set_game_locked should be able to unlock a previously locked game."""
    add_game(app_dir, sample_game)
    set_game_locked(app_dir, "celeste", locked=True)
    set_game_locked(app_dir, "celeste", locked=False)
    game = get_game(app_dir, "celeste")
    assert game.locked is False


def test_set_game_locked_not_found(app_dir):
    """set_game_locked should raise KeyError for unknown slug."""
    with pytest.raises(KeyError):
        set_game_locked(app_dir, "unknown", locked=True)


def test_locked_state_roundtrip(app_dir, sample_game):
    """locked field should survive a write/read roundtrip."""
    sample_game.locked = True
    add_game(app_dir, sample_game)
    game = get_game(app_dir, "celeste")
    assert game.locked is True
