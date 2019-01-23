
class Singleton(object):
    _instance = None

    def __new__(cls, edge, config):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls)  
        return cls._instance  


class ServiceProvider(Singleton):
    def __init__(self, edge, config):
        """
        edge: MerceEdge instance
        config: user config
        """
        self.edge = edge
        self.config = config
    
    def setup(self, edge, config):
        raise NotImplementedError
    
    # def new_instance_setup(self, interface_config, is_settimer=False):
    #     # default do nothing
    #     pass

    def conn_output_sink(self, output, output_wire_params, callback):
        # TODO mqtt client subscribe topic
        # Subscribe callback -> EventBus -> Wire input (output sink ) -> EventBus(Send) -> Service provider  
        raise NotImplementedError

    def conn_input_slot(self):
        """connect input interface on wire input slot """
        raise NotImplementedError

    def emit_input_slot(self, input, payload):
        """send data to input slot"""
        raise NotImplementedError

    def disconn_output_sink(self, output):
        """ disconnect wire output sink
        """
        raise NotImplementedError
