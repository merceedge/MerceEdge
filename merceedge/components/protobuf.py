import os
import json
from google.protobuf.message import Message
from google.protobuf import json_format

from merceedge.core import WireLoad
from merceedge.util.module import load_modules
from merceedge.exceptions import (
    MerceEdgeError,
    ComponentNeedInitParamsError
)

merce_edge_home = os.path.dirname(os.environ['MERCE_EDGE_HOME'])


class ProtobufMessageDefineNotFound(MerceEdgeError):
    """ Raised when a protobuf message not fount in  specific proto file
    """
    def __init__(self, message_name, proto_file_path) -> None:
        """Initialize error."""
        super().__init__(
            self, "Message {} cannot found in {}".format(message_name, proto_file_path))
        self.message_name = message_name
        self.proto_file_path = proto_file_path


class ProtobufWireLoad(WireLoad):
    """ ProtobufWireLoad
        usage:
        json string or dict object <---> protobuf binary message  
    """
    name = 'protobuf'
    def __init__(self, edge, model_template_config, component_id=None, init_params=None):
        super(ProtobufWireLoad, self).__init__(edge, model_template_config, component_id, init_params)
        self.init_params = init_params
        # return dict python object
        self.return_object = init_params.get('return_object', True)
        self.before_run_setup()

    def before_run_setup(self):
        ############
        # generate message code
        #############

        proto_file_path = self.init_params.get('proto_file_path')
        if proto_file_path is None:
            raise ComponentNeedInitParamsError(self.__class__.__name__, 'proto_file_path')

        proto_include_path, proto_file = os.path.split(proto_file_path)
        # get genreate code path
        try:
            gen_code_path = self.edge.user_config["protobuf"]["generate_code_path"]
            gen_code_dst_path = os.path.join(merce_edge_home, gen_code_path)
        except KeyError:
            pass
            #TODO raise wireload load error exception
        # genrete code
        os.system("protoc -I={} --python_out={} {}".format(
                                                proto_include_path, gen_code_dst_path, proto_file_path))
        # load messager class modules dict
        msg_classes = load_modules(gen_code_dst_path, Message)

        self.message_name = self.init_params.get('message_name')
        if self.message_name is None:
            raise ComponentNeedInitParamsError(self.__class__.__name__, 'message_name')
        try:
            self.message_class = msg_classes[self.message_name]
        except KeyError:
            raise ProtobufMessageDefineNotFound(self.message_name, gen_code_dst_path)

    async def process(self, payload):
        output = None
        if isinstance(payload, dict): # dict
            output = self._dict_to_binary(payload)
        elif isinstance(payload, str): # json string or binary message
            try:
                # test payload is a json string
                json.loads(payload) 
                # json string to binary message
                output = self._json_txt_to_binary(payload)
            except (TypeError, OverflowError, ValueError):
                # binary message to json string
                if self.return_object:
                    output = self._binary_to_dict(payload)
                else:
                    output = self._binary_to_json_txt(payload)
        if output:
            await self.put_output_payload(output_name='output', payload=output)

    def _json_txt_to_binary(self, json_text):
        """ Parses a JSON representation of a protocol message into a message binary format.
        Args: 
            json_text: Message JSON representation.
        """
        message = self.message_class()
        try:
            message = json_format.Parse(json_text, message)
            binary =  message.SerializeToString()
        except json_format.ParseError:
            # TODO log
            return None
        return binary
    
    def _binary_to_json_txt(self, binary_message):
        """Converts protobuf message to JSON format
        """
        message = self.message_class()
        try:
            message.ParseFromString(binary_message)
            json_str = json_format.MessageToJson(message)
        except json_format.SerializeToJsonError:
            # TODO log
            return None
        return json_str
    
    def _dict_to_binary(self, json_dict):
        """Converts dict object to protobuf binary message
        """
        message = self.message_class()
        try:
            message = json_format.ParseDict(json_dict, message)
            binary =  message.SerializeToString()
        except json_format.ParseError:
            # TODO log
            return None
        return binary
    
    def _binary_to_dict(self, binary_message):
        """Converts protobuf binary message to dict object
        """
        message = self.message_class()
        try:
            message.ParseFromString(binary_message)
            dict_object = json_format.MessageToDict(message)
        except json_format.SerializeToJsonError:
            # TODO log
            return None
        return dict_object

    

