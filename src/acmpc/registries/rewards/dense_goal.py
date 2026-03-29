from .registry import RewardRegistry


@RewardRegistry.register("dense_goal")
def dense_goal_reward(state, action, next_state, info) -> float:
    """Dense reward based on goal distance."""
    return 0.0  # placeholder
