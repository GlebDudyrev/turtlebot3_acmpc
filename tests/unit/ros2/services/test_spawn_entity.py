"""Tests for SpawnEntityServiceClient."""

from acmpc.ros2 import SpawnEntityServiceClient


class TestSpawnEntityServiceClient:
    """Test suite for SpawnEntityServiceClient."""

    def test_build_request_format(self, mock_ros):
        """Test _build_request returns correct structure."""
        service = SpawnEntityServiceClient(mock_ros)

        request = service._build_request(
            name="turtlebot3",
            xml="<robot></robot>",
            position=(1.0, 2.0, 0.0),
            orientation=(0.0, 0.0, 0.0, 1.0),
        )

        assert "name" in request
        assert "xml" in request
        assert "initial_pose" in request
        assert "reference_frame" in request
        assert request["name"] == "turtlebot3"
        assert request["xml"] == "<robot></robot>"
        assert request["initial_pose"]["position"]["x"] == 1.0
        assert request["initial_pose"]["position"]["y"] == 2.0
        assert request["initial_pose"]["position"]["z"] == 0.0
        assert request["initial_pose"]["orientation"]["x"] == 0.0
        assert request["initial_pose"]["orientation"]["w"] == 1.0

    def test_build_request_default_values(self, mock_ros):
        """Test _build_request with default values."""
        service = SpawnEntityServiceClient(mock_ros)

        request = service._build_request(name="robot", xml="<robot/>")

        assert request["name"] == "robot"
        assert request["xml"] == "<robot/>"
        assert request["robot_namespace"] == ""
        assert request["reference_frame"] == "world"
        assert request["initial_pose"]["position"] == {"x": 0.0, "y": 0.0, "z": 0.0}
        assert request["initial_pose"]["orientation"] == {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "w": 1.0,
        }

    def test_service_name(self, mock_ros):
        """Test service is created with correct name."""
        service = SpawnEntityServiceClient(mock_ros)

        assert service.name == "/spawn_entity"

    def test_service_type(self, mock_ros):
        """Test service uses correct type."""
        service = SpawnEntityServiceClient(mock_ros)

        assert service.service_type == "gazebo_msgs/SpawnEntity"

    def test_build_request_with_namespace(self, mock_ros):
        """Test _build_request with robot_namespace."""
        service = SpawnEntityServiceClient(mock_ros)

        request = service._build_request(
            name="turtlebot3",
            xml="<robot/>",
            robot_namespace="tb3",
        )

        assert request["robot_namespace"] == "tb3"
