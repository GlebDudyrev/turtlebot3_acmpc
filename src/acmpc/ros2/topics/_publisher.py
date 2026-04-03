import logging
from abc import ABC, abstractmethod
import roslibpy
from ._base_topic import BaseTopic


LOGGER = logging.getLogger(__name__)


class Publisher(BaseTopic, ABC):

    def publish(self, *args, **kwargs):
        if not self.ros.is_connected:
            raise RuntimeError("Ros bridge is not connected.")
        
        message = self.build_message(*args, **kwargs)
        self.topic.publish(message)

        LOGGER.info('Topic', self.name, 'published message:', message)

    @abstractmethod
    def build_message(self, *args, **kwargs) -> roslibpy.Message:
        pass
