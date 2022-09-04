"""Test the code at app/config.py."""
from __future__ import annotations  # Remove if using python3.10 or greater

import asyncio
import collections
import functools
import json
import logging
import threading
from time import sleep
from typing import Any, NamedTuple

import pytest
import pytest_asyncio
import requests
from aiohttp import ClientSession
from fixtures import ServerUrls  # type: ignore[import]  # Ignore missing imports
from fixtures import server_urls  # type: ignore[import]  # Ignore missing imports
from requests import Response

from app.config import (  # type: ignore[import]  # Ignore missing imports
    LogJSONFormatter,
    LogTransmissionStatus,
    StructuredMessage,
    async_transmit_log,
    resolve_transmission,
    save_transmission_result,
    start_transmission_loop,
    transmission_cleanup,
    transmission_loop,
)
from app.models import HttpUrl  # type: ignore[import]  # Ignore missing imports

NUM_ITEMS_LARGE = 10000
NUM_ITEMS_SMALL = 100


@pytest.mark.asyncio
async def test_async_transmit_log(log_data: list[str], flask_server_port, n_space):
    """GIVEN: log data.

    WHEN: ``async_transmit_log`` is used to transmit logs.

    THEN: Response is correct confirmation message and status code.
    """
    namespace: str = n_space
    log_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/namespaces/{namespace}/"
    )
    confirm_msg = f"Received JSON Data as POST for {namespace}"
    headers: dict[str, str] = {"Content-Type": "application/json"}

    async with ClientSession(headers=headers) as session:
        tasks = []
        for log in log_data:
            tasks.append(
                asyncio.create_task(
                    async_transmit_log(log_data=log, session=session, url=log_url)
                )
            )
        responses: list[tuple[str, int]] = await asyncio.gather(*tasks)

    for response_text, response_status in responses:
        assert (response_text, response_status) == (
            confirm_msg,
            200,
        ), "Couldn't save log message."


@pytest.fixture(scope="class")
def q_transmission_log_items(log_data: list[str]) -> collections.deque:
    """Return a deque filled with `log_data` items."""
    q: collections.deque = collections.deque(maxlen=100)
    for item in log_data:
        q.append(item)
    return q


@pytest.fixture(scope="class")
def transmission_results_q() -> collections.deque:
    """Return an empty deque for storing transmission results."""
    q: collections.deque = collections.deque(maxlen=100)
    return q


@pytest.fixture(scope="class")
def transmission_stop_event() -> threading.Event:
    """Return a ``threading.Event`` instance."""
    stop_event = threading.Event()
    return stop_event


class TransmissionLoopResult(NamedTuple):
    """Represent result of calling ``transmission_loop``."""

    status: LogTransmissionStatus
    namespace: str
    result_queue: collections.deque
    log_data_response: list[dict[str, str | int]]


