from acmpc.cases.registry import get_case, list_cases
from ..models import CaseSummaryView


def get_case_names() -> list[str]:
    return list_cases()


def build_case_summary(name: str) -> CaseSummaryView:
    case = get_case(name)
    config = case.config

    return CaseSummaryView(
        name=config.name,
        description=config.description or "-",
        world=config.env.world_name,
        robot=config.env.robot_name,
        reward=config.env.reward_fn,
        goal_threshold=config.env.goal_threshold,
        max_steps=config.env.max_steps,
        device=config.device,
        seed=config.seed,
        max_epochs=config.max_epochs,
        eval_freq=config.eval_freq,
        save_freq=config.save_freq,
        learning_rate=config.ppo.learning_rate,
        batch_size=config.ppo.batch_size,
        n_steps=config.ppo.n_steps,
        clip_range=config.ppo.clip_range,
    )