import threading
from typing import (  # noqa: F401 pylint: disable=unused-import
    Optional, Any, Callable, List, TypeVar, Dict, Coroutine, Set,
    TYPE_CHECKING, Awaitable, Iterator)
import asyncio
from async_timeout import timeout
from types import MappingProxyType
import voluptuous as vol
import logging
import merceedge.util as util

from merceedge.const import (
    EVENT_CALL_SERVICE,
    EVENT_SERVICE_REGISTERED,
    EVENT_SERVICE_REMOVED,
    EVENT_SERVICE_EXECUTED,
    ATTR_DOMAIN,
    ATTR_SERVICE,
    ATTR_SERVICE_DATA,
    ATTR_SERVICE_CALL_ID,
)
from merceedge.util.async_util import (
    Context,
    callback,
    is_callback,
    run_callback_threadsafe,
    run_coroutine_threadsafe,
    CALLBACK_TYPE
)
from merceedge.exceptions import (
    ServiceNotFound,
    Unauthorized
)

# Typing imports that create a circular dependency
# pylint: disable=using-constant-test
if TYPE_CHECKING:
    from merceedge.core import MerceEdge

_LOGGER = logging.getLogger(__name__)
# How long we wait for the result of a service call
SERVICE_CALL_LIMIT = 10  # seconds

# pylint: disable=too-few-public-methods
class Service(object):
    """Represents a callable service."""

    __slots__ = ['func', 'schema', 'is_callback', 'is_coroutinefunction']

    def __init__(self, func: Callable, schema: Optional[vol.Schema],
                 context: Optional[Context] = None) -> None:
        """Initialize a service."""
        self.func = func
        self.schema = schema
        self.is_callback = is_callback(func)
        self.is_coroutinefunction = asyncio.iscoroutinefunction(func)


class ServiceCall:
    """Representation of a call to a service."""

    __slots__ = ['domain', 'service', 'data', 'context']

    def __init__(self, domain: str, service: str, data: Optional[Dict] = None,
                 context: Optional[Context] = None) -> None:
        """Initialize a service call."""
        self.domain = domain.lower()
        self.service = service.lower()
        self.data = MappingProxyType(data or {})
        self.context = context or Context()

    def __repr__(self) -> str:
        """Return the representation of the service."""
        if self.data:
            return "<ServiceCall {}.{} (c:{}): {}>".format(
                self.domain, self.service, self.context.id,
                util.repr_helper(self.data))

        return "<ServiceCall {}.{} (c:{})>".format(
            self.domain, self.service, self.context.id)



