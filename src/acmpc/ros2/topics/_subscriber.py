import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import roslibpy

from ..client import RosBridgeClient
from ._base_topic import BaseTopic

LOGGER = logging.getLogger(__name__)


class Subscriber(BaseTopic, ABC):
    def __init__(
        self,
        ros: RosBridgeClient,
        name: str,
        message_type: str,
        callback: Callable,
    ):
        super().__init__(ros, name, message_type)
        self.callback: Callable = callback

    def subscribe(self):
        if not self.ros.is_connected:
            raise RuntimeError("Ros bridge is not connected.")

        self.topic.subscribe(self._handle_raw_message)
        LOGGER.info("Subscriber %s is ready.", self.name)

    def unsubscribe(self):
        self.topic.unsubscribe()

    def _handle_raw_message(self, message: roslibpy.Message):
        LOGGER.debug("Subscriber %s get message: %s", self.name, message)
        parsed = self._parse_message(message)
        self._handle(parsed)

    def _handle(self, parsed_message: dict):
        self.callback(parsed_message)

    @abstractmethod
    def _parse_message(self, message: roslibpy.Message) -> dict[str, Any]:
        pass
