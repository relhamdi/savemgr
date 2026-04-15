import typer
from rich.console import Console

from savemgr.constants import APP_DIR
from savemgr.core import config
from savemgr.core import snapshot as snapshot_core

console = Console()


def backup(
    slug: str = typer.Argument(..., help="Game slug to save."),
    compress: bool = typer.Option(
        False,
        "--compress",
        "-c",
        help="Compress the snapshot into a ZIP file.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simulate without copying anything.",
    ),
    comment: str = typer.Option(
        "",
        "--comment",
        help="Optional comment for this snapshot.",
    ),
):
    """Save game files."""
    try:
        game = config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
        raise typer.Exit(1)

    prefix = "[DRY-RUN] " if dry_run else ""
    console.print(f"\n{prefix}[bold]Backup of[/bold] [cyan]{game.name}[/cyan]")

    try:
        snap = snapshot_core.backup(
            APP_DIR,
            game,
            compress=compress,
            dry_run=dry_run,
            comment=comment,
        )
        if not dry_run:
            msg = f"[green]✓[/green] Snapshot created: [bold]{snap.folder_name}[/bold]"
            if comment:
                msg += f" — [italic]{comment}[/italic]"
            console.print(msg)
    except (ValueError, FileNotFoundError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
