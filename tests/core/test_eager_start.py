"""A contact callback starts at once and runs up to its first await before the frame goes on."""

import asyncio

import pytest

import play.loop
from play.globals import ProgramState, globals_list


def _run(coroutine):
    return play.loop.get_loop().run_until_complete(coroutine)


@pytest.mark.parametrize(
    "start",
    [
        lambda coro: play.loop.create_task(coro, eager=True),
        lambda coro: play.loop._start_eagerly(coro, "play: test"),
    ],
    ids=["create_task", "by hand, as on Python 3.11"],
)
def test_an_eager_start_runs_up_to_the_first_await_and_then_finishes(start):
    steps = []

    async def callback():
        steps.append("before")
        await asyncio.sleep(0)
        steps.append("after")
        return "done"

    async def frame():
        task = start(callback())
        steps.append("frame goes on")
        return await task

    assert _run(frame()) == "done"
    assert steps == ["before", "frame goes on", "after"]


def test_a_coroutine_started_by_hand_that_finishes_at_once_needs_no_task():
    async def callback():
        return "done"

    async def frame():
        return play.loop._start_eagerly(callback(), "play: test")

    assert _run(frame()) is None


def test_an_error_after_the_first_await_reaches_the_task_started_by_hand():
    async def callback():
        await asyncio.sleep(0)
        raise ValueError("typo after the await")

    async def frame():
        await play.loop._start_eagerly(callback(), "play: test")

    with pytest.raises(ValueError, match="typo after the await"):
        _run(frame())


def test_cancelling_a_task_started_by_hand_cancels_the_coroutine():
    cleaned_up = []

    async def callback():
        try:
            await asyncio.sleep(10)
        finally:
            cleaned_up.append(True)

    async def frame():
        task = play.loop._start_eagerly(callback(), "play: test")
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    _run(frame())

    assert cleaned_up == [True]


def test_a_callback_started_by_hand_that_stops_the_program_goes_no_further():
    steps = []

    async def callback():
        globals_list.program_state = ProgramState.STOPPED
        await asyncio.sleep(0)
        steps.append("after the stop")

    async def frame():
        task = play.loop._start_eagerly(callback(), "play: test")
        await asyncio.sleep(0.01)
        return task

    assert _run(frame()) is None
    assert steps == []


@pytest.mark.parametrize(
    "start",
    [
        lambda coro: play.loop.create_task(coro, eager=True),
        lambda coro: play.loop._start_eagerly(coro, "play: test"),
    ],
    ids=["create_task", "by hand, as on Python 3.11"],
)
def test_an_eager_start_resumes_one_loop_turn_after_a_bare_await(start):
    order = []

    async def callback():
        await asyncio.sleep(0)
        order.append("callback")

    async def frame():
        start(callback())
        for turn in range(3):
            order.append(f"turn {turn}")
            await asyncio.sleep(0)

    _run(frame())

    assert order == ["turn 0", "callback", "turn 1", "turn 2"]
