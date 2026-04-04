from abc import ABC

import roslibpy

from ..client import RosBridgeClient


class BaseTopic(ABC):
    def __init__(self, ros_client: RosBridgeClient, name: str, message_type: str):
        self.ros = ros_client
        self.name = name
        self.message_type = message_type
        self.topic = roslibpy.Topic(ros_client.client, name, message_type)
