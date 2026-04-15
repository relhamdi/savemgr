import typer

from savemgr.cli import backup, game, import_save, restore, save

app = typer.Typer(help="SaveMGR — Game save management system.")

app.add_typer(game.app, name="game")
app.add_typer(save.app, name="save")

app.command("backup")(backup.backup)
app.command("restore")(restore.restore)
app.command("import")(import_save.import_save)

if __name__ == "__main__":
    app()
