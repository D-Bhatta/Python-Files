"""Check that logging config in config.py works.

This will log to STDOUT and a file.
"""
import logging
from pathlib import Path

from config import create_handlers


def raise_error():
    """Raise ValueError."""
    raise ValueError("This is an example")


logger = logging.getLogger(__name__)
# logger is set to WARNING by default. Setting log level to DEBUG ensures that
# the handlers can filter from this.
logger.setLevel(logging.DEBUG)

file_path = Path("app.log")

handlers = create_handlers(file_path=file_path, log_level=logging.DEBUG)

for handler in handlers:
    logger.addHandler(handler)

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error message")
logger.critical("This is critical")
try:
    raise_error()
except ValueError:
    logger.exception(msg="ValueError raised")
