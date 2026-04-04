import roslibpy

from ..client import RosBridgeClient
from ._publisher import Publisher


class CmvVelPublisher(Publisher):
    def __init__(self, ros: RosBridgeClient):
        super().__init__(ros, "/cmd_vel", "geometry_msgs/Twist")

    def _build_message(self, linear_vel: float, angular_vel: float):
        message = roslibpy.Message(
            {
                "linear": {"x": linear_vel, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": angular_vel},
            }
        )

        return message
