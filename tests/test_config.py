"""Test the code at app/config.py."""
import asyncio

import pytest
from aiohttp import ClientSession

from app.config import async_transmit_log  # type: ignore[import]  # Ignore missing imports
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
