from ..case import Case
from ..registry import CaseRegistryInstance
from ..configs import CaseConfig, EnvConfig

nav_obstacles = Case(
    name="nav_obstacles",
    description="Navigation with obstacles",
    config=CaseConfig(
        name="nav_obstacles",
        env=EnvConfig(
            robot_name="burger",
            reward_fn="dense_goal",
        ),
    ),
)

CaseRegistryInstance.register("nav_obstacles", nav_obstacles)
