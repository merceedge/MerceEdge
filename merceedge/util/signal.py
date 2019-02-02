"""Signal handling related helpers."""
import logging
import signal
import sys
from merceedge.util.async_util import callback

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_signal_handling(edge) -> None:
    """Register system signal handler for core."""
    if sys.platform != 'win32':
        @callback
        def async_signal_handle(exit_code) -> None:
            """Wrap signal handling.

            * queue call to shutdown task
            * re-instate default handler
            """
            edge.loop.remove_signal_handler(signal.SIGTERM)
            edge.loop.remove_signal_handler(signal.SIGINT)
            edge.async_stop_track_tasks()
            edge.async_create_task(edge.async_stop(exit_code))
        
        for signame in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            try:
                edge.loop.add_signal_handler(
                    signame, async_signal_handle, 0)
                
            except ValueError:
                _LOGGER.warning("Could not bind to SIGHUP")

    
    # else:
    #     old_sigterm = None
    #     old_sigint = None

    #     @callback
    #     def async_signal_handle(exit_code: int, frame: FrameType) -> None:
    #         """Wrap signal handling.

    #         * queue call to shutdown task
    #         * re-instate default handler
    #         """
    #         signal.signal(signal.SIGTERM, old_sigterm)
    #         signal.signal(signal.SIGINT, old_sigint)
    #         edge.async_create_task(edge.async_stop(exit_code))

    #     try:
    #         old_sigterm = signal.signal(signal.SIGTERM, async_signal_handle)
    #     except ValueError:
    #         _LOGGER.warning("Could not bind to SIGTERM")

    #     try:
    #         old_sigint = signal.signal(signal.SIGINT, async_signal_handle)
    #     except ValueError:
    #         _LOGGER.warning("Could not bind to SIGINT")
        