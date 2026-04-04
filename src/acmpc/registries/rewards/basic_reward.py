from typing import Any

from .registry import RewardRegistry


@RewardRegistry.register("basic_reward")
def basic_reward(info: dict[str, Any]) -> float:
    """Basic reward function from article (Equation 5).

    r1(st, at) = {
        r_arrive if d_t < c_d
        r_collision if max(x_t) < c_o
        c_r * (d_{t-1} - d_t) otherwise
    }
    """
    c_d = 0.3
    c_o = 0.1
    r_arrive = 100.0
    r_collision = -100.0
    c_r = 10.0

    distance_to_goal = info.get("distance_to_goal", float("inf"))
    prev_distance = info.get("prev_distance", distance_to_goal)
    min_lidar = info.get("min_lidar", float("inf"))

    if distance_to_goal < c_d:
        return r_arrive

    if min_lidar < c_o:
        return r_collision

    progress = prev_distance - distance_to_goal
    return float(c_r * progress)
