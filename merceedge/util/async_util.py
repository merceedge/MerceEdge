import concurrent.futures
import threading
import logging
from asyncio import coroutines
from asyncio.events import AbstractEventLoop
from asyncio.futures import Future

import asyncio
from asyncio import ensure_future
from typing import Any, Union, Coroutine, Callable, Generator, TypeVar, \
                   Awaitable

_LOGGER = logging.getLogger(__name__)



def run_callback_threadsafe(loop: AbstractEventLoop, callback: Callable,
                            *args: Any) -> concurrent.futures.Future:
    """Submit a callback object to a given event loop.

    Return a concurrent.futures.Future to access the result.
    """
    ident = loop.__dict__.get("_thread_ident")
    if ident is not None and ident == threading.get_ident():
        raise RuntimeError('Cannot be called from within the event loop')

    future = concurrent.futures.Future()  # type: concurrent.futures.Future

    def run_callback() -> None:
        """Run callback and store result."""
        try:
            future.set_result(callback(*args))
        except Exception as exc:  # pylint: disable=broad-except
            if future.set_running_or_notify_cancel():
                future.set_exception(exc)
            else:
                _LOGGER.warning("Exception on lost future: ", exc_info=True)

    loop.call_soon_threadsafe(run_callback)
    return future