"""Config module.

Drop this module somewhere and import from it.

1. create_handlers(): Return handlers that can be added to a logger.
"""
from __future__ import annotations  # Remove if using python3.10 or greater

import asyncio
import collections
import json
import logging
import queue
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


class LogTransmissionStatus(Enum):
    """Enumerate categories of log transmission status that can exist.

    The transmission process has various phases. They can occur non-linearly,
    at times concurrent with each other. Errors arise during transmission as well.
    This enum can be used to articulate the status of the transmission process
    during each phase.

    Examples:
    This enum can be used anywhere there is a need to save the current state of the
    transmission process.

        >>> import functools
        >>> import threading
        >>> from time import sleep
        >>> from app.config import LogTransmissionStatus
        >>> import queue
        >>> def do_something():
        ...    return LogTransmissionStatus.InTransmit
        >>> do_something()
        <LogTransmissionStatus.InTransmit: 'The log record is in process of transmission.'>
        >>> def result_in_queue(q: queue.Queue):
        ...     sleep(3)
        ...     q.put(LogTransmissionStatus.Success)
        ...     q.task_done()
        >>> q = queue.Queue()
        >>> t = threading.Thread(target=functools.partial(result_in_queue, q))
        >>> t.start()
        >>> result = q.get()
        >>> print(result)
        LogTransmissionStatus.Success
    """

    InTransmit = "The log record is in process of transmission."
    Success = "The log record has been successfully transmitted to the server."
    Failed = "The log record failed to transmit successfully."
    ResultSaved = "The result of the log record transmission has been saved to queue."
    ResultNotSaved = "The result of the log record transmission could not be saved."
    CleanupSuccessful = "The transmission task has been cleaned up successfully."
    TransmissionResolved = "The transmission has been resolved successfully."
    TransmissionResolutionFailed = (
        "The transmission could not be resolved successfully."
    )


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


async def transmission_loop(
    q: queue.Queue,
    log_url: HttpUrl,
    qsize: int = None,
) -> LogTransmissionStatus:
    """Continuously blocks until a record is available in the ``q`` queue, and transmits it.

    Saves response from transmission in the ``result_queue``. If ``qsize`` is not
    passed to the function, then the loop runs continuously. Else, it exits when logs
    equal in number to ``qsize`` have been transmitted.

    Args:
        q: A queue.Queue that contains log records to be transmitted.
        log_url: Validated ``HttpUrl`` of the log server.
        qsize (optional): Size of the queue ``q``.

    Returns:
        LogTransmissionStatus: An ``enum.Enum`` subclass that represents various states
        of the status of the log transmission.

        Will return ``LogTransmissionStatus.Success`` in case of success.
        TODO: Add other return values.

    Examples:
        If ``qsize`` param is more than the actual number of queue items, the thread
        will block entirely. If ``qsize`` param is not specified, the thread will
        block until an item arrives in the queue.

        >>> from app.config import transmission_loop
        >>> from app.models import HttpUrl
        >>> import asyncio
        >>> import queue
        >>> log_data = {
        ...     "time": "2022-06-06 09:39:40,304",
        ...     "log_level": "ERROR",
        ...     "line": "38",
        ...     "name": "__main__",
        ...     "processID": "3856",
        ...     "message": "This is an error message",
        ...     "index": 21,
        ... }
        >>> log_url = HttpUrl(
        ...     url="http://localhost:3000/log/namespaces/0004a334-ef94-4570-9107-8f0016bd6b59/"
        ... )
        >>> queue_with_items: queue.Queue = queue.Queue()
        >>> for item in log_data:
        ...     queue_with_items.put(item)
        ...
        >>> asyncio.run(transmission_loop(q=queue_with_items, log_url=log_url, qsize=1))
        <LogTransmissionStatus.Success: 'The log record has been successfully transmitted to the server.'>
    """
    loop = asyncio.get_running_loop()

    tasks: set[asyncio.Task] = set()

    headers: dict[str, str] = {"Content-Type": "application/json"}

    transmissions = qsize

    def done_callback(task: asyncio.Task):
        resolve_transmission(tasks=tasks, task=task)

    async with ClientSession(headers=headers) as session:
        while True:
            if transmissions:
                transmissions = transmissions - 1
            else:
                break
            log_data = await loop.run_in_executor(executor=None, func=q.get)

            task = asyncio.create_task(
                async_transmit_log(log_data=log_data, session=session, url=log_url)
            )
            tasks.add(task)
            task.add_done_callback(done_callback)

        await asyncio.sleep(3)

        return LogTransmissionStatus.Success


