from merceedge.core import WireLoad
from collections import deque
import numpy as np

class StreamAnaylsisWireLoad(WireLoad):
    """
    This  stream analysis wireload class calculates the average temperature over 
    a rolling 30 period. When the average temperature reaches 70, 
    the wireload sends an alert for the device to take action.
    """
    name = 'stream_analysis_wireload'
    
    def __init__(self, init_params={}):
        super(StreamAnaylsisWireLoad, self).__init__(init_params)
        self.analysis_array_len = init_params.get('analysis_array_len', 30)
        self.threshold = init_params.get('threshold')
        self.before_run_setup()

    def before_run_setup(self):
        self.data = deque(maxlen=self.analysis_array_len)
    
    def process(self, input_data):
        self.data.append(input_data)
        mean_value = np.mean(list(self.data))
        if mean_value > self.threshold:
            await self.put_output_payload(output_name="alert", payload=True)

