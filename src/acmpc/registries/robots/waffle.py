"""TurtleBot3 Waffle robot parameters."""

import numpy as np

from .robot_params import RobotParams
from .registry import RobotParamsRegistry


waffle = RobotParams(
    name="TurtleBot3 Waffle",
    max_linear_vel=0.26,
    max_angular_vel=1.82,
    max_linear_acc=1.0,
    max_angular_acc=4.0,
    wheel_radius=0.033,
    wheel_base=0.287,
    lidar_range=3.5,
    lidar_rays=360,
    lidar_fov=2 * np.pi,
)

RobotParamsRegistry.register("waffle", waffle)
