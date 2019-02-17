

from merceedge.providers.base import ServiceProvider
from merceedge.util.module import load_modules

class ServiceProviderFactory(object):
    provider_classes = {}
    providers = {}
    config = {}
    edge = None
    @staticmethod
    def init(provider_path, edge, config):
        ServiceProviderFactory.provider_classes = load_modules(path=provider_path, base_class=ServiceProvider)
        ServiceProviderFactory.config = config
        ServiceProviderFactory.edge = edge
        # for name, provider_class in ServiceProviderFactory.provider_classes.items():
        #     ServiceProviderFactory.providers[name] = provider_class(edge, config)
    
    @staticmethod 
    def get_provider(provider_name):
        try:
            provider_class = ServiceProviderFactory.provider_classes[provider_name]
            provider_obj = provider_class(ServiceProviderFactory.edge, ServiceProviderFactory.config)
            return provider_obj
        except KeyError:
            return None
            # TODO raise UnKownProviderError
        

