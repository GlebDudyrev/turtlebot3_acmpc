"""Robot parameters."""

from .registry import (
    RobotParams,
    RobotParamsRegistry,
    get_robot_params,
)

from . import burger
from . import waffle
from . import waffle_pi

__all__ = [
    "RobotParams",
    "RobotParamsRegistry",
    "get_robot_params",
]
