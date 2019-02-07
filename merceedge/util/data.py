PROTOCOL_BINARY = 0
PROTOCOL_JSON = 1
PROTOCOL_PROTOBUF = 2

struct_formats_char_map = {
        "interger_int8": "b",
        "interger_int16": "h",
        "interger_int32": "i",
        "interger_int64": "q",
        "interger_uint8": "B",
        "interger_uint16": "H",
        "interger_uint32": "I",
        "interger_uint64": "Q",
        "number_float": "f",
        "number_double": "d",
        "string_byte": "s",
        "string_binary": "p",
        "boolean": "?",
    }


class Data:
    """Data class responsible for protocol conversion
    TODO
    """
    def __init__(self, _type):
        self.origin_data = None # {}, binary or protobuf
        self.data = {} 
        self.schema = {}
        self.type = _type

    @property
    def content(self):
        return self.origin_data
    
    def set_schema(self, schema):
        self.schema = schema

    def _to_binary(self):
        """
        TODO nest data struct
        """
        pass
    
    def _to_json(self):
        pass

    def _to_protobuf(self):
        pass

    def _from_json(self, json_data):
        pass

    def _from_binary(self, binary_data):
        """TODO nest data struct
            binary to dict data
        """
    
    def _schema_to_struct_str(self, schema_name):
        """  convert json data schema to binary string list
        """
        # 1.  Get schema object from repo by name.
        

        pass


    def _from_protobuf(self, protobuf_data):
        pass


class DataSchemas:
    """ Data schema repository
    TODO
    """
    
    def __init__(self):
        self.schemas = {}
        """
        name: propreties
        name: {component_template_name}_{interface_name}
        """
    
    def get(self, component_template_name, interface_name):
        """
        """

        return self.schemas.get("{}_{}".format(component_template_name, interface_name))

    def load_swagger_spec(self, spec):
        """ Read swagger 2.0 spec part
        """
        pass
    
     
    


    


