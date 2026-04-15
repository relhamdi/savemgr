import typer
from rich.console import Console
from rich.table import Table

from savemgr.constants import APP_DIR
from savemgr.core import config
from savemgr.core import snapshot as snapshot_core

app = typer.Typer(help="Manage snapshots.")
console = Console()


@app.command("list")
def list_saves(
    slug: str = typer.Argument(..., help="Game slug."),
):
    """List a game's snapshots."""
    try:
        game = config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
        raise typer.Exit(1)

    snapshots = snapshot_core.list_snapshots(APP_DIR, slug)

    if not snapshots:
        console.print(f"[dim]No snapshots for {game.name}.[/dim]")
        raise typer.Exit()

    table = Table(title=f"Snapshots — {game.name}")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Platform", style="yellow")
    table.add_column("Compressed")
    table.add_column("Type")
    table.add_column("Comment", style="italic")

    for snap in snapshots:
        table.add_row(
            snap.timestamp,
            snap.platform,
            "zip" if snap.compressed else "folder",
            "[dim]autosave[/dim]" if snap.autosave else "manual",
            snap.comment or "[dim]—[/dim]",
        )

    console.print(table)


@app.command("delete")
def delete_save(
    slug: str = typer.Argument(..., help="Game slug."),
    timestamp: str = typer.Argument(
        ...,
        help="Timestamp of the snapshot to be deleted.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Do not ask for confirmation.",
    ),
):
    """Delete a snapshot."""
    try:
        config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
        raise typer.Exit(1)

    snapshots = snapshot_core.list_snapshots(APP_DIR, slug)
    match = next((s for s in snapshots if s.timestamp == timestamp), None)

    if not match:
        console.print(f"[red]Snapshot not found:[/red] {timestamp}")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete the snapshot {match.folder_name}?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit()

    try:
        snapshot_core.delete_snapshot(APP_DIR, slug, match.folder_name)
        console.print(
            f"[green]✓[/green] Snapshot [bold]{match.folder_name}[/bold] was deleted."
        )
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
