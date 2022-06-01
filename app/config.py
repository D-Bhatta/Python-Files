"""Config module.

Drop this module somewhere and import from it.

1. create_handlers(): Return handlers that can be added to a logger.
"""

import json
import logging
from pathlib import Path

log_formatter = logging.Formatter(
    json.dumps(
        {
            "time": "%(asctime)s",
            "log_level": "%(levelname)s",
            "line": "%(lineno)d",
            "name": "%(name)s",
            "processID": "%(process)d",
            "message": "%(message)s",
        }
    )
)


def create_handlers(
    file_path: Path | str = "server.log",
    log_level: int = logging.DEBUG,
    formatter: logging.Formatter = log_formatter,
) -> tuple[logging.StreamHandler, logging.FileHandler]:
    """Return handlers that can be added to a logger.

    Returns a tuple of handlers like StreamHandler, FileHandler that can be
    used with a logger's `addHandler` method.

    Args:
        file_path: Path like object or string object. Points to where the
            FileHandler will write the log messages to file.

        log_level: The log level that should be set. Defaults to DEBUG. The
            handlers will filter incoming messages from the logger using this
            level.

            Can be any of the following from the logging module:

            CRITICAL
            ERROR
            WARNING
            INFO
            DEBUG

            The logger these handlers are attached to should have a log level
            that is lower or equal to what is passed to the `log_level`
            variable. Otherwise the log messages with a level lower than the
            logger's set level will simply be filtered out by the logger and
            will never reach the handlers.

            If the logger has a log level lower than what is passed to this
            function as `log_level` then the handlers will simply filter out
            the messages that are lower than their level.

        formatter: A `logging.Formatter` object. Defaults to `log_formatter`
            defined in this module.

            Formats the log messages accordingly.

    Returns:
        tuple: A tuple of `logging.Handler` objects. Each handler has a
        formatter, and log_level attached to it.

        Returns the following handlers:
        - StreamHandler that logs to console.
        - FileHandler that logs to file.

    Examples:
        Add the handlers to a logger object with a lower log level than the
        handlers, and then log as needed.

        >>> import logging
        >>> from pathlib import Path
        >>> from config import create_handlers
        >>> logger = logging.getLogger(__name__)
        >>> logger.setLevel(logging.DEBUG)
        >>> file_path = Path("app.log")
        >>> handlers = create_handlers(file_path=file_path, log_level=logging.DEBUG)
        >>> for handler in handlers:
        ...     logger.addHandler(handler)
        ...
        >>> logger.debug("This is a debug message")
        {
            "time": "2022-05-31 09:20:16,416",
            "log_level": "DEBUG",
            "line": "1",
            "message": "This is a debug message",
        }
        >>> logger.info("This is an info message")
        {
            "time": "2022-05-31 09:20:16,440",
            "log_level": "INFO",
            "line": "1",
            "message": "This is an info message",
        }
        >>> logger.warning("This is a warning")
        {
            "time": "2022-05-31 09:20:16,445",
            "log_level": "WARNING",
            "line": "1",
            "message": "This is a warning",
        }
        >>> logger.error("This is an error message")
        {
            "time": "2022-05-31 09:20:16,499",
            "log_level": "ERROR",
            "line": "1",
            "message": "This is an error message",
        }
        >>> logger.critical("This is critical")
        {
            "time": "2022-05-31 09:20:18,409",
            "log_level": "CRITICAL",
            "line": "1",
            "message": "This is critical",
        }
    """
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    file_handler = logging.FileHandler(
        filename=file_path, mode="a", encoding="utf-8", errors="strict"
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    return stream_handler, file_handler
