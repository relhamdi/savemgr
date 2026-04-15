from pathlib import Path

import typer
from rich.console import Console

from savemgr.constants import APP_DIR
from savemgr.core import config
from savemgr.core import snapshot as snapshot_core

console = Console()


def import_save(
    slug: str = typer.Argument(..., help="Game slug to import into."),
    source: Path = typer.Argument(
        ...,
        help="Path to the save file or directory to import.",
    ),
    compress: bool = typer.Option(
        False,
        "--compress",
        "-c",
        help="Compress the snapshot into a ZIP file.",
    ),
    comment: str = typer.Option(
        "",
        "--comment",
        help="Optional comment for this snapshot.",
    ),
):
    """Import an external save file or directory into the versioning system."""
    try:
        game = config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
        raise typer.Exit(1)

    if not source.exists():
        console.print(f"[red]Source path not found:[/red] {source}")
        raise typer.Exit(1)

    console.print(f"\n[bold]Importing into[/bold] [cyan]{game.name}[/cyan]")
    console.print(f"  Source : {source}")

    try:
        snap = snapshot_core.import_snapshot(
            APP_DIR,
            game,
            source=source,
            compress=compress,
            comment=comment,
        )
        msg = f"[green]✓[/green] Snapshot imported: [bold]{snap.folder_name}[/bold]"
        if comment:
            msg += f" — [italic]{comment}[/italic]"
        console.print(msg)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
