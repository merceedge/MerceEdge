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
    get_method_from_action
)

from merceedge.providers.base import ServiceProvider
from merceedge.const import (
    EVENT_TIME_CHANGED,
)
from merceedge.service import (
    Service,
    ServiceCall
)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ATTR_URL = 'url'
ATTR_PAYLOAD = 'payload'
ATTR_HEADERS = 'headers'
ATTR_ACTION = 'action'
ATTR_ACTION = 'files'


class RestApiProvider(ServiceProvider):
    DOMAIN = 'rest'
    SERVICE_REST_REQUEST = 'rest_request'
    def __init__(self, edge, config):
        """
        edge: MerceEdge instance
        config: user config
        """
        self._requesters = {}
        super(RestApiProvider, self).__init__(edge, config)
    
    def setup(self, edge, config):
        # setup request timer
        self.edge.bus.listen(EVENT_TIME_CHANGED, self.request_timer_handler)

        # setup request service
        self.edge.services.register(self.DOMAIN, self.SERVICE_REST_REQUEST, self._request_service)
    
    def _request_service(self, call: ServiceCall):
        """Handle REST API request service calls"""
        url = call.data.get(ATTR_URL)
        body = call.data.get(ATTR_PAYLOAD)
        headers = call.data.get(ATTR_HEADERS)
        action = call.data.get(ATTR_ACTION)
        # request
        api_client = requests
        response = get_method_from_action(api_client, action)(url, 
                                                              headers=dict(headers),
                                                              data=body)
        logger.info(u"request service response: {} {}".format(response.status_code, response.text))
        
    def _new_requester_setup(self, output, response_handler):
        """ Read input or output interface config(swagger 2.0 standard compliant).
            create rest api requester instance. if is_settimer is True, register periodic api requester
            in EventBus.
        """
        request_action, url, body, headers, files = self._get_request_args(output)
        logger.info(u'regisiter requester {0} {1}'.format(request_action.upper(), url))

        self._requesters[output.get_attrs('operationId')] = \
                                                        (request_action.upper(), 
                                                        url,
                                                        headers, 
                                                        body,
                                                        response_handler)

    def request_timer_handler(self):
        # corotutine requests
        async def request(session, action, url, headers, body, response_handler):
                response = await session.request(action, url=url, headers=headers, body=body)
                wire_payload = await response.json()
                logger.info(u'{} {} response: {}'.format(action, url, wire_payload))
                # wire fire output
                response_handler(wire_payload)
                return wire_payload
                 
        async def request_all():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for operationId, args in self._requesters:
                    tasks.append(
                        request(session, args[0], args[1], args[2], args[3], args[4]))
                responses = await asyncio.gather(*tasks, return_exceptions=False)
                return responses
        
        asyncio.run(request_all())

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
    
    def _get_request_args(self, name, interface):
        """Read input or output interface config(swagger 2.0 standard compliant).
        """
        swagger_filename = interface.get_attrs('swagger_ref')
        swagger_file_fullpath = "{}/{}".format(self.config['OpenAPI']['swagger_path'], swagger_filename)
        # Get swagger parser instance
        swagger_parser = SwaggerParser(swagger_file_fullpath, use_example=False)
        
        # Create requester by swagger operationId
        operations = swagger_parser.operation.copy()
        operations.update(swagger_parser.generated_operation)
        request_path, request_action = operations.get(interface.get_attrs('operationId'))
        
        request_args = get_request_args(request_path, request_action, swagger_parser)
        url, body, headers, files = get_url_body_from_request(request_path, request_path, request_args, swagger_parser)
        return request_action, url, body, headers, files

    def emit_input_slot(self, input, payload):
        """send data to input slot, for rest api, invoide corotutine request.
        """
        request_action, url, body, headers, files = self._get_request_args(input)
        logger.info(u'requester {0} {1}'.format(request_action.upper(), url))
        # Call rest request service
        data = {ATTR_ACTION: request_action,
                ATTR_URL: url,
                ATTR_PAYLOAD: payload,
                ATTR_HEADERS: headers}
        self.edge.services.call(self.DOMAIN, self.SERVICE_REST_REQUEST, data)
        



        
        
    

    


    