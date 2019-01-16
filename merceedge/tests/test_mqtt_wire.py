import sys
from multiprocessing import Process
import threading
import signal

from merceedge.core import (
    MerceEdge,
    Component,
    Wire,
    Input,
    Output
)
from merceedge.providers import PROVIDERS
from merceedge.util import yaml as yaml_util

def run_edge_process(edge_proc):
    """ Runs a child hass process. Returns True if it should be restarted.  """
    requested_stop = threading.Event()
    edge_proc.daemon = True

    def request_stop(*args):
        """ request hass stop, *args is for signal handler callback """
        requested_stop.set()
        edge_proc.terminate()

    try:
        signal.signal(signal.SIGTERM, request_stop)
    except ValueError:
        print('Could not bind to SIGTERM. Are you running in a thread?')

    edge_proc.start()
    try:
        edge_proc.join()
    except KeyboardInterrupt:
        request_stop()
        try:
            edge_proc.join()
        except KeyboardInterrupt:
            return False

    return (not requested_stop.isSet() and
            edge_proc.exitcode == 100,
            edge_proc.exitcode)


def setup_and_run_hass(edge, top_process=False):
    """
    Setup HASS and run. Block until stopped. Will assume it is running in a
    subprocess unless top_process is set to true.
    """
   

    edge.start()
    # exit_code = int(edge.block_till_stopped())

    # if not top_process:
    #     sys.exit(exit_code)
    return 0


def test_template_load():
    edge = MerceEdge()
    edge.load_local_component_templates('./merceedge/tests/')
    print(edge.component_templates)
    assert len(edge.component_templates) == 2

    # check inputs and outputs
    names = []
    for name, template in edge.component_templates.items():
        print(template.inputs)
        print(template.outputs)
        names.append(name)

    # test deepcopy template
    print(names)
    for template_name in names:
        edge.generate_component_instance(template_name)
    
    print("components instances: {}".format(edge.components))
    assert len(edge.components) == 2

    # setup services
    user_config = yaml_util.load_yaml('./merceedge/config.yaml')
    PROVIDERS['mqtt'].setup(edge, user_config)
    # for name, provider in PROVIDERS:
    #     provider.setup(edge, user_config)

    # test connect wire
    # create new wire
    wire = Wire(edge.components[1].outputs['toggle_output'], 
                edge.components[0].inputs['toggle_input'])
    # connect wire
    edge.components[1].outputs['toggle_output'].add_wire(wire)
    edge.components[0].inputs['toggle_input'].add_wire(wire)
    edge.components[1].outputs['toggle_output'].conn_output_sink()
    
    keep_running = True
    while keep_running:
        hass_proc = Process(target=setup_and_run_hass)
        keep_running, exit_code = run_edge_process(hass_proc)
        
    return exit_code

if __name__ == "__main__":
    sys.exit(test_template_load())
    
    



