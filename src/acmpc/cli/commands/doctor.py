import typer


app = typer.Typer(
    help="Run enviroment diagnostics.",
    no_args_is_help=True,
)


@app.command("sim")
def doctor_sim() -> None:
    typer.echo("Not implemented yet")
