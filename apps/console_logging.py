from __future__ import annotations

import logging
import sys


class SingleLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return super().format(record).replace("\r", "\\r").replace("\n", "\\n")


def configure_console_logging(level: int | str = logging.INFO) -> None:
    resolved_level = logging.getLevelName(level.upper()) if isinstance(level, str) else level
    if not isinstance(resolved_level, int):
        raise ValueError(f"Invalid logging level: {level!r}")

    formatter = SingleLineFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    root_logger = logging.getLogger()
    console_handlers = []

    loggers = [root_logger]
    loggers.extend(
        logger
        for logger in logging.root.manager.loggerDict.values()
        if isinstance(logger, logging.Logger)
    )
    for logger in loggers:
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and (
                handler.stream is sys.stdout or handler.stream is sys.stderr
            ):
                handler.setFormatter(formatter)
                console_handlers.append(handler)

    if not any(handler in root_logger.handlers for handler in console_handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    root_logger.setLevel(resolved_level)


def uvicorn_log_config() -> dict[str, object]:
    formatter = {
        "()": "apps.console_logging.SingleLineFormatter",
        "fmt": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    }
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": formatter,
            "access": formatter,
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "class": "logging.StreamHandler",
                "formatter": "access",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
