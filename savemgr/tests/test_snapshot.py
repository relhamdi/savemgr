import json
from pathlib import Path

import pytest

from savemgr.core.platform import get_current_platform
from savemgr.core.snapshot import backup, delete_snapshot, list_snapshots, restore


@pytest.fixture
def game_with_local_sources(tmp_path: Path, sample_game):
    """Override game sources to point to real tmp directories."""
    platform = get_current_platform()
    save_dir = tmp_path / "game_saves"
    save_dir.mkdir()
    (save_dir / "save1.dat").write_text("data")

    from savemgr.models.game import GameSource

    sample_game.sources = GameSource(**{platform: [str(save_dir)]})
    return sample_game


def test_backup_creates_snapshot(app_dir, game_with_local_sources):
    snap = backup(app_dir, game_with_local_sources)
    snapshots = list_snapshots(app_dir, "celeste")
    assert len(snapshots) == 1
    assert snapshots[0].timestamp == snap.timestamp


def test_backup_dry_run_creates_nothing(app_dir, game_with_local_sources):
    backup(app_dir, game_with_local_sources, dry_run=True)
    snapshots = list_snapshots(app_dir, "celeste")
    assert len(snapshots) == 0


def test_backup_compress_creates_zip(app_dir, game_with_local_sources):
    snap = backup(app_dir, game_with_local_sources, compress=True)
    game_dir = app_dir / "saves" / "celeste"
    zip_file = game_dir / f"{snap.folder_name}.zip"
    assert zip_file.exists()
    assert not (game_dir / snap.folder_name).exists()


def test_list_snapshots_sorted(app_dir, game_with_local_sources):
    from unittest.mock import patch

    with patch("savemgr.core.snapshot._make_timestamp", return_value="20250101_120000"):
        backup(app_dir, game_with_local_sources)

    with patch("savemgr.core.snapshot._make_timestamp", return_value="20250102_120000"):
        backup(app_dir, game_with_local_sources)

    snapshots = list_snapshots(app_dir, "celeste")
    assert len(snapshots) == 2
    assert snapshots[0].timestamp >= snapshots[1].timestamp


def test_delete_snapshot(app_dir, game_with_local_sources):
    snap = backup(app_dir, game_with_local_sources)
    delete_snapshot(app_dir, "celeste", snap.folder_name)
    assert list_snapshots(app_dir, "celeste") == []


def test_delete_snapshot_not_found(app_dir):
    with pytest.raises(FileNotFoundError):
        delete_snapshot(app_dir, "celeste", "20250101_000000-windows")


def test_backup_no_sources_raises(app_dir, sample_game):
    from savemgr.models.game import GameSource

    sample_game.sources = GameSource()
    with pytest.raises(ValueError):
        backup(app_dir, sample_game)


def test_restore_copies_files_back(app_dir, game_with_local_sources, tmp_path):
    """Restore should copy snapshot files back to source directories."""
    snap = backup(app_dir, game_with_local_sources)

    # Simulate source being wiped
    platform = get_current_platform()
    source_dir = Path(game_with_local_sources.get_sources_for_platform(platform)[0])
    for f in source_dir.iterdir():
        f.unlink()
    assert list(source_dir.iterdir()) == []

    restore(app_dir, game_with_local_sources, snap, dry_run=False)
    assert any(source_dir.iterdir())


def test_restore_dry_run_does_not_copy(app_dir, game_with_local_sources):
    """Dry-run restore should not modify source directories."""
    snap = backup(app_dir, game_with_local_sources)

    platform = get_current_platform()
    source_dir = Path(game_with_local_sources.get_sources_for_platform(platform)[0])
    for f in source_dir.iterdir():
        f.unlink()

    restore(app_dir, game_with_local_sources, snap, dry_run=True)
    assert list(source_dir.iterdir()) == []


def test_restore_creates_autosave_first(app_dir, game_with_local_sources):
    """Restore should create an autosave snapshot before restoring."""
    snap = backup(app_dir, game_with_local_sources)
    restore(app_dir, game_with_local_sources, snap, dry_run=False)

    snapshots = list_snapshots(app_dir, "celeste")
    assert any(s.autosave for s in snapshots)


def test_restore_wipes_destination_before_copy(app_dir, game_with_local_sources):
    """Restore should wipe destination so no extra files survive."""
    snap = backup(app_dir, game_with_local_sources)

    platform = get_current_platform()
    source_dir = Path(game_with_local_sources.get_sources_for_platform(platform)[0])

    # Create a new file that was not in the snapshot
    (source_dir / "intruder.dat").write_text("should be gone after restore")

    restore(app_dir, game_with_local_sources, snap, dry_run=False)

    assert not (source_dir / "intruder.dat").exists()


def test_backup_autosave_folder_name(app_dir, game_with_local_sources):
    """Autosave snapshots should have the correct suffix in folder name."""
    snap = backup(app_dir, game_with_local_sources, autosave=True)
    assert snap.folder_name.endswith("_autosave")
    snapshots = list_snapshots(app_dir, "celeste")
    assert snapshots[0].autosave is True


def test_backup_compressed_snapshot_is_restorable(app_dir, game_with_local_sources):
    """A compressed snapshot should be correctly restored."""
    snap = backup(app_dir, game_with_local_sources, compress=True)

    platform = get_current_platform()
    source_dir = Path(game_with_local_sources.get_sources_for_platform(platform)[0])
    for f in source_dir.iterdir():
        f.unlink()

    restore(app_dir, game_with_local_sources, snap, dry_run=False)
    assert any(source_dir.iterdir())


def test_backup_comment_stored_in_meta(app_dir, game_with_local_sources):
    """Comment passed to backup should be written to .meta.json."""
    snap = backup(app_dir, game_with_local_sources, comment="before final boss")
    meta_path = app_dir / "saves" / "celeste" / snap.folder_name / ".meta.json"
    meta = json.loads(meta_path.read_text())
    assert meta["comment"] == "before final boss"


def test_list_snapshots_reads_comment(app_dir, game_with_local_sources):
    """list_snapshots should populate the comment field from .meta.json."""
    backup(app_dir, game_with_local_sources, comment="level 4 cleared")
    snapshots = list_snapshots(app_dir, "celeste")
    assert snapshots[0].comment == "level 4 cleared"


def test_backup_empty_comment_by_default(app_dir, game_with_local_sources):
    """Snapshots created without --comment should have an empty comment."""
    backup(app_dir, game_with_local_sources)
    snapshots = list_snapshots(app_dir, "celeste")
    assert snapshots[0].comment == ""
