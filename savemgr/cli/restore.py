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
):
    """Restore game files from a snapshot."""
    try:
        game = config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
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
