from savemgr.models.snapshot import Snapshot


def test_game_get_sources_for_platform(sample_game):
    assert sample_game.get_sources_for_platform("linux") == [
        "$HOME/.local/share/Celeste/Saves"
    ]
    assert sample_game.get_sources_for_platform("macos") == [
        "$HOME/Library/Application Support/Celeste/Saves"
    ]


def test_game_get_sources_unknown_platform(sample_game):
    assert sample_game.get_sources_for_platform("unknown") == []


def test_snapshot_folder_name_manual():
    snap = Snapshot(
        game_slug="celeste",
        timestamp="20250114_183000",
        platform="windows",
        compressed=False,
        autosave=False,
    )
    assert snap.folder_name == "20250114_183000-windows"


def test_snapshot_folder_name_autosave():
    snap = Snapshot(
        game_slug="celeste",
        timestamp="20250114_183000",
        platform="linux",
        compressed=False,
        autosave=True,
    )
    assert snap.folder_name == "20250114_183000-linux_autosave"
