"""Tests for OdomSubscriber."""

from acmpc.ros2 import OdomSubscriber


class TestOdomSubscriber:
    """Test suite for OdomSubscriber."""

    def test_parse_message_structure(self, mock_ros):
        """Test _parse_message returns correct structure."""
        callback_received = []

        def callback(msg):
            callback_received.append(msg)

        subscriber = OdomSubscriber(mock_ros, callback)

        raw_message = {
            "pose": {
                "pose": {
                    "position": {"x": 1.0, "y": 2.0, "z": 0.0},
                    "orientation": {"x": 0.0, "y": 0.0, "z": 0.707, "w": 0.707},
                }
            },
            "twist": {
                "twist": {
                    "linear": {"x": 0.1, "y": 0.0, "z": 0.0},
                    "angular": {"x": 0.0, "y": 0.0, "z": 0.05},
                }
            },
        }

        result = subscriber._parse_message(raw_message)

        assert "position" in result
        assert "orientation" in result
        assert "linear" in result
        assert "angular" in result
        assert result["position"]["x"] == 1.0
        assert result["position"]["y"] == 2.0
        assert result["linear"]["x"] == 0.1

    def test_topic_name(self, mock_ros):
        """Test subscriber is created with correct topic name."""

        def callback(msg):
            pass

        subscriber = OdomSubscriber(mock_ros, callback)

        assert subscriber.name == "/odom"

    def test_message_type(self, mock_ros):
        """Test subscriber uses correct message type."""

        def callback(msg):
            pass

        subscriber = OdomSubscriber(mock_ros, callback)

        assert subscriber.message_type == "nav_msgs/Odometry"

    def test_callback_called(self, mock_ros):
        """Test callback is called with parsed message."""
        callback_received = []

        def callback(msg):
            callback_received.append(msg)

        subscriber = OdomSubscriber(mock_ros, callback)

        raw_message = {
            "pose": {
                "pose": {
                    "position": {"x": 1.0, "y": 2.0, "z": 0.0},
                    "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                }
            },
            "twist": {
                "twist": {
                    "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "angular": {"x": 0.0, "y": 0.0, "z": 0.0},
                }
            },
        }

        subscriber._handle_raw_message(raw_message)

        assert len(callback_received) == 1
        assert "position" in callback_received[0]
