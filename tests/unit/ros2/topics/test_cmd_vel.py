"""Tests for CmdVelPublisher."""

import pytest

from acmpc.ros2 import CmvVelPublisher
from tests.conftest import MockRos


class TestCmdVelPublisher:
    """Test suite for CmvVelPublisher."""

    def test_build_message_format(self):
        """Test build_message returns correct Twist message format."""
        mock_ros = MockRos()
        publisher = CmvVelPublisher(mock_ros)

        message = publisher._build_message(linear_vel=0.5, angular_vel=0.3)

        assert "linear" in message
        assert "angular" in message
        assert message["linear"]["x"] == 0.5
        assert message["linear"]["y"] == 0.0
        assert message["linear"]["z"] == 0.0
        assert message["angular"]["x"] == 0.0
        assert message["angular"]["y"] == 0.0
        assert message["angular"]["z"] == 0.3

    def test_build_message_zero_velocities(self):
        """Test build_message with zero velocities."""
        mock_ros = MockRos()
        publisher = CmvVelPublisher(mock_ros)

        message = publisher._build_message(linear_vel=0.0, angular_vel=0.0)

        assert message["linear"]["x"] == 0.0
        assert message["angular"]["z"] == 0.0

    @pytest.mark.skip(reason="Requires full roslibpy mock setup")
    def test_publish_calls_topic(self):
        """Test publish calls topic.publish."""
        mock_ros = MockRos()
        mock_ros.run()

        publisher = CmvVelPublisher(mock_ros)
        publisher.publish(linear_vel=0.5, angular_vel=0.3)

        assert len(publisher.topic._published_messages) == 1

    def test_topic_name(self):
        """Test publisher is created with correct topic name."""
        mock_ros = MockRos()
        publisher = CmvVelPublisher(mock_ros)

        assert publisher.name == "/cmd_vel"

    def test_message_type(self):
        """Test publisher uses correct message type."""
        mock_ros = MockRos()
        publisher = CmvVelPublisher(mock_ros)

        assert publisher.message_type == "geometry_msgs/Twist"
