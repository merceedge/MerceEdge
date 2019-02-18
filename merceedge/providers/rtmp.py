from threading import Thread
import cv2
import numpy as np
import time

from merceedge.providers.base import ServiceProvider
from merceedge.const import EVENT_EDGE_STOP

class RTMPProvider(ServiceProvider):
    """ Receive video stream from rtmp url and convert to video frame data.
    """
    DOMAIN = "rtmp"
    name=DOMAIN
    RTMP_FRAME_EVENT = 'rtmp_frame'

    def __init__(self, edge, config):
        super(RTMPProvider, self).__init__(edge, config)
        self.abort_immediately = False

    async def async_setup(self, edge, config):
        print("async setup: ", self.name)
        self.edge.bus.async_listen_once(EVENT_EDGE_STOP, self.async_stop_rtmp)
    
    async def async_stop_rtmp(self, event):
        """Stop RTMP."""
        print("rtmp provider aborting...")
        self.abort_immediately = True
        self.t.join()
    
    def _rtmp_pull_stream(self, rtmp_id, rtmp_url, params, callback):
        """
            TODO user params
        """
        stream = cv2.VideoCapture(rtmp_url)
        while True:
            
            if self.abort_immediately:
                print('rtmp provider thread exit')
                return
            grabbed, frame = stream.read()
            # if the frame was not grabbed, then we have reached the end
            # of the stream
            if not grabbed:
                break
            
            time.sleep(0.08)
            # callback(frame)
            self.edge.bus.async_fire("{}_{}".format(self.RTMP_FRAME_EVENT, self.output.id), frame)
            

    def _new_rtmp_client(self, rtmp_id, rtmp_url, params, callback):
        # Setup a thread, read rtmp urls   
        self.t = Thread(target=self._rtmp_pull_stream, args=(rtmp_id, rtmp_url, params, callback))
        self.t.start()
    
    # TODO  disconn_output_sink

    async def conn_output_sink(self, output, output_wire_params, callback):       
        rtmp_id = output.id
        rtmp_url = output.get_attrs('rtmp_url')
        self.output = output
        self.edge.bus.async_listen("{}_{}".format(self.RTMP_FRAME_EVENT, output.id), callback)
        self._new_rtmp_client(rtmp_id, rtmp_url, output_wire_params, callback)