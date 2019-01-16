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
from merceedge.api_server import app as api_server

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


def main():
    """Start Merce edge
     0. Load local yaml component templates
     1. Setup services
     
     2. Read database and restore components / wires
     3. Wait client call HTTP API(registe, connentc wire, search, etc)
       3.1 component templates APIs
       3.2 component APIs
       3.3 Wire APIs 
    4. translate data
    """

    # 0. Load local yaml component templates
    edge = MerceEdge()
    edge.load_local_component_templates('./merceedge/tests/')
    print(edge.component_templates)
    
    # 1. setup services
    user_config = yaml_util.load_yaml('./merceedge/config.yaml')
    # TODO need walk throught service provider path and load all services
    PROVIDERS['mqtt'].setup(edge, user_config)
    # for name, provider in PROVIDERS:
    #     provider.setup(edge, user_config)
    
    # 2. Read database and restore components / wires
    # edge.restore_entities_from_db()

    # 3. setup api server
    api_server.setup(edge)
    
    # 4. run ...
    keep_running = True
    while keep_running:
        edge_proc = Process(target=setup_and_run_hass, args=(edge, ))
        keep_running, exit_code = run_edge_process(edge_proc)

        
    return exit_code
    
    
if __name__ == "__main__":
    sys.exit(main())