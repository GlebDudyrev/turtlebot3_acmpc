from .cases import app as cases_app
from .doctor import app as doctor_app
from .rewards import app as rewards_app
from .robots import app as robots_app
from .sim import app as sim_app
from .train import train


__all__ = [
    "cases_app",
    "doctor_app",
    "rewards_app",
    "robots_app",
    "sim_app",
    "train"
]
