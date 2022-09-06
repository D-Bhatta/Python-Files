"""Test the code at app/config.py."""
from __future__ import annotations  # Remove if using python3.10 or greater

import json
import logging
from typing import Any, NamedTuple

import pytest

from app.config import (  # type: ignore[import]  # Ignore missing imports
    LogJSONFormatter,
    StructuredMessage,
)

NUM_ITEMS_LARGE = 10000
NUM_ITEMS_SMALL = 100


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

    log_dicts: list[dict[str, Any]]
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


@pytest.fixture
def call_StructuredLogFormatter(
    structured_log_messages: list[dict[str, Any]]
) -> LogJSONFormatterResult:
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

    for log in structured_log_messages:
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
        struct_msg = StructuredMessage(
            message=log["message"],
            name=log["name"],
            address=log["address"],
            car=log["car"],
            num=log["num"],
            another_dict=log["another_dict"],
        )
        if count == 0:
            logger.debug(struct_msg)
        if count == 1:
            logger.info(struct_msg)
        if count == 2:
            logger.warning(struct_msg)
        if count == 3:
            logger.error(struct_msg)
        if count == 4:
            logger.critical(struct_msg)
        if count == 5:
            try:
                raise ValueError(struct_msg)
            except ValueError:
                logger.exception(struct_msg)
        count = count + 1
        if count == 6:
            count = 0

    log_dicts: list[dict[str, Any]] = list()
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
        Structured log records are generated.

    THEN: `LogJSONFormatter` formats them correctly.
        The message is correctly stored in the JSON string.
        Structured log records are correctly stored in the JSON string.
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
                messages.add(log_dict["message"])
            except KeyError:
                messages.add("There is no key `message` in the log.")
        assert messages == log_strings, "Messages were not properly logged."

    def test_structured_messages(
        self,
        call_StructuredLogFormatter: LogJSONFormatterResult,
        structured_log_messages: list[dict[str, Any]],
    ):
        """THEN: Structured log records are correctly stored in the JSON string."""
        messages: list[dict[str, Any]] = list()
        for log_dict in call_StructuredLogFormatter.log_dicts:
            try:
                msg = log_dict["message"]
                messages.append(msg)
            except KeyError:
                messages.append(
                    {"no_message_found": "There is no key `message` in the log."}
                )
        sort_by_num = lambda log_item: log_item["num"]
        messages.sort(key=sort_by_num)
        assert messages == structured_log_messages, "Messages were not properly logged."


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