def start_transmission_loop(
    q: queue.Queue, log_url: HttpUrl, qsize: int = None
) -> LogTransmissionStatus:
    """Start the asynchronous ``transmission_loop`` function and block until it returns.

    This function acts as the core entry point for the asynchronous transmission loop.
    It will block any thread that runs it, and since it is meant to run for the lifetime
    of the application, this can cause the entire process to block execution. It is
    recommended that this function be run in an entirely separate thread.

    Args:
        q: A queue.Queue that contains log records to be transmitted.
        log_url: Validated ``HttpUrl`` of the log server.
        qsize (optional): Size of the queue ``q``.

    Returns:
        LogTransmissionStatus: An ``enum.Enum`` subclass that represents various states
        of the status of the log transmission.

    Examples:
        This function will block the thread until the loop ends. If ``qsize`` param is
        more than the actual number of queue items, the thread will block entirely. If
        ``qsize`` param is not specified, the thread will block until an item arrives in
        the queue.

        >>> from app.config import start_transmission_loop
        >>> from app.models import HttpUrl
        >>> import queue
        >>> log_data = {
        ...     "time": "2022-06-06 09:39:40,304",
        ...     "log_level": "ERROR",
        ...     "line": "38",
        ...     "name": "__main__",
        ...     "processID": "3856",
        ...     "message": "This is an error message",
        ...     "index": 21,
        ... }
        >>> log_url = HttpUrl(
        ...     url="http://localhost:3000/log/namespaces/0004a334-ef94-4570-9107-8f0016bd6b59/"
        ... )
        >>> queue_with_items: queue.Queue = queue.Queue()
        >>> for item in log_data:
        ...     queue_with_items.put(item)
        ...
        >>> start_transmission_loop(q=queue_with_items, log_url=log_url, qsize=1)
        <LogTransmissionStatus.Success: 'The log record has been successfully transmitted to the server.'>
    """
    result = asyncio.run(transmission_loop(q=q, log_url=log_url, qsize=qsize))
    return result


def transmission_cleanup(
    tasks: set[asyncio.Task], task: asyncio.Task
) -> LogTransmissionStatus:
    """Cleanup after task completion.

    Tasks need to be discarded from the ``tasks`` set, so that they do not keep
    consuming memory. This function discards them, and assumes that the tasks have been
    completed.

    Args:
        tasks: ``set`` of ``asyncio.Task`` objects.
        task: A task that has been completed.

    Returns:
        LogTransmissionStatus: Returns ``LogTransmissionStatus.CleanupSuccessful`` if
        the task cleanup is successful.

    Examples:
        This function is constrained to the usage of sets only. ``list`` do not have
        ``discard`` methods.

        >>> import asyncio
        >>> import functools
        >>> from app.config import transmission_cleanup
        >>> async def do_async_work(num) -> str:
        ...     result = f"task_completed{num}"
        ...     return result
        >>> async def async_tasks() -> set[asyncio.Task]:
        ...     tasks = set()
        ...     for i in range(3):
        ...         task = asyncio.create_task(do_async_work(num=i))
        ...         tasks.add(task)
        ...     return tasks
        >>> async def cleanup_tasks():
        ...     tasks = await async_tasks()
        ...     loop = asyncio.get_running_loop()
        ...     async_task_list = list(tasks)
        ...     results = []
        ...     for i, task in enumerate(async_task_list):
        ...         task_result = await loop.run_in_executor(
        ...             executor=None,
        ...             func=functools.partial(transmission_cleanup, tasks, task),
        ...         )
        ...         results.append(task_result)
        ...     return results
        >>> asyncio.run(cleanup_tasks())
        [<LogTransmissionStatus.CleanupSuccessful: 'The transmission task has been cleaned up successfully.'>, <LogTransmissionStatus.CleanupSuccessful: 'The transmission task has been cleaned up successfully.'>, <LogTransmissionStatus.CleanupSuccessful: 'The transmission task has
        been cleaned up successfully.'>]
    """
    tasks.discard(task)

    return LogTransmissionStatus.CleanupSuccessful


