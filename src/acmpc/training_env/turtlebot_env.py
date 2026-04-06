"""TurtleBot3 Environment for AC-MPC."""

from __future__ import annotations

import time
from typing import Any

import gymnasium as gym
import numpy as np
from numpy.typing import NDArray

from acmpc.cases import Case
from acmpc.ros2 import (
    CmvVelPublisher,
    LaserScanSubscriber,
    OdomSubscriber,
    RosBridgeClient,
    SetEntityStateServiceClient,
    SpawnEntityServiceClient,
)

GOAL_ENTITY_NAME = "goal_marker"

GOAL_SDF = """<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="goal_marker">
    <static>true</static>
    <link name="link">
      <pose>0 0 0.5 0 0 0</pose>
      <visual name="visual">
        <geometry>
          <sphere>
            <radius>0.1</radius>
          </sphere>
        </geometry>
        <material>
          <ambient>1 0 0 1</ambient>
          <diffuse>1 0 0 1</diffuse>
          <specular>1 0 0 1</specular>
        </material>
      </visual>
      <gravity>false</gravity>
    </link>
  </model>
</sdf>"""


class TurtleBotEnv(gym.Env):
    """Gymnasium environment for TurtleBot3 navigation.

    This environment provides an interface to Gazebo simulation through
    ROS2/rosbridge for training AC-MPC agent.

    Args:
        case: Case configuration containing robot params, env config, and reward fn
        ros_host: ROS bridge host address
        ros_port: ROS bridge port
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        case: Case,
    ):
        super().__init__()

        self.case = case
        self.robot_params = case.robot_params
        self.env_config = case.env_config
        self.reward_fn = case.reward_fn

        self._ros_client = RosBridgeClient()
        self._ros_client.run()

        self._cmd_vel = CmvVelPublisher(self._ros_client)
        self._odom = OdomSubscriber(self._ros_client, self._on_odom)
        self._scan = LaserScanSubscriber(self._ros_client, self._on_scan)

        self._spawn_entity = SpawnEntityServiceClient(self._ros_client)
        self._set_entity_state = SetEntityStateServiceClient(self._ros_client)

        self._odom.subscribe()
        self._scan.subscribe()

        self._current_position: NDArray[np.float32] | None = None
        self._current_velocity: NDArray[np.float32] | None = None
        self._current_scan: NDArray[np.float32] | None = None
        self._goal_entity_name: str | None = None
        self._goal_position: NDArray[np.float32] | None = None
        self._prev_distance: float | None = None
        self._steps: int = 0

        self.observation_space = gym.spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(15,),
            dtype=np.float32,
        )

        self.action_space = gym.spaces.Box(
            low=np.array(
                [-self.robot_params.max_linear_vel, -self.robot_params.max_angular_vel],
                dtype=np.float32,
            ),
            high=np.array(
                [self.robot_params.max_linear_vel, self.robot_params.max_angular_vel],
                dtype=np.float32,
            ),
            dtype=np.float32,
        )

    def _on_odom(self, data: dict[str, Any]) -> None:
        """Callback for odometry data."""
        orientation = data["orientation"]
        yaw = self._quaternion_to_yaw(orientation)

        self._current_position = np.array(
            [data["position"]["x"], data["position"]["y"], yaw],
            dtype=np.float32,
        )
        self._current_velocity = np.array(
            [data["linear"]["x"], data["angular"]["z"]],
            dtype=np.float32,
        )

    def _on_scan(self, data: dict[str, Any]) -> None:
        """Callback for laser scan data."""
        self._current_scan = np.array(data["ranges"], dtype=np.float32)

    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[NDArray[np.float32], dict[str, Any]]:
        """Reset the environment to initial state."""
        super().reset(seed=seed)

        self._steps = 0
        self._prev_distance = None

        if self._goal_entity_name is None:
            self._spawn_goal()
        else:
            self._teleport_episode()

        self._wait_for_sensor_data()

        observation = self._get_observation()
        info = self._get_info()

        return observation, info

    def _spawn_goal(self) -> None:
        """Spawn goal entity in Gazebo."""
        goal_pos = self._generate_goal_position()
        self._goal_position = np.array(goal_pos, dtype=np.float32)

        try:
            response = self._spawn_entity.call(
                name=GOAL_ENTITY_NAME,
                xml=GOAL_SDF,
                position=(goal_pos[0], goal_pos[1], 0.5),
            )
            if response.get("success", False):
                self._goal_entity_name = GOAL_ENTITY_NAME
        except Exception:
            pass

    def _teleport_episode(self) -> None:
        """Teleport robot and goal to new positions."""
        robot_pos = (0.0, 0.0, 0.0)
        self._set_entity_state.call(
            name=self.env_config.robot_name,
            position=robot_pos,
        )

        goal_pos = self._generate_goal_position()
        self._goal_position = np.array(goal_pos, dtype=np.float32)

        self._set_entity_state.call(
            name=GOAL_ENTITY_NAME,
            position=(goal_pos[0], goal_pos[1], 0.5),
        )

    def _generate_goal_position(self) -> tuple[float, float]:
        """Generate random goal position within specified bounds."""
        rng = np.random.default_rng()
        angle = rng.uniform(0, 2 * np.pi)
        distance = rng.uniform(
            self.env_config.goal_min_distance, self.env_config.goal_max_distance
        )

        x = distance * np.cos(angle)
        y = distance * np.sin(angle)

        return (float(x), float(y))

    def _wait_for_sensor_data(self, timeout: float = 5.0) -> None:
        """Wait for sensor data to arrive."""
        start_time = time.time()

        self._current_scan = None
        while self._current_scan is None:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.01)

    def step(
        self, action: NDArray[np.float32]
    ) -> tuple[
        NDArray[np.float32],
        float,
        bool,
        bool,
        dict[str, Any],
    ]:
        """Execute one step of the environment."""
        self._steps += 1

        linear_vel, angular_vel = action
        self._cmd_vel.publish(
            linear_vel=float(linear_vel), angular_vel=float(angular_vel)
        )

        time.sleep(self.env_config.dt)

        observation = self._get_observation()

        current_distance = self._get_distance_to_goal()
        info = self._get_info()

        reward = self._compute_reward(info)

        self._prev_distance = current_distance

        terminated = self._is_terminated()
        truncated = self._is_truncated()

        return observation, reward, terminated, truncated, info

    def _get_observation(self) -> NDArray[np.float32]:
        """Form observation from sensor data."""
        lidar_processed = self._process_lidar()

        if self._current_velocity is not None:
            prev_vel = np.array(
                [self._current_velocity[0], self._current_velocity[1]],
                dtype=np.float32,
            )
        else:
            prev_vel = np.array([0, 0], dtype=np.float32)

        rho, phi, yaw = self._get_goal_info()

        # Replace inf/nan with safe values
        rho = float(rho) if rho != float("inf") and not (rho != rho) else 10.0
        phi = float(phi) if not (phi != phi) else 0.0
        yaw = float(yaw) if not (yaw != yaw) else 0.0

        observation = np.concatenate(
            [
                lidar_processed,
                prev_vel,
                np.array([rho, phi]),
                np.array([yaw]),
            ],
            dtype=np.float32,
        )

        # Final safety check - replace any remaining nan/inf
        observation = np.nan_to_num(observation, nan=0.0, posinf=10.0, neginf=-10.0)

        return observation

    def _process_lidar(self) -> NDArray[np.float32]:
        """Process LiDAR data: front 180 degrees, batch to 10 values."""
        if self._current_scan is None:
            return np.zeros(10, dtype=np.float32)

        scan = self._current_scan
        n_rays = len(scan)

        front_start = n_rays // 4
        front_end = 3 * n_rays // 4
        front_scan = scan[front_start:front_end]

        batch_size = len(front_scan) // 10
        batched = []

        for i in range(10):
            start = i * batch_size
            end = start + batch_size
            batch_min = np.min(front_scan[start:end])
            batched.append(batch_min)

        batched = np.array(batched, dtype=np.float32)
        normalized = batched / self.robot_params.lidar_range
        normalized = np.clip(normalized, 0.0, 1.0)

        return normalized

    def _get_goal_info(self) -> tuple[float, float, float]:
        """Get goal information in polar coordinates."""
        if self._current_position is None or self._goal_position is None:
            return 0.0, 0.0, 0.0

        dx = self._goal_position[0] - self._current_position[0]
        dy = self._goal_position[1] - self._current_position[1]

        rho = np.sqrt(dx**2 + dy**2)
        phi = np.arctan2(dy, dx) - self._current_position[2]
        phi = np.arctan2(np.sin(phi), np.cos(phi))

        yaw = self._current_position[2]

        return float(rho), float(phi), float(yaw)

    def _get_distance_to_goal(self) -> float:
        """Get current distance to goal."""
        if self._current_position is None or self._goal_position is None:
            return float("inf")

        dx = self._goal_position[0] - self._current_position[0]
        dy = self._goal_position[1] - self._current_position[1]

        return float(np.sqrt(dx**2 + dy**2))

    def _get_heading_deviation(self) -> float:
        """Get heading deviation as cosine of angle to goal."""
        if self._current_position is None or self._goal_position is None:
            return 0.0
        dx = self._goal_position[0] - self._current_position[0]
        dy = self._goal_position[1] - self._current_position[1]
        angle_to_goal = np.arctan2(dy, dx)
        robot_yaw = self._current_position[2]

        heading_deviation = np.cos(angle_to_goal - robot_yaw)
        return float(heading_deviation)

    def _compute_reward(
        self,
        info: dict[str, Any],
    ) -> float:
        """Compute reward using function from case."""
        reward = self.reward_fn(info=info)

        return reward

    def _is_terminated(self) -> bool:
        """Check termination conditions."""
        distance = self._get_distance_to_goal()

        if distance < self.env_config.goal_threshold:
            return True

        if self._current_scan is not None:
            min_lidar = np.min(self._current_scan)
            if min_lidar < 0.1:
                return True

        return False

    def _is_truncated(self) -> bool:
        """Check truncation conditions."""
        if self._steps >= self.env_config.max_steps:
            return True

        return False

    def _get_info(self) -> dict[str, Any]:
        """Get additional information."""
        distance = self._get_distance_to_goal()
        prev_dist = self._prev_distance if self._prev_distance is not None else distance
        min_lidar = (
            np.min(self._current_scan)
            if self._current_scan is not None
            else float("inf")
        )

        return {
            "distance_to_goal": distance,
            "steps": self._steps,
            "position": self._current_position,
            "goal_position": self._goal_position,
            "prev_distance": prev_dist,
            "min_lidar": min_lidar,
            "heading_deviation": self._get_heading_deviation(),
        }

    def _quaternion_to_yaw(self, orientation: dict[str, float]) -> float:
        """Convert quaternion to yaw angle."""
        x = orientation["x"]
        y = orientation["y"]
        z = orientation["z"]
        w = orientation["w"]

        yaw = np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
        return float(yaw)


def make(case: Case, **kwargs) -> TurtleBotEnv:
    """Factory function to create TurtleBotEnv."""
    return TurtleBotEnv(case=case)
