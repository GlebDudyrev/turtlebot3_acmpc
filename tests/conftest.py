"""Pytest configuration for turtlebot3_acmpc tests."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def src_path() -> Path:
    """Return the src directory."""
    return Path(__file__).parent.parent / "src"


class MockRos:
    """Mock for roslibpy.Ros."""

    def __init__(self, host: str = "localhost", port: int = 9090):
        self.host = host
        self.port = port
        self._is_connected = False
        self._is_connecting = False
        self._callbacks: dict = {}
        self.id_counter = 0

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_connecting(self) -> bool:
        return self._is_connecting

    @property
    def client(self):
        """Return self to mock RosBridgeClient behavior."""
        return self

    def on(self, event: str, callback):
        self._callbacks[event] = callback

    def run(self):
        self._is_connecting = True
        if "ready" in self._callbacks:
            self._callbacks["ready"]()
        self._is_connected = True
        self._is_connecting = False

    def terminate(self):
        self._is_connected = False
        self._is_connecting = False

    def close(self):
        self._is_connected = False


class MockTopic:
    """Mock for roslibpy.Topic."""

    def __init__(self, ros, name: str, message_type: str):
        self.ros = ros
        self.name = name
        self.message_type = message_type
        self._subscribed = False
        self._published_messages: list = []

    def publish(self, message):
        self._published_messages.append(message)

    def subscribe(self, callback):
        self._subscribed = True

    def unsubscribe(self):
        self._subscribed = False


class MockService:
    """Mock for roslibpy.Service."""

    def __init__(self, ros, name: str, service_type: str):
        self.ros = ros
        self.name = name
        self.service_type = service_type
        self._called = False
        self._last_request = None

    def call(self, request, timeout: int = 5):
        self._called = True
        self._last_request = request
        return {"success": True, "status_message": "OK"}