def save_transmission_result(
    result_queue: collections.deque, task: asyncio.Task
) -> LogTransmissionStatus:
    """Save the transmission result in ``result_queue``.

    When a transmission task is completed, the result should be saved in a queue object
    that is threadsafe. Append to the queue, and pop from the queue, should both be fast
    to prevent negative effects on performance. The queue should also automatically
    remove entries over a threshold, to prevent the queue from growing too large.

    Args:
        result_queue: A queue holds the transmission results.
        task: A task that has finished execution.

    Returns:
        LogTransmissionStatus: ``LogTransmissionStatus.ResultNotSaved`` in case of failure
        and ``LogTransmissionStatus.ResultSaved`` in case of success.

    Examples:
        This function expects a completed coroutine. In case of running coroutine, or a
        cancelled coroutine, it will not save the result.

        >>>
        >>> import collections
        >>> import asyncio
        >>> from app.config import save_transmission_result
        >>>
        >>> result_queue:collections.deque = collections.deque()
        >>>
        >>> async def do_async_work(num) -> str:
        ...     result = f"task_completed{num}"
        ...     return result
        ...
        >>>
        >>> async def async_tasks() -> set[asyncio.Task]:
        ...     tasks = set()
        ...     for i in range(3):
        ...         task = asyncio.create_task(do_async_work(num=i))
        ...         tasks.add(task)
        ...     return tasks
        ...
        >>>
        >>> def save_result(result_q: collections.deque):
        ...     tasks = asyncio.run(async_tasks())
        ...     for task in tasks:
        ...         save_transmission_result(result_queue=result_q, task=task)
        ...
        >>> save_result(result_q=result_queue)
        >>>
        >>> for _ in range(len(result_queue)):
        ...     print(result_queue.pop())
        ...
        task_completed1
        task_completed2
        task_completed0
        >>>
    """
    try:
        result = task.result()
        result_queue.append(result)
        return LogTransmissionStatus.ResultSaved
    except asyncio.CancelledError:
        return LogTransmissionStatus.ResultNotSaved
    except asyncio.InvalidStateError:
        return LogTransmissionStatus.ResultNotSaved

    return LogTransmissionStatus.ResultNotSaved


def resolve_transmission(
    tasks: set[asyncio.Task],
    task: asyncio.Task,
    result_queue: collections.deque | None = None,
) -> LogTransmissionStatus:
    """Resolve the aftermath of a transmission.

    After a transmission has completed it's execution, the ``asyncio.Task`` object
    should be discarded to prevent excess memory usage. If needed, the result should be
    saved.

    Args:
        tasks: ``set`` of ``asyncio.Task`` objects.
        task: A task that has finished execution.
        result_queue (optional): A queue holds the transmission results.

    Returns:
        LogTransmissionStatus: ``LogTransmissionStatus.TransmissionResolutionFailed`` in
        case of failure and ``LogTransmissionStatus.TransmissionResolved`` in case of
        success.

    Examples:
        This function expects a completed coroutine. In case of a running coroutine or a
        cancelled coroutine, the transmission will not be resolved successfully.

        >>> import collections
        >>> import asyncio
        >>> from app.config import resolve_transmission
        >>>
        >>> result_queue: collections.deque = collections.deque()
        >>>
        >>> async def do_async_work(num) -> str:
        ...     result = f"task_completed{num}"
        ...     return result
        ...
        >>>
        >>> async def async_tasks() -> set[asyncio.Task]:
        ...     tasks = set()
        ...     for i in range(3):
        ...         task = asyncio.create_task(do_async_work(num=i))
        ...         tasks.add(task)
        ...     return tasks
        ...
        >>>
        >>> async_tasks_set = asyncio.run(async_tasks())
        >>> tasks = list(async_tasks_set)
        >>> for task in tasks:
        ...     resolve_transmission(result_queue=result_queue, task=task, tasks=async_tasks_set)
        ...
        <LogTransmissionStatus.TransmissionResolved: 'The transmission has been resolved successfully.'>
        <LogTransmissionStatus.TransmissionResolved: 'The transmission has been resolved successfully.'>
        <LogTransmissionStatus.TransmissionResolved: 'The transmission has been resolved successfully.'>
        >>> for _ in range(len(result_queue)):
        ...     print(result_queue.pop())
        ...
        task_completed0
        task_completed1
        task_completed2
    """
    if result_queue is None:
        cleanup_result = transmission_cleanup(tasks=tasks, task=task)
        if cleanup_result == LogTransmissionStatus.CleanupSuccessful:
            return LogTransmissionStatus.TransmissionResolved

    saving_result = save_transmission_result(result_queue=result_queue, task=task)  # type: ignore[arg-type]  # Ignore incompatible type Optional[deque[Any]]
    cleanup_result = transmission_cleanup(tasks=tasks, task=task)

    if (
        saving_result == LogTransmissionStatus.ResultSaved
        and cleanup_result == LogTransmissionStatus.CleanupSuccessful
    ):
        return LogTransmissionStatus.TransmissionResolved

    return LogTransmissionStatus.TransmissionResolutionFailed
