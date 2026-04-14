"""Robot parameters registry."""

from ..registry import Registry
from .robot_params import RobotParams

RobotParamsRegistry = Registry[RobotParams]("robot_params")


def get_robot_params(robot_name: str) -> RobotParams:
    """Get robot parameters by name."""
    return RobotParamsRegistry.get(robot_name)

def list_robots() -> list[str]:
    return RobotParamsRegistry.list_available()