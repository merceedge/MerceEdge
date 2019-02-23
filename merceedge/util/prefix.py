import os, sys, site
from merceedge.exceptions import MerceEdgeError

def binaries_directory(is_develop_setup=False):
    """Return the installation directory, or None"""
    if is_develop_setup:
        this_file_path = os.path.dirname(os.path.realpath(__file__))
        project_dev_dir_path = os.path.abspath(os.path.join(this_file_path, os.pardir))
        paths = (project_dev_dir_path, )
    else:
        py_version = '%s.%s' % (sys.version_info[0], sys.version_info[1])
        paths = (s % (py_version) for s in (
            sys.prefix + '/lib/python%s/dist-packages/',
            sys.prefix + '/lib/python%s/site-packages/',
            sys.prefix + '/local/lib/python%s/dist-packages/',
            sys.prefix + '/local/lib/python%s/site-packages/',
            '/Library/Python/%s/site-packages/',
        ))

    for path in paths:
        if os.path.exists(path):
            return path
    raise MerceEdgeError("no installation path found")