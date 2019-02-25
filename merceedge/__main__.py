import sys
from multiprocessing import Process
import threading
import signal
import argparse
import pyfiglet
import os 
import asyncio
dir_path = os.path.dirname(os.path.realpath(__file__))


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

def set_loop() -> None:
    """Attempt to use uvloop."""
    import asyncio
    from asyncio.events import BaseDefaultEventLoopPolicy

    policy = None

    if sys.platform == 'win32':
        if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
            # pylint: disable=no-member
            policy = asyncio.WindowsProactorEventLoopPolicy()
        else:
            class ProactorPolicy(BaseDefaultEventLoopPolicy):
                """Event loop policy to create proactor loops."""

                _loop_factory = asyncio.ProactorEventLoop

            policy = ProactorPolicy()
    else:
        try:
            import uvloop
        except ImportError:
            pass
        else:
            policy = uvloop.EventLoopPolicy()

    if policy is not None:
        asyncio.set_event_loop_policy(policy)


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

    set_loop()

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--formula', dest='formula', help='formula yml')
    args = parser.parse_args()

    # 0. Load local yaml component templates
    merceedge_home_path = os.environ['MERCE_EDGE_HOME']
    print("Load user config file: {}".format(os.path.join(merceedge_home_path, 'merceedge', 'config.yaml')))
    user_config = yaml_util.load_yaml(os.path.join(merceedge_home_path, 'merceedge', 'config.yaml'))
    edge = MerceEdge(user_config=user_config)
    print("Load component tempalte path: {}".format(os.path.join(dir_path, 'tests', 'component_template')))
    # Get component template load paths from config.yml

    edge.load_local_component_templates(user_config)
    # print(edge.component_templates)
    
    # 1. setup services
    # Walk throught service provider path and load all services
    print("Load service provider path: {}".format(os.path.join(dir_path, user_config['provider_path'])))
    ServiceProviderFactory.init(os.path.join(dir_path, user_config['provider_path']), edge, user_config)
    # setup_tasks = []
    # for name, provider in ServiceProviderFactory.providers.items():
    #     setup_tasks.append(provider.async_setup(edge, user_config))
    # edge.loop.run_until_complete(asyncio.wait(setup_tasks))
    

    # 3. setup api server
    api_server.setup(edge)

    # load formula

    if args.formula:
        formula_path = args.formula.strip()
        edge.loop.run_until_complete(edge.load_formula(formula_path))

    # 4. run ...
    from merceedge.util.signal import async_register_signal_handling
    async_register_signal_handling(edge)

    exit_code = edge.start()

    return exit_code
    
if __name__ == "__main__":
    sys.exit(main())

