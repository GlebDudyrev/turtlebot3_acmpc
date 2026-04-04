from typing import Any

from .registry import RewardRegistry


@RewardRegistry.register("advanced_reward")
def advanced_reward(info: dict[str, Any]) -> float:
    """Advanced reward function.

    r2(st, at) = {
        r_arrive if d_t < c_d
        r_collision if x_t < c_o
        c_r * (d_{t-1} - d_t) * 2^(d_{t-1}/d_t) - c_p * (1 - hd) otherwise
    }
    """
    c_d = 0.3
    c_o = 0.1
    r_arrive = 100.0
    r_collision = -100.0
    c_r = 10.0
    c_p = 0.5

    distance_to_goal = info.get("distance_to_goal", float("inf"))
    prev_distance = info.get("prev_distance", distance_to_goal)
    min_lidar = info.get("min_lidar", float("inf"))
    heading_deviation = info.get("heading_deviation", 0.0)

    if distance_to_goal < c_d:
        return r_arrive

    if min_lidar < c_o:
        return r_collision

    progress = prev_distance - distance_to_goal
    if distance_to_goal > 0:
        exponential_term = 2 ** (prev_distance / distance_to_goal)
    else:
        exponential_term = 1.0

    penalty = c_p * (1.0 - heading_deviation)

    return c_r * progress * exponential_term - penalty
