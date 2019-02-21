from merceedge.core import WireLoad

class WireloadTemplate(WireLoad):
    name = "wireload_template"
    """
    Version:
    Author:
    License:
    Description:
    """
    def __init__(self, edge, model_template_config, component_id=None, init_params={}):
        super(WireloadTemplate, self).__init__(edge, model_template_config, component_id, init_params)

    def before_run_setup(self):
        # TODO
        pass
    
    async def process(self, payload): 
         # TODO
         output1 = ''
         await self.put_output_payload(output_name='output1', payload=output1)