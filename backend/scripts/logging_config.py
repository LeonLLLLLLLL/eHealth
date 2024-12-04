import logging
from logging.config import dictConfig

# Logging configuration
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "app.log",  # Logs will be saved in this file
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "watchfiles.main": {  # Suppress watchfiles logs
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

dictConfig(logging_config)
logger = logging.getLogger()
