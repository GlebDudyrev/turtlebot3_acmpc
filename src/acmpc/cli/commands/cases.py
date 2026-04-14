from typing import Annotated, cast

import typer

from ..renderers.cases import (
    render_case_names_text,
    render_case_summary_json,
    render_case_summary_text,
    render_cases_names_json,
)
from ..services.cases import (
    build_case_summary,
    get_case_names
)
from ..context import CLIContext


app = typer.Typer(
    help="Inspect available training cases.",
    no_args_is_help=True,
)


@app.command("list")
def list_cases_command(ctx: typer.Context) -> None:
    cli = cast(CLIContext | None, ctx.obj)
    names = get_case_names()

    if cli and cli.output == "json":
        render_cases_names_json(names)
        return

    render_case_names_text(names)


@app.command("show")
def show_case_command(
    name: Annotated[
        str,
        typer.Argument(help="Registered case name."),
    ],
    ctx: typer.Context
) -> None:
    cli = cast(CLIContext | None, ctx.obj)
    summary = build_case_summary(name)

    if cli and cli.output == "json":
        render_case_summary_json(summary)
        return

    render_case_summary_text(summary)
