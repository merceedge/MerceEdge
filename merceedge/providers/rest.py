""" REST API provider
    1. User-defined periodic API request
    2. API Webhook
"""
import json
import logging
import os
import requests
import six
import time
from swagger_parser import SwaggerParser
from swagger_tester.swagger_tester import (
    get_request_args,
    get_url_body_from_request,
    get_method_from_action
)

from merceedge.providers.base import ServiceProvider
from merceedge.const import (
    EVENT_TIME_CHANGED,
)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class RestApiProvider(ServiceProvider):

    def __init__(self, edge, config):
        """
        edge: MerceEdge instance
        config: user config
        """
        self._requesters = {}
        super(RestApiProvider, self).__init__(edge, config)
    
    def setup(self, edge, config):
        # do nothing now
        self.edge.bus.listen(EVENT_TIME_CHANGED, self.request_timer_handler)
        
    def _new_requester_setup(self, interface_name, interface_config, response_handler):
        """ Read input or output interface config(swagger 2.0 standard compliant).
            create rest api requester instance. if is_settimer is True, register periodic api requester
            in EventBus.
        """
        swagger_filename = interface_config.get('protocol').get('swagger_ref')
        swagger_file_fullpath = "{}/{}".format(self.config['OpenAPI']['swagger_path'], swagger_filename)
        # Get swagger parser instance
        app_client = requests
        swagger_parser = SwaggerParser(swagger_file_fullpath, use_example=False)
        
        # Create requester by swagger operationId
        operations = swagger_parser.operation.copy()
        operations.update(swagger_parser.generated_operation)
        request_path, request_action = operations.get(interface_config['protocol']['operationId'])
        
        request_args = get_request_args(request_path, request_action, swagger_parser)
        url, body, headers, files = get_url_body_from_request(request_path, request_path, request_args, swagger_parser)
        
        logger.info(u'regisiter requester {0} {1}'.format(request_action.upper(), url))

        self._requesters[interface_config['protocol']['operationId']] = \
                                                        (get_method_from_action(app_client, request_action), 
                                                        url, 
                                                        headers, 
                                                        body,
                                                        response_handler)


    def request_timer_handler(self, method, args):
        # TODO  corotutine requests?
        pass
        

    def _register_webhook_api(self):
        """ register webhook rest api, like:
        {domain or ip:port}/webhook/{component_name}/{interface_name}
        """
        # TODO
        raise NotImplementedError
    
    def conn_output_sink(self, output, callback):       
        # api response or webhook -> EventBus -> Wire input (output sink ) -> EventBus(Send) -> Service provider  
        self._new_requester_setup(output.name, output.attrs, callback)
        

    def conn_input_slot(self):
        """connect input interface on wire input slot """
        # TODO
        raise NotImplementedError

    def emit_input_slot(self, data):
        """send data to input slot"""
        # TODO 
        raise NotImplementedError
    
    


    