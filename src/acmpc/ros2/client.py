"""ROS2 client for connecting to rosbridge."""

import roslibpy


class RosClient:
    """Context manager для подключения к rosbridge."""

    def __init__(self, host: str = "localhost", port: int = 9090, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._client: roslibpy.Ros | None = None

    def __enter__(self) -> "RosClient":
        self._client = roslibpy.Ros(host=self.host, port=self.port)
        self._client.run()
        return self

    def __exit__(self, *args):
        if self._client:
            self._client.terminate()

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    @property
    def client(self) -> roslibpy.Ros:
        """Получить raw roslibpy.Ros клиент."""
        if self._client is None:
            raise RuntimeError("RosClient not connected. Use context manager.")
        return self._client
