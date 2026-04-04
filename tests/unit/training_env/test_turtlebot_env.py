"""Tests for TurtleBotEnv."""

import numpy as np

from acmpc.cases.configs import EnvConfig
from acmpc.registries.robots import RobotParamsRegistry
from acmpc.training_env import TurtleBotEnv


class TestTurtleBotEnv:
    """Test suite for TurtleBotEnv."""

    def test_process_lidar(self):
        """Test LiDAR processing - batch to 10 values."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env.robot_params = RobotParamsRegistry.get("burger")

        scan_data = np.array([1.0] * 360, dtype=np.float32)
        env._current_scan = scan_data

        result = env._process_lidar()

        assert result.shape == (10,)
        assert np.all(result <= 1.0)

    def test_process_lidar_with_different_ranges(self):
        """Test LiDAR processing with varying distances."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env.robot_params = RobotParamsRegistry.get("burger")

        scan_data = np.array([3.5] * 180 + [0.5] * 180, dtype=np.float32)
        env._current_scan = scan_data

        result = env._process_lidar()

        assert result.shape == (10,)

    def test_process_lidar_returns_zeros_when_no_scan(self):
        """Test LiDAR processing returns zeros when no scan data."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env.robot_params = RobotParamsRegistry.get("burger")
        env._current_scan = None

        result = env._process_lidar()

        assert result.shape == (10,)
        assert np.all(result == 0.0)

    def test_get_distance_to_goal(self):
        """Test distance calculation to goal."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        env._goal_position = np.array([3.0, 4.0, 0.0], dtype=np.float32)

        distance = env._get_distance_to_goal()

        assert np.isclose(distance, 5.0)

    def test_get_distance_to_goal_at_same_position(self):
        """Test distance calculation when at goal position."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([1.0, 1.0, 0.0], dtype=np.float32)
        env._goal_position = np.array([1.0, 1.0, 0.0], dtype=np.float32)

        distance = env._get_distance_to_goal()

        assert np.isclose(distance, 0.0)

    def test_get_distance_to_goal_returns_inf_when_no_position(self):
        """Test distance calculation returns inf when no position data."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = None
        env._goal_position = np.array([1.0, 1.0, 0.0], dtype=np.float32)

        distance = env._get_distance_to_goal()

        assert distance == float("inf")

    def test_is_terminated_goal_reached(self):
        """Test termination when goal is reached."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        env._goal_position = np.array([0.2, 0.0, 0.0], dtype=np.float32)
        env._current_scan = np.array([1.0] * 360, dtype=np.float32)
        env.env_config = EnvConfig(goal_threshold=0.3)

        result = env._is_terminated()

        assert result is True

    def test_is_terminated_collision(self):
        """Test termination when collision detected."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        env._goal_position = np.array([3.0, 0.0, 0.0], dtype=np.float32)
        env._current_scan = np.array([0.05] * 360, dtype=np.float32)
        env.env_config = EnvConfig(goal_threshold=0.3)

        result = env._is_terminated()

        assert result is True

    def test_is_terminated_no_termination(self):
        """Test no termination when conditions not met."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        env._goal_position = np.array([3.0, 0.0, 0.0], dtype=np.float32)
        env._current_scan = np.array([1.0] * 360, dtype=np.float32)
        env.env_config = EnvConfig(goal_threshold=0.3)

        result = env._is_terminated()

        assert result is False

    def test_is_truncated_max_steps(self):
        """Test truncation when max steps reached."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._steps = 500
        env.env_config = EnvConfig(max_steps=500)

        result = env._is_truncated()

        assert result is True

    def test_is_truncated_not_truncated(self):
        """Test no truncation when under max steps."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._steps = 100
        env.env_config = EnvConfig(max_steps=500)

        result = env._is_truncated()

        assert result is False

    def test_get_goal_info(self):
        """Test goal info calculation in polar coordinates."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        env._goal_position = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        rho, phi, yaw = env._get_goal_info()[:3]

        assert np.isclose(rho, 1.0)
        assert np.isclose(phi, 0.0)
        assert np.isclose(yaw, 0.0)

    def test_get_heading_deviation(self):
        """Test heading deviation calculation."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        env._goal_position = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        deviation = env._get_heading_deviation()

        assert np.isclose(deviation, 1.0)  # facing goal

    def test_get_heading_deviation_opposite_direction(self):
        """Test heading deviation when facing opposite direction."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([0.0, 0.0, np.pi], dtype=np.float32)
        env._goal_position = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        deviation = env._get_heading_deviation()

        assert np.isclose(deviation, -1.0)  # opposite direction

    def test_quaternion_to_yaw(self):
        """Test quaternion to yaw conversion."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)

        yaw = env._quaternion_to_yaw({"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})
        assert np.isclose(yaw, 0.0)

        yaw = env._quaternion_to_yaw({"x": 0.0, "y": 0.0, "z": 0.707, "w": 0.707})
        assert np.isclose(yaw, np.pi / 2, rtol=1e-3)

    def test_get_info_dict(self):
        """Test info dictionary creation."""
        env = TurtleBotEnv.__new__(TurtleBotEnv)
        env._current_position = np.array([1.0, 2.0, 0.0], dtype=np.float32)
        env._goal_position = np.array([1.0, 3.0, 0.0], dtype=np.float32)
        env._current_scan = np.array([1.0] * 360, dtype=np.float32)
        env._prev_distance = 2.0
        env._steps = 10

        info = env._get_info()

        assert "distance_to_goal" in info
        assert "steps" in info
        assert "position" in info
        assert "goal_position" in info
        assert "prev_distance" in info
        assert "min_lidar" in info
        assert "heading_deviation" in info
        assert info["steps"] == 10
