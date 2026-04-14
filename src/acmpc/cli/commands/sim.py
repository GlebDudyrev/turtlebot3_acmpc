import typer


app = typer.Typer(
    help="Manage simulation enviroment.",
    no_args_is_help=True,
)


@app.command("up")
def sim_up() -> None:
    typer.echo("Not implemented yet")


@app.command("down")
def sim_down() -> None:
    typer.echo("Not implemented yet")


@app.command("status")
def sim_status() -> None:
    typer.echo("Not implemented yet")
