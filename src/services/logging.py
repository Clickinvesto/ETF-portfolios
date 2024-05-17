import pathlib
import logging
import logging.config


class ChattyFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage().startswith("Chatbot:")


class NonChattyFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().startswith("Chatbot:")


def get_logger(env):
    if env in ["local", "dev"]:
        return ["console", "chatbot_file", "file"]
    else:
        return ["chatbot_file", "file"]


def get_handlers(env, log_path):
    general_log_path = log_path / "general.log"
    chatbot_log_path = log_path / "chatbot.log"

    if env in ["local", "dev"]:
        return {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "chatbot_file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": chatbot_log_path,
                "maxBytes": 1000000,
                "backupCount": 40,
                "filters": ["chatty_filter"],
            },
            "file": {
                "level": "WARNING",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": general_log_path,
                "maxBytes": 10000,
                "backupCount": 10,
                "filters": ["non_chatty_filter"],
            },
        }

    else:
        return {
            "chatbot_file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": f"{chatbot_log_path}",
                "maxBytes": 10000,
                "backupCount": 20,
                "filters": ["chatty_filter"],
            },
            "file": {
                "level": "WARNING",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": f"{general_log_path}",
                "maxBytes": 10000,
                "backupCount": 10,
                "filters": ["non_chatty_filter"],
            },
        }


def configure_logger(env, log_path, name="default"):
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "filters": {
                "chatty_filter": {
                    "()": ChattyFilter,
                },
                "non_chatty_filter": {
                    "()": NonChattyFilter,
                },
            },
            "formatters": {
                "error_form": {
                    "format": "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]",
                },
                "default": {
                    "format": "%(asctime)s %(levelname)s: %(message)s",
                },
            },
            "handlers": get_handlers(env, log_path),
            "loggers": {
                "default": {
                    "level": "INFO",
                    "handlers": get_logger(env),
                }
            },
            "root": {
                "level": "INFO",
                "handlers": get_logger(env),
            },
        }
    )
    return logging.getLogger(name)
