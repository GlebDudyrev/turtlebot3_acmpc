from typing import cast

import typer

from ..context import CLIContext
from ..services.rewards import get_reward_names
from ..renderers.rewards import (
    render_reward_names_json,
    render_reward_names_text
)


app = typer.Typer(
    help="Inspect available reward functions.",
    no_args_is_help=True,
)


@app.command("list")
def list_rewards(ctx: typer.Context) -> None:
    cli = cast(CLIContext | None, ctx.obj)
    names = get_reward_names()

    if cli and cli.output == "json":
        render_reward_names_json(names)
        return

    render_reward_names_text(names)
