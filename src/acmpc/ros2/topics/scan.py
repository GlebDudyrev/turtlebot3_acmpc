import math
from typing import Callable, Any
import roslibpy

from ._subscriber import Subscriber


class LaserScanSubscriber(Subscriber):
    def __init__(self, ros: roslibpy.Ros, callback: Callable):
        super().__init__(ros, '/scan', 'sensor_msgs/LaserScan', callback)

    def parse_message(self, message: roslibpy.Message) -> dict[str, Any]:
        raw_ranges = message['ranges']
        range_min = message['range_min']
        range_max = message['range_max']

        ranges_with_angles = []
        for i, value in enumerate(raw_ranges):
            angle = message['angle_min'] + i * message['angle_increment']
            ranges_with_angles.append({
                'index': i,
                'angle': angle,
                'distance': value,
            })

        return {
            'frame_id': message['header']['frame_id'],
            'stamp': message['header']['stamp'],
            'angle_min': message['angle_min'],
            'angle_max': message['angle_max'],
            'angle_increment': message['angle_increment'],
            'range_min': range_min,
            'range_max': range_max,
            'ranges': raw_ranges,
            'intensities': message.get('intensities', []),
            'ranges_with_angles': ranges_with_angles,
        }

    def handle(self, parsed_message):
        self.callback(parsed_message)