@pytest.fixture(scope="class")
def call_transmission_loop(
    q_transmission_log_items: collections.deque,
    server_urls: ServerUrls,
    transmission_results_q: collections.deque,
    transmission_stop_event: threading.Event,
    len_log_json_data: int,
    request_session: requests.Session,
) -> TransmissionLoopResult:
    """Call ``transmission_loop`` function and return a ``TransmissionLoopResult`` instance."""
    run_loop_result: dict[str, LogTransmissionStatus] = {
        "result": LogTransmissionStatus.InTransmit
    }

    def run_loop():
        result: LogTransmissionStatus = asyncio.run(
            transmission_loop(
                q=q_transmission_log_items,
                log_url=server_urls.log_url,
                stop_event=transmission_stop_event,
                result_queue=transmission_results_q,
            )
        )
        run_loop_result["result"] = result

    t = threading.Thread(target=run_loop, name="run_loop")
    t.start()

    count = 0

    while count < 100:
        count = count + 1
        # Using ``len`` on a ``collections.deque`` is not threadsafe.
        # However, we do not actually need thread safety here, since the loop will
        # eventually terminate independently of the following ``if`` block.
        # This does insert some uncertainty into the test, and it should be refactored
        # to a better solution if possible.
        if len(transmission_results_q) >= len_log_json_data:
            break
        else:
            sleep(0.1)

    transmission_stop_event.set()

    sleep(0.3)  # Why: Wait for the loop to stop.

    status: LogTransmissionStatus = run_loop_result["result"]

    data_url_str = str(server_urls.data_url.url)

    try:
        data_response: Response = request_session.get(data_url_str)
    except Exception as e:
        raise AssertionError("Failed to make a connection to the logging server.")

    try:
        data_dict = data_response.json()
        log_data: list[dict[str, str | int]] = data_dict[server_urls.namespace]
    except json.JSONDecodeError:
        raise AssertionError(
            f"There was a problem decoding to JSON. Response text: {data_response.text}"
        )
    except KeyError as e:
        if data_response.text == "This namespace doesn't exist.":
            raise AssertionError(
                f"The data was not saved to the namespace: {server_urls.namespace}"
            )
        raise e

    result = TransmissionLoopResult(
        status=status,
        namespace=server_urls.namespace,
        result_queue=transmission_results_q,
        log_data_response=log_data,
    )
    return result


class TestTransmissionLoop:
    """
    Unit test for ``transmission_loop`` function.

    GIVEN: A queue object that hold log data in json format.
        Validated server url where log data will be transmitted.
        ``threading.Event`` that is used to communicate loop termination.
        A queue object that stores transmission results.

    WHEN: There is an item in the queue.
        ``transmission_loop`` is used to continuously transmit log data.

    THEN: Data is transmitted successfully from the queue to the server.
        Transmission aftermath is resolved.
        Returns ``LogTransmissionStatus.Success`` on completion.
    """

    def test_status(self, call_transmission_loop: TransmissionLoopResult):
        """THEN: Returns ``LogTransmissionStatus.Success`` on completion."""
        error_string = "`transmission_loop` failed to return success."
        assert (
            call_transmission_loop.status == LogTransmissionStatus.Success
        ), error_string

    def test_result_queue(
        self,
        call_transmission_loop: TransmissionLoopResult,
        log_json_data: list[dict[str, str | int]],
    ):
        """THEN: Transmission aftermath is resolved."""
        expected_results: list[tuple[str, int]] = [
            (f"Received JSON Data as POST for {call_transmission_loop.namespace}", 200)
            for _ in range(len(log_json_data))
        ]

        error_string = (
            "The task results in the queue are not as expected in order or form."
        )

        assert (
            list(call_transmission_loop.result_queue) == expected_results
        ), error_string

    def test_data_transmission(
        self,
        call_transmission_loop: TransmissionLoopResult,
        log_json_data: list[dict[str, str | int]],
    ):
        """THEN: Data is transmitted successfully from the queue to the server."""
        assert (
            call_transmission_loop.log_data_response
        ), f"No data was transmitted to the server at namespace: {call_transmission_loop.namespace}"

        call_transmission_loop.log_data_response.sort(key=lambda x: x["index"])
        error_string = "The log data returned from the server doesn't match the transmitted log data in either value or order of values."

        assert call_transmission_loop.log_data_response == log_json_data, error_string


class StartTransmissionLoopResult(NamedTuple):
    """Represent result of calling ``transmission_loop``."""

    status: LogTransmissionStatus
    namespace: str
    result_queue: collections.deque


