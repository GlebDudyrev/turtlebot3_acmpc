from rich.console import Console
from rich.json import JSON
from rich.table import Table


console = Console()


def render_robot_names_text(names: list[str]) -> None:
    table = Table(title="Available robots")
    table.add_column("Name")

    for name in names:
        table.add_row(name)

    console.print(table)


def render_robot_names_json(names: list[str]) -> None:
    console.print(JSON.from_data(names))
