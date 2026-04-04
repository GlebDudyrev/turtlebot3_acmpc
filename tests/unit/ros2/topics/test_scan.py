"""Tests for LaserScanSubscriber."""

from acmpc.ros2 import LaserScanSubscriber
from tests.conftest import MockRos


class TestLaserScanSubscriber:
    """Test suite for LaserScanSubscriber."""

    def test_parse_message_structure(self):
        """Test _parse_message returns correct structure."""
        mock_ros = MockRos()
        callback_received = []

        def callback(msg):
            callback_received.append(msg)

        subscriber = LaserScanSubscriber(mock_ros, callback)

        raw_message = {
            "header": {
                "frame_id": "base_scan",
                "stamp": {"secs": 1, "nsecs": 0},
            },
            "angle_min": -2.356,
            "angle_max": 2.356,
            "angle_increment": 0.0058,
            "range_min": 0.1,
            "range_max": 3.5,
            "ranges": [1.0, 1.1, 1.2] * 360,
            "intensities": [],
        }

        result = subscriber._parse_message(raw_message)

        assert "frame_id" in result
        assert "angle_min" in result
        assert "angle_max" in result
        assert "range_min" in result
        assert "range_max" in result
        assert "ranges" in result
        assert result["frame_id"] == "base_scan"
        assert result["angle_min"] == -2.356
        assert result["range_min"] == 0.1

    def test_topic_name(self):
        """Test subscriber is created with correct topic name."""
        mock_ros = MockRos()

        def callback(msg):
            pass

        subscriber = LaserScanSubscriber(mock_ros, callback)

        assert subscriber.name == "/scan"

    def test_message_type(self):
        """Test subscriber uses correct message type."""
        mock_ros = MockRos()

        def callback(msg):
            pass

        subscriber = LaserScanSubscriber(mock_ros, callback)

        assert subscriber.message_type == "sensor_msgs/LaserScan"

    def test_ranges_with_angles(self):
        """Test ranges_with_angles is calculated correctly."""
        mock_ros = MockRos()

        def callback(msg):
            pass

        subscriber = LaserScanSubscriber(mock_ros, callback)

        raw_message = {
            "header": {"frame_id": "base_scan", "stamp": {"secs": 0, "nsecs": 0}},
            "angle_min": 0.0,
            "angle_max": 1.0,
            "angle_increment": 0.5,
            "range_min": 0.1,
            "range_max": 3.0,
            "ranges": [1.0, 2.0, 3.0],
            "intensities": [],
        }

        result = subscriber._parse_message(raw_message)

        assert "ranges_with_angles" in result
        assert len(result["ranges_with_angles"]) == 3
        assert result["ranges_with_angles"][0]["index"] == 0
        assert result["ranges_with_angles"][0]["angle"] == 0.0
        assert result["ranges_with_angles"][0]["distance"] == 1.0

    def test_callback_called(self):
        """Test callback is called via _handle method."""
        mock_ros = MockRos()
        callback_received = []

        def callback(msg):
            callback_received.append(msg)

        subscriber = LaserScanSubscriber(mock_ros, callback)

        parsed_message = {
            "frame_id": "base_scan",
            "ranges": [1.0, 2.0],
            "angle_min": 0.0,
            "angle_max": 1.0,
        }

        subscriber._handle(parsed_message)

        assert len(callback_received) == 1
        assert callback_received[0]["frame_id"] == "base_scan"
