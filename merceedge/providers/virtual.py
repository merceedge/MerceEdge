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

    async def conn_input_slot(self, input):
        """connect input interface on wire input slot """
        # 注册输入（Input）组件监听的输出事件类型（输出组件id_输出接口名称），监听者为虚拟组件聚合的Input对象callback函数
        input_slot_wires = input.input_wires
        for wire_id, wire in input_slot_wires.items():
            outcom_id = wire.output_sink.component.id
            out_name = wire.output_sink.name
            event_type = "{}_{}".format(outcom_id, out_name)
            self.edge.bus.async_listen(event_type, input.emit_data_to_input)

    async def emit_input_slot(self, input, payload):
        """直接把数据放入组件的输入数据队列，并创建异步任务"""
        await input.component.put_payload(payload)

    async def disconn_output_sink(self, output):
        """ disconnect wire output sink
        """
        raise NotImplementedError
