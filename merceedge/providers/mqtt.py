import logging

from merceedge.providers.base import (
    ServiceProvider,
    Singleton
)
from merceedge.service import (
    Service,
    ServiceCall
)
# from merceedge.core import (
#     Input,
#     Output
# )
from merceedge import util

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

class MqttServiceProvider(Singleton):
    # __metaclass__ = Singleton
    DOMAIN = 'mqtt'
    SERVICE_PUBLISH = 'publish'
    MQTT_MSG_RCV_EVENT = 'mqtt_msg_rcv'
    
    def __init__(self):
        # TODO broker_ip broker_port username password etc.
        pass

    def setup(self, edge , config):
        self.edge = edge
        # TODO need validate config
        
        # TODO MQTT client setup
        conf = config[self.DOMAIN]
        broker = conf[CONF_BROKER]
        port = util.convert(conf.get(CONF_PORT), int, DEFAULT_PORT)
        client_id = util.convert(conf.get(CONF_CLIENT_ID), str)
        keepalive = util.convert(conf.get(CONF_KEEPALIVE), int, DEFAULT_KEEPALIVE)
        username = util.convert(conf.get(CONF_USERNAME), str)
        password = util.convert(conf.get(CONF_PASSWORD), str)
        certificate = util.convert(conf.get(CONF_CERTIFICATE), str)
        protocol = util.convert(conf.get(CONF_PROTOCOL), str, DEFAULT_PROTOCOL)

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

        self._mqttc.connect(broker, port, keepalive)
        self._mqttc.loop_start()
        # register mqtt publish service 
        self.edge.services.register(self.DOMAIN, 
                                self.SERVICE_PUBLISH,
                                self._publish_service,
                                # description=self.SERVICE_PUBLISH
                                )
    
    def _publish_service(self, call: ServiceCall):
        """Handle MQTT publish service calls."""
        msg_topic = call.data.get(ATTR_TOPIC)
        payload = call.data.get(ATTR_PAYLOAD)
        payload_template = call.data.get(ATTR_PAYLOAD_TEMPLATE)
        qos = call.data.get(ATTR_QOS, DEFAULT_QOS)
        retain = call.data.get(ATTR_RETAIN, DEFAULT_RETAIN)
        if payload is None:
            if payload_template is None:
                _LOGGER.error(
                    "You must set either '%s' or '%s' to use this service",
                    ATTR_PAYLOAD, ATTR_PAYLOAD_TEMPLATE)
                return
            # try:
            #     payload = template.render(hass, payload_template)
            # except template.jinja2.TemplateError as exc:
            #     _LOGGER.error(
            #         "Unable to publish to '%s': rendering payload template of "
            #         "'%s' failed because %s.",
            #         msg_topic, payload_template, exc)
            #     return
        if msg_topic is None or payload is None:
            return
        self._mqttc.publish(msg_topic, payload, qos, retain)

    def _build_publish_data(self, topic, qos, retain):
        """Build the arguments for the publish service without the payload."""
        data = {ATTR_TOPIC: topic}
        if qos is not None:
            data[ATTR_QOS] = qos
        if retain is not None:
            data[ATTR_RETAIN] = retain
        return data

    def _mqtt_on_message(self, _mqttc, _userdata, msg):
        # TODO need fix this proto code
        self.edge.bus.fire(self.MQTT_MSG_RCV_EVENT, msg.payload.decode('utf-8'))

    def conn_output_sink(self, output , callback):
        # TODO mqtt client subscribe topic (need fix this proto code)
        self._mqttc.subscribe(output.get_attrs('topic'), 0)
        # Subscribe callback -> EventBus -> Wire input (output sink ) -> EventBus(Send) -> Service provider  
        try:
            mqtt_listener_num = self.edge.bus.listeners[self.MQTT_MSG_RCV_EVENT]
        except KeyError:
            # TODO log no need listen MQTT_MSG_RCV_EVENT msg again
            self.edge.bus.listen(self.MQTT_MSG_RCV_EVENT, callback)

    def disconn_output_sink(self, output):
        """ disconnect wire output sink
        """
        if len(output.output_wires) == 1:
            self._mqttc.unsubscribe(output.get_attrs('topic'))
        
    def emit_input_slot(self, input, payload):
        """Publish message to an MQTT topic."""
        data = self._build_publish_data(input.get_attrs('topic'),
                                        input.get_attrs('qos'), 
                                        input.get_attrs('retain'))
        data[ATTR_PAYLOAD] = payload
        self.edge.services.call(self.DOMAIN, self.SERVICE_PUBLISH, data)
