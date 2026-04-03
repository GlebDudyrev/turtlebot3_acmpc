from pydantic import BaseModel, ConfigDict, Field


class RobotParams(BaseModel):
    """Physical and kinematic parameters for a robot."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Robot name")
    max_linear_vel: float = Field(gt=0, description="Maximum linear velocity (m/s)")
    max_angular_vel: float = Field(gt=0, description="Maximum angular velocity (rad/s)")
    max_linear_acc: float = Field(
        gt=0, description="Maximum linear acceleration (m/s²)"
    )
    max_angular_acc: float = Field(
        gt=0, description="Maximum angular acceleration (rad/s²)"
    )
    wheel_radius: float = Field(gt=0, description="Wheel radius (m)")
    wheel_base: float = Field(gt=0, description="Wheel base length (m)")
    lidar_range: float = Field(gt=0, description="LiDAR maximum range (m)")
    lidar_rays: int = Field(gt=0, description="Number of LiDAR rays")
    lidar_fov: float = Field(gt=0, description="LiDAR field of view (rad)")
