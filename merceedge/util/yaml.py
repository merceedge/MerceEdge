import yaml

from merceedge.exceptions import MerceEdgeError
from merceedge.settings import (
    logger_access,
    logger_code,
    logger_console
)

_LOGGER = logger_code

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


def write_yaml(fname, yaml_dict):
    """Write a yaml file from dict"""
    try:
        with open(fname, 'w', encoding='utf-8') as outfile:
            yaml.dump(yaml_dict, outfile, default_flow_style=False)
    except yaml.YAMLError:
        error = 'Error write YAML configuration file {}'.format(fname)
        _LOGGER.exception(error)
        raise MerceEdgeError(error)
