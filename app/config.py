"""Config module.

Drop this module somewhere and import from it.

1. create_handlers(): Return handlers that can be added to a logger.
"""
from __future__ import annotations  # Remove if using python3.10 or greater

import json
import logging
from pathlib import Path
from typing import Any

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


class StructuredMessage:
    """JSON structured log message.

    Create a structured log message that will be encoded to JSON.

    Structured logging provides context to log messages, so that
    a clear and comprehensive picture of the state of the application
    can be observed when looking at the logs. This class helps easily
    capture log messages, as well as any other associated context, as
    a JSON string.

    After passing the log message as the first argument, other values
    can be logged by passing them as keyword arguments.

    The message and keyword arguments will be encoded into a JSON
    string. The message will be encoded with the key ``message`` as
    part of the JSON string. All keys in the JSON string will be sorted.

    Args:
        message: The log message.

    Examples:
        Calling ``str`` on this class will return ``JSON::`` followed by a
        JSON encoded string.

        >>> from app.config import StructuredMessage
        >>> str(StructuredMessage(message="message one", name="computer", address="Gaia", phone=1234567890))
        'JSON::{"address":"Gaia","message":"message one","name":"computer","phone":1234567890}'
    """

    def __init__(self, message: str, **kwargs) -> None:
        self.kwargs = kwargs
        self.kwargs["message"] = message

    def __str__(self) -> str:
        """Encode the message and keyword arguments as JSON string."""
        json_encoded_message = "JSON::%s" % json.dumps(
            self.kwargs, indent=None, separators=(",", ":"), sort_keys=True
        )
        return json_encoded_message


class LogJSONFormatter(logging.Formatter):
    """Formats log records as JSON strings.

    Log records contain message strings, as well as other data about the log. They may
    also contain stack traces from exceptions. All of these need to be formatted
    by the logger as JSON before being logged for easier and structured parsing.

    Attributes:
        fmt (str): Format strings.

    Args:
        fmt (str, optional): Format strings.

    Examples:
        This formatter can be used without the ``fmt`` argument.

        >>> import logging
        >>> from app.config import LogJSONFormatter
        >>> logger = logging.getLogger("logger-new")
        >>> stream_handler = logging.StreamHandler()
        >>> formatter = LogJSONFormatter()
        >>> stream_handler.setFormatter(formatter)
        >>> stream_handler.setLevel(logging.DEBUG)
        >>> logger.addHandler(stream_handler)
        >>> logger.setLevel(logging.DEBUG)
        >>>
        >>> logger.debug("Hello")
        {"asctime":"2022-08-17 10:43:44.888","filename":"<stdin>","full_file_path":"<stdin>","function_name":"<module>","level":"DEBUG","line_number":1,"message":"Hello","module_name":"<stdin>","name":"logger-new","process_id":13904,"process_name":"MainProcess","thread_id":10664,"thread_name":"MainThread"}
        >>>
    """

    default_msec_format = "%s.%03d"

    def json_format(
        self,
        record: logging.LogRecord,
        asctime: str,
        msg: str | dict[str, Any],
        exception_msg: str | None = None,
    ) -> str:
        """Return a JSON string from arguments.

        Args:
            record: ``LogRecord`` instance from which
                attributes will be extracted.
            asctime: RFC 3339 formatted time string.
            msg: The log message.
            exception_msg (optional): Execution information, i.e. traceback.

        Returns:
            A JSON encoded string mapping record attributes to
            corresponding keys and values. For example:

            {
                "asctime": "Formatted time when log originated",
                "exec_info": "Execution information, i.e. traceback(optional)"
                "filename": "Name of the file",
                "full_file_path": "Full path to file(optional)",
                "function_name": "Name of the function",
                "level": "DEBUG/INFO/WARNING/ERROR/CRITICA/EXCEPTION",
                "line_number": "Line number of the log(optional)",
                "message": "Message string",
                "module_name": "Name of the module",
                "name": "Name of the logger",
                "process_id": "Id of the process(optional)",
                "process_name": "Name of the process(optional)",
                "thread_id": "Id of the thread(optional)",
                "thread_name": "Name of the thread(optional)"
            }
        """
        return json.dumps(
            {
                "asctime": asctime,
                "exec_info": exception_msg,
                "filename": record.filename,
                "full_file_path": record.pathname,
                "function_name": record.funcName,
                "level": record.levelname,
                "line_number": record.lineno,
                "message": msg,
                "module_name": record.module,
                "name": record.name,
                "process_id": record.process,
                "process_name": record.processName,
                "thread_id": record.thread,
                "thread_name": record.threadName,
            },
            separators=(",", ":"),
            sort_keys=True,
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format the log as JSON.

        Formats the exception message and traceback into a single line.

        Args:
            record: The log record.

        Returns:
            A JSON encoded string mapping record attributes to
            corresponding keys and values. For example:

            {
                "asctime": "Formatted time when log originated",
                "exec_info": "Execution information, i.e. traceback(optional)"
                "filename": "Name of the file",
                "full_file_path": "Full path to file(optional)",
                "function_name": "Name of the function",
                "level": "DEBUG/INFO/WARNING/ERROR/CRITICA/EXCEPTION",
                "line_number": "Line number of the log(optional)",
                "message": "Message string",
                "module_name": "Name of the module",
                "name": "Name of the logger",
                "process_id": "Id of the process(optional)",
                "process_name": "Name of the process(optional)",
                "thread_id": "Id of the thread(optional)",
                "thread_name": "Name of the thread(optional)"
            }
        """
        asctime = self.formatTime(record, self.datefmt)
        msg = record.getMessage()

        exception_msg: str | None = None

        if msg[:6] == "JSON::":
            msg = json.loads(msg[6:])

        if record.exc_info:
            exception_msg = repr(self.formatException(record.exc_info))
            exception_msg = exception_msg.replace("\n", " | ")

        return self.json_format(
            record=record, asctime=asctime, msg=msg, exception_msg=exception_msg
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
