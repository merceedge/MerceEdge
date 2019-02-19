import logging
import asyncio
import json
from merceedge.providers.base import ServiceProvider

from merceedge.service import (
    Service,
    ServiceCall
)

from merceedge.const import (
    EVENT_EDGE_STOP
)
from merceedge import util
from merceedge.util.async_util import (
    Context,
    callback,
    is_callback,
    run_callback_threadsafe,
    run_coroutine_threadsafe,
    CALLBACK_TYPE,
    T
)

_LOGGER = logging.getLogger(__name__)
CONF_BROKER = 'broker'
CONF_PORT = 'port'
CONF_CLIENT_ID = 'client_id'
CONF_KEEPALIVE = 'keepalive'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_CERTIFICATE = 'certificate'
CONF_PROTOCOL = 'protocol'

PROTOCOL_31 = '3.1'
PROTOCOL_311 = '3.1.1'

DEFAULT_PORT = 1883
DEFAULT_KEEPALIVE = 60
DEFAULT_QOS = 0
DEFAULT_RETAIN = False
DEFAULT_PROTOCOL = PROTOCOL_311

ATTR_TOPIC = 'topic'
ATTR_PAYLOAD = 'payload'
ATTR_PAYLOAD_TEMPLATE = 'payload_template'
ATTR_QOS = 'qos'
ATTR_RETAIN = 'retain'

MAX_RECONNECT_WAIT = 300  # seconds

class MqttServiceProvider(ServiceProvider):
    DOMAIN = 'mqtt'
    name=DOMAIN
    SERVICE_PUBLISH = 'publish'
    MQTT_MSG_RCV_EVENT = 'mqtt_msg_rcv'
    
    def __init__(self, edge, config):
        # TODO broker_ip broker_port username password etc.
        self._paho_lock = asyncio.Lock(loop=edge.loop)
        super(MqttServiceProvider, self).__init__(edge, config)
        
    async def async_setup(self, edge, attrs):
        self.edge = edge
        # TODO need validate config
        
        # TODO MQTT client setup
        conf = self.config[self.DOMAIN]
        broker = attrs.get(CONF_BROKER, conf[CONF_BROKER])
        port = util.convert(attrs.get(CONF_PORT), int, DEFAULT_PORT)
        client_id = util.convert(attrs.get(CONF_CLIENT_ID), str, conf.get(CONF_CLIENT_ID))
        keepalive = util.convert(attrs.get(CONF_KEEPALIVE), int, DEFAULT_KEEPALIVE)
        username = util.convert(attrs.get(CONF_USERNAME), str)
        password = util.convert(attrs.get(CONF_PASSWORD), str)
        certificate = util.convert(attrs.get(CONF_CERTIFICATE), str)
        protocol = util.convert(attrs.get(CONF_PROTOCOL), str, DEFAULT_PROTOCOL)

        if protocol not in (PROTOCOL_31, PROTOCOL_311):
            _LOGGER.error('Invalid protocol specified: %s. Allowed values: %s, %s',
                        protocol, PROTOCOL_31, PROTOCOL_311)
            return False
        
        import paho.mqtt.client as mqtt
        
        if protocol == PROTOCOL_31:
            proto = mqtt.MQTTv31
        else:
            proto = mqtt.MQTTv311
        
        if client_id is None:
            self._mqttc = mqtt.Client(protocol=proto)
        else:
            self._mqttc = mqtt.Client(client_id, protocol=proto)

        if username is not None:
            self._mqttc.username_pw_set(username, password)
        if certificate is not None:
            self._mqttc.tls_set(certificate)

        # self._mqttc.on_subscribe = self._mqtt_on_subscribe
        # self._mqttc.on_unsubscribe = self._mqtt_on_unsubscribe
        # self._mqttc.on_connect = self._mqtt_on_connect
        # self._mqttc.on_disconnect = self._mqtt_on_disconnect
        self._mqttc.on_message = self._mqtt_on_message
        self._mqttc.on_publish  = self.on_publish 

        result = await self.edge.async_add_job(
                    self._mqttc.connect, broker, port, keepalive
        )
        
        if result != 0:
            import paho.mqtt.client as mqtt
            _LOGGER.error("Failed to connect: %s", mqtt.error_string(result))
            return False
        
        self._mqttc.loop_start()
       
        self.edge.bus.async_listen_once(EVENT_EDGE_STOP, self.async_stop_mqtt)

    async def async_stop_mqtt(self, event):
        """Stop the MQTT client.

        This method must be run in the event loop and returns a coroutine.
        """
        def stop():
            """Stop the MQTT client."""
            self._mqttc.disconnect()
            self._mqttc.loop_stop()
        print("mqtt provider aborting...")
        await self.edge.async_add_job(stop)
            
    async def async_publish(self, data):
        """Handle MQTT publish service calls."""
        msg_topic = data.get(ATTR_TOPIC)
        payload = data.get(ATTR_PAYLOAD)

        payload_template = data.get(ATTR_PAYLOAD_TEMPLATE)
        qos = data.get(ATTR_QOS, DEFAULT_QOS)
        retain = data.get(ATTR_RETAIN, DEFAULT_RETAIN)
        if payload is None:
            if payload_template is None:
                _LOGGER.error(
                    "You must set either '%s' or '%s' to use this service",
                    ATTR_PAYLOAD, ATTR_PAYLOAD_TEMPLATE)
                return
           
        if msg_topic is None or payload is None:
            return

        async with self._paho_lock:
            _LOGGER.debug("Transmitting message on %s: %s", msg_topic, payload)
            await self.edge.async_add_job(
                self._mqttc.publish, msg_topic, payload, qos, retain)
        

    def _build_publish_data(self, topic, qos, retain, payload=None):
        """Build the arguments for the publish service without the payload."""
        data = {ATTR_TOPIC: topic}
        if qos is not None:
            data[ATTR_QOS] = qos
        if retain is not None:
            data[ATTR_RETAIN] = retain
        if type(payload) in (list, dict):
            payload = json.dumps(payload)
        data[ATTR_PAYLOAD] = payload
        return data

    def on_publish(self, client, obj, mid):
        # print("mqtt publish: " + str(mid))
        pass

    def _mqtt_on_message(self, _mqttc, _userdata, msg):
        # TODO need fix this proto code
        self.edge.bus.fire(self.event_type, msg.payload.decode('utf-8'))
    

    async def conn_output_sink(self, output, output_wire_params, callback):                       
        # TODO mqtt client subscribe topic (need fix this proto code)
        # self._mqttc.subscribe(output.get_attrs('topic'), 0)
        topic = output.get_attrs('topic')
        _LOGGER.debug("Subscribing to %s", topic)

        async with self._paho_lock:
            result = None  # type: int
            result, _ = await self.edge.async_add_job(
                self._mqttc.subscribe, topic, 0)
        
        # Subscribe callback -> EventBus -> Wire input (output sink ) -> EventBus(Send) -> Service provider  
        # try:
        #     mqtt_listener_num = await self.edge.bus.listeners[self.MQTT_MSG_RCV_EVENT]
        # except KeyError:
        #     # TODO log no need listen MQTT_MSG_RCV_EVENT msg again
        event_type = "{}_{}".format(self.MQTT_MSG_RCV_EVENT, output.id)
        self.event_type = event_type
        self.edge.bus.listen(event_type, callback)

    def disconn_output_sink(self, output):
        """ disconnect wire output sink
        """
        if len(output.output_wires) == 1:
            self._mqttc.unsubscribe(output.get_attrs('topic'))
        
    async def emit_input_slot(self, input, payload):
        """Publish message to an MQTT topic."""
        data = self._build_publish_data(input.get_attrs('topic'),
                                        input.get_attrs('qos'), 
                                        input.get_attrs('retain'),
                                        payload)
        
        # print("mqtt emit_input_slot")
        await self.async_publish(data)
