from threading import Thread
import cv2
import numpy as np

from merceedge.providers.base import ServiceProvider

class RTMPProvider(ServiceProvider):
    """ Receive video stream from rtmp url and convert to video frame data.
    """
    DOMAIN = "rtmp"
    name=DOMAIN
    RTMP_FRAME_EVENT = 'rtmp_frame'

    def __init__(self, edge, config):
        super(RTMPProvider, self).__init__(edge, config)

    async def async_setup(self, edge, config):

        pass

    def _rtmp_pull_stream(self, rtmp_id, rtmp_url, params, callback):
        """
            TODO user params
        """
        stream = cv2.VideoCapture(rtmp_url)
        while True:
            grabbed, frame = stream.read()
            # if the frame was not grabbed, then we have reached the end
            # of the stream
            if not grabbed:
                break
            # send frame event on eventbus
            # TODO send shape info
            # print(frame.shape)
            # data = frame.tobytes()
            # print("len: {}".format(len(data)))

            # self.edge.bus.fire("{}_{}".format(self.RTMP_FRAME_EVENT, rtmp_id),
            #                     data)
            # TODO Send frame to process queue
            callback(frame)
            

    def _new_rtmp_client(self, rtmp_id, rtmp_url, params, callback):
        # Setup a thread, read rtmp urls   
        t = Thread(target=self._rtmp_pull_stream, args=(rtmp_id, rtmp_url, params, callback))
        t.start()
    
    # TODO  disconn_output_sink

    async def conn_output_sink(self, output, output_wire_params, callback):       
        rtmp_id = output.id
        rtmp_url = output.get_attrs('rtmp_url')
        self._new_rtmp_client(rtmp_id, rtmp_url, output_wire_params, callback)