import enum
import queue
import threading
from datetime import datetime
from types import MappingProxyType
from .dt import datetime_to_local_str, utcnow

from merceedge.util.dt import utcnow
from merceedge.const import (
    EVENT_CALL_SERVICE,
    EVENT_SERVICE_REGISTERED,
    EVENT_SERVICE_EXECUTED,
    EVENT_STATE_CHANGED,
    EVENT_TIME_CHANGED,
)

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

    