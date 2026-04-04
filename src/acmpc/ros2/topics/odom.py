from collections.abc import Callable
from typing import Any

import roslibpy

from ..client import RosBridgeClient
from ._subscriber import Subscriber


class OdomSubscriber(Subscriber):
    def __init__(self, ros: RosBridgeClient, callback: Callable):
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
