import paho.mqtt.client as mqtt
from queue import Queue
import json
import cv2
import numpy as np
import time
from merceedge.tests.detect_object.utils.app_utils import FPS

broker = '127.0.0.1'
port = 1883
keepalive = False
width=0
height=0
frame = None
input_q = Queue()  # fps is better if queue is higher but then more lags

def _mqtt_on_message(_mqttc, _userdata, msg):
    global width, height
    # print("-"*30)
    # print(len(msg.payload))
    # print(msg.topic)
    if msg.topic == u'/mercedge/rtmp_video_size':
        # print("-"*30)
        # print(len(msg.payload), type(msg.payload))
        # print(msg.topic)
        size = json.loads(msg.payload.decode('utf-8'))
        # print(size)
        width = size['width']
        height = size['height']
        # print(msg.payload, width, height)

    elif msg.topic == u'/mercedge/rtmp_bytes':

        input_q.put(('rtmp_bytes', msg.payload))

    elif msg.topic == u'/mercedge/object_detection_result':
        # print("-"*30)
        input_q.put(('object_detection_result', msg.payload))
    
_mqttc = mqtt.Client(protocol=mqtt.MQTTv31)
_mqttc.on_message = _mqtt_on_message
_mqttc.connect(broker, port, keepalive)
_mqttc.loop_start()


def main():
    _mqttc.subscribe('/mercedge/rtmp_video_size', 0)
    _mqttc.subscribe('/mercedge/rtmp_bytes', 0)
    _mqttc.subscribe('/mercedge/object_detection_result', 0)
    # fps = FPS().start()
    while True:

        t = time.time()
        global width, height
        if width == 0 or height == 0:
            # print('waiting video size parameters', width, height)
            continue

        if input_q.empty():
            # print("input empty")
            pass
        else:
            payload = input_q.get()
            # print(msg)
            global frame
            
            if payload[0] == 'rtmp_bytes':
                
                frame_bytes = payload[1]
                frame = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(height, width, 3)

            elif payload[0] == 'object_detection_result':
                
                object_detection_result = json.loads(payload[1].decode('utf-8'))
                # print(object_detection_result, frame)
                if frame is None:
                    continue
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                rec_points = object_detection_result['rect_points']
                class_names = object_detection_result['class_names']
                class_colors = object_detection_result['class_colors']
                for point, name, color in zip(rec_points, class_names, class_colors):
                    cv2.rectangle(frame, (int(point['xmin'] * width), int(point['ymin'] * height)),
                                (int(point['xmax'] * width), int(point['ymax'] * height)), color, 3)
                    cv2.rectangle(frame, (int(point['xmin'] * width), int(point['ymin'] * height)),
                                (int(point['xmin'] * width) + len(name[0]) * 6,
                                int(point['ymin'] * height) - 10), color, -1, cv2.LINE_AA)
                    cv2.putText(frame, name[0], (int(point['xmin'] * width), int(point['ymin'] * height)), font,
                                0.3, (0, 0, 0), 1)
                cv2.imshow('Video', frame)
            
        # fps.update()

        # print('[INFO] elapsed time: {:.2f}'.format(time.time() - t), end="\r", flush=True)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # fps.stop()
    # print('[INFO] elapsed time (total): {:.2f}'.format(fps.elapsed()))
    # print('[INFO] approx. FPS: {:.2f}'.format(fps.fps()))

    cv2.destroyAllWindows()


main()

