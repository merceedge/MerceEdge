from enum import Enum
from collections import OrderedDict

"""Support Data protocol type
"""
DATA_PROTOCOL_BINARY_TYPE = 'binary'
DATA_PROTOCOL_JSON_TYPE = 'json'
DATA_PROTOCOL_PROTOBUF_TYPE = 'protobuf'
DATA_PROTOCOL_OBJECT_TYPE = 'object' # python object data

DataProtocol = Enum('DataProtocol', (DATA_PROTOCOL_BINARY_TYPE, 
                                     DATA_PROTOCOL_JSON_TYPE,
                                     DATA_PROTOCOL_PROTOBUF_TYPE,
                                     DATA_PROTOCOL_OBJECT_TYPE))

""" Data Schema type
"""
DATA_SCHEMA_MERCEEDGE_TYPE = 'merceedge'
DATA_SCHEMA_SWAGGER_TYPE = 'swagger'
DATA_SCHEMA_PROTOBUF_TYPE = 'protobuf'

DataSchemaType = Enum('DataSchemaType', (DATA_SCHEMA_MERCEEDGE_TYPE, 
                                     DATA_SCHEMA_SWAGGER_TYPE, 
                                     DATA_SCHEMA_PROTOBUF_TYPE))

""" Support data type
"""
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

class DataType:
    def __init__(self, datatype: str, format=None):
        self.datatype = datatype
        self.format = None
    
    @property
    def datatype(self):
        if self.format is None:
            if self.datatype == 'interger':
                self.format = 'int64'
            elif self.datatype == 'number':
                self.format == 'double'
            elif self.datatype == 'string':
                self.format = 'byte'
            elif self.datatype == 'boolean':
                self.format = ''
        return "{}_{}".format(self.datatype, self.format)
    
    @property
    def guess_type(self, value):
        # TODO
        pass



class DataSchema:
    """  ABC schema object parser  class
    转换 yaml node 到 schema结构
    """
    schema_type = None
    def __init__(self, component_yml, interface_type, interface_flat_name):
        self.component_yml = component_yml
        self.interface_type = interface_type
        self.interface_flat_name = interface_flat_name

        self.schema_flat_name = None
        self.schema_yml = None
        """
        schema is a python ordered dict object, example:
        schema = {"simple_porprety1": "boolean", "simple_porprety2": "interger_int64",
                  "nest_proprety1": {"sub_porprety1": "string_byte"},
                  ...
                  }
        """
        self.schema = OrderedDict()
    
    @property
    def schema_flat_name(self):
        raise NotImplementedError

    @property
    def schema_object(self) -> OrderedDict:
        raise NotImplementedError

    @property
    def schema_yml(self):
        raise NotImplementedError

    # def _schema_to_struct_str(self, schema_name):
    #     """  convert json data schema to binary string list
    #     """
    #     # 1.  Get schema object from repo by name.

    #     pass


class MerceEdgeSchema(DataSchema):
    schema_type = DATA_SCHEMA_MERCEEDGE_TYPE
    
    def __init__(self, component_yml, interface_type, interface_flat_name):
        super(MerceEdgeSchema, self).__init__(component_yml, interface_type, interface_flat_name)

    @property
    def schema_flat_name(self):
        raise NotImplementedError
        #TODO

    @property
    def schema_object(self) -> OrderedDict:
        raise NotImplementedError
        #TODO

    @property
    def schema_yml(self):
        raise NotImplementedError 
        #TODO


class SwaggerSchema(DataSchema):
    schema_type = DATA_SCHEMA_SWAGGER_TYPE
    def __init__(self, component_yml, interface_type, interface_flat_name):
        super(SwaggerSchema, self).__init__(component_yml, interface_type, interface_flat_name)

    @property
    def schema_flat_name(self):
        raise NotImplementedError
        #TODO

    @property
    def schema_object(self) -> OrderedDict:
        raise NotImplementedError
        #TODO

    @property
    def schema_yml(self):
        raise NotImplementedError 
        #TODO


class ProtobufSchema(DataSchema):
    schema_type = DATA_SCHEMA_PROTOBUF_TYPE
    def __init__(self, component_yml, interface_type, interface_flat_name):
        super(ProtobufSchema, self).__init__(component_yml, interface_type, interface_flat_name)

    @property
    def schema_flat_name(self):
        raise NotImplementedError
        #TODO

    @property
    def schema_object(self) -> OrderedDict:
        raise NotImplementedError
        #TODO

    @property
    def schema_yml(self):
        raise NotImplementedError 
        #TODO


class DataSchemaFactory:
    _data_schema_cls = {
        DATA_SCHEMA_MERCEEDGE_TYPE: MerceEdgeSchema,
        DATA_SCHEMA_SWAGGER_TYPE: SwaggerSchema,
        DATA_SCHEMA_PROTOBUF_TYPE: ProtobufSchema
    }
    
    @classmethod
    def get_data_schema(cls, schema_type:str, interface_yml_node):
        # TODO raise no such schema class exception
        schema_cls = cls._data_schema_cls.get(schema_type)
        return schema_cls(interface_yml_node)


class Data:
    """ABC Data class responsible for protocol conversion.
    """
    protocol_type = None

    def __init__(self, origin_value, schema: DataSchema):
        self.origin_value = None # json, binary or protobuf
        """
        value: {"proprety1": value, 
                "nest_property1": [value, value, ...],
                "nest_property2": {"sub_property1": value, ...},
                ...}
        """
        self.value = {} # converted value 
        self.schema = schema

    @property
    def converted(self):
        return self.value

    @converted.setter
    def converted(self, value: dict):
        self.value = value

    @property
    def protocol(self) -> DataProtocol:
        return DataProtocol[self.protocol_type]
        
    def unpack(self):
        """ Origin value to convert
        """
        raise NotImplementedError
    
    def pack(self):
        """ Converted value to origin
        """
        raise NotImplementedError


class BinaryData(Data):
    protocol_type = DATA_PROTOCOL_BINARY_TYPE
    
    def unpack(self):
        """ Origin value to convert
        """
        raise NotImplementedError
    
    def pack(self):
        """ Converted value to origin
        """
        raise NotImplementedError

class JsonData(Data):
    protocol_type = DATA_PROTOCOL_JSON_TYPE
    pass

class ProtobufData(Data):
    protocol_type = DATA_PROTOCOL_PROTOBUF_TYPE
    pass



class DataFactory:
    _dataClass = {
            DATA_PROTOCOL_BINARY_TYPE: BinaryData,
            DATA_PROTOCOL_JSON_TYPE: JsonData,
            DATA_PROTOCOL_PROTOBUF_TYPE: ProtobufData
        }

    @classmethod
    def get_data(cls, protocol: str, value, schema: DataSchema):
        # TODO raise no such protocol exception
        _cls = cls._dataClass.get(protocol)
        return _cls(value, schema)


class DataSchemaRepository:
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
     
    


    


