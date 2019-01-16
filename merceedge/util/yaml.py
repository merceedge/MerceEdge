import yaml
import logging

from merceedge.exceptions import MerceEdgeError

_LOGGER = logging.getLogger(__name__)

def load_yaml(fname):
    """Load a YAML file."""
    try:
        with open(fname, encoding='utf-8') as conf_file:
            # If configuration file is empty YAML returns None
            # We convert that to an empty dict
            return yaml.safe_load(conf_file) or {}
    except yaml.YAMLError:
        error = 'Error reading YAML configuration file {}'.format(fname)
        _LOGGER.exception(error)
        raise MerceEdgeError(error)
