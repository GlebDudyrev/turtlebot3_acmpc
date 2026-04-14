from acmpc.registries.robots import list_robots


def get_robot_names() -> list[str]:
    return list_robots()
