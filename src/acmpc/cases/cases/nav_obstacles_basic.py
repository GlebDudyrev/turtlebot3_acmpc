from ..case import Case
from ..configs import CaseConfig, EnvConfig
from ..registry import CaseRegistryInstance

nav_obstacles_basic = Case(
    name="nav_obstacles_basic",
    description="Navigation with obstacles - basic reward",
    config=CaseConfig(
        name="nav_obstacles_basic",
        env=EnvConfig(
            robot_name="burger",
            reward_fn="basic_reward",
        ),
    ),
)

CaseRegistryInstance.register("nav_obstacles_basic", nav_obstacles_basic)
