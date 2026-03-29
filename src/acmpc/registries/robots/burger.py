"""TurtleBot3 Burger robot parameters."""

import numpy as np

from .robot_params import RobotParams
from .registry import RobotParamsRegistry


burger = RobotParams(
    name="TurtleBot3 Burger",
    max_linear_vel=0.22,
    max_angular_vel=2.84,
    max_linear_acc=1.0,
    max_angular_acc=4.0,
    wheel_radius=0.033,
    wheel_base=0.16,
    lidar_range=3.5,
    lidar_rays=360,
    lidar_fov=2 * np.pi,
)

RobotParamsRegistry.register("burger", burger)
