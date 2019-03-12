import asyncio
import functools
from typing import (  # noqa: F401 pylint: disable=unused-import
    Optional, Any, Callable, List, TypeVar, Dict, Coroutine, Set,
    TYPE_CHECKING, Awaitable, Iterator)

from merceedge.core import EventBus


def gen_test_loop(edge):
    """ Test decorator, generate test asyncio loop
    """
    def real_dec(func):
        @functools.wraps(func)
        def wrapper_do_loop(*args, **kwargs):
            edge.loop.run_until_complete(func(*args, **kwargs))
            edge.loop.close()
        return wrapper_do_loop
    return real_dec
        
        
class MockEdge:
    def __init__(self, package_config):
        self.user_config = package_config
        self.loop = asyncio.get_event_loop()
        self.bus = EventBus(self)

    def wireload_emit_output_payload(self, 
                                    output_name, 
                                    mock_output_call, 
                                    output_payload):
        mock_output_call(output_name, output_payload)   

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
        
        if asyncio.iscoroutinefunction(check_target):
            task = self.loop.create_task(target(*args))
        else:
            task = self.loop.run_in_executor(  # type: ignore
                None, target, *args)
        return task