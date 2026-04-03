"""Tests for RosBridgeClient."""

from acmpc.ros2 import RosBridgeClient
from tests.conftest import MockRos


class TestRosBridgeClient:
    """Test suite for RosBridgeClient."""

    def test_constructor(self):
        """Test client initialization with host and port."""
        client = RosBridgeClient(host="test_host", port=9999)

        assert client.host == "test_host"
        assert client.port == 9999

    def test_connect(self):
        """Test connect method calls run on roslibpy client."""
        mock_ros = MockRos()

        client = RosBridgeClient.__new__(RosBridgeClient)
        client.host = "localhost"
        client.port = 9090
        client.client = mock_ros

        client.connect()

        assert mock_ros.is_connected is True

    def test_disconnect(self):
        """Test disconnect method calls terminate on roslibpy client."""
        mock_ros = MockRos()
        mock_ros.run()

        client = RosBridgeClient.__new__(RosBridgeClient)
        client.host = "localhost"
        client.port = 9090
        client.client = mock_ros

        client.disconnect(terminate=True)

        assert mock_ros.is_connected is False

    def test_is_connected_property(self):
        """Test is_connected property returns roslibpy client state."""
        mock_ros = MockRos()
        mock_ros.run()

        client = RosBridgeClient.__new__(RosBridgeClient)
        client.host = "localhost"
        client.port = 9090
        client.client = mock_ros

        assert client.is_connected is True
