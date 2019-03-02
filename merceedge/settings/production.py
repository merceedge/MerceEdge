
import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

if not os.path.exists(os.path.join(BASE_DIR, 'logs')):
    os.mkdir(os.path.join(BASE_DIR, 'logs'))

LOG_CONFIG = {
    "version": 1,
    "formatters": {
        "console": {
            '()': 'colorlog.ColoredFormatter',
            'format': "%(log_color)s[%(levelname)s] %(message)s",
            "datefmt": "%Y/%m/%d %H:%M:%S",
            "log_colors": {
                'DEBUG': 'white',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },

        },
        "code": {
            "format": "[%(asctime)s] %(levelname)s [%(filename)s->%(funcName)s:%(lineno)s] %(message)s",
            "datefmt": "%Y/%m/%d %H:%M:%S"
        },
        "timeRotation": {
            "format": "[%(asctime)s] %(name)-12s %(levelname)-8s %(message)s"
        },
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }      
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console"
        },
        "access": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/merceedge.access.log"),
            "when": "midnight",
            "backupCount": 90,  # 3 months
            "formatter": "timeRotation",
        },
        "code": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/merceedge.code.log"),
            "backupCount": 90,  # Store up to three files
            "formatter": "code",
        }
    },
    "loggers": {
        "merceedge.access": {
            "handlers": ["console", "access"],
            "level": "INFO",
            "color": True,
            "propagate": False
        },
        "code": {
            "handlers": ["code", 'console'],
            "level": "DEBUG",
            "color": True,
            "propagate": True
        },
        "console": {
            "handlers": ["console"],
            "level": "DEBUG",
            "color": True,
            "propagate": True
        },

    }
}