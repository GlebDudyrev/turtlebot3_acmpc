import typer

from .commands import (
    cases_app,
    rewards_app,
    robots_app,
    doctor_app,
    sim_app,
    train
)
from .context import CLIContext


app = typer.Typer(
    name="acmpc",
    help='CLI for turtlebot3_acmpc',
    no_args_is_help=True,
)

app.add_typer(cases_app, name="cases")
app.add_typer(rewards_app, name="rewards")
app.add_typer(robots_app, name="robots")
app.add_typer(sim_app, name="sim")
app.add_typer(doctor_app, name="doctor")

app.command(
    "train",
    help="Starting training loop.",
    no_args_is_help=True,
)(train)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose output for all comands."
    ),
    output: str = typer.Option(
        "text",
        "--output",
        help="Output format for commands",
    ),
) -> None:
    ctx.obj = CLIContext(
        verbose=verbose,
        output=output,
    )

    if verbose and ctx.invoked_subcommand is not None:
        typer.echo(f"[verbose] Running command group: {ctx.invoked_subcommand}", err=True)


if __name__ == '__main__':
    app()