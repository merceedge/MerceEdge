from merceedge.core import WireLoad

class FilterWireLoad(WireLoad):
    
    name = 'filter_wireload'
    
    def __init__(self, init_params={}):
        super(FilterWireLoad, self).__init__(init_params)
        self.threshold = init_params.get('threshold')

    async def process(self, input_data):
        try:
            value = float(input_data)
        except ValueError:
            return
        
        if value > self.threshold:
            await self.put_output_payload(output_name="alert", payload=True)