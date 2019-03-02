import threading
import enum
import os
import sys
import copy
import json
import asyncio
import attr
import uuid
import functools
import datetime
import multiprocessing
from time import monotonic
import time
import copy
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from async_timeout import timeout
from collections import namedtuple

from typing import (  # noqa: F401 pylint: disable=unused-import
    Optional, Any, Callable, List, TypeVar, Dict, Coroutine, Set,
    TYPE_CHECKING, Awaitable, Iterator)
from os.path import join
dir_path = os.path.dirname(os.path.realpath(__file__))


import merceedge.util as util
import merceedge.util.dt as dt_util
import merceedge.util.id as id_util
import merceedge.util.yaml as yaml_util
import merceedge.util.module as module_util
from merceedge.util.async_util import (
    Context,
    callback,
    is_callback,
    run_callback_threadsafe,
    run_coroutine_threadsafe,
    fire_coroutine_threadsafe,
    CALLBACK_TYPE,
    T
)
from merceedge.util.signal import async_register_signal_handling
from merceedge.exceptions import (
    MerceEdgeError,
    ComponentTemplateNotFound
) 
from merceedge.const import (
    MATCH_ALL,
    EVENT_TIME_CHANGED,
    EVENT_SERVICE_EXECUTED,
    EVENT_CALL_SERVICE,
    EVENT_STATE_CHANGED,
    EVENT_TIMER_OUT_OF_SYNC,
    EVENT_EDGE_STOP,
    ATTR_NOW,
    ATTR_DATE,
    ATTR_TIME,
    ATTR_SECONDS,
)
from merceedge.service import ServiceRegistry
from merceedge.providers import ServiceProviderFactory
from merceedge.api_server.models import (
    ComponentDBModel, 
    WireDBModel
)
from merceedge.settings import (
    logger_access,
    logger_code,
    logger_console
)

DOMAIN = "merceedge"

_LOGGER = logger_code


