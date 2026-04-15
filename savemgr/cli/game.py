import typer
from rich.console import Console
from rich.table import Table

from savemgr.constants import APP_DIR
from savemgr.core import config
from savemgr.models.game import Game, GameSource

app = typer.Typer(help="Manage configured games.")
console = Console()


@app.command("add")
def add_game(
    slug: str = typer.Argument(..., help="Short slug for the game (ex: mgr)."),
    name: str = typer.Option(..., prompt=True, help="Full title of the game."),
):
    """Add a game to the configuration interactively."""
    console.print(f"\n[bold]Configuring paths for [cyan]{name}[/cyan][/bold]")
    console.print("[dim]Leave blank to skip a platform.[/dim]\n")

    sources = {}
    for platform in ["windows", "linux", "macos"]:
        paths = []
        console.print(f"[yellow]{platform.capitalize()}[/yellow]")
        while True:
            raw = typer.prompt("  Path (leave blank to finish)", default="")
            if not raw:
                break
            paths.append(raw)
        if paths:
            sources[platform] = paths

    game = Game(
        slug=slug,
        name=name,
        sources=GameSource(
            windows=sources.get("windows", []),
            linux=sources.get("linux", []),
            macos=sources.get("macos", []),
        ),
    )

    config.add_game(APP_DIR, game)
    console.print(f"\n[green]✓[/green] Game [bold]{name}[/bold] was added.")


@app.command("list")
def list_games():
    """List all configured games."""
    games = config.load_games(APP_DIR)

    if not games:
        console.print("[dim]No games configured.[/dim]")
        raise typer.Exit()

    table = Table(title="Configured games")
    table.add_column("Slug", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Locked")
    table.add_column("Windows", style="dim")
    table.add_column("Linux", style="dim")
    table.add_column("macOS", style="dim")

    for game in games.values():
        table.add_row(
            game.slug,
            game.name,
            "[red]locked[/red]" if game.locked else "[dim]—[/dim]",
            "\n".join(game.sources.windows) or "—",
            "\n".join(game.sources.linux) or "—",
            "\n".join(game.sources.macos) or "—",
        )

    console.print(table)


@app.command("remove")
def remove_game(
    slug: str = typer.Argument(..., help="Game slug to be removed."),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Do not ask for confirmation.",
    ),
):
    """Remove a game from the config."""
    try:
        game = config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Remove '{game.name}' from config?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit()

    config.remove_game(APP_DIR, slug)
    console.print(f"[green]✓[/green] Game [bold]{game.name}[/bold] was removed.")


@app.command("lock")
def lock_game(
    slug: str = typer.Argument(..., help="Game slug to lock."),
):
    """Lock a game to prevent backup and restore operations."""
    try:
        game = config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
        raise typer.Exit(1)

    if game.locked:
        console.print(f"[yellow]{game.name} is already locked.[/yellow]")
        raise typer.Exit()

    config.set_game_locked(APP_DIR, slug, locked=True)
    console.print(f"[green]✓[/green] [bold]{game.name}[/bold] is now locked.")


@app.command("unlock")
def unlock_game(
    slug: str = typer.Argument(..., help="Game slug to unlock."),
):
    """Unlock a game to allow backup and restore operations."""
    try:
        game = config.get_game(APP_DIR, slug)
    except KeyError:
        console.print(f"[red]Game not found:[/red] {slug}")
        raise typer.Exit(1)

    if not game.locked:
        console.print(f"[yellow]{game.name} is already unlocked.[/yellow]")
        raise typer.Exit()

    config.set_game_locked(APP_DIR, slug, locked=False)
    console.print(f"[green]✓[/green] [bold]{game.name}[/bold] is now unlocked.")
