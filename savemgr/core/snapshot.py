import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from savemgr.core.platform import get_current_platform
from savemgr.core.resolver import resolve_path
from savemgr.models.game import Game
from savemgr.models.snapshot import Snapshot


def _make_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _get_game_saves_dir(app_dir: Path, slug: str) -> Path:
    return app_dir / "saves" / slug


def _write_meta(dest: Path, snapshot: Snapshot) -> None:
    meta = {
        "game_slug": snapshot.game_slug,
        "timestamp": snapshot.timestamp,
        "platform": snapshot.platform,
        "compressed": snapshot.compressed,
        "autosave": snapshot.autosave,
        "comment": snapshot.comment,
    }
    (dest / ".meta.json").write_text(json.dumps(meta, indent=2))


def _copy_sources(
    sources: list[str],
    dest: Path,
    dry_run: bool,
) -> list[tuple[Path, Path]]:
    """Copy each source (file or folder) to the destination.

    Args:
        sources (list[str]): List of sources for the game.
        dest (Path): Destination path.
        dry_run (bool): If True, will perform a dry-run (just logging what will be done).

    Raises:
        FileNotFoundError: Raised if any source path does not exist.

    Returns:
        list[tuple[Path, Path]]: List of the processed (source, destination) tuples.
    """
    operations: list[tuple[Path, Path]] = []

    for raw_path in sources:
        src = resolve_path(raw_path)
        # Subfolder in the snapshot named after the last segment of the source path
        target = dest / src.name

        if not src.exists():
            raise FileNotFoundError(f"Source path not found: {src}")

        operations.append((src, target))

        # Perform action if not dry-run
        if not dry_run:
            if src.is_dir():
                shutil.copytree(src, target, dirs_exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)

    return operations


def _compress_snapshot(snapshot_dir: Path) -> Path:
    """Compress a snapshot folder into a ZIP file and deletes the folder.

    Args:
        snapshot_dir (Path): Snapshot path.

    Returns:
        Path: ZIP file path.
    """
    zip_path = snapshot_dir.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in snapshot_dir.rglob("*"):
            zf.write(file, file.relative_to(snapshot_dir))
    shutil.rmtree(snapshot_dir)
    return zip_path


def backup(
    app_dir: Path,
    game: Game,
    compress: bool = False,
    dry_run: bool = False,
    autosave: bool = False,
    comment: str = "",
) -> Snapshot:
    """Create a game snapshot for the current platform.

    Args:
        app_dir (Path): Application directory.
        game (Game): Game object.
        compress (bool, optional): If True, will compress the save in a ZIP file.
            Defaults to False.
        dry_run (bool, optional): If True, will perform a dry-run (just logging what will be done).
            Defaults to False.
        autosave (bool, optional): If True, the save is flagged as an autosave (before a restoration).
            Defaults to False.
        comment (str, optional): Comment for the snapshot.
            Defaults to "".

    Raises:
        ValueError: Raised if no source were configured for a platform.

    Returns:
        Snapshot: Created snapshot.
    """
    platform = get_current_platform()
    sources = game.get_sources_for_platform(platform)

    if not sources:
        raise ValueError(f"No sources configured for '{game.slug}' on {platform}")

    timestamp = _make_timestamp()
    snapshot = Snapshot(
        game_slug=game.slug,
        timestamp=timestamp,
        platform=platform,
        compressed=compress,
        autosave=autosave,
        comment=comment,
    )

    dest = _get_game_saves_dir(app_dir, game.slug) / snapshot.folder_name

    print(f"  Source(s): {', '.join(sources)}")
    print(f"  Dest     : {dest}")

    operations = _copy_sources(sources, dest, dry_run=dry_run)

    if dry_run:
        print("\n[DRY-RUN] Files that would be copied:")
        for src, target in operations:
            if src.is_dir():
                files = list(src.rglob("*"))
                size = sum(f.stat().st_size for f in files if f.is_file())
                print(
                    f"  + {src.name}/  ({len(files)} files, {size / 1024 / 1024:.1f} MB)"
                )
            else:
                size = src.stat().st_size
                print(f"  + {src.name}  ({size / 1024 / 1024:.1f} MB)")
        print("\n[DRY-RUN] No action performed.")
        return snapshot

    dest.mkdir(parents=True, exist_ok=True)
    _write_meta(dest, snapshot)

    if compress:
        _compress_snapshot(dest)

    return snapshot