@pytest.fixture(scope="class")
def call_start_transmission_loop(
    q_transmission_log_items: collections.deque,
    server_urls: ServerUrls,
    transmission_results_q: collections.deque,
    transmission_stop_event: threading.Event,
    len_log_json_data: int,
) -> StartTransmissionLoopResult:
    """Call ``start_transmission_loop`` and return a ``StartTransmissionLoopResult`` instance."""
    transmission_loop_result: dict[str, LogTransmissionStatus] = {
        "result": LogTransmissionStatus.InTransmit
    }

    def run_start_loop():
        result = start_transmission_loop(
            q=q_transmission_log_items,
            log_url=server_urls.log_url,
            stop_event=transmission_stop_event,
            result_queue=transmission_results_q,
        )
        transmission_loop_result["result"] = result

    t = threading.Thread(target=run_start_loop, name="start_run_loop")

    t.start()

    count = 0

    while count < 100:
        count = count + 1
        # Using ``len`` on a ``collections.deque`` is not threadsafe.
        # However, we do not actually need thread safety here, since the loop will
        # eventually terminate independently of the following ``if`` block.
        # This does insert some uncertainty into the test, and it should be refactored
        # to a better solution if possible.
        if len(transmission_results_q) >= len_log_json_data:
            break
        else:
            sleep(0.1)

    transmission_stop_event.set()

    sleep(0.3)  # Why: Wait for the loop to stop.

    status: LogTransmissionStatus = transmission_loop_result["result"]

    result = StartTransmissionLoopResult(
        status=status,
        namespace=server_urls.namespace,
        result_queue=transmission_results_q,
    )

    return result


class TestStartTransmissionLoop:
    """
    Unit test for ``start_transmission_loop`` function.

    GIVEN: A queue object that hold log data in json format.
        Validated server url where log data will be transmitted.
        ``threading.Event`` that is used to communicate loop termination.
        A queue object that stores transmission results.

    WHEN: There is an item in the queue.
        ``start_transmission_loop`` starts transmission and blocks until loop ends.

    THEN: Returns ``LogTransmissionStatus.Success`` on completion.
        Transmission aftermath is resolved.
    """

    def test_return(self, call_start_transmission_loop: StartTransmissionLoopResult):
        """THEN: Returns ``LogTransmissionStatus.Success`` on completion."""
        error_string = f"`start_transmission_loop` failed to return {LogTransmissionStatus.Success}"
        assert (
            call_start_transmission_loop.status == LogTransmissionStatus.Success
        ), error_string

    def test_aftermath(
        self,
        call_start_transmission_loop: StartTransmissionLoopResult,
        log_json_data: list[dict[str, str | int]],
    ):
        """THEN: Transmission aftermath is resolved."""
        expected_results: list[tuple[str, int]] = [
            (
                f"Received JSON Data as POST for {call_start_transmission_loop.namespace}",
                200,
            )
            for _ in range(len(log_json_data))
        ]

        error_string = (
            "The task results in the queue are not as expected in order or form."
        )

        assert (
            list(call_start_transmission_loop.result_queue) == expected_results
        ), error_string


async def do_async_work(num) -> str:
    """Return result from a mock task."""
    result = f"task_completed{num}"
    return result


@pytest_asyncio.fixture
async def async_tasks() -> set[asyncio.Task]:
    """Create a set of fire and forget tasks."""
    tasks = set()
    for i in range(10):
        task = asyncio.create_task(coro=do_async_work(num=i), name=f"Task:{i}")
        tasks.add(task)
    return tasks


@pytest.mark.asyncio
async def test_transmission_cleanup(
    async_tasks: set[asyncio.Task],
):
    """
    Unit test for ``transmission_cleanup`` function.

    GIVEN: A set of ``asyncio.Task`` that are being completed asynchronously.
        ``transmission_cleanup`` removes tasks from the set.

    WHEN: There are a number of tasks in the set. ``transmission_cleanup`` is called to
        cleanup the tasks.

    THEN: ``transmission_cleanup`` returns ``LogTransmissionStatus.CleanupSuccessful``.
        All tasks have been discarded from the set, and it has 0 items in it.
    """
    loop = asyncio.get_running_loop()
    tasks = list(async_tasks)
    for task in tasks:
        result = await loop.run_in_executor(
            executor=None,
            func=functools.partial(transmission_cleanup, async_tasks, task),
        )

        assert (
            result == LogTransmissionStatus.CleanupSuccessful
        ), f"Transmission cleanup has failed on {task.get_name()}"
    assert (
        len(async_tasks) == 0
    ), "Cleanup has failed, there are still items remaining in the set."


