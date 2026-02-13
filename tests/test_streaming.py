"""Tests for the StreamEmitter and event types."""

from __future__ import annotations

import asyncio
import json

import pytest

from engine.streaming import StreamEmitter
from engine.streaming.events import EventType, StreamEvent


def test_stream_event_to_ndjson() -> None:
    event = StreamEvent(event=EventType.CONTENT, data={"text": "hello"})
    line = event.to_ndjson()
    assert line.endswith("\n")
    parsed = json.loads(line)
    assert parsed["event"] == "content"
    assert parsed["data"]["text"] == "hello"


def test_event_types_are_strings() -> None:
    assert EventType.STATUS.value == "status"
    assert EventType.CONTENT.value == "content"
    assert EventType.TOOL_USE.value == "tool_use"
    assert EventType.DONE.value == "done"
    assert EventType.ERROR.value == "error"


async def test_emitter_emit_and_iterate() -> None:
    emitter = StreamEmitter(debug=False)

    async def produce() -> None:
        await emitter.emit_status("started")
        await emitter.emit_content("Hello world")
        await emitter.emit_done(result="done")

    task = asyncio.create_task(produce())

    events: list[str] = []
    async for line in emitter:
        events.append(line)

    await task

    assert len(events) == 3
    assert json.loads(events[0])["event"] == "status"
    assert json.loads(events[1])["event"] == "content"
    assert json.loads(events[2])["event"] == "done"


async def test_emitter_error_event() -> None:
    emitter = StreamEmitter()

    async def produce() -> None:
        await emitter.emit_error("something broke", details={"code": 500})
        await emitter.close()

    task = asyncio.create_task(produce())

    events: list[str] = []
    async for line in emitter:
        events.append(line)

    await task

    assert len(events) == 1
    parsed = json.loads(events[0])
    assert parsed["event"] == "error"
    assert "something broke" in parsed["data"]["error"]


async def test_emitter_debug_only_when_enabled() -> None:
    emitter_no_debug = StreamEmitter(debug=False)

    async def produce_no_debug() -> None:
        await emitter_no_debug.emit_debug({"info": "test"})
        await emitter_no_debug.close()

    task = asyncio.create_task(produce_no_debug())
    events: list[str] = []
    async for line in emitter_no_debug:
        events.append(line)
    await task
    assert len(events) == 0

    emitter_debug = StreamEmitter(debug=True)

    async def produce_debug() -> None:
        await emitter_debug.emit_debug({"info": "test"})
        await emitter_debug.close()

    task2 = asyncio.create_task(produce_debug())
    events2: list[str] = []
    async for line in emitter_debug:
        events2.append(line)
    await task2
    assert len(events2) == 1
    assert json.loads(events2[0])["event"] == "debug"


async def test_emitter_tool_events() -> None:
    emitter = StreamEmitter()

    async def produce() -> None:
        await emitter.emit_tool_use("Bash", {"command": "ls"})
        await emitter.emit_tool_result("Bash", "file1.py\nfile2.py")
        await emitter.close()

    task = asyncio.create_task(produce())

    events: list[str] = []
    async for line in emitter:
        events.append(line)

    await task

    assert len(events) == 2
    assert json.loads(events[0])["event"] == "tool_use"
    assert json.loads(events[1])["event"] == "tool_result"
