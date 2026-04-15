from pathlib import Path

import tomli_w
import tomllib

from savemgr.models.game import Game, GameSource


def _get_config_path(app_dir: Path) -> Path:
    return app_dir / "games.toml"


def load_games(app_dir: Path) -> dict[str, Game]:
    """Load games.toml and returns a dict slug -> Game.

    Args:
        app_dir (Path): Application directory.

    Returns:
        dict[str, Game]: Dict slug -> Game.
    """
    config_path = _get_config_path(app_dir)

    if not config_path.exists():
        return {}

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    games = {}
    for slug, entry in data.get("games", {}).items():
        sources_data = entry.get("sources", {})
        sources = GameSource(
            windows=sources_data.get("windows", []),
            linux=sources_data.get("linux", []),
            macos=sources_data.get("macos", []),
        )
        games[slug] = Game(
            slug=slug,
            name=entry["name"],
            locked=entry.get("locked", False),
            sources=sources,
        )

    return games


def save_games(app_dir: Path, games: dict[str, Game]) -> None:
    """Serialize and writes all games to games.toml.

    Args:
        app_dir (Path): Application directory.
        games (dict[str, Game]): Dict slug -> Game.
    """
    config_path = _get_config_path(app_dir)
    app_dir.mkdir(parents=True, exist_ok=True)

    data: dict = {"games": {}}

    for slug, game in games.items():
        data["games"][slug] = {
            "name": game.name,
            "locked": game.locked,
            "sources": {
                "windows": game.sources.windows,
                "linux": game.sources.linux,
                "macos": game.sources.macos,
            },
        }

    with open(config_path, "wb") as f:
        tomli_w.dump(data, f)


def add_game(app_dir: Path, game: Game) -> None:
    """Add or replace a game in the settings.

    Args:
        app_dir (Path): Application directory.
        game (Game): Game object.
    """
    games = load_games(app_dir)
    games[game.slug] = game
    save_games(app_dir, games)


def remove_game(app_dir: Path, slug: str) -> None:
    """Remove a game from the configuration.

    Args:
        app_dir (Path): Application directory.
        slug (str): Game slug.

    Raises:
        KeyError: Raised if game not found.
    """
    games = load_games(app_dir)
    if slug not in games:
        raise KeyError(f"Game not found: {slug}")
    del games[slug]
    save_games(app_dir, games)


def get_game(app_dir: Path, slug: str) -> Game:
    """Get one game per slug.

    Args:
        app_dir (Path): Application directory.
        slug (str): Game slug.

    Raises:
        KeyError: Raised if game not found.

    Returns:
        Game: Game object.
    """
    games = load_games(app_dir)
    if slug not in games:
        raise KeyError(f"Game not found: {slug}")
    return games[slug]


def set_game_locked(app_dir: Path, slug: str, locked: bool) -> None:
    """Set the locked state of a game.

    Args:
        app_dir (Path): Application directory.
        slug (str): Game slug.
        locked (bool): Lock state of the game.

    Raises:
        KeyError: Raised if the game is not found.
    """
    games = load_games(app_dir)
    if slug not in games:
        raise KeyError(f"Game not found: {slug}")
    games[slug].locked = locked
    save_games(app_dir, games)
