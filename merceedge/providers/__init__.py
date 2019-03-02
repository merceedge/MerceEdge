
import os
from merceedge.providers.base import ServiceProvider
from merceedge.util.module import load_modules
from merceedge.exceptions import MerceEdgeError

from merceedge.settings import (
    logger_access,
    logger_code,
    logger_console
)

_LOGGER = logger_code

class ServiceProviderFactory(object):
    provider_classes = {}
    providers = {}
    config = {}
    edge = None

    @staticmethod
    def init(provider_paths, edge, config):
        def get_valid_path(path):
            try:
                ab_path = ''
                if path.startswith('/') or path[1] == ":":
                    ab_path = path
                else:
                    ab_path = os.path.join(os.environ['MERCE_EDGE_HOME'], 'merceedge', path)
                # test ab_path is exist
                if not os.path.exists(ab_path):
                    raise MerceEdgeError('Load provider failed!')
                return ab_path
            except KeyError:
                raise MerceEdgeError('Load provider failed!')
        
        for path in provider_paths:
            ab_path = get_valid_path(path)
            _LOGGER.info("Load service provider path: {}".format(ab_path))
            classes = {}    
            classes = load_modules(path=ab_path, base_class=ServiceProvider)
            ServiceProviderFactory.provider_classes.update(classes)
        ServiceProviderFactory.config = config
        ServiceProviderFactory.edge = edge
    
    @staticmethod 
    def get_provider(provider_name):
        try:
            provider_class = ServiceProviderFactory.provider_classes[provider_name]
            provider_obj = provider_class(ServiceProviderFactory.edge, ServiceProviderFactory.config)
            return provider_obj
        except KeyError:
            return None
            # TODO raise UnKownProviderError
        

