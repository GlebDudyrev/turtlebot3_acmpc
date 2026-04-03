import roslibpy

from ._base_service_client import BaseService


class SpawnEntityServiceClient(BaseService):
    def __init__(self, ros: roslibpy.Ros, service_name: str = '/spawn_entity'):
        super().__init__(ros, service_name, 'gazebo_msgs/SpawnEntity')

    def _build_request(
        self,
        *,
        name: str,
        xml: str,
        robot_namespace: str = '',
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        orientation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        reference_frame: str = 'world',
    ) -> roslibpy.ServiceRequest:
        px, py, pz = position
        ox, oy, oz, ow = orientation

        return roslibpy.ServiceRequest({
            'name': name,
            'xml': xml,
            'robot_namespace': robot_namespace,
            'initial_pose': {
                'position': {
                    'x': px,
                    'y': py,
                    'z': pz,
                },
                'orientation': {
                    'x': ox,
                    'y': oy,
                    'z': oz,
                    'w': ow,
                },
            },
            'reference_frame': reference_frame,
        })
