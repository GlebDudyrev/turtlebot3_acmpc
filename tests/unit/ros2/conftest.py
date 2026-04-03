"""Pytest configuration for ROS2 unit tests."""

from __future__ import annotations

import pytest

from tests.conftest import MockRos, MockService, MockTopic


@pytest.fixture
def mock_ros():
    """Return a MockRos instance."""
    return MockRos()


@pytest.fixture
def mock_topic(mock_ros):
    """Return a MockTopic instance."""
    return MockTopic(mock_ros, "/test_topic", "std_msgs/String")


@pytest.fixture
def mock_service(mock_ros):
    """Return a MockService instance."""
    return MockService(mock_ros, "/test_service", "std_srvs/Empty")
