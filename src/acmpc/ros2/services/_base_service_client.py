import logging
from typing import Callable
from abc import ABC, abstractmethod
import roslibpy


LOGGER = logging.getLogger(__name__)


class BaseServiceClient(ABC):
    def __init__(self, ros: roslibpy.Ros, name: str, service_type: str):
        self.ros = ros
        self.name = name
        self.service_type = service_type
        self.service = roslibpy.Service(ros, name, service_type)

        LOGGER.info('Created service ', self.name)

    def call(self, *args, timeout: int = 5, **kwargs) -> roslibpy.ServiceResponse:
        if not self.ros.is_connected:
            raise RuntimeError('ROS bridge is not connected')
        
        LOGGER.debug('Call sync service ', self.name)

        request = self._build_request(*args, **kwargs)
        response = self.service.call(request, timeout=timeout)

        if not response.get('success', False):
            raise RuntimeError(f"Service completed but returned failure: {response}")
        
        return response
    
    def call_async(self, callback: Callable, errback:Callable | None = None, *args, **kwargs):
        if not self.ros.is_connected:
            raise RuntimeError('ROS bridge is not connected')

        LOGGER.debug('Call async service ', self.name)

        request = self.build_request(*args, **kwargs)
        self.service.call(request, callback=callback, errback=errback)

    @abstractmethod
    def _build_request(self, *args, **kwargs) -> roslibpy.ServiceRequest:
        pass
