DEBUG = True

if DEBUG:
    from .development import *
elif not DEBUG:
    from .production import *

import logging
import logging.config
import colorlog

logging.config.dictConfig(LOG_CONFIG)
logger_code = logging.getLogger("code")
logger_console = logging.getLogger("console")
logger_access = logging.getLogger("access")
