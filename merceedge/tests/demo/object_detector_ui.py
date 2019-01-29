import paho.mqtt.client as mqtt
from queue import Queue
import json
import cv2
import numpy as np
import time
from merceedge.tests.detect_object.utils.app_utils import FPS

broker = '127.0.0.1'
port = 1883
keepalive = True
width=960
height=544



input_q = Queue()  # fps is better if queue is higher but then more lags

def _mqtt_on_message(_mqttc, _userdata, msg):
    # print(msg.payload)
    input_q.put(msg.payload)


_mqttc = mqtt.Client(protocol=mqtt.MQTTv31)
_mqttc.on_message = _mqtt_on_message
_mqttc.connect(broker, port, keepalive)
_mqttc.loop_start()



def main():
    _mqttc.subscribe('/mercedge/toggle_switch', 0)
    # fps = FPS().start()
    while True:

        t = time.time()
        if input_q.empty():
            # print("input empty")
            time.sleep(0.1)
        else:
            msg = input_q.get()
            frame_bytes = msg[:height*width*3]
            detect_bytes = msg[height*width*3:]
            # print(msg)
            # print ("-"*30)
            # print(detect_bytes.decode('utf8'))
            data = json.loads(detect_bytes.decode('utf8'))
            print(len(data))
            # # frame_str = data['frame']

            frame = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(height, width, 3)
            font = cv2.FONT_HERSHEY_SIMPLEX

            rec_points = data['rect_points']
            class_names = data['class_names']
            class_colors = data['class_colors']
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

    fps.stop()
    print('[INFO] elapsed time (total): {:.2f}'.format(fps.elapsed()))
    print('[INFO] approx. FPS: {:.2f}'.format(fps.fps()))

    cv2.destroyAllWindows()


main()

