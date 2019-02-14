from merceedge.providers.base import (
    ServiceProvider,
    Singleton
)

class VirtualInterfaceProvider(ServiceProvider):
    DOMAIN = 'virtual'
    name=DOMAIN

    def __init__(self, edge, config):
        """
        edge: MerceEdge instance
        config: user config
        """
        super(VirtualInterfaceProvider, self).__init__(edge, config)
    
    async def async_setup(self, edge , config):
        pass
        # do nothing now.
    
    async def conn_output_sink(self, output, output_wire_params, callback):
        # Subscribe callback -> EventBus -> Wire input (output sink ) -> EventBus(Send) -> Service provider  
        pass
        # do nothing

    async def conn_input_slot(self, input, conn_input_slot):
        """connect input interface on wire input slot """
        pass

    async def emit_input_slot(self, input, payload):
        """直接把数据放入组件的输入数据队列，并创建异步任务"""
        await input.component.put_input_payload(payload)

    async def disconn_output_sink(self, output):
        """ disconnect wire output sink
        """
        raise NotImplementedError
