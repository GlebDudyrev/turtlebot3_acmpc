"""Robot parameters."""

from . import burger, waffle, waffle_pi
from .registry import (
    RobotParams,
    RobotParamsRegistry,
    get_robot_params,
)

__all__ = [
    "RobotParams",
    "RobotParamsRegistry",
    "get_robot_params",
]
