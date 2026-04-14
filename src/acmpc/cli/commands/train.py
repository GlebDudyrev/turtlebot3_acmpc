from typing import Annotated, cast

import typer

from acmpc.cli.context import CLIContext


def train(
    ctx: typer.Context,
    case: Annotated[
        str,
        typer.Argument(help="Registered case name to train."),
    ],
) -> None:
    cli = cast(CLIContext | None, ctx.obj)

    if cli and cli.output == "json":
        typer.echo(f'{{"case": "{case}", "status": "not implemented yet"}}')
        return

    typer.echo(f"Training case: {case}")
    typer.echo("Training is not implemented yet.")