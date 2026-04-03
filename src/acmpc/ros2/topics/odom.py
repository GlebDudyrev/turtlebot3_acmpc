from typing import Any

import roslibpy

from ._subscriber import Subscriber


class OdomSubscriber(Subscriber):
    def __init__(self, ros, callback):
        super().__init__(ros, "/odom", "nav_msgs/Odometry", callback)

    def _parse_message(self, message: roslibpy.Message) -> dict[str, Any]:
        pose = message["pose"]["pose"]
        twist = message["twist"]["twist"]

        return {
            "position": pose["position"],
            "orientation": pose["orientation"],
            "linear": twist["linear"],
            "angular": twist["angular"],
        }
