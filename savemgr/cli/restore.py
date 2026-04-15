import typer
from rich.console import Console

from savemgr.constants import APP_DIR
from savemgr.core import config
from savemgr.core import snapshot as snapshot_core

console = Console()


def restore(
    slug: str = typer.Argument(..., help="Game slug to restore."),
    timestamp: str = typer.Argument(
        None,
        help="Snapshot timestamp (default: most recent).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simulate without copying anything.",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Bypass lock."),
):
    """Restore game files from a snapshot."""
    try:
        game = config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
        raise typer.Exit(1)

    if game.locked and not force:
        console.print(
            f"[red]{game.name} is locked.[/red] Unlock it or use --force to bypass."
        )
        raise typer.Exit(1)

    snapshots = snapshot_core.list_snapshots(APP_DIR, slug)

    if not snapshots:
        console.print(f"[red]No snapshots found for:[/red] {slug}")
        raise typer.Exit(1)

    if timestamp:
        match = next((s for s in snapshots if s.timestamp == timestamp), None)
        if not match:
            console.print(f"[red]Snapshot not found:[/red] {timestamp}")
            raise typer.Exit(1)
        snap = match
    else:
        snap = snapshots[0]  # Most recent
        console.print(f"[dim]Selected snapshot: {snap.folder_name}[/dim]")

    # Warn if any destination path does not exist
    platform = snapshot_core.get_current_platform()
    missing = [
        p
        for p in game.get_sources_for_platform(platform)
        if not snapshot_core.resolve_path(p).exists()
    ]
    if missing:
        console.print(
            "\n[yellow]Warning: the following destination paths do not exist:[/yellow]"
        )
        for p in missing:
            console.print(f"  [dim]{p}[/dim]")
        console.print("[yellow]No autosave will be created for these paths.[/yellow]\n")

    prefix = "[DRY-RUN] " if dry_run else ""
    console.print(
        f"\n{prefix}[bold]Restoring[/bold] [cyan]{game.name}[/cyan] — [bold]{snap.folder_name}[/bold]"
    )

    if not dry_run:
        confirm = typer.confirm("Confirm the restoration?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit()

    try:
        snapshot_core.restore(APP_DIR, game, snap, dry_run=dry_run)
        if not dry_run:
            console.print("[green]✓[/green] Restoration completed.")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
