"""Test the code at app/config.py."""
from __future__ import annotations  # Remove if using python3.10 or greater

import asyncio
import functools
import json
import queue

import pytest
import pytest_asyncio
from aiohttp import ClientSession
from requests import Response

from app.config import LogTransmissionStatus  # type: ignore[import]  # Ignore missing imports
from app.config import async_transmit_log, start_transmission_loop, transmission_loop, transmission_cleanup  # type: ignore[import]  # Ignore missing imports
from app.models import HttpUrl  # type: ignore[import]  # Ignore missing imports


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


@pytest.fixture
def queue_with_items(log_data: list[str]) -> queue.Queue:
    """Return a queue filled with `log_data` items."""
    q: queue.Queue = queue.Queue()
    for item in log_data:
        q.put(item)
    return q


@pytest.mark.asyncio
async def test_transmission_loop(
    queue_with_items: queue.Queue,
    flask_server_port: str,
    n_space: str,
    request_session,
    log_json_data: list[dict[str, str | int]],
):
    """
    GIVEN: queue object that hold log data. Server url.

    WHEN: There is an item in the queue.
        ``transmission_loop`` is used to continuously transmit log data.

    THEN: Data is transmitted successfully from the queue to the server.
    """
    # get each item from queue and pass it to the async_transmit_log function
    namespace: str = n_space
    log_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/namespaces/{namespace}/"
    )

    result = await transmission_loop(q=queue_with_items, log_url=log_url, qsize=24)

    data_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/data/{namespace}/"
    )
    data_url_str = str(data_url.url)

    loop = asyncio.get_running_loop()

    data_response: Response = await loop.run_in_executor(
        executor=None, func=functools.partial(request_session.get, data_url_str)
    )

    try:
        data_dict = data_response.json()
        if not data_dict[namespace]:
            raise AssertionError(
                f"No data transmitted to the server at namespace: {namespace}."
            )
        log_data: list[dict[str, str | int]] = data_dict[namespace]
    except json.JSONDecodeError:
        raise AssertionError(
            f"There was a problem decoding to JSON: {data_response.text}"
        )
    except KeyError as e:
        if data_response.text == "This namespace doesn't exist.":
            raise AssertionError(
                f"The data was not saved to the namespace: {namespace}."
            )
        raise e

    log_data.sort(key=lambda x: x["index"])

    assert (
        result == LogTransmissionStatus.Success
    ), "Something went wrong while running the transmission loop."

    assert (
        log_data == log_json_data
    ), "The log data returned from the server doesn't match the transmitted log data in either value or order of values."


def test_start_transmission_loop(
    queue_with_items: queue.Queue,
    flask_server_port: str,
    n_space: str,
    request_session,
    log_json_data: list[dict[str, str | int]],
):
    """
    GIVEN: queue object that hold log data. Server url.

    WHEN: There may be items in the queue.
        `start_transmission_loop` starts transmission and blocks until loop ends.

    THEN: Data is transmitted successfully from the queue to the server.
    """
    namespace: str = n_space
    log_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/namespaces/{namespace}/"
    )

    result = start_transmission_loop(q=queue_with_items, log_url=log_url, qsize=24)

    data_url = HttpUrl(
        url=f"http://localhost:{flask_server_port}/log/data/{namespace}/"
    )
    data_url_str = str(data_url.url)

    data_response: Response = request_session.get(data_url_str)

    try:
        data_dict = data_response.json()
        if not data_dict[namespace]:
            raise AssertionError(
                f"No data transmitted to the server at namespace: {namespace}."
            )
        log_data: list[dict[str, str | int]] = data_dict[namespace]
    except json.JSONDecodeError:
        raise AssertionError(
            f"There was a problem decoding to JSON: {data_response.text}"
        )
    except KeyError as e:
        if data_response.text == "This namespace doesn't exist.":
            raise AssertionError(
                f"The data was not saved to the namespace: {namespace}."
            )
        raise e

    assert (
        result == LogTransmissionStatus.Success
    ), "Something went wrong while running the transmission loop."

    log_data.sort(key=lambda x: x["index"])

    assert (
        log_data == log_json_data
    ), "The log data returned from the server doesn't match the transmitted log data in either value or order of values."


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