class ServiceRegistry(object):
    """Offers services over the eventbus."""

    def __init__(self, edge):
        """Initialize a service registry."""
        self._services = {}  # type: Dict[str, Dict[str, Service]]
        self.edge = edge

    @property
    def services(self) -> Dict[str, Dict[str, Service]]:
        """Return dictionary with per domain a list of available services."""
        return run_callback_threadsafe(  # type: ignore
            self.edge.loop, self.async_services,
        ).result()
    
    @callback
    def async_services(self) -> Dict[str, Dict[str, Service]]:
        """Return dictionary with per domain a list of available services.

        This method must be run in the event loop.
        """
        return {domain: self._services[domain].copy()
                for domain in self._services}

    def has_service(self, domain, service):
        """Test if specified service exists."""
        return service.lower() in self._services.get(domain.lower(), [])


    def register(self, domain: str, service: str, service_func: Callable,
                 schema: Optional[vol.Schema] = None) -> None:
        """
        Register a service.

        Schema is called to coerce and validate the service data.
        """
        run_callback_threadsafe(
            self.edge.loop,
            self.async_register, domain, service, service_func, schema
        ).result()


    @callback
    def async_register(self, domain: str, service: str, service_func: Callable,
                       schema: Optional[vol.Schema] = None) -> None:
        """
        Register a service.

        Schema is called to coerce and validate the service data.

        This method must be run in the event loop.
        """
        domain = domain.lower()
        service = service.lower()
        service_obj = Service(service_func, schema)

        if domain in self._services:
            self._services[domain][service] = service_obj
        else:
            self._services[domain] = {service: service_obj}

        self.edge.bus.async_fire(
            EVENT_SERVICE_REGISTERED,
            {ATTR_DOMAIN: domain, ATTR_SERVICE: service}
        )

    def remove(self, domain: str, service: str) -> None:
        """Remove a registered service from service handler."""
        run_callback_threadsafe(
            self.edge.loop, self.async_remove, domain, service).result()

    @callback
    def async_remove(self, domain: str, service: str) -> None:
        """Remove a registered service from service handler.

        This method must be run in the event loop.
        """
        domain = domain.lower()
        service = service.lower()

        if service not in self._services.get(domain, {}):
            _LOGGER.warning(
                "Unable to remove unknown service %s/%s.", domain, service)
            return

        self._services[domain].pop(service)

        self.edge.bus.async_fire(
            EVENT_SERVICE_REMOVED,
            {ATTR_DOMAIN: domain, ATTR_SERVICE: service}
        )

    def call(self, domain: str, service: str,
             service_data: Optional[Dict] = None,
             blocking: bool = False,
             context: Optional[Context] = None) -> Optional[bool]:
        """
        Call a service.

        Specify blocking=True to wait till service is executed.
        Waits a maximum of SERVICE_CALL_LIMIT.

        If blocking = True, will return boolean if service executed
        successfully within SERVICE_CALL_LIMIT.

        This method will fire an event to call the service.
        This event will be picked up by this ServiceRegistry and any
        other ServiceRegistry that is listening on the EventBus.

        Because the service is sent as an event you are not allowed to use
        the keys ATTR_DOMAIN and ATTR_SERVICE in your service_data.
        """
        return run_coroutine_threadsafe(  # type: ignore
            self.async_call(domain, service, service_data, blocking, context),
            self.edge.loop
        ).result()

    async def async_call(self, domain: str, service: str,
                         service_data: Optional[Dict] = None,
                         blocking: bool = False,
                         context: Optional[Context] = None) -> Optional[bool]:
        """
        Call a service.

        Specify blocking=True to wait till service is executed.
        Waits a maximum of SERVICE_CALL_LIMIT.

        If blocking = True, will return boolean if service executed
        successfully within SERVICE_CALL_LIMIT.

        This method will fire an event to call the service.
        This event will be picked up by this ServiceRegistry and any
        other ServiceRegistry that is listening on the EventBus.

        Because the service is sent as an event you are not allowed to use
        the keys ATTR_DOMAIN and ATTR_SERVICE in your service_data.

        This method is a coroutine.
        """
        domain = domain.lower()
        service = service.lower()
        context = context or Context()
        service_data = service_data or {}

        try:
            handler = self._services[domain][service]
        except KeyError:
            raise ServiceNotFound(domain, service) from None

        if handler.schema:
            processed_data = handler.schema(service_data)
        else:
            processed_data = service_data

        service_call = ServiceCall(domain, service, processed_data, context)

        self.edge.bus.async_fire(EVENT_CALL_SERVICE, {
            ATTR_DOMAIN: domain.lower(),
            ATTR_SERVICE: service.lower(),
            ATTR_SERVICE_DATA: service_data,
        })

        if not blocking:
            self.edge.async_create_task(
                self._safe_execute(handler, service_call))
            return None

        try:
            with timeout(SERVICE_CALL_LIMIT):
                await asyncio.shield(
                    self._execute_service(handler, service_call))
            return True
        except asyncio.TimeoutError:
            return False

    async def _safe_execute(self, handler: Service,
                            service_call: ServiceCall) -> None:
        """Execute a service and catch exceptions."""
        try:
            await self._execute_service(handler, service_call)
        except Unauthorized:
            _LOGGER.warning('Unauthorized service called %s/%s',
                            service_call.domain, service_call.service)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception('Error executing service %s', service_call)

    async def _execute_service(self, handler: Service,
                               service_call: ServiceCall) -> None:
        """Execute a service."""
        if handler.is_callback:
            handler.func(service_call)
        elif handler.is_coroutinefunction:
            await handler.func(service_call)
        else:
            await self.edge.async_add_executor_job(handler.func, service_call)
