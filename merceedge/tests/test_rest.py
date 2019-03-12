# swagger 2.0 provider unit test case


import pytest
import os

from merceedge.providers.rest import RestApiProvider
from merceedge.util.yaml import load_yaml
from merceedge.util.mock import MockEdge, gen_test_loop
from merceedge.core import Component, Output, Input
from merceedge.core import _async_create_timer

__config__ = {
    "OpenAPI":
    {
        "swagger_path": "merceedge/tests/swagger_ref"
    }
}
mock_edge = MockEdge(__config__)

@pytest.mark.run(order=1)
@gen_test_loop(mock_edge)
async def test_rest_provider():
    test_config = __config__

    new_provider_obj = RestApiProvider(edge=mock_edge,
                                       config=test_config)

    # 1. Test asnyc setup
    await new_provider_obj.async_setup(mock_edge, test_config)
    
     # 2. Test conn_output_sink
    mock_component = Component(mock_edge, {"component": {}})
    mock_output = Output(mock_edge, "test_output", mock_component)
    output_attrs = {
        "swagger_ref": "petstore_api.yaml",
        "operationId": "findPetsByTags",
        "security": {
            "api_key": "12312312312312312313q",
            "petstore_auth": "12334546556521123fsfss"
        }
    }
    mock_output.set_attrs(output_attrs)
    def output_sink_callback(payload):
        print(payload)
        # TODO assert ..
    mock_output_params = {
        "tags": ["blackcat"]
    }
    await new_provider_obj.conn_output_sink(mock_output, mock_output_params, output_sink_callback)

    # start timer event
    # _async_create_timer(mock_edge)
    await new_provider_obj.request_timer_handler(event="")

