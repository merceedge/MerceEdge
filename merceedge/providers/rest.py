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
import asyncio
import aiohttp

from swagger_parser import SwaggerParser
from swagger_tester.swagger_tester import (
    get_request_args,
    get_url_body_from_request,
    # get_method_from_action
)

from merceedge.providers.base import ServiceProvider
from merceedge.const import (
    EVENT_TIME_CHANGED,
)
from merceedge.service import (
    Service,
    ServiceCall
)
from os.path import join
dir_path = os.path.dirname(os.environ['MERCE_EDGE_HOME'])

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ATTR_URL = 'url'
ATTR_PAYLOAD = 'payload'
ATTR_HEADERS = 'headers'
ATTR_ACTION = 'action'
ATTR_ACTION = 'files'

_HTTP_METHODS = ['put', 'post', 'get', 'delete', 'options', 'head', 'patch']

class RestApiProvider(ServiceProvider):
    DOMAIN = 'swagger2.0'
    name=DOMAIN
    SERVICE_REST_REQUEST = 'rest_request'
    def __init__(self, edge, config):
        """
        edge: MerceEdge instance
        config: user config
        """
        self._requesters = {}
        super(RestApiProvider, self).__init__(edge, config)
    
    async def async_setup(self, edge, config):
        # setup request timer
        self.edge.bus.async_listen(EVENT_TIME_CHANGED, self.request_timer_handler)

        # setup request service
        self.edge.services.async_register(self.DOMAIN, 
                                          self.SERVICE_REST_REQUEST, 
                                          self.async_request_service)
    
    def _get_method_from_action(self, client, action):
        """ Get aiohttp action request method
        """
        error_msg = "Action '{0}' is not recognized; needs to be one of {1}.".format(action, str(_HTTP_METHODS))
        assert action in _HTTP_METHODS, error_msg

        return client.__getattribute__(action)


    async def async_request_service(self, call: ServiceCall):
        """Handle REST API request service calls"""
        # print("_request_service!!!")
        url = call.data.get(ATTR_URL)
        body = call.data.get(ATTR_PAYLOAD) or {}
        headers = call.data.get(ATTR_HEADERS) or {}
        action = call.data.get(ATTR_ACTION)
        # request
        api_client = requests
        method = self._get_method_from_action(api_client, action)
        response =  method(url=url, 
                                                          headers=dict(headers),
                                                          data=body)
        logger.info(u"request service response: {} {}".format(response.status_code, response.text))
        
    def _new_requester_setup(self, output, output_wire_params, response_handler):
        """ Read input or output interface config(swagger 2.0 standard compliant).
            Create rest api requester instance. if is_settimer is True, register periodic api requester
            in EventBus.
        """
        request_action, url, body, headers, files = self._get_request_attrs(output, output_wire_params)
        logger.info(u'regisiter requester {0} {1}'.format(request_action.upper(), url))

        self._requesters[output.get_attrs('operationId')] = \
                                                        (request_action, 
                                                        url,
                                                        body,
                                                        headers, 
                                                        response_handler)

    async def request_timer_handler(self, event):
        print("*"*30)
        print(event)
        for operationId, args in self._requesters.items():
            # request_action, url, body, headers, files
            data = {
                ATTR_ACTION: args[0],
                ATTR_URL: args[1],
                ATTR_PAYLOAD: args[2],
                ATTR_HEADERS: args[3]}
            await self.edge.services.async_call(self.DOMAIN, self.SERVICE_REST_REQUEST, data)

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
        # TODO
        raise NotImplementedError
    
    def _get_request_attrs(self, interface, interface_params={}):
        """Read input or output interface config(swagger 2.0 standard compliant).
        """
        swagger_filename = interface.get_attrs('swagger_ref')
        swagger_file_fullpath = os.path.join(dir_path, self.config['OpenAPI']['swagger_path'], swagger_filename)
        # Get swagger parser instance
        swagger_parser = SwaggerParser(swagger_file_fullpath, use_example=False)
        
        # Create requester by swagger operationId
        operations = swagger_parser.operation.copy()
        operations.update(swagger_parser.generated_operation)
        request_path, request_action, tag = operations.get(interface.get_attrs('operationId'))
        
        # Get host and schemes
        host = swagger_parser.specification.get('host')
        schemes = swagger_parser.specification.get('schemes')
        # TODO Get auth
        # request_args = get_request_args(request_path, request_action, swagger_parser)
        request_args = interface_params
        url, body, headers, files = get_url_body_from_request(request_action, request_path, request_args, swagger_parser)
        url = "{}://{}{}".format(schemes[0], host, url)
        return request_action, url, body, headers, files

    async def emit_input_slot(self, input, payload):
        """send data to input slot, for rest api, invoide corotutine request.
        """
        request_action, url, body, headers, files = self._get_request_attrs(input, payload)
     
        logger.info(u'requester {0} {1}'.format(request_action.upper(), url))
        # Call rest request service
        data = {ATTR_ACTION: request_action,
                ATTR_URL: url,
                ATTR_PAYLOAD: body or {},
                ATTR_HEADERS: headers or {}}
        await self.edge.services.async_call(self.DOMAIN, self.SERVICE_REST_REQUEST, data)
