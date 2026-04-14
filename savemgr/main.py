import typer

from savemgr.cli import backup, game, restore, save

app = typer.Typer(help="SaveMGR — Game save management system.")

app.add_typer(game.app, name="game")
app.add_typer(save.app, name="save")

app.command("backup")(backup.backup)
app.command("restore")(restore.restore)

if __name__ == "__main__":
    app()
