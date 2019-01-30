""" Exceptions used by Merce Edge """
from typing import Optional, Tuple, TYPE_CHECKING


class MerceEdgeError(Exception):
    """ General Merce Edge exception occured. """
    pass


class Unauthorized(MerceEdgeError):
    """When an action is unauthorized."""

    def __init__(self, context: Optional['Context'] = None,
                 user_id: Optional[str] = None,
                 entity_id: Optional[str] = None,
                 config_entry_id: Optional[str] = None,
                 perm_category: Optional[str] = None,
                 permission: Optional[Tuple[str]] = None) -> None:
        """Unauthorized error."""
        super().__init__(self.__class__.__name__)
        self.context = context
        self.user_id = user_id
        self.entity_id = entity_id
        self.config_entry_id = config_entry_id
        # Not all actions have an ID (like adding config entry)
        # We then use this fallback to know what category was unauth
        self.perm_category = perm_category
        self.permission = permission


class ServiceNotFound(MerceEdgeError):
    """Raised when a service is not found."""

    def __init__(self, domain: str, service: str) -> None:
        """Initialize error."""
        super().__init__(
            self, "Service {}.{} not found".format(domain, service))
        self.domain = domain
        self.service = service