import enum
import queue
import threading
from datetime import datetime
from types import MappingProxyType
import logging

from merceedge.util.dt import utcnow
from merceedge.const import (
    EVENT_CALL_SERVICE,
    EVENT_SERVICE_REGISTERED,
    EVENT_SERVICE_EXECUTED,
    EVENT_STATE_CHANGED,
    EVENT_TIME_CHANGED,
)
from .dt import datetime_to_local_str, utcnow

# Define number of MINIMUM worker threads.
# During bootstrap of HA (see bootstrap._setup_component()) worker threads
# will be added for each component that polls devices.
MIN_WORKER_THREAD = 2

_LOGGER = logging.getLogger(__name__)


def create_worker_pool(worker_count=None):
    """Create a worker pool."""
    if worker_count is None:
        worker_count = MIN_WORKER_THREAD

    def job_handler(job):
        """Called whenever a job is available to do."""
        try:
            func, arg = job
            func(arg)
        except Exception:  
            
            # Catch any exception our service/event_listener might throw
            # We do not want to crash our ThreadPool
            _LOGGER.exception("BusHandler:Exception doing job")

    def busy_callback(worker_count, current_jobs, pending_jobs_count):
        """Callback to be called when the pool queue gets too big."""
        _LOGGER.warning(
            "WorkerPool:All %d threads are busy and %d jobs pending",
            worker_count, pending_jobs_count)

        for start, job in current_jobs:
            _LOGGER.warning("WorkerPool:Current job from %s: %s",
                            datetime_to_local_str(start), job)
    
    return ThreadPool(job_handler, worker_count, busy_callback)


def repr_helper(inp):
    """ Helps creating a more readable string representation of objects. """
    if isinstance(inp, (dict, MappingProxyType)):
        return ", ".join(
            repr_helper(key)+"="+repr_helper(item) for key, item
            in inp.items())
    elif isinstance(inp, datetime):
        return datetime_to_local_str(inp)
    else:
        return str(inp)


def convert(value, to_type, default=None):
    """ Converts value to to_type, returns default if fails. """
    try:
        return default if value is None else to_type(value)
    except (ValueError, TypeError):
        # If value could not be converted
        return default


class OrderedEnum(enum.Enum):
    """ Taken from Python 3.4.0 docs. """
    # pylint: disable=no-init, too-few-public-methods

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class JobPriority(OrderedEnum):
    """Provides job priorities for event bus jobs."""

    EVENT_CALLBACK = 0
    EVENT_SERVICE = 1
    EVENT_STATE = 2
    EVENT_TIME = 3
    EVENT_DEFAULT = 4

    @staticmethod
    def from_event_type(event_type):
        """Return a priority based on event type."""
        if event_type == EVENT_TIME_CHANGED:
            return JobPriority.EVENT_TIME
        elif event_type == EVENT_STATE_CHANGED:
            return JobPriority.EVENT_STATE
        elif event_type == EVENT_CALL_SERVICE:
            return JobPriority.EVENT_SERVICE
        elif event_type == EVENT_SERVICE_EXECUTED:
            return JobPriority.EVENT_CALLBACK
        else:
            return JobPriority.EVENT_DEFAULT

class ThreadPool(object):
    """A priority queue-based thread pool."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, job_handler, worker_count=0, busy_callback=None):
        """
        job_handler: method to be called from worker thread to handle job
        worker_count: number of threads to run that handle jobs
        busy_callback: method to be called when queue gets too big.
                       Parameters: worker_count, list of current_jobs,
                                   pending_jobs_count
        """
        self._job_handler = job_handler
        self._busy_callback = busy_callback

        self.worker_count = 0
        self.busy_warning_limit = 0
        self._work_queue = queue.PriorityQueue()
        self.current_jobs = []
        self._lock = threading.RLock()
        self._quit_task = object()

        self.running = True

        for _ in range(worker_count):
            self.add_worker()

    def add_worker(self):
        """Add worker to the thread pool and reset warning limit."""
        with self._lock:
            if not self.running:
                raise RuntimeError("ThreadPool not running")

            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()

            self.worker_count += 1
            self.busy_warning_limit = self.worker_count * 3

    def remove_worker(self):
        """Remove worker from the thread pool and reset warning limit."""
        with self._lock:
            if not self.running:
                raise RuntimeError("ThreadPool not running")

            self._work_queue.put(PriorityQueueItem(0, self._quit_task))

            self.worker_count -= 1
            self.busy_warning_limit = self.worker_count * 3

    def add_job(self, priority, job):
        """ Add a job to the queue. """
        with self._lock:
            if not self.running:
                raise RuntimeError("ThreadPool not running")

            self._work_queue.put(PriorityQueueItem(priority, job))

            # check if our queue is getting too big
            if self._work_queue.qsize() > self.busy_warning_limit \
               and self._busy_callback is not None:

                # Increase limit we will issue next warning
                self.busy_warning_limit *= 2

                self._busy_callback(
                    self.worker_count, self.current_jobs,
                    self._work_queue.qsize())

    def block_till_done(self):
        """Block till current work is done."""
        self._work_queue.join()
        # import traceback
        # traceback.print_stack()

    def stop(self):
        """Finish all the jobs and stops all the threads."""
        self.block_till_done()

        with self._lock:
            if not self.running:
                return

            # Tell the workers to quit
            for _ in range(self.worker_count):
                self.remove_worker()

            self.running = False

            # Wait till all workers have quit
            self.block_till_done()

    def _worker(self):
        """Handle jobs for the thread pool."""
        while True:
            # Get new item from work_queue
            job = self._work_queue.get().item

            if job == self._quit_task:
                self._work_queue.task_done()
                return

            # Add to current running jobs
            job_log = (utcnow(), job)
            self.current_jobs.append(job_log)

            # Do the job
            self._job_handler(job)

            # Remove from current running job
            self.current_jobs.remove(job_log)

            # Tell work_queue the task is done
            self._work_queue.task_done()


class PriorityQueueItem(object):
    """ Holds a priority and a value. Used within PriorityQueue. """

    # pylint: disable=too-few-public-methods
    def __init__(self, priority, item):
        self.priority = priority
        self.item = item

    def __lt__(self, other):
        return self.priority < other.priority

    