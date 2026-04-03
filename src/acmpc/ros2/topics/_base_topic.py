from abc import ABC

import roslibpy


class BaseTopic(ABC):

    def __init__(self, ros: roslibpy.Ros, name: str, message_type: str):
        self.ros = ros
        self.name = name
        self.message_type = message_type
        self.topic = roslibpy.Topic(ros, name, message_type)
