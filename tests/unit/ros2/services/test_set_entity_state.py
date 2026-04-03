"""Tests for SetEntityStateServiceClient."""

from acmpc.ros2 import SetEntityStateServiceClient


class TestSetEntityStateServiceClient:
    """Test suite for SetEntityStateServiceClient."""

    def test_build_request_format(self, mock_ros):
        """Test _build_request returns correct structure."""
        service = SetEntityStateServiceClient(mock_ros)

        request = service._build_request(
            name="turtlebot3",
            position=(1.0, 2.0, 0.0),
            orientation=(0.0, 0.0, 0.0, 1.0),
            linear=(0.1, 0.0, 0.0),
            angular=(0.0, 0.0, 0.05),
        )

        assert "state" in request
        assert request["state"]["name"] == "turtlebot3"
        assert request["state"]["pose"]["position"]["x"] == 1.0
        assert request["state"]["pose"]["position"]["y"] == 2.0
        assert request["state"]["pose"]["orientation"]["w"] == 1.0
        assert request["state"]["twist"]["linear"]["x"] == 0.1
        assert request["state"]["twist"]["angular"]["z"] == 0.05

    def test_build_request_default_values(self, mock_ros):
        """Test build_request with default values."""
        service = SetEntityStateServiceClient(mock_ros)

        request = service._build_request(name="robot", position=(0.0, 0.0, 0.0))

        assert request["state"]["name"] == "robot"
        assert request["state"]["reference_frame"] == "world"
        assert request["state"]["pose"]["position"] == {"x": 0.0, "y": 0.0, "z": 0.0}
        assert request["state"]["twist"]["linear"] == {"x": 0.0, "y": 0.0, "z": 0.0}

    def test_service_name(self, mock_ros):
        """Test service is created with correct name."""
        service = SetEntityStateServiceClient(mock_ros)

        assert service.name == "/set_entity_state"

    def test_service_type(self, mock_ros):
        """Test service uses correct type."""
        service = SetEntityStateServiceClient(mock_ros)

        assert service.service_type == "gazebo_msgs/SetEntityState"

    def test_build_request_with_reference_frame(self, mock_ros):
        """Test build_request with custom reference_frame."""
        service = SetEntityStateServiceClient(mock_ros)

        request = service._build_request(
            name="turtlebot3",
            position=(0.0, 0.0, 0.0),
            reference_frame="base_link",
        )

        assert request["state"]["reference_frame"] == "base_link"
