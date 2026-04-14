from typing import cast

import typer

from ..context import CLIContext
from ..services.robots import get_robot_names
from ..renderers.robots import (
    render_robot_names_json,
    render_robot_names_text
)

app = typer.Typer(
    help="Inspect available robot configuration.",
    no_args_is_help=True,
)


@app.command("list")
def list_robots(ctx: typer.Context) -> None:
    cli = cast(CLIContext | None, ctx.obj)
    names = get_robot_names()

    if cli and cli.output == "json":
        render_robot_names_json(names)
        return

    render_robot_names_text(names)
