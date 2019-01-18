import functools as ft
import logging
import threading
import enum
import os
import copy
import json
from os.path import join

import merceedge.util as util
import merceedge.util.dt as dt_util
import merceedge.util.id as id_util
import merceedge.util.yaml as yaml_util
from merceedge.exceptions import MerceEdgeError
from merceedge.const import (
    MATCH_ALL,
    EVENT_TIME_CHANGED,
    EVENT_SERVICE_EXECUTED,
    EVENT_CALL_SERVICE,
    EVENT_STATE_CHANGED
)
from merceedge.service import ServiceRegistry
from merceedge.providers import PROVIDERS
from merceedge.api_server.models import ComponentDBModel, WireDBModel

DOMAIN = "merceedge"

# How often time_changed event should fire
TIMER_INTERVAL = 1  # seconds

# Define number of MINIMUM worker threads.
# During bootstrap of HA (see bootstrap._setup_component()) worker threads
# will be added for each component that polls devices.
# MIN_WORKER_THREAD = 2

_LOGGER = logging.getLogger(__name__)


class MerceEdge(object):
    """Root object of Merce Edge node"""
    def __init__(self):
        self.component_templates = {} # key: component template name
        self.components = {}  # key: component id
        self.wires = {} # key: wire id
        self.pool = pool = util.create_worker_pool()
        self.bus = EventBus(pool)
        self.services = ServiceRegistry(self.bus, pool)
        # self.states = StateMachine(self.bus)
        # self.config = Config()
        self._lock = threading.Lock()
        
    def dyload_component(self, component_config):
        """dynamic load new component"""
        # TODO
    
    def start(self):
        # TODO 
        pass

    def stop(self):
        # TODO 
        pass

    def load_local_component_templates(self, config_path):
        """Read local config file, generate component templates
        """
        template_configs = []
        template_configs += [each for each in os.listdir(config_path) if each.endswith('.yaml')]
        for template_config in template_configs:
            com_tmp_yaml = yaml_util.load_yaml(join(config_path, template_config))
            # new_com_tmp = Component(com_tmp_yaml)
            self.component_templates[com_tmp_yaml['component']['name']] = com_tmp_yaml
            

    def generate_component_instance(self, component_template_name, id=None):
        """Deepcopy component from component template
        """
        with self._lock:
            com_tmp_yaml = self.component_templates.get(component_template_name, None)
            if com_tmp_yaml:
                new_com = Component(com_tmp_yaml, id)
                self.components[new_com.id] = new_com
                return new_com
            else:
                # TODO logger warn no such  name component compnent
                pass
            return None

    def connect_interface(self, output_component_id, output_name, input_component_id, input_name, wire_id=None):
        """ connenct wire
        """
        wire = Wire(self.components[output_component_id].outputs[output_name], 
                self.components[input_component_id].inputs[input_name], wire_id)
        self.wires[wire.id] = wire
        with self._lock:
            self.components[output_component_id].outputs[output_name].conn_output_sink()
            return wire
        return None
    
    def delete_wire(self, wire_id):
        """Disconnect wire
        """
        try:
            wire = self.wires[wire_id]
            wire.disconnect()
            del self.wires[wire.id]
            return wire
        except KeyError:
            return None

    def restore_entities_from_db(self):
        """Restore components / wires from local db when edge start.
            1. 获取所有的组件信息, 根据组件类型名称创建组件对象， 注意：组件的uuid从记录读取
            2. 获取所有的连线信息，连接相关接口
        """
        # TODO
        # Restruct components
        component_db_list = ComponentDBModel.query.all()
        for component_db_record in component_db_list:
            self.generate_component_instance(component_db_record.template_name, 
                                                            component_db_record.uuid)
        # Restruct wires
        wire_db_list = WireDBModel.query.all()
        for wire_db_record in wire_db_list:
            try:
                output_component_uuid = wire_db_record.output_component_uuid
                input_component_uuid = wire_db_record.input_component_uuid
                output_name = wire_db_record.output_name
                input_name = wire_db_record.input_name
                wire_id = wire_db_record.id
                self.connect_interface(output_component_uuid, output_name,
                                     input_component_uuid, input_name, 
                                     wire_id)
            except KeyError:
                # TODO logger warn
                continue

        
class Entity(object):
    """ABC for Merce Edge entity(Component, Interface, etc.)"""
    id = id_util.generte_unique_id()
    attrs = {}

    def load_attrs(self, config):
        # TODO
        raise NotImplementedError 
    
    def get_attrs(self, attr_key):
        try:
            return self.attrs.get(attr_key)
        except KeyError as e:
            _LOGGER.error(str(e))


class Component(Entity):
    """ABC for Merce Edge components"""
    
    def __init__(self, model_template_config, id=None):
        """
        model_template_config: yaml object
        """
        self.model_template_config = model_template_config
        self.id = id or id_util.generte_unique_id()
        self.inputs = {}
        self.outputs = {}
        # self.components = {}
        
        # init interfaces
        self._init_interfaces()
    
    def _init_interfaces(self):
        """initiate inputs & outputs
        """
        inputs = self.model_template_config['component'].get('inputs', None)
        if inputs:
            for _input in inputs:
                self.inputs[_input['name']] = Input(_input['name'], self, _input['protocol']['name'], _input['protocol'])
        
        outputs = self.model_template_config['component'].get('outputs', None)
        if outputs:
            for _ouput in outputs:
                self.outputs[_ouput['name']] = Output(_ouput['name'], self, _ouput['protocol']['name'], _ouput['protocol'])   

    def get_start_wires_info(self):
        """ Get wires infomation that start from component
        """
        wires = []
        for output in self.outputs:
            for wire in output.output_wires:
                # TODO 
                pass
        return wires

    def update_state(self, data):
        # TODO update state
        pass
    

class Interface(Entity):
    """Interface ABC 
    1. Read configuration file and load interface using service(eg: mqtt service).
    2. Listen message from EventBus, or call fire event provide by service(eg: mqtt service).
    """
    def __init__(self, name, component, protocol, attrs=None):
        self.name = name
        self.component = component
        self.protocol = protocol
        self.attrs = attrs or {}
    
   
class Output(Interface):
    """Virtual output interface, receive data from real world
    """
    def __init__(self, name, component, protocol, attrs):
        super(Output, self).__init__(name, component, protocol, attrs)
        self.output_wires = {}
        self.data = {}

        # read output configuration,
        self._init_provider()

    def wires_info(self):
        info = {}
        for wire_id, wire in self.output_wires.items():
            info[wire_id] = wire.__repr__()
        return info
    
    def add_wire(self, wire):
        """Add new wire"""
        self.output_wires[wire.id] = wire
    
    def del_wire(self, wire_id):
        """Remove wire
        """
        self.provider.disconn_output_sink(self)
        del self.output_wires[wire_id]
        print("output wires: {}".format(self.output_wires))
    
    def _init_provider(self):
        try:
            self.provider = PROVIDERS.get(self.protocol, None)
            self.provider.new_instance_setup(self.name, self.attrs, True)
        except KeyError as e:
            # TODO log no such provider key error
            raise
    
    def conn_output_sink(self):
        """ register EventBus listener"""
        self.provider.conn_output_sink(self, self._output_sink_callback)
    
    def _output_sink_callback(self, payload):
        """Emit data to all wires
            1. get all wire input_sink
            2. emit data into input sink
        """
        #TODO self.protocol_provider.output_sink()
        
        for wire_id, wire in self.output_wires.items():
            wire.fire(payload)


class Input(Interface):
    """Input"""
    def __init__(self, name, component, protocol, attrs):
        super(Input, self).__init__(name, component, protocol, attrs)
        # self.component = component
        self.input_wires = {}
        self._conn_input_slot()
    
    def wires_info(self):
        info = {}
        for wire_id, wire in self.input_wires.items():
            info[wire_id] = wire.__repr__()
        return json.dumps(info)

    def add_wire(self, wire):
        """Add new wire"""
        self.input_wires[wire.id] = wire
    
    def del_wire(self, wire_id):
        """Remove wire
        """
        del self.input_wires[wire_id]
        
    def _conn_input_slot(self):
        try:
            self.provider = PROVIDERS.get(self.protocol, None)
        except KeyError as e:
            # TODO log no such provider key error
            raise
    
    def emit_data_to_input(self, payload):
        # TODO emit data to EventBus and invoke configuration service send data function.
        # TODO payload根据wire类型进行转换
        self.provider.emit_input_slot(self, payload)


class State(object):
    """Component State"""
    # raise NotImplementedError
    # TODO
    pass