@pytest.fixture
def results_queue(max_q_len=100) -> collections.deque:
    """Return an empty results queue limited to ``max_q_len``."""
    q: collections.deque = collections.deque(maxlen=max_q_len)
    return q


class SaveTransmissionResult(NamedTuple):
    """Represent result of calling ``save_transmission_result``."""

    status: list[LogTransmissionStatus]
    result_queue: collections.deque


@pytest.fixture
def call_save_transmission_result(
    results_queue: collections.deque,
    async_tasks: set[asyncio.Task],
) -> SaveTransmissionResult:
    """Call ``save_transmission_result`` and return ``SaveResults`` instance."""
    statuses = []
    for task in async_tasks:
        status = save_transmission_result(result_queue=results_queue, task=task)
        statuses.append(status)

    save_tr_res = SaveTransmissionResult(status=statuses, result_queue=results_queue)
    return save_tr_res


async def cancelled_async_work() -> str:
    """Raise ``asyncio.CancelledError`` so that the coroutine ends up being cancelled."""
    raise asyncio.CancelledError


@pytest_asyncio.fixture
async def cancelled_async_tasks() -> set[asyncio.Task]:
    """Create a set of fire and forget tasks that end up being cancelled."""
    tasks = set()
    for i in range(10):
        task = asyncio.create_task(
            coro=cancelled_async_work(), name=f"Cancelled task:{i}"
        )
        tasks.add(task)
    return tasks


@pytest.fixture
def call_save_transmission_result_with_cancelled_tasks(
    results_queue: collections.deque, cancelled_async_tasks: set[asyncio.Task]
) -> SaveTransmissionResult:
    """Call ``save_transmission_result`` on cancelled tasks and return ``SaveTransmissionResult`` instance."""
    statuses = []
    for task in cancelled_async_tasks:
        status = save_transmission_result(result_queue=results_queue, task=task)
        statuses.append(status)

    save_tr_res = SaveTransmissionResult(status=statuses, result_queue=results_queue)
    return save_tr_res


class TestSaveTransmissionResult:
    """
    Unit test for ``save_transmission_result`` function.

    GIVEN: A queue object with a ``maxlen`` property of 100.
        ``save_transmission_result`` saves transmission results to the queue.

    WHEN: All ``asyncio.Task`` have finished execution.

    THEN: ``save_transmission_result`` saves the result in the queue.
        Returns ``LogTransmissionStatus.ResultSaved`` for each saved result.
        Returns ``LogTransmissionStatus.ResultNotSaved`` in case of failure.
    """

    def test_return_on_saved(
        self,
        call_save_transmission_result: SaveTransmissionResult,
    ):
        """THEN: Returns ``LogTransmissionStatus.ResultSaved`` for each saved result."""
        assert call_save_transmission_result.status == [
            LogTransmissionStatus.ResultSaved for i in range(10)
        ], "save_transmission_result returned unexpected values when result should have been saved."

    def test_return_on_not_saved(
        self, call_save_transmission_result_with_cancelled_tasks: SaveTransmissionResult
    ):
        """THEN: Returns ``LogTransmissionStatus.ResultNotSaved`` in case of failure."""
        assert call_save_transmission_result_with_cancelled_tasks.status == [
            LogTransmissionStatus.ResultNotSaved for i in range(10)
        ], "save_transmission_result returned unexpected values when result shouldn't have been saved."

    def test_results_saved_in_queue(
        self, call_save_transmission_result: SaveTransmissionResult
    ):
        """THEN: ``save_transmission_result`` saves the result in the queue."""
        expected_task_results = set([f"task_completed{num}" for num in range(10)])
        received_task_results = set()

        len_result_queue: int = len(call_save_transmission_result.result_queue)

        for _ in range(len_result_queue):
            received_task_results.add(call_save_transmission_result.result_queue.pop())

        missing_results = expected_task_results.difference(received_task_results)
        extra_results = received_task_results.difference(expected_task_results)

        error_string = (
            "Results saved in queue don't match the expected result in value."
        )

        if missing_results:
            missing_results_string = f" There are a number of missing elements in the queue: {missing_results}."
            error_string = error_string + missing_results_string

        if extra_results:
            extra_results_string = (
                f" There are a number of extra elements in the queue: {extra_results}."
            )
            error_string = error_string + extra_results_string

        assert expected_task_results == received_task_results, error_string


