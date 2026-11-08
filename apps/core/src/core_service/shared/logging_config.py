import logging
import logging.config

from core_service.shared.settings.application import app_settings

global_logging_level = app_settings.LOGGING_LEVEL


def setup_logging():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {"core_service": {"handlers": ["console"], "level": global_logging_level, "propagate": False}},
        "root": {"handlers": ["console"], "level": "WARNING"},
    }

    logging.config.dictConfig(logging_config)
