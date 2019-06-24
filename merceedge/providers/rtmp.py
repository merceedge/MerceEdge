from threading import Thread
import cv2
import numpy as np
import time

from merceedge.providers.base import ServiceProvider
from merceedge.const import EVENT_EDGE_STOP
from merceedge.settings import (
    logger_access,
    logger_code,
    logger_console
)

_LOGGER = logger_code

class RTMPProvider(ServiceProvider):
    """ Receive video stream from rtmp url and convert to video frame data.
    """
    DOMAIN = "rtmp"
    name=DOMAIN
    RTMP_FRAME_EVENT = 'rtmp_frame'

    def __init__(self, edge, config):
        super(RTMPProvider, self).__init__(edge, config)
        self.abort_immediately = False
        self.t = None

    async def async_setup(self, edge, config):
        _LOGGER.debug("async setup: {}".format(self.name))
        self.edge.bus.async_listen_once(EVENT_EDGE_STOP, self.async_stop_rtmp)
    
    async def async_stop_rtmp(self, event):
        """Stop RTMP."""
        print("rtmp provider aborting...")
        self.abort_immediately = True
    
    def _rtmp_pull_stream(self, rtmp_id, rtmp_url, params, callback):
        """
            TODO user params
        """
        stream = cv2.VideoCapture(rtmp_url)
        resize_height = params.get('resize_height', 0)
        resize_width = params.get('resize_width', 0)
        while True:
            
            if self.abort_immediately:
                print('rtmp provider thread exit')
                return
            grabbed, frame = stream.read()

            # quality = 20 # quality 0 to 100. default:95
            # ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

            # if the frame was not grabbed, then we have reached the end
            # of the stream
            if not grabbed:
                break
            if resize_height != 0 and resize_width != 0:
                frame = cv2.resize(frame,(resize_width, resize_height),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)

            time.sleep(0.08)
            self.edge.bus.async_fire("{}_{}".format(self.RTMP_FRAME_EVENT, self.output.id), frame)
            

    def _new_rtmp_client(self, rtmp_id, rtmp_url, params, callback):
        # Setup a thread, read rtmp urls   
        if self.t is None:
            self.t = Thread(target=self._rtmp_pull_stream, 
                            args=(rtmp_id, rtmp_url, params, callback),
                            daemon=True)
            self.t.start()
    
    def disconn_output_sink(self, output):
        """ disconnect wire output sink
        """
        if len(output.output_wires) == 1:
            self.abort_immediately = True
            self.t = None

    async def conn_output_sink(self, output, output_wire_params, callback):       
        rtmp_id = output.id
        rtmp_url = output.get_attrs('rtmp_url')
        self.output = output
        self.edge.bus.async_listen("{}_{}".format(self.RTMP_FRAME_EVENT, output.id), callback)
        self._new_rtmp_client(rtmp_id, rtmp_url, output_wire_params, callback)