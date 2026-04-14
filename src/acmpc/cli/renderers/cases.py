from rich.console import Console
from rich.json import JSON
from rich.table import Table

from ..models.cases import CaseSummaryView


console = Console()


def render_case_names_text(names: list[str]) -> None:
    table = Table(title="Available cases")
    table.add_column("Name")

    for name in names:
        table.add_row(name)

    console.print(table)


def render_cases_names_json(names: list[str]) -> None:
    console.print(JSON.from_data(names))


def render_case_summary_text(view: CaseSummaryView) -> None:
    table = Table(title=f"Case: {view.name}")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("Description", view.description)
    table.add_row("World", view.world)
    table.add_row("Robot", view.robot)
    table.add_row("Reward", view.reward)
    table.add_row("Goal threshold", str(view.goal_threshold))
    table.add_row("Max steps", str(view.max_steps))
    table.add_row("Device", view.device)
    table.add_row("Seed", str(view.seed))
    table.add_row("Max epochs", str(view.max_epochs))
    table.add_row("Eval freq", str(view.eval_freq))
    table.add_row("Save freq", str(view.save_freq))
    table.add_row("Learning rate", str(view.learning_rate))
    table.add_row("Batch size", str(view.batch_size))
    table.add_row("N steps", str(view.n_steps))
    table.add_row("Clip range", str(view.clip_range))

    console.print(table)


def render_case_summary_json(view: CaseSummaryView) -> None:
    console.print(JSON.from_data(view.model_dump()))
