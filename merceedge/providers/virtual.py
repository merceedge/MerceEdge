from merceedge.providers.base import (
    ServiceProvider
)

class VirtualInterfaceProvider(ServiceProvider):
    DOMAIN = 'virtual'
    name=DOMAIN
    VIRTUAL_WIRE_EVENT = "virtual_wire_event"

    def __init__(self, edge, config):
        """
        edge: MerceEdge instance
        config: user config
        """
        super(VirtualInterfaceProvider, self).__init__(edge, config)
        self.output = None
    
    async def async_setup(self, edge , config):
        pass
        # do nothing now.
    
    async def conn_output_sink(self, output, output_wire_params, callback):
        # Subscribe callback -> EventBus -> Wire input (output sink ) -> EventBus(Send) -> Service provider  
        pass
        # 虚拟连线输出事件监听注册
        print("virtual conn_output_sink***********")
        self.output = output
        self.edge.bus.async_listen("{}_{}_{}".format(self.VIRTUAL_WIRE_EVENT, 
                                                     output.component.id,
                                                    output.name), callback)

    async def conn_input_slot(self, input, input_wire_params):
        """connect input interface on wire input slot """
        pass

    async def emit_input_slot(self, input, payload):
        """直接把数据放入组件的输入数据队列，并创建异步任务"""
        await input.component.put_input_payload(payload)
        # print("output:", self.output)
        # if self.output:
        #     await input.component.emit_output_payload("{}_{}".format(self.VIRTUAL_WIRE_EVENT, self.output.id))

    async def disconn_output_sink(self, output):
        """ disconnect wire output sink
        """
        raise NotImplementedError
