from ..case import Case
from ..configs import CaseConfig, EnvConfig
from ..registry import CaseRegistryInstance

nav_obstacles_advanced = Case(
    name="nav_obstacles_advanced",
    description="Navigation with obstacles - advanced reward",
    config=CaseConfig(
        name="nav_obstacles_advanced",
        env=EnvConfig(
            robot_name="burger",
            reward_fn="advanced_reward",
        ),
    ),
)

CaseRegistryInstance.register("nav_obstacles_advanced", nav_obstacles_advanced)
