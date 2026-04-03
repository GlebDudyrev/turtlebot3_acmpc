import logging
from typing import Callable, Any
from abc import ABC, abstractmethod
import roslibpy
from ._base_topic import BaseTopic


LOGGER = logging.getLogger(__name__)


class Subscriber(BaseTopic, ABC):
    def __init__(self, ros, name, message_type, callback):
        super().__init__(ros, name, message_type)
        self.callback: Callable = callback

    def subscribe(self):
        self.topic.subscribe(self._handle_raw_message)
        LOGGER.info('Subscriber ', self.name, 'is ready.')

    def unsubscribe(self):
        self.topic.unsubscribe()

    def _handle_raw_message(self, message: roslibpy.Message):
        LOGGER.debug('Subscriber', self.name, 'get message: ', message)
        parsed = self._parse_message(message)
        self._handle(parsed)

    def _handle(self, parsed_message: dict):
        self.callback(parsed_message)

    @abstractmethod
    def _parse_message(self, message: roslibpy.Message) -> dict[str, Any]:
        pass
