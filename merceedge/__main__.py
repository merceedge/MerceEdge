import sys
from multiprocessing import Process
import threading
import signal
import argparse
import pyfiglet
import os 
import asyncio
dir_path = os.path.dirname(os.path.realpath(__file__))

from merceedge.util.async_util import asyncio_run
from merceedge.core import (
    MerceEdge,
    Component,
    Wire,
    Input,
    Output
)
from merceedge.providers import ServiceProviderFactory
from merceedge.util import yaml as yaml_util
from merceedge.api_server import app as api_server



# def run_edge_process(edge_proc):
#     """ Runs a child hass process. Returns True if it should be restarted.  """
#     requested_stop = threading.Event()
#     edge_proc.daemon = True

#     def request_stop(*args):
#         """ request hass stop, *args is for signal handler callback """
#         requested_stop.set()
#         edge_proc.terminate()

#     try:
#         signal.signal(signal.SIGTERM, request_stop)
#     except ValueError:
#         print('Could not bind to SIGTERM. Are you running in a thread?')

#     edge_proc.start()
#     try:
#         edge_proc.join()
#     except KeyboardInterrupt:
#         request_stop()
#         try:
#             edge_proc.join()
#         except KeyboardInterrupt:
#             return False

#     return (not requested_stop.isSet() and
#             edge_proc.exitcode == 100,
#             edge_proc.exitcode)


async def setup_and_run_edge(edge):
    """
    Setup Edge and run. Block until stopped. Will assume it is running in a
    subprocess unless top_process is set to true.
    """
    return await edge.async_run()

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
    
    ascii_banner = pyfiglet.figlet_format("MerceEdge")
    print(ascii_banner)

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--formula', dest='formula', help='formula yml')
    args = parser.parse_args()


    # 0. Load local yaml component templates
    print("Load user config file: {}".format(os.path.join(dir_path, 'config.yaml')))
    user_config = yaml_util.load_yaml(os.path.join(dir_path, 'config.yaml'))
    edge = MerceEdge(user_config=user_config)
    print("Load component tempalte path: {}".format(os.path.join(dir_path, 'tests', 'component_template')))
    edge.load_local_component_templates(os.path.join(dir_path, 'tests', 'component_template'))
    # print(edge.component_templates)
    
    # 1. setup services
    # Walk throught service provider path and load all services
    print("Load service provider path: {}".format(os.path.join(dir_path, user_config['provider_path'])))
    ServiceProviderFactory.init(os.path.join(dir_path, user_config['provider_path']), edge, user_config)
    setup_tasks = []
    for name, provider in ServiceProviderFactory.providers.items():
        print(name)
        setup_tasks.append(provider.async_setup(edge, user_config))
    
    edge.loop.run_until_complete(asyncio.wait(setup_tasks))
    
    print('start run---')
    # 2. Read database and restore components / wires
    # edge.restore_entities_from_db()

    # 3. setup api server
    api_server.setup(edge)

    # load formula
    if args.formula:
        formula_path = args.formula.strip()
        edge.loop.run_until_complete(edge.load_formula(formula_path))

    # 4. run ...
    # keep_running = True
    # while keep_running:
    #     edge_proc = Process(target=setup_and_run_hass, args=(edge, ))
    #     keep_running, exit_code = run_edge_process(edge_proc)
    
    # exit_code = asyncio_run(setup_and_run_edge(edge))
    edge.start()

    return 0


if __name__ == "__main__":
    sys.exit(main())