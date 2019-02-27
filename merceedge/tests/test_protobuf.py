
import pytest
import os

from merceedge.components.protobuf import ProtobufWireLoad
from merceedge.util.yaml import load_yaml
from merceedge.util.mock import MockEdge, gen_test_loop

protobuf_config = {
        'protobuf':
            {'generate_code_path': 'merceedge/components/protobuf_gen'}
    }
mock_edge = MockEdge(protobuf_config)

@pytest.mark.run(order=1)
@gen_test_loop(mock_edge)
async def test_protobuf_wireload():
   
    tests_path = os.path.dirname(os.path.realpath(__file__))
    protobuf_template_yml = load_yaml(os.path.join(tests_path, 'component_template', 'protobuf_component.yaml'))
    here = os.path.dirname(os.path.realpath(__file__))

    init_params = {
        'proto_file_path': os.path.join(here, 'test.proto'), 
        'message_name': 'ForeignMessage'
    }
    protobuf_wireload_obj = ProtobufWireLoad(edge=mock_edge,
                                  model_template_config=protobuf_template_yml,
                                  init_params=init_params)

    binary_output_payload = None 
    def get_binary_output(output_payload):
        global binary_output_payload
        binary_output_payload = output_payload


    # mock output
    protobuf_wireload_obj.emit_output_call = get_binary_output
    # Test json dict to protobuf binary
    # input
    input_payload = {
        "ForeignMessage": 
        {
            'c': 1,
            'd': [2, 3, 4]
        }
    }
    await protobuf_wireload_obj.process(input_payload)
    
    # Test protobuf binary to json dict
    def get_json_dict_output(output_payload):
        print("get_json_dict_output: -------", output_payload)
        assert output_payload == input_payload

    protobuf_wireload_obj.emit_output_call = get_json_dict_output
    await protobuf_wireload_obj.process(binary_output_payload)



   

    
    

        
