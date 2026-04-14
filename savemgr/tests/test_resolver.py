import os
from pathlib import Path

from savemgr.core.resolver import resolve_path


def test_resolve_home():
    resolved = resolve_path("~/documents")
    assert not str(resolved).startswith("~")


def test_resolve_env_variable(monkeypatch):
    monkeypatch.setenv("MY_SAVE_DIR", str(Path("/tmp/saves")))
    resolved = resolve_path("$MY_SAVE_DIR/game")
    assert resolved == Path(os.environ["MY_SAVE_DIR"]) / "game"


def test_resolve_plain_path():
    path = Path("/absolute/path/to/saves")
    resolved = resolve_path(str(path))
    assert resolved == path
