from dataclasses import dataclass


@dataclass(slots=True)
class CLIContext:
    verbose: bool = False
    output: str = "text"