class ResolveTransmissionResult(NamedTuple):
    """Represent result of calling ``transmission_cleanup``."""

    status: list[LogTransmissionStatus]
    tasks_set: set[asyncio.Task]
    result_queue: collections.deque


@pytest.fixture(scope="session")
def event_loop():
    """Redefine the fixture scoped to session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="class")
async def async_tasks_2() -> set[asyncio.Task]:
    """Create a set of fire and forget tasks."""
    tasks = set()
    for i in range(10):
        task = asyncio.create_task(coro=do_async_work(num=i), name=f"Task:{i}")
        tasks.add(task)
    return tasks


@pytest.fixture(scope="class")
def call_resolve_transmission(
    async_tasks_2: set[asyncio.Task],
) -> ResolveTransmissionResult:
    """Call ``resolve_transmission`` and return ``ResolveTransmissionResult`` instance."""
    tasks = list(async_tasks_2)
    results = []

    q: collections.deque = collections.deque(maxlen=100)

    for task in tasks:
        result = resolve_transmission(tasks=async_tasks_2, task=task, result_queue=q)
        results.append(result)

    transmission_cleanup_result = ResolveTransmissionResult(
        status=results, tasks_set=async_tasks_2, result_queue=q
    )
    return transmission_cleanup_result


class TestResolveTransmission:
    """
    Unit test for ``resolve_transmission`` function.

    GIVEN: A queue object with a ``maxlen`` property of 100.
        A set of ``asyncio.Task`` that are being completed asynchronously.
        ``resolve_transmission`` handles the aftermath of the transmission finishing
        it's execution.

    WHEN: All ``asyncio.Task`` have finished execution.

    THEN: The set of tasks is empty.
        Result of each completed task is stored inside the queue.
        Returns ``LogTransmissionStatus.TransmissionResolved`` on success.
    """

    def test_result_saved(self, call_resolve_transmission: ResolveTransmissionResult):
        """THEN: Result of each completed task is stored inside the queue."""
        expected_task_results = set([f"task_completed{num}" for num in range(10)])
        received_task_results = set(call_resolve_transmission.result_queue)

        missing_results = expected_task_results.difference(received_task_results)
        extra_results = received_task_results.difference(expected_task_results)

        error_string = (
            "Results saved in queue don't match the expected result in value."
        )

        if missing_results:
            missing_results_string = f" There are a number of missing elements in the queue: {missing_results}."
            error_string = error_string + missing_results_string

        if extra_results:
            extra_results_string = (
                f" There are a number of extra elements in the queue: {extra_results}."
            )
            error_string = error_string + extra_results_string

        assert expected_task_results == received_task_results, error_string

    def test_set_empty(self, call_resolve_transmission: ResolveTransmissionResult):
        """THEN: The set of tasks is empty."""
        assert (
            len(call_resolve_transmission.tasks_set) == 0
        ), "Cleanup has failed, there are still items remaining in the set."

    def test_return(self, call_resolve_transmission: ResolveTransmissionResult):
        """THEN: Returns ``LogTransmissionStatus.TransmissionResolved`` on success."""
        assert call_resolve_transmission.status == [
            LogTransmissionStatus.TransmissionResolved for _ in range(10)
        ], "`resolve_transmission` returned unexpected values when transmission should have been resolved."


class ResolveTransmissionResultNoQueue(NamedTuple):
    """Represent result of calling ``resolve_transmission`` with no result queue."""

    status: list[LogTransmissionStatus]
    tasks_set: set[asyncio.Task]


@pytest.fixture(scope="class")
def call_resolve_transmission_no_queue(
    async_tasks_2: set[asyncio.Task],
) -> ResolveTransmissionResultNoQueue:
    """Call ``resolve_transmission`` and return ``ResolveTransmissionResultNoQueue`` instance."""
    tasks = list(async_tasks_2)
    results = []

    for task in tasks:
        result = resolve_transmission(tasks=async_tasks_2, task=task)
        results.append(result)

    transmission_cleanup_result = ResolveTransmissionResultNoQueue(
        status=results, tasks_set=async_tasks_2
    )
    return transmission_cleanup_result


class TestResolveTransmissionNoResultQueue:
    """
    Unit test for ``resolve_transmission`` function with no result queue.

    GIVEN:
        A set of ``asyncio.Task`` that are being completed asynchronously.
        ``resolve_transmission`` handles the aftermath of the transmission finishing
        it's execution.

    WHEN: All ``asyncio.Task`` have finished execution.

    THEN: The set of tasks is empty.
        Returns ``LogTransmissionStatus.TransmissionResolved`` on success.
    """

    def test_set_empty(
        self, call_resolve_transmission_no_queue: ResolveTransmissionResultNoQueue
    ):
        """THEN: The set of tasks is empty."""
        assert (
            len(call_resolve_transmission_no_queue.tasks_set) == 0
        ), "Cleanup has failed, there are still items remaining in the set."

    def test_return(
        self, call_resolve_transmission_no_queue: ResolveTransmissionResultNoQueue
    ):
        """THEN: Returns ``LogTransmissionStatus.TransmissionResolved`` on success."""
        assert call_resolve_transmission_no_queue.status == [
            LogTransmissionStatus.TransmissionResolved for _ in range(10)
        ], "`resolve_transmission` returned unexpected values when transmission should have been resolved."


@pytest.fixture(scope="class")
def log_strings() -> set[str]:
    """Return a set of log strings."""
    strings: set[str] = set()

    for i in range(NUM_ITEMS_SMALL):
        strings.add(f"Log message: {i}")

    return strings


class CustomHandlerForTest(logging.Handler):
    """A custom ``logging.Handler`` class for testing.

    Instead of emitting log messages, it saves them to the passed
    ``emit_set``.

    Attributes:
        emit_set (set[str]): set that contains

    Args:
        emit_set: Stores formatted log messages.
    """

    def __init__(self, emit_set: set[str], level=logging.DEBUG) -> None:
        super().__init__(level)
        self.emit_set: set[str] = emit_set

    def emit(self, record: logging.LogRecord) -> None:
        """Save the record in ``emit_set``."""
        msg = self.format(record)
        self.emit_set.add(msg)


class LogJSONFormatterResult(NamedTuple):
    """Represent result of using ``LogJSONFormatter``."""

    log_dicts: list[dict[str, str]]
    err_set: list[str]


@pytest.fixture(scope="class")
def call_LogJSONFormatter(log_strings: set[str]) -> LogJSONFormatterResult:
    """Call `LogJSONFormatter.format` and return the result."""
    emit_set: set[str] = set()
    log_json_formatter = LogJSONFormatter()

    custom_handler = CustomHandlerForTest(emit_set=emit_set)
    custom_handler.setFormatter(log_json_formatter)

    logger = logging.getLogger("test-logger")
    logger.addHandler(custom_handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    count = 0

    for log in log_strings:
        """
        +-------+ +1 +--------+ +1 +--------+ +1 +--------+ +1 +---------+ +1 +---------+ +1+----------+
        | count +--->+ count  +----> count  +--->+ count  +--->+ count   +--->+ count   +-->+ count    |
        | = 0   |    | = 1    |    | = 2    |    | = 3    |    | = 4     |    | = 5     |   | = 6      |
        +----+--+    +--------+    +--------+    +--------+    +---------+    +---------+   +-----+----+
            ^                                                                                    |
            |                                                                                    |
            |                                      set count = 0                                 |
            +------------------------------------------------------------------------------------+
        Made with ``https://asciiflow.com/legacy/``.
        """
        if count == 0:
            logger.debug(log)
        if count == 1:
            logger.info(log)
        if count == 2:
            logger.warning(log)
        if count == 3:
            logger.error(log)
        if count == 4:
            logger.critical(log)
        if count == 5:
            try:
                raise ValueError(log)
            except ValueError:
                logger.exception(log)
        count = count + 1
        if count == 6:
            count = 0

    log_dicts: list[dict[str, str]] = list()
    err_set: list[str] = list()

    for lg in emit_set:
        try:
            log_dict = json.loads(lg)
            log_dicts.append(log_dict)

        except json.JSONDecodeError:
            err_string = f"Didn't format them into json correctly: {log}"
            err_set.append(err_string)
    return LogJSONFormatterResult(log_dicts=log_dicts, err_set=err_set)


class TestLogJSONFormatter:
    """Unit test for `LogJSONFormatter` class.

    GIVEN: `LogJSONFormatter` formats log records.

    WHEN: Log records are generated.

    THEN: `LogJSONFormatter` formats them correctly.
        The message is correctly stored in the JSON string.
    """

    def test_log_format_is_json(
        self, call_LogJSONFormatter: LogJSONFormatterResult, log_strings: set[str]
    ):
        """THEN: `LogJSONFormatter` formats them correctly."""
        assert (
            call_LogJSONFormatter.err_set == []
        ), "Logs were not correctly formatted into JSON."

    def test_messages(
        self, call_LogJSONFormatter: LogJSONFormatterResult, log_strings: set[str]
    ):
        """THEN: The message is correctly stored in the JSON string."""
        messages: set[str] = set()
        for log_dict in call_LogJSONFormatter.log_dicts:
            try:
                if " | " in log_dict["message"][:20]:
                    msg = log_dict["message"][:20]
                    index = msg.find(" | ")
                    msg = msg[:index]
                    messages.add(msg)
                else:
                    messages.add(log_dict["message"])
            except KeyError:
                messages.add("There is no key `message` in the log.")
        assert messages == log_strings, "Messages were not properly logged."


@pytest.fixture
def structured_log_messages() -> list[dict[str, Any]]:
    """Return a ``list`` of ``dicts`` that look like structured log messages."""
    structured_log_messages: list[dict[str, Any]] = [
        {
            "address": "address:%s" % i,
            "another_dict": {
                "another_message": "another_message:%s" % i,
                "another_num": i,
            },
            "car": "car:%s" % i,
            "message": "message:%s" % i,
            "name": "name:%s" % i,
            "num": i,
        }
        for i in range(NUM_ITEMS_SMALL)
    ]
    return structured_log_messages


def test_StructuredMessage(structured_log_messages: list[dict[str, Any]]):
    """Unit test for ``StructuredMessage``.

    GIVEN: ``StructuredMessage`` creates a structured log message.

    WHEN: Message and keyword arguments are passed to ``StructuredMessage``.

    THEN: ``StructuredMessage`` 's ``__str__`` returns a JSON string.
    """
    expected_messages = []
    for item in structured_log_messages:
        msg = str(
            StructuredMessage(
                message=item["message"],
                name=item["name"],
                address=item["address"],
                car=item["car"],
                num=item["num"],
                another_dict=item["another_dict"],
            )
        )
        expected_messages.append(json.loads(msg[6:]))

    assert (
        expected_messages == structured_log_messages
    ), "Structured messages are incorrect."
