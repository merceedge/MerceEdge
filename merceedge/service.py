import threading

import merceedge.util as util

from merceedge.const import (
    EVENT_CALL_SERVICE,
    EVENT_SERVICE_REGISTERED,
    EVENT_SERVICE_EXECUTED,
    ATTR_DOMAIN,
    ATTR_SERVICE,
    ATTR_SERVICE_DATA,
    ATTR_SERVICE_CALL_ID,
)

# How long we wait for the result of a service call
SERVICE_CALL_LIMIT = 10  # seconds

# pylint: disable=too-few-public-methods
class Service(object):
    """Represents a callable service."""

    __slots__ = ['func', 'description', 'fields']

    def __init__(self, func, description, fields):
        """Initialize a service."""
        self.func = func
        self.description = description or ''
        self.fields = fields or {}

    def as_dict(self):
        """Return dictionary representation of this service."""
        return {
            'description': self.description,
            'fields': self.fields,
        }

    def __call__(self, call):
        """Execute the service."""
        self.func(call)


# pylint: disable=too-few-public-methods
class ServiceCall(object):
    """Represents a call to a service."""

    __slots__ = ['domain', 'service', 'data', 'call_id']

    def __init__(self, domain, service, data=None, call_id=None):
        """Initialize a service call."""
        self.domain = domain
        self.service = service
        self.data = data or {}
        self.call_id = call_id

    def __repr__(self):
        if self.data:
            return "<ServiceCall {}.{}: {}>".format(
                self.domain, self.service, util.repr_helper(self.data))
        else:
            return "<ServiceCall {}.{}>".format(self.domain, self.service)


class ServiceRegistry(object):
    """Offers services over the eventbus."""

    def __init__(self, bus, pool=None):
        """Initialize a service registry."""
        self._services = {}
        self._lock = threading.Lock()
        self._pool = pool or util.create_worker_pool()
        self._bus = bus
        self._cur_id = 0
        bus.listen(EVENT_CALL_SERVICE, self._event_to_service_call)

    @property
    def services(self):
        """Dict with per domain a list of available services."""
        with self._lock:
            return {domain: {key: value.as_dict() for key, value
                             in self._services[domain].items()}
                    for domain in self._services}

    def has_service(self, domain, service):
        """Test if specified service exists."""
        return service in self._services.get(domain, [])

    def register(self, domain, service, service_func, description=None):
        """
        Register a service.

        Description is a dict containing key 'description' to describe
        the service and a key 'fields' to describe the fields.
        """
        description = description or {}
        service_obj = Service(service_func, description.get('description'),
                              description.get('fields', {}))
        with self._lock:
            if domain in self._services:
                self._services[domain][service] = service_obj
            else:
                self._services[domain] = {service: service_obj}

            self._bus.fire(
                EVENT_SERVICE_REGISTERED,
                {ATTR_DOMAIN: domain, ATTR_SERVICE: service})

    def call(self, domain, service, service_data=None, blocking=False):
        """
        Call a service.

        Specify blocking=True to wait till service is executed.
        Waits a maximum of SERVICE_CALL_LIMIT.

        If blocking = True, will return boolean if service executed
        succesfully within SERVICE_CALL_LIMIT.

        This method will fire an event to call the service.
        This event will be picked up by this ServiceRegistry and any
        other ServiceRegistry that is listening on the EventBus.

        Because the service is sent as an event you are not allowed to use
        the keys ATTR_DOMAIN and ATTR_SERVICE in your service_data.
        """
        call_id = self._generate_unique_id()

        event_data = {
            ATTR_DOMAIN: domain,
            ATTR_SERVICE: service,
            ATTR_SERVICE_DATA: service_data,
            ATTR_SERVICE_CALL_ID: call_id,
        }

        if blocking:
            executed_event = threading.Event()

            def service_executed(call):
                """Callback method that is called when service is executed."""
                if call.data[ATTR_SERVICE_CALL_ID] == call_id:
                    executed_event.set()

            self._bus.listen(EVENT_SERVICE_EXECUTED, service_executed)

        self._bus.fire(EVENT_CALL_SERVICE, event_data)

        if blocking:
            success = executed_event.wait(SERVICE_CALL_LIMIT)
            self._bus.remove_listener(
                EVENT_SERVICE_EXECUTED, service_executed)
            return success

    def _event_to_service_call(self, event):
        """Callback for SERVICE_CALLED events from the event bus."""
        service_data = event.data.get(ATTR_SERVICE_DATA)
        domain = event.data.get(ATTR_DOMAIN)
        service = event.data.get(ATTR_SERVICE)
        call_id = event.data.get(ATTR_SERVICE_CALL_ID)

        if not self.has_service(domain, service):
            return

        service_handler = self._services[domain][service]
        service_call = ServiceCall(domain, service, service_data, call_id)

        # Add a job to the pool that calls _execute_service
        self._pool.add_job(util.JobPriority.EVENT_SERVICE,
                           (self._execute_service,
                            (service_handler, service_call)))

    def _execute_service(self, service_and_call):
        """Execute a service and fires a SERVICE_EXECUTED event."""
        service, call = service_and_call
        service(call)

        if call.call_id is not None:
            self._bus.fire(
                EVENT_SERVICE_EXECUTED, {ATTR_SERVICE_CALL_ID: call.call_id})

    def _generate_unique_id(self):
        """Generate a unique service call id."""
        self._cur_id += 1
        return "{}-{}".format(id(self), self._cur_id)