class MerceEdge(object):
    """Root object of Merce Edge node"""
    def __init__(self, user_config):
        self.user_config = user_config

        self.loop = asyncio.get_event_loop()
        executor_opts = {'max_workers': None}  # type: Dict[str, Any]
        if sys.version_info[:2] >= (3, 6):
            executor_opts['thread_name_prefix'] = 'SyncWorker'
        self.executor = ThreadPoolExecutor(**executor_opts)
        self.loop.set_default_executor(self.executor)

        self._pending_tasks = []  # type: list
        self._track_task = True
        self.exit_code = 0
        # _async_stop will set this instead of stopping the loop
        # self._stopped = asyncio.Event()


        self.bus = EventBus(self)
        self.services = ServiceRegistry(self)
        
        self.component_templates = {} # key: component template name
        self.components = {}  # key: component id
        self.wires = {} # key: wire id
        self.wireload_factory = WireLoadFactory(user_config)

        
    def dyload_component(self, component_config):
        """dynamic load new component"""
        # TODO
    
    def start(self):
        """Start.

        Note: This function is only used for testing.
        For regular use, use "await edge.run()".
        """

        # Register the async start
        fire_coroutine_threadsafe(self.async_start(), self.loop)
     
        # Run forever
        try:
            # Block until stopped
            _LOGGER.info("Starting MerceEdge core loop")
            self.loop.run_forever()
        except KeyboardInterrupt:
            # Optionally show a message if the shutdown may take a while
            _LOGGER.info("Attempting graceful shutdown, press Ctrl+C again to exit…", flush=True)

            # Do not show `asyncio.CancelledError` exceptions during shutdown
            # (a lot of these may be generated, skip this if you prefer to see them)
            def shutdown_exception_handler(loop, context):
                if "exception" not in context \
                or not isinstance(context["exception"], asyncio.CancelledError):
                    loop.default_exception_handler(context)
            self.loop.set_exception_handler(shutdown_exception_handler)

            # Handle shutdown gracefully by waiting for all tasks to be cancelled
            tasks = asyncio.gather(*asyncio.Task.all_tasks(loop=self.loop), loop=self.loop, return_exceptions=True)
            tasks.add_done_callback(lambda t: self.loop.stop())
            tasks.cancel()

            # Keep the event loop running until it is either destroyed or all
            # tasks have really terminated
            while not tasks.done() and not self.loop.is_closed():
                self.loop.run_forever()
        finally:
            self.loop.close()
        return self.exit_code

    def stop(self):
        fire_coroutine_threadsafe(self.async_stop(), self.loop)

    def load_local_component_templates(self, config_yml_dict):
        # 1. Absolute path 2. MERCE_EDGE_HOME path
        try:
            component_template_paths = config_yml_dict['component_template']['paths']
            for path in component_template_paths:
                ab_path = ''
                if path.startswith('/') or path[1]==":":
                    ab_path = path
                else:
                    ab_path = os.path.join(os.environ['MERCE_EDGE_HOME'], 'merceedge', path)
                self._load_local_component_templates(ab_path)
        except KeyError:
            raise MerceEdgeError('config.yaml foramt invalide')

    def _load_local_component_templates(self, component_template_path):
        """Read local component templates path, generate component template objects
        """
        template_configs = []
        template_configs += [each for each in os.listdir(component_template_path) if each.endswith('.yaml')]
        for template_config in template_configs:
            com_tmp_yaml = yaml_util.load_yaml(join(component_template_path, template_config))
            # new_com_tmp = Component(com_tmp_yaml)
            self.component_templates[com_tmp_yaml['component']['name']] = com_tmp_yaml
            
    def _generate_component_instance(self, component_template_name, id=None, init_params=None):
        """Deepcopy component from component template
        """
        com_tmp_yaml = self.component_templates.get(component_template_name, None)
        if com_tmp_yaml:
            if com_tmp_yaml['component'].get('virtual', False):
                new_com_cls = self.wireload_factory.get_class(com_tmp_yaml['component']['name'])
                new_com = new_com_cls(self, com_tmp_yaml, id, init_params)
            else:
                new_com = Component(self, com_tmp_yaml, id, init_params)
            self.components[new_com.id] = new_com
            return new_com
        else:
            # TODO logger warn no such  name component compnent
            pass
        return None
    
    def generate_component_instance(self, component_template_name, component_id, init_params=None):
        """ Get component from self.components dict by id, if not exit, create new one, and 
            save into self.components
        """
        component = self.components.get(component_id, None)
        if component is None:
            component = self._generate_component_instance(component_template_name, component_id, init_params)
            if component:
                return component
        raise ComponentTemplateNotFound

    async def connect_interface(self, 
                                output_component_id, output_name, 
                                input_component_id, input_name, 
                                output_params={}, input_params={},
                                wire_id=None):
        """ connenct wire
        """
        output_sink = self.components[output_component_id].outputs[output_name]
        input_slot = self.components[input_component_id].inputs[input_name]
        wire = Wire(edge=self, output_sink=output_sink, input_slot=input_slot, id=wire_id)
        wire.set_input_params(output_params)
        wire.set_output_params(input_params)
        # print(wire.output_sink.name, wire.output_sink, output_params, wire.output_sink.attrs)
        # print(wire.input_slot.name, wire.input_slot, input_params, wire.input_slot.attrs)

        self.wires[wire.id] = wire
        
        await self.components[output_component_id].outputs[output_name].conn_output_sink(output_wire_params=output_params)
        await self.components[input_component_id].inputs[input_name].conn_input_slot(input_wire_params=input_params)
        wire.connect()
        return wire

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
    
    def stop_wireload_exec(self):
        # for wireid, wire in self.wires.items():
        #     if wire.wire_load:
        #         wire.wire_load.is_stop = True
        # TODO
        pass
                
    def restore_entities_from_db(self):
        """Restore components / wires from local db when edge start.
            1. 获取所有的组件信息, 根据组件类型名称创建组件对象， 注意：组件的uuid从记录读取
            2. 获取所有的连线信息，连接相关接口
        """
        # TODO
        # Restruct components
        component_db_list = ComponentDBModel.query.all()
        for component_db_record in component_db_list:
            self._generate_component_instance(component_db_record.template_name, 
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
                # TODO need modify
                self.connect_interface(output_component_uuid, output_name,
                                     input_component_uuid, input_name, 
                                     wire_id)
            except KeyError:
                # TODO logger warn
                continue

    async def load_formula(self, formula_path):
        formula_yaml = yaml_util.load_yaml(formula_path)
        
        try:
            components = formula_yaml['components']
            wires = formula_yaml['wires']
            for component in components:
                # TODO init component parameters
                self.generate_component_instance(component['template'], 
                                                 component['id'], 
                                                 component.get('parameters', None))

            for wire in wires:
                # struct components
                output_com = self.components[wire['output_sink']['component_id']]
                input_com = self.components[wire['input_slot']['component_id']]
                # struct wire
                output_name = wire['output_sink']['output']
                input_name = wire['input_slot']['input']

                # wire interface paramaters
                output_params = wire['output_sink'].get('parameters', {})
                input_params = wire['input_slot'].get('parameters', {})
                
                await self.connect_interface(output_com.id, output_name,
                                        input_com.id, input_name,
                                        output_params, input_params)
                
        except KeyError as e:
            _LOGGER.error("Load formula error, program exit!: {}".format(e))
            sys.exit(-1)
        except ComponentTemplateNotFound:
            _LOGGER.error(ComponentTemplateNotFound.__str__)
    
    def add_job(self, target: Callable[..., None], *args: Any) -> None:
        """Add job to the executor pool.

        target: target to call.
        args: parameters for method to call.
        """
        if target is None:
            raise ValueError("Don't call add_job with None")
        self.loop.call_soon_threadsafe(self.async_add_job, target, *args)
    
    
    @callback
    def async_add_job(
            self,
            target: Callable[..., Any],
            *args: Any) -> Optional[asyncio.Future]:
        """Add a job from within the event loop.

        This method must be run in the event loop.

        target: target to call.
        args: parameters for method to call.
        """
        task = None
        
        # Check for partials to properly determine if coroutine function
        check_target = target
        while isinstance(check_target, functools.partial):
            check_target = check_target.func
        if asyncio.iscoroutine(check_target):
            task = self.loop.create_task(target)  # type: ignore
        elif is_callback(check_target):
            self.loop.call_soon(target, *args)
        elif asyncio.iscoroutinefunction(check_target):
            # print('iscoroutinefunction {}'.format(check_target.__name__))
            task = self.loop.create_task(target(*args))
        else:
            task = self.loop.run_in_executor(  # type: ignore
                None, target, *args)

        # If a task is scheduled
        if self._track_task and task is not None:
            # print("5!!!")
            self._pending_tasks.append(task)

        return task
    
    @callback
    def async_run_job(self, target: Callable[..., None], *args: Any) -> None:
        """Run a job from within the event loop.

        This method must be run in the event loop.

        target: target to call.
        args: parameters for method to call.
        """
        if not asyncio.iscoroutine(target) and is_callback(target):
            target(*args)
        else:
            self.async_add_job(target, *args)
    
    @callback
    def async_create_task(self, target: Coroutine) -> asyncio.tasks.Task:
        """Create a task from within the eventloop.

        This method must be run in the event loop.

        target: target to call.
        """
        task = self.loop.create_task(target)  # type: asyncio.tasks.Task

        if self._track_task:
            self._pending_tasks.append(task)

        return task

    @callback
    def async_add_executor_job(
            self,
            target: Callable[..., T],
            *args: Any) -> Awaitable[T]:
        """Add an executor job from within the event loop."""
        task = self.loop.run_in_executor(
            None, target, *args)

        # If a task is scheduled
        if self._track_task:
            self._pending_tasks.append(task)

        return task

    @callback
    def async_track_tasks(self) -> None:
        """Track tasks so you can wait for all tasks to be done."""
        self._track_task = True

    @callback
    def async_stop_track_tasks(self) -> None:
        """Stop track tasks so you can't wait for all tasks to be done."""
        self._track_task = False

    def block_till_done(self) -> None:
        """Block till all pending work is done."""
        run_coroutine_threadsafe(
            self.async_block_till_done(), loop=self.loop).result()

    async def async_block_till_done(self) -> None:
        """Block till all pending work is done."""
        # To flush out any call_soon_threadsafe
        await asyncio.sleep(0)
        
        while self._pending_tasks:
            _LOGGER.debug("async_block_till_done -----")
            pending = [task for task in self._pending_tasks
                       if not task.done()]
            self._pending_tasks.clear()
            _LOGGER.debug(pending)
            if pending:
                _LOGGER.debug('pending')
                await asyncio.wait(pending)
            else:
                _LOGGER.debug('no pending')
                await asyncio.sleep(0)
    
    async def async_run(self) -> int:
        """ MerceEdge main entry point.

        Start and block until stopped.

        This method is a coroutine.
        """
        # _async_stop will set this instead of stopping the loop
        self._stopped = asyncio.Event()

        await self.async_start()
        async_register_signal_handling(self)

        _LOGGER.debug("self._stopped.wait() start")
        print(self._stopped)
        await self._stopped.wait()
        _LOGGER.debug("self._stopped.wait() stop")
        
        return self.exit_code
    
    async def async_start(self) -> None:
        """Finalize startup from inside the event loop.

        This method is a coroutine.
        """
        # _LOGGER.info("Starting Merce Edge")

        setattr(self.loop, '_thread_ident', threading.get_ident())
        # self.bus.async_fire(EVENT_HOMEASSISTANT_START)

        try:
            # Only block for EVENT_HOMEASSISTANT_START listener
            self.async_stop_track_tasks()
            with timeout(15):
                await self.async_block_till_done()
        except asyncio.TimeoutError:
            # TODO warning
            pass
            # _LOGGER.warning(
            #     'Something is blocking Home Assistant from wrapping up the '
            #     'start up phase. We\'re going to continue anyway. Please '
            #     'report the following info at http://bit.ly/2ogP58T : %s',
            #     ', '.join(self.config.components))

        # Allow automations to set up the start triggers before changing state
        await asyncio.sleep(0)

        # if self.state != CoreState.starting:
        #     _LOGGER.warning(
        #         'Home Assistant startup has been interrupted. '
        #         'Its state may be inconsistent.')
        #     return

        # self.state = CoreState.running
        _async_create_timer(self)

    async def async_stop(self, exit_code: int = 0, *,
                         force: bool = False) -> None:
        """Stop MerceEdge and shuts down all threads.

        The "force" flag commands async_stop to proceed regardless of
        Home Assistan't current state. You should not set this flag
        unless you're testing.

        This method is a coroutine.
        """
        _LOGGER.debug("Stop all wire load execution...")
        self.stop_wireload_exec()

        self.async_track_tasks()
        self.bus.async_fire(EVENT_EDGE_STOP)
        await self.async_block_till_done()
 
        self.executor.shutdown()
        
        _LOGGER.debug('MerceEdge loop stop...')
        self.loop.stop()
    
    def wireload_emit_output_payload(self, output_name, emit_call, payload):
        self.add_job(emit_call)


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
            return None
    
    def set_attrs(self, _attrs):
        self.attrs.update(_attrs)


class Component(Entity):
    """ABC for Merce Edge components"""
    
    def __init__(self, edge, model_template_config, id=None, init_params=None):
        """
        model_template_config: yaml object
        """
        self.edge = edge
        self.model_template_config = model_template_config
        self.id = id or id_util.generte_unique_id()
        self.inputs = {}
        self.outputs = {}
        self.init_params = init_params or {}
        # self.components = {}
        
        # init interfaces
        self._init_interfaces()

    @property
    def parameters(self):
        return self.init_params

    @parameters.setter
    def parameters(self, params):
        self.init_params = params
    
    def _init_interfaces(self):
        """initiate inputs & outputs
        """
        inputs = self.model_template_config['component'].get('inputs', None)
        if inputs:
            for _input in inputs:
                self.inputs[_input['name']] = Input(edge=self.edge, 
                                                    name=_input['name'], 
                                                    component=self, 
                                                    attrs=_input['protocol'],
                                                    propreties=_input.get('propreties', None))
        
        outputs = self.model_template_config['component'].get('outputs', None)
        if outputs:
            for _output in outputs:
                self.outputs[_output['name']] = Output(edge=self.edge,
                                                      name=_output['name'],
                                                      component=self,
                                                      attrs=_output['protocol'],
                                                      propreties=_output.get('propreties', None))   

    def get_start_wires_info(self):
        """ Get wires infomation that start from component
        """
        wires = []
        for output in self.outputs:
            for wire in output.output_wires:
                # TODO 
                pass
        return wires
    

class Interface(Entity):
    """Interface ABC 
    1. Read configuration file and load interface using service(eg: mqtt service).
    2. Listen message from EventBus, or call fire event provide by service(eg: mqtt service).
    """
    def __init__(self, edge, name, component, 
                 attrs=None, propreties=None):
        self.edge = edge
        self.name = name
        self.component = component
        self.propreties = propreties or {}
        self.attrs = attrs or {}
        self._set_protocol()
    
    def _set_protocol(self):
        self.protocol = self.attrs.get('name', 'virtual_interface')
        
   
class Output(Interface):
    """Virtual output interface, receive data from real world
    """
    def __init__(self, edge, name, component, attrs=None, propreties=None):
        super(Output, self).__init__(edge, name, component, attrs, propreties)
        self.output_wires = {}
        self.data = {}

        # read output configuration
        # print("init output {} {}".format(name, protocol))
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
    
    def _init_provider(self):
        try:
            self.provider = ServiceProviderFactory.get_provider(self.protocol)
            _LOGGER.debug("Output {} load provider {}".format(self.name, self.provider))
            # if self.provider:
            #     self.provider.new_instance_setup(self.name, self.attrs, True)
            # self.edge.add_job(self.provider.async_setup, self.edge, self.attrs)
        except KeyError as e:
            # log no such provider key error
            _LOGGER.error("Cannot load {} provider".format(self.protocol))
            raise
    
    async def conn_output_sink(self, output_wire_params={}):
        """ register EventBus listener"""
        self.edge.add_job(self.provider.async_setup, self.edge, self.attrs)
        await self.provider.conn_output_sink(output=self, 
                                       output_wire_params=output_wire_params,
                                       callback=self.output_sink_callback)
    
    def output_sink_callback(self, event):
        """Send output Event"""
        # 发送wirefire Event（连线的时候Wire的Output需要注册Input的wirefire事件）
        wirefire_event_type = "wirefire_{}_{}".format(self.component.id, self.name)
        self.edge.bus.fire(wirefire_event_type, event.data)


class Input(Interface):
    """Input"""
    def __init__(self, edge, name, component, attrs=None, propreties=None):
        super(Input, self).__init__(edge, name, component, attrs, propreties)
        self.input_wires = {}
        self._init_provider()
    
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
        
    def _init_provider(self):
        try:
            self.provider = ServiceProviderFactory.get_provider(self.protocol)
            # self.edge.add_job(self.provider.async_setup, self.edge, self.attrs)
        except KeyError:
            # TODO log no such provider key error
            raise

    async def conn_input_slot(self, input_wire_params={}):
        self.edge.add_job(self.provider.async_setup, self.edge, self.attrs)
        await self.provider.conn_input_slot(self, input_wire_params)

    async def emit_data_to_input(self, event):
        # Emit data to EventBus and invoke configuration service send data function.
        await self.provider.emit_input_slot(self, event.data)


class State(object):
    """Component State"""
    # raise NotImplementedError
    # TODO
    pass


class Wire(Entity):
    """Wire """
    def __init__(self, edge: MerceEdge, output_sink: Output, input_slot: Input, id=None):
        self.edge = edge
        self.id = id or id_util.generte_unique_id()
        self.input = output_sink
        self.output = input_slot
        self.input_params = dict()
        self.output_params = dict()

        self.input.add_wire(self)
        self.output.add_wire(self)
    
    def connect(self):
        outcom_id = self.output_sink.component.id
        out_name = self.output_sink.name
        wirefire_event_type = "wirefire_{}_{}".format(outcom_id, out_name)
        self.edge.bus.async_listen(wirefire_event_type, self.input_slot.emit_data_to_input)
          
    def _add_input(self, output_sink: Output):
        output_sink.add_wire(self)
    
    def _add_output(self, input_slot: Input):
        input_slot.add_wire(self)
    
    @property
    def output_sink(self):
        return self.input
    
    @property
    def input_slot(self):
        return self.output

    def __repr__(self):
        wire_info = {}
        wire_info["input"] = {"component_id": self.input.component.id, 
                            "name": self.input.name}
        wire_info["output"] = {"component_id": self.output.component.id,
                            "name": self.output.name}
        return wire_info      
    
    def set_input_params(self, parameters):
        self.input_params = parameters
        self.input.set_attrs(parameters)

    def set_output_params(self, parameters):
        self.output_params = parameters
        self.output.set_attrs(parameters)

    def disconnect(self):
        self.input.del_wire(self.id)
        self.output.del_wire(self.id)


class WireLoadFactory:
    def __init__(self, config):
        """
        config: user configuration
        """
        self._classes = {}
        paths = config['wireload']['paths']
        self._load(paths)

    def _load(self, paths):
        """Walk throuth path and load WireLoad subclass
        """
        classes = {}
        for path in paths:
            path = os.path.join(dir_path, path)
            classes = module_util.load_modules(path, WireLoad)
            self._classes.update(classes)
        _LOGGER.debug("Load wireloads modules: {}".format(self._classes))
        
    def get_class(self, wireload_name):
        return self._classes.get(wireload_name, None)


class WireLoad(Component):
    """Wire load abstract class. Mounted on wire, processing data through wire.
        Filter, Analiysis, Process, etc.
    """
    name = ''

    def __init__(self, edge, model_template_config, component_id=None, init_params=None):
        super(WireLoad, self).__init__(edge, model_template_config, id=component_id, init_params=init_params)
        self.input_q = asyncio.Queue(maxsize=3, loop=self.edge.loop)
        self.output_q = asyncio.Queue(maxsize=3, loop=self.edge.loop)
        self.is_stop = False
        self.emit_output_call = self.emit_output_payload

    def before_run_setup(self):
        """Need implemented"""
        raise NotImplementedError

    async def put_input_payload(self, payload):
        await self.input_q.put(payload)
        self.edge.add_job(self.run)
        
    async def put_output_payload(self, output_name, payload):
        await self.output_q.put((output_name, payload))
        self.edge.wireload_emit_output_payload(output_name, self.emit_output_call, payload)

    def process(self, input_payload):
        """Need implemented"""
        raise NotImplementedError

    async def run(self):
        while True:
            if self.is_stop:
                _LOGGER.debug("stop wireload------------")
                break
            input_payload = await self.input_q.get()
            
            await self.process(input_payload)
            del input_payload
            
            # if result:
            #     await self.output_q.put(result)
            #     self.edge.add_job(self.emit_output_payload)

    async def emit_output_payload(self):
        output_payload = await self.output_q.get()
        try:
            if output_payload:
                
                # self.outputs[output_payload[0]].output_sink_callback(output_payload[1])
                event_type = "{}_{}_{}".format("virtual_wire_event", self.id, output_payload[0])
                self.edge.bus.async_fire(event_type, output_payload[1])
        except KeyError as e:
            _LOGGER.warn("Cannot find output: {}".format(e))

    
class Event(object):
    # pylint: disable=too-few-public-methods
    """Represents an event within the Bus."""

    __slots__ = ['event_type', 'data', 'time_fired', 'context']

    def __init__(self, event_type: str, data: Optional[Dict] = None,
                 time_fired: Optional[int] = None,
                 context: Optional[Context] = None) -> None:
        """Initialize a new event."""
        self.event_type = event_type
        # TODO 
        self.data = data
        self.time_fired = time_fired or dt_util.utcnow()
        self.context = context or Context()

    def as_dict(self) -> Dict:
        """Create a dict representation of this Event."""
        return {
            'event_type': self.event_type,
            'data': dict(self.data),
            'time_fired': self.time_fired,
            'context': self.context.as_dict()
        }

    def __repr__(self) -> str:
        # pylint: disable=maybe-no-member
        """Return the representation."""
        # pylint: disable=maybe-no-member
        if self.data:
            return "<Event {}: {}>".format(
                self.event_type,
                util.repr_helper(self.data))

        return "<Event {}>".format(self.event_type)

    def __eq__(self, other: Any) -> bool:
        """Return the comparison."""
        return (self.__class__ == other.__class__ and  # type: ignore
                self.event_type == other.event_type and
                self.data == other.data and
                self.time_fired == other.time_fired and
                self.context == other.context)


class EventBus(object):
    """Allows firing of and listening for events.

       NOTE: This part of code references home-assistant and chage a little.
    """

    def __init__(self, edge: MerceEdge) -> None:
        """Initialize a new event bus."""
        self._listeners = {} # type: Dict[str, List[Callable]]
        self.edge = edge
    
    @callback
    def async_listeners(self) -> Dict[str, int]:
        """Dict with events and the number of listeners."""
        return {key: len(self._listeners[key])
                for key in self._listeners}

    @property
    def listeners(self) -> Dict[str, int]:
         """Dict with events and the number of listeners.
         """
         return run_callback_threadsafe(  # type: ignore
            self.edge.loop, self.async_listeners
        ).result()

    def fire(self, event_type: str, event_data: Optional[Dict] = None,
             context: Optional[Context] = None) -> None:
        """Fire an event."""
        self.edge.loop.call_soon_threadsafe(
            self.async_fire, event_type, event_data, context)
    
    @callback
    def async_fire(self, event_type: str, event_data: Optional[Dict] = None,
             context: Optional[Context] = None) -> None:
        """Fire an event.
        This method must be run in the event loop
        """
        # _LOGGER.info("async_fire: {}".format(event_type))

        listeners = self._listeners.get(event_type, [])

        # EVENT_HOMEASSISTANT_CLOSE should go only to his listeners
        match_all_listeners = self._listeners.get(MATCH_ALL)
        if (match_all_listeners is not None):
            listeners = match_all_listeners + listeners

        event = Event(event_type, event_data, None, context)

        # if event_type != EVENT_TIME_CHANGED:
        #     _LOGGER.debug("Bus:Handling %s", event)

        if not listeners:
            return

        for func in listeners:
            self.edge.async_add_job(func, event)
    
    def listen(
            self, event_type: str, listener: Callable) -> CALLBACK_TYPE:
        """Listen for all events or events of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.
        """
        async_remove_listener = run_callback_threadsafe(
            self.edge.loop, self.async_listen, event_type, listener).result()

        def remove_listener() -> None:
            """Remove the listener."""
            run_callback_threadsafe(
                self.edge.loop, async_remove_listener).result()

        return remove_listener
    
    @callback
    def async_listen(self, event_type: str, listener: Callable) -> CALLBACK_TYPE:
        """Listen for all events or events of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.

        This method must be run in the event loop.
        """
        if event_type in self._listeners:
            self._listeners[event_type].append(listener)
        else:
            self._listeners[event_type] = [listener]

        def remove_listener() -> None:
            """Remove the listener."""
            self._async_remove_listener(event_type, listener)

        return remove_listener

    def listen_once(
            self, event_type: str, listener: Callable) -> CALLBACK_TYPE:
        """Listen once for event of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.

        Returns function to unsubscribe the listener.
        """
        async_remove_listener = run_callback_threadsafe(
            self.edge.loop, self.async_listen_once, event_type, listener,
        ).result()

        def remove_listener() -> None:
            """Remove the listener."""
            run_callback_threadsafe(
                self.edge.loop, async_remove_listener).result()

        return remove_listener

    @callback
    def async_listen_once(
            self, event_type: str, listener: Callable) -> CALLBACK_TYPE:
        """Listen once for event of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.

        Returns registered listener that can be used with remove_listener.

        This method must be run in the event loop.
        """
        @callback
        def onetime_listener(event: Event) -> None:
            """Remove listener from event bus and then fire listener."""
            if hasattr(onetime_listener, 'run'):
                return
            # Set variable so that we will never run twice.
            # Because the event bus loop might have async_fire queued multiple
            # times, its possible this listener may already be lined up
            # multiple times as well.
            # This will make sure the second time it does nothing.
            setattr(onetime_listener, 'run', True)
            self._async_remove_listener(event_type, onetime_listener)
            self.edge.async_run_job(listener, event)

        return self.async_listen(event_type, onetime_listener)

    @callback
    def _async_remove_listener(
            self, event_type: str, listener: Callable) -> None:
        """Remove a listener of a specific event_type.

        This method must be run in the event loop.
        """
        try:
            self._listeners[event_type].remove(listener)

            # delete event_type list if empty
            if not self._listeners[event_type]:
                self._listeners.pop(event_type)
        except (KeyError, ValueError):
            # KeyError is key event_type listener did not exist
            # ValueError if listener did not exist within event_type
            _LOGGER.warning("Unable to remove unknown listener %s", listener)



def _async_create_timer(edge: MerceEdge) -> None:
    """Create a timer that will start on EVENT_EDGE_START."""
    handle = None

    def schedule_tick(now: datetime.datetime) -> None:
        """Schedule a timer tick when the next second rolls around."""
        nonlocal handle

        slp_seconds = 1 - (now.microsecond / 10**6)
        target = monotonic() + slp_seconds
        handle = edge.loop.call_later(slp_seconds, fire_time_event, target)

    @callback
    def fire_time_event(target: float) -> None:
        """Fire next time event."""
        now = dt_util.utcnow()

        edge.bus.async_fire(EVENT_TIME_CHANGED,
                            {ATTR_NOW: now})

        # If we are more than a second late, a tick was missed
        late = monotonic() - target
        if late > 1:
            edge.bus.async_fire(EVENT_TIMER_OUT_OF_SYNC,
                                {ATTR_SECONDS: late})

        schedule_tick(now)

    @callback
    def stop_timer(_: Event) -> None:
        """Stop the timer."""
        if handle is not None:
            handle.cancel()

    edge.bus.async_listen_once(EVENT_EDGE_STOP, stop_timer)
    
    _LOGGER.info("Timer:starting")
    schedule_tick(dt_util.utcnow())