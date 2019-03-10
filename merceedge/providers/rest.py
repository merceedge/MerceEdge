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
# import asyncio
# import aiohttp
from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client

from swagger_parser import SwaggerParser
from swagger_tester.swagger_tester import (
    get_request_args,
    get_url_body_from_request,
    # get_method_from_action
)

from merceedge.providers.base import ServiceProvider
from merceedge.const import (
    EVENT_TIME_CHANGED,
    EVENT_EDGE_STOP
)
from merceedge.service import (
    Service,
    ServiceCall
)
from os.path import join
merce_edge_home = os.path.dirname(os.environ['MERCE_EDGE_HOME'])

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RestApiProvider(ServiceProvider):
    DOMAIN = 'swagger2.0'
    name=DOMAIN
    SERVICE_REST_REQUEST = 'rest_request'
    REST_REQUEST_EVNET = 'rest_request_event'
    def __init__(self, edge, config):
        """
        edge: MerceEdge instance
        config: user config
        """
        self._requesters = {}
        self.client = None

        super(RestApiProvider, self).__init__(edge, config)
    
    async def async_setup(self, edge, config):
        # setup request timer
        self.remove_request_timer_handler = self.edge.bus.async_listen(EVENT_TIME_CHANGED, self.request_timer_handler)

        self.edge.bus.async_listen_once(EVENT_EDGE_STOP, self.async_stop_rest)
    
    async def async_stop_rest(self, event):
        print("rest provider aborting...")
        self.remove_request_timer_handler()

    def _new_requester_setup(self, output, output_wire_params, response_handler):
        """ Read input or output interface config(swagger 2.0 standard compliant).
            Create rest api requester instance. if is_settimer is True, register periodic api requester
            in EventBus.
        """
        operation = self._get_request_attrs(output, output_wire_params)
        # logger.info(u'regisiter requester {0} {1}'.format(request_action.upper(), url))
        self.event_type = "{}_{}".format(self.REST_REQUEST_EVNET, output.id)
        self.edge.bus.async_listen(self.event_type, response_handler)
        self._requesters[output.get_attrs('operationId')] = \
                                                        (operation, 
                                                        response_handler)

    async def request_timer_handler(self, event):
        for op, _ in self._requesters.items():
            response = self.client.request(op).data
            # input callback
            self.edge.bus.async_fire(self.event_type, response)


    def _register_webhook_api(self):
        """ register webhook rest api, like:
        {domain or ip:port}/webhook/{component_name}/{interface_name}
        """
        # TODO
        raise NotImplementedError
    
    async def conn_output_sink(self, output, output_wire_params, callback):       
        # api response or webhook -> EventBus -> Wire input (output sink ) -> EventBus(Send) -> Service provider  
        self._new_requester_setup(output, output_wire_params, callback)

    def conn_input_slot(self):
        """connect input interface on wire input slot """
        # TODO init swagger client
        # self._init_swagger_client()
        pass

    def _init_swagger_client(self, interface, swagger_file_fullpath):
         # load Swagger resource file into App object
        app = App._create_(swagger_file_fullpath)
        # swagger security
        auth = Security(app)
        security = interface.get_attrs('security')
        for auth_key in security:
            auth.update_with(auth_key, security[auth_key]) # api key

        # init swagger client
        client = Client(auth)
        return client, app
    
    def _get_request_attrs(self, interface, interface_params={}):
        """Read input or output interface config(swagger 2.0 standard compliant).
        """
        swagger_filename = interface.get_attrs('swagger_ref')
        swagger_file_fullpath = os.path.join(merce_edge_home, self.config['OpenAPI']['swagger_path'], swagger_filename)

        # Get swagger parser instance
        swagger_parser = SwaggerParser(swagger_file_fullpath, use_example=False)
        
        # Create requester by swagger operationId
        operations = swagger_parser.operation.copy()
        operations.update(swagger_parser.generated_operation)
        request_path, request_action, tag = operations.get(interface.get_attrs('operationId'))
        
        # Get host and schemes
        host = swagger_parser.specification.get('host')
        schemes = swagger_parser.specification.get('schemes')
        request_args = interface_params
        url, body, headers, files = get_url_body_from_request(request_action, request_path, request_args, swagger_parser)
        url = "{}://{}{}".format(schemes[0], host, url)

        self.client, app = self._init_swagger_client(interface, swagger_file_fullpath)
        op = app.op[interface.get_attrs('operationId')](body=body, headers=headers)
        return op


    def disconn_output_sink(self, output):
        """ disconnect wire output sink
        """
        # Delete timer handler
        self.remove_request_timer_handler()
    
    async def emit_input_slot(self, input, payload):
        """send data to input slot, for rest api, invoide corotutine request.
        """
        op = self._get_request_attrs(input, payload)
        self.client.request(op)