def list_snapshots(app_dir: Path, slug: str) -> list[Snapshot]:
    """List the snapshots for a game, sorted from newest to oldest.

    Args:
        app_dir (Path): Application directory.
        slug (str): Game slug.

    Returns:
        list[Snapshot]: Snapshot list.
    """
    game_dir = _get_game_saves_dir(app_dir, slug)

    if not game_dir.exists():
        return []

    snapshots = []
    for entry in game_dir.iterdir():
        # “entry” is either a folder or a .zip file
        folder_name = entry.stem if entry.suffix == ".zip" else entry.name
        compressed = entry.suffix == ".zip"

        # Parse folder_name: YYYYMMDD_HHMMSS-{platform}[_autosave]
        try:
            timestamp, suffix = folder_name.split("-", 1)
            autosave = suffix.endswith("_autosave")
            platform = suffix.removesuffix("_autosave")
        except ValueError:
            # Unrecognized input
            continue

        # Read comment from .meta.json if available
        comment = ""
        meta_path = entry if entry.is_dir() else None
        if meta_path and (meta_path / ".meta.json").exists():
            try:
                meta = json.loads((meta_path / ".meta.json").read_text())
                comment = meta.get("comment", "")
            except (json.JSONDecodeError, OSError):
                pass

        snapshots.append(
            Snapshot(
                game_slug=slug,
                timestamp=timestamp,
                platform=platform,
                compressed=compressed,
                autosave=autosave,
                comment=comment,
            )
        )

    return sorted(snapshots, key=lambda s: s.timestamp, reverse=True)


def delete_snapshot(app_dir: Path, slug: str, folder_name: str) -> None:
    """Delete a snapshot (folder or .zip file).

    Args:
        app_dir (Path): Application directory.
        slug (str): Game slug.
        folder_name (str): Folder name.

    Raises:
        FileNotFoundError: Raised if snapshot couldn't be found.
    """
    game_dir = _get_game_saves_dir(app_dir, slug)

    target_dir = game_dir / folder_name
    target_zip = game_dir / f"{folder_name}.zip"

    if target_dir.exists():
        shutil.rmtree(target_dir)
    elif target_zip.exists():
        target_zip.unlink()
    else:
        raise FileNotFoundError(f"Snapshot not found: {folder_name}")


def restore(
    app_dir: Path,
    game: Game,
    snapshot: Snapshot,
    dry_run: bool = False,
) -> None:
    """Restore a snapshot to the paths configured for the current platform.
    Performs an autosave before the restore.

    Args:
        app_dir (Path): Application directory.
        game (Game): Game object.
        snapshot (Snapshot): Game snapshot.
        dry_run (bool, optional): If True, will perform a dry-run (just logging what will be done).
            Defaults to False.

    Raises:
        ValueError: Raised if no source were configured for a platform.
    """
    platform = get_current_platform()
    sources = game.get_sources_for_platform(platform)

    if not sources:
        raise ValueError(f"No sources configured for '{game.slug}' on {platform}")

    game_dir = _get_game_saves_dir(app_dir, game.slug)
    snapshot_path = game_dir / snapshot.folder_name

    # If compressed, extract to a temporary folder
    if snapshot.compressed:
        zip_path = game_dir / f"{snapshot.folder_name}.zip"
        snapshot_path = game_dir / f"{snapshot.folder_name}_tmp"
        if not dry_run:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(snapshot_path)

    for raw_path in sources:
        dest = resolve_path(raw_path)
        src = snapshot_path / Path(raw_path).name

        if not src.exists():
            print(f"  [WARN] Source not found in snapshot: {src.name}")
            continue

        if dry_run:
            print(f"[DRY-RUN] {src} -> {dest}")
            continue

        # Autosave only if destination currently exists
        dest_exists = dest.exists()
        if dest_exists:
            backup(app_dir, game, compress=False, dry_run=False, autosave=True)
        else:
            print(f"  [INFO] Destination does not exist, skipping autosave: {dest}")

        # Clear destination before restore
        if dest_exists:
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()

        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    # Clear the temporary folder after extraction
    if snapshot.compressed and not dry_run and snapshot_path.exists():
        shutil.rmtree(snapshot_path)
