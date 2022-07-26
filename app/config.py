"""Config module.

Drop this module somewhere and import from it.

1. create_handlers(): Return handlers that can be added to a logger.
"""
from __future__ import annotations  # Remove if using python3.10 or greater

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any

from aiohttp import (
    ClientConnectionError,
    ClientOSError,
    ClientSession,
    ContentTypeError,
)

from app.models import HttpUrl  # type: ignore[import]  # Ignore missing imports


class ErrorType(Enum):
    """Enumerate categories of transmission errors than can be encountered.

    Errors during transmission can occur due to a variety of factors. This enum can be
    used to classify errors based on the set of factors that cause them. This will be
    helpful in adding structure to how errors are addressed.

    Examples:
        >>> from app.config import ErrorType
        >>> try:
        ...     raise ValueError("Some content error happens.")
        ... except ValueError:
        ...     raise ValueError(f"type:{ErrorType.ContentType}")
        Traceback (most recent call last):
            File "<stdin>", line 2, in <module>
        ValueError: Some content error happens.

        During handling of the above exception, another exception occurred:

        Traceback (most recent call last):
            File "<stdin>", line 4, in <module>
        ValueError: type:ErrorType.ContentType
    """

    ContentType = "ContentType"
    Header = "Header"
    System = "System"
    Connection = "Connection"


class ResponseError(Exception):
    """Error in the response.

    A request can successfully return a response, but the response itself might contain
    errors that should be raised as exception.

    Args:
        types: Types of error information.
        message: Description of the error.
        partial_message: Data returned in the response, formatted as string.
        status_code: Status code returned by the response.
        headers: Headers returned by the response.
        request_info (optional): Information about the request preceding the response.

    Examples:
        >>> from app.config import ResponseError, ErrorType
        >>> import requests
        >>> with requests.get(url="http://httpbin.org/get") as response:
        ...     response_text = response.text
        ...     response_status_code = response.status_code
        ...     if response_status_code == 200:
        ...         raise ResponseError(
        ...             types=(ErrorType.ContentType,),
        ...             message="There is an error in the content type header. Should be a form of text.",
        ...             partial_message=response_text,
        ...             status_code=response.status_code,
        ...             headers=response.headers,
        ...             request_info=response.request,
        ...         )
        Traceback (most recent call last):
          File "<stdin>", line 5, in <module>
        app.config.ResponseError: There is an error in the content type header. Should be a form of text.
    """

    def __init__(
        self,
        types: tuple[ErrorType, ...],
        message: str,
        partial_message: str,
        status_code: int,
        headers: Any,
        request_info: Any | None,
    ):
        self.types = types
        self.message = message
        self.partial_message = partial_message
        self.status_code = status_code
        self.headers = headers
        self.request_info = request_info

        super().__init__(self.message)


class TransmissionError(Exception):
    """Error in any stage of the transmission.

    Args:
        types: Types of error information.
        message: Description of the error.

    Examples:
        >>> from app.config import TransmissionError, ErrorType
        >>> import requests
        >>> try:
        ...     requests.get("http://httpbiin.org/ge")
        ... except:
        ...     raise TransmissionError(
        ...         types=(ErrorType.Connection, ErrorType.System),
        ...         message="There was an error during transmission.",
        ...     )
        Traceback (most recent call last):...
        socket.gaierror: [Errno 11001] getaddrinfo failed

        During handling of the above exception, another exception occurred:

        Traceback (most recent call last):
        File "<stdin>", line 4, in <module>
        app.config.TransmissionError: There was an error during transmission.
    """

    def __init__(self, types: tuple[ErrorType, ...], message: str):
        self.types = types
        self.message = message

        super().__init__(self.message)


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


async def async_transmit_log(
    log_data: str,
    session: ClientSession,
    url: HttpUrl,
) -> tuple[str, int]:
    """Asynchronously POST log data to given url using session.

    This function uses the ClientSession object to POST logs to the server URL. It
    assumes that the ClientSession will not close during transmission, that the URL is
    valid and working, and that the log data is a valid payload.

    Args:
        log_data: The log data to be transmitted.
        session: The ClientSession object to be used to POST data. Assumes all
        correct headers are already assigned.
        url: Validated ``HttpUrl`` of the log server. The ``str`` of this url will be
        used.

    Returns:
        tuple[str, int]: A tuple comprised of the response text and the status code.

    Raises:
        ResponseError: If there is an error in the response.
        TransmissionError: If there is an error during any part of the transmission.

    Examples:
        The ``session`` param should be created within a context manager.

        >>> import asyncio, aiohttp
        >>> from app.models import HttpUrl
        >>> asyncio.run(
        ... async_transmit_log(
        ...     log_data="This is a log",
        ...     session=aiohttp.ClientSession(
        ...         headers={"Content-Type": "application/json"}
        ...         ),
        ...     url=HttpUrl(url="localhost:3000/log/")
        ...     )
        ... )
        'Received JSON Data as POST for 4c4de413-bfbe-4024-9c5c-ae8cc7bf636a', 200

    """
    url_str = str(url.url)
    try:
        async with session.post(url_str, data=log_data) as response:
            response_text = await response.text()
            response_status_code = response.status
    except ContentTypeError as e:
        raise ResponseError(
            types=(ErrorType.ContentType,),
            message="There is an error in the content type header. Should be a form of text.",
            partial_message=e.message,
            status_code=e.status,
            headers=e.headers,
            request_info=e.request_info,
        )
    except ClientConnectionError:
        raise TransmissionError(
            types=(
                ErrorType.Connection,
                ErrorType.System,
            ),
            message="There was an error during connection to the log server.",
        )
    except ClientOSError:
        raise TransmissionError(
            types=(ErrorType.System,),
            message="There was a low level error during transmission of the log.",
        )

    return response_text, response_status_code
