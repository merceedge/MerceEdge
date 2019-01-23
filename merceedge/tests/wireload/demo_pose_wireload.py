from merceedge.core import WireLoad

class PoseWireLoad(WireLoad):
    name = 'pose_wireload'
    
    def __init__(self, init_params={}):
        super(PoseWireLoad, self).__init__(init_params)
    
    def process(self, input_data):
        # TODO
        pass