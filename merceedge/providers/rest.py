""" REST API provider
    1. User-defined periodic API request
    2. API Webhook
"""
from merceedge.providers.base import (
    ServiceProvider
)

class RestApiProvider(ServiceProvider):

    def __init__(self, edge, config):
        # TODO
        pass

    def _read_config(self):
        """ Read input or output interface config part(swagger 3.x standard compliant).
        """
        # TODO
        pass

    def _register_webhook_api(self):
        """ register webhook rest api, like:
        {domain or ip:port}/webhook/{component_name}/{interface_name}
        """
        # TODO
        pass
    
    def setup(self, edge, config):
        raise NotImplementedError

    def conn_output_sink(self):       
        # TODO api response or webhook -> EventBus -> Wire input (output sink ) -> EventBus(Send) -> Service provider  
        raise NotImplementedError

    def conn_input_slot(self):
        """connect input interface on wire input slot """
        raise NotImplementedError

    def emit_input_slot(self, data):
        """send data to input slot"""
        raise NotImplementedError
    
    


    