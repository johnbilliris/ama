import logging
import sys

import pytest

from apps.console_logging import SingleLineFormatter, configure_console_logging


def test_formatter_escapes_newlines_in_message_and_exception() -> None:
    try:
        raise RuntimeError("first\r\nsecond")
    except RuntimeError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="message\ncontinued",
            args=(),
            exc_info=sys.exc_info(),
        )

    formatted = SingleLineFormatter("%(message)s").format(record)

    assert "\n" not in formatted
    assert "\r" not in formatted
    assert "\\n" in formatted
    assert "\\r" in formatted
    assert "RuntimeError: first\\r\\nsecond" in formatted


def test_configure_console_logging_installs_single_line_root_handler() -> None:
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    try:
        root_logger.handlers.clear()
        configure_console_logging()

        console_handlers = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, logging.StreamHandler)
            and (handler.stream is sys.stdout or handler.stream is sys.stderr)
        ]
        assert console_handlers
        assert all(isinstance(handler.formatter, SingleLineFormatter) for handler in console_handlers)
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
        root_logger.setLevel(original_level)


def test_configure_console_logging_rejects_invalid_level() -> None:
    with pytest.raises(ValueError, match="Invalid logging level"):
        configure_console_logging(level="NOT_A_LEVEL")
