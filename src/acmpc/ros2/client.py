"""ROS2 client for connecting to rosbridge."""

import logging

import roslibpy


LOGGER = logging.getLogger(__name__)


class RosBridgeClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.client = roslibpy.Ros(host=host, port=port)
        self.client.on_ready(self._on_ready)
        self.client.on('close', self._on_close)
        self.client.on('error', self._on_error)

    def _on_ready(self):
        LOGGER.info('Connected to ws://', self.host, ':', self.port)

    def _on_close(self):
        LOGGER.info('Connection closed')

    def _on_error(self, error):
        LOGGER.error('Connection error:', error)

    def connect(self):
        if self.client.is_connected:
            LOGGER.warning('Client already connected.')
        elif self.client.is_connecting:
            LOGGER.warning('Connection is already in pregress.')
        else:
            LOGGER.info(f'Attempting connection to ws://', self.host, ':', self.port)
            self.client.run()

    def disconnect(self, terminate: bool = True):
        if not self.client.is_connected and not self.client.is_connecting:
            LOGGER.warning('Client is already disconnected')
            return

        LOGGER.info('Disconnecting client...')

        if terminate:
            self.client.terminate()
        else:
            self.client.close()

    @property
    def is_connected(self) -> bool:
        return self.client.is_connected
    
    @property
    def topics(self):
        return self._topics
