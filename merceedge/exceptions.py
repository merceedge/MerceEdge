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


class ComponentTemplateNotFound(MerceEdgeError):
    """Raised when a component template is not found."""

    def __init__(self, component_template: str) -> None:
        """Initialize error."""
        super().__init__(
            self, "Component template {} not found".format(component_template))
        self.component_template = component_template


class ComponentNeedInitParamsError(MerceEdgeError):
    """ Raised when a component needed parameter not found in formula file.
    """
    def __init__(self, cls_name, param_key: str) -> None:
        """Initialize error."""
        super().__init__(
            self, "Component  {} need init parameter {}".format(cls_name, param_key))
        self.cls_name = cls_name
        self.param_key = param_key