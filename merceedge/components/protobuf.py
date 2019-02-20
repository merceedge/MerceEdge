from merceedge.core import WireLoad

class ProtobufWireLoad(WireLoad):
    """
        json <---> protobuf
    """
    def __init__(self, edge, model_template_config, component_id=None, init_params=None):
        super(ProtobufWireLoad, self).__init__(edge, model_template_config, component_id, init_params)
        self.before_run_setup()
    
    async def process(self, payload):
        pass
        #TODO
    
    def json_to_protobuf(self, input):
        pass
        # TODO
    
    def protobuf_to_json(self, input):
        pass
        #TODO

    

