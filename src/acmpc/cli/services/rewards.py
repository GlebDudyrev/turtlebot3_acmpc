from acmpc.registries.rewards import list_rewards


def get_reward_names() -> list[str]:
    return list_rewards()
