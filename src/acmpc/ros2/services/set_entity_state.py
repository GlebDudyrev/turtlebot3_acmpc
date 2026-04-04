import roslibpy

from ._base_service_client import BaseServiceClient


class SetEntityStateServiceClient(BaseServiceClient):
    def __init__(self, ros: roslibpy.Ros, service_name: str = "/set_entity_state"):
        super().__init__(ros, service_name, "gazebo_msgs/SetEntityState")

    def _build_request(
        self,
        *,
        name: str,
        position: tuple[float, float, float],
        orientation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        linear: tuple[float, float, float] = (0.0, 0.0, 0.0),
        angular: tuple[float, float, float] = (0.0, 0.0, 0.0),
        reference_frame: str = "world",
    ) -> roslibpy.ServiceRequest:
        px, py, pz = position
        ox, oy, oz, ow = orientation
        lx, ly, lz = linear
        ax, ay, az = angular

        return roslibpy.ServiceRequest(
            {
                "state": {
                    "name": name,
                    "pose": {
                        "position": {
                            "x": px,
                            "y": py,
                            "z": pz,
                        },
                        "orientation": {
                            "x": ox,
                            "y": oy,
                            "z": oz,
                            "w": ow,
                        },
                    },
                    "twist": {
                        "linear": {
                            "x": lx,
                            "y": ly,
                            "z": lz,
                        },
                        "angular": {
                            "x": ax,
                            "y": ay,
                            "z": az,
                        },
                    },
                    "reference_frame": reference_frame,
                }
            }
        )
