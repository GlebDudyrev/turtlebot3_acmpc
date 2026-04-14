from pydantic import BaseModel


class CaseSummaryView(BaseModel):
    name: str
    description: str
    world: str
    robot: str
    reward: str
    goal_threshold: float
    max_steps: int
    device: str
    seed: int
    max_epochs: int
    eval_freq: int
    save_freq: int
    learning_rate: float
    batch_size: int
    n_steps: int
    clip_range: float