class Wire(Entity):
    """Wire """
    def __init__(self, output_sink, input_slot, id=None):
        self.id = id or id_util.generte_unique_id()
        self.input = output_sink
        self.output = input_slot
        self.input.add_wire(self)
        self.output.add_wire(self)

        # TODO condition if ... elif ... else ... 
        # TODO filter/AI/custom module, etc...
        self.wire_load = None
    
    def __repr__(self):
        wire_info = {}
        wire_info["input"] = {"component_id": self.input.component.id, 
                            "name": self.input.name}
        wire_info["output"] = {"component_id": self.output.component.id,
                            "name": self.output.name}
        return wire_info    
        
    
    # @property
    # def input(self):
    #     return self.input
    
    # @property
    # def output(self):
    #     return self.output

    def disconnect(self):
        self.input.del_wire(self.id)
        self.output.del_wire(self.id)
            
    def fire(self, payload):
        """Fire payload data from input to output"""
        # TODO data根据
        self.output.emit_data_to_input(payload.data)


class Event(object):
    # pylint: disable=too-few-public-methods
    """Represents an event within the Bus."""

    __slots__ = ['event_type', 'data', 'time_fired']

    def __init__(self, event_type, data=None,
                 time_fired=None):
        """Initialize a new event."""
        self.event_type = event_type
        self.data = data or {}
        self.time_fired = dt_util.strip_microseconds(
            time_fired or dt_util.utcnow())

    def as_dict(self):
        """Create a dict representation of this Event."""
        return {
            'event_type': self.event_type,
            'data': dict(self.data),
            'time_fired': dt_util.datetime_to_str(self.time_fired),
        }

    def __repr__(self):
        # pylint: disable=maybe-no-member
        if self.data:
            return "<Event {}[{}]: {}>".format(
                self.event_type, str(self.origin)[0],
                util.repr_helper(self.data))
        else:
            return "<Event {}[{}]>".format(self.event_type,
                                           str(self.origin)[0])

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.event_type == other.event_type and
                self.data == other.data and
                self.time_fired == other.time_fired)




class WireLoad(Entity):
    """Wire load abstract class. Mounted on wire, processing data through wire.
        Filter, Analiysis, Process, etc.
    """

    def __init__(self, name, input_data):
        self.name = name
        self.input_data = input_data
        self.ouput_data = None
    
    def update_input(self, input_data):
        self.input_data = input_data
    
    def process(self):
        raise NotImplementedError

    @property
    def output(self):
        return self.ouput_data
    

class EventBus(object):
    """Allows firing of and listening for events."""

    def __init__(self, pool=None):
        """Initialize a new event bus."""
        self._listeners = {}
        self._lock = threading.Lock()
        self._pool = pool or util.create_worker_pool()

    @property
    def listeners(self):
        """Dict with events and the number of listeners."""
        with self._lock:
            return {key: len(self._listeners[key])
                    for key in self._listeners}

    def fire(self, event_type, event_data=None):
        """Fire an event."""
        if not self._pool.running:
            raise MerceEdgeError('Merce Edge has shut down.')

        with self._lock:
            # Copy the list of the current listeners because some listeners
            # remove themselves as a listener while being executed which
            # causes the iterator to be confused.
            get = self._listeners.get
            listeners = get(MATCH_ALL, []) + get(event_type, [])

            event = Event(event_type, event_data)

            if event_type != EVENT_TIME_CHANGED:
                _LOGGER.info("Bus:Handling %s", event)

            if not listeners:
                return

            job_priority = util.JobPriority.from_event_type(event_type)

            for func in listeners:
                self._pool.add_job(job_priority, (func, event))

    def listen(self, event_type, listener):
        """Listen for all events or events of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.
        """
        with self._lock:
            if event_type in self._listeners:
                self._listeners[event_type].append(listener)
            else:
                self._listeners[event_type] = [listener]

    def listen_once(self, event_type, listener):
        """Listen once for event of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.

        Returns registered listener that can be used with remove_listener.
        """
        @ft.wraps(listener)
        def onetime_listener(event):
            """Remove listener from eventbus and then fires listener."""
            if hasattr(onetime_listener, 'run'):
                return
            # Set variable so that we will never run twice.
            # Because the event bus might have to wait till a thread comes
            # available to execute this listener it might occur that the
            # listener gets lined up twice to be executed.
            # This will make sure the second time it does nothing.
            onetime_listener.run = True

            self.remove_listener(event_type, onetime_listener)

            listener(event)

        self.listen(event_type, onetime_listener)

        return onetime_listener

    def remove_listener(self, event_type, listener):
        """Remove a listener of a specific event_type."""
        with self._lock:
            try:
                self._listeners[event_type].remove(listener)

                # delete event_type list if empty
                if not self._listeners[event_type]:
                    self._listeners.pop(event_type)

            except (KeyError, ValueError):
                # KeyError is key event_type listener did not exist
                # ValueError if listener did not exist within event_type
                pass






