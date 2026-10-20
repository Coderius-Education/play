"""A contact callback starts at once and runs up to its first await before the frame goes on."""

import asyncio
import contextvars
import gc
import sys

import pytest

import play.loop
from play.globals import ProgramState, globals_list


@pytest.fixture(
    params=[True, False], ids=["eager_task_factory", "by hand, as on Python 3.11"]
)
def eager_start(request, monkeypatch):
    if request.param and not play.loop._HAS_EAGER_TASK_FACTORY:
        pytest.skip("eager_task_factory needs Python 3.12")
    if not request.param and sys.version_info >= (3, 14):
        pytest.skip("on 3.14+ asyncio does not see a pure-Python Task as current")
    monkeypatch.setattr(play.loop, "_HAS_EAGER_TASK_FACTORY", request.param)
    return play.loop.start_task


def _run(coroutine):
    return play.loop.get_loop().run_until_complete(coroutine)


def test_an_eager_start_runs_up_to_the_first_await_and_then_finishes(eager_start):
    steps = []

    async def callback():
        steps.append("before")
        await asyncio.sleep(0)
        steps.append("after")
        return "done"

    async def frame():
        task = eager_start(callback())
        steps.append("frame goes on")
        return await task

    assert _run(frame()) == "done"
    assert steps == ["before", "frame goes on", "after"]


def test_an_eager_start_of_a_coroutine_that_ends_at_once_is_done_at_once(
    eager_start,
):
    async def callback():
        return "done"

    async def frame():
        return eager_start(callback())

    started = _run(frame())

    assert started.done()
    assert started.result() == "done"


def test_an_error_before_the_first_await_is_kept_in_the_eager_task(eager_start):
    async def callback():
        raise ValueError("typo before the await")

    async def frame():
        return eager_start(callback())

    started = _run(frame())

    assert started.done()
    assert str(started.exception()) == "typo before the await"


def test_an_error_after_the_first_await_reaches_the_eager_task(eager_start):
    async def callback():
        await asyncio.sleep(0)
        raise ValueError("typo after the await")

    async def frame():
        await eager_start(callback())

    with pytest.raises(ValueError, match="typo after the await"):
        _run(frame())


@pytest.mark.parametrize(
    "turns_before_cancel", [0, 1], ids=["before its first turn", "after"]
)
def test_cancelling_an_eager_task_cancels_the_coroutine(
    eager_start, turns_before_cancel
):
    seen = []

    async def callback():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            seen.append("cancelled")
            raise
        finally:
            seen.append("cleaned up")

    async def frame():
        task = eager_start(callback())
        for _ in range(turns_before_cancel):
            await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    _run(frame())

    assert seen == ["cancelled", "cleaned up"]


def test_an_eager_task_is_the_current_task_from_its_first_step(eager_start):
    current = []

    async def callback():
        current.append(asyncio.current_task())
        await asyncio.sleep(0)

    async def frame():
        task = eager_start(callback())
        await task
        return task

    assert current == [_run(frame())]


def test_a_timeout_set_in_the_first_step_ends_the_eager_task(eager_start):
    async def callback():
        try:
            async with asyncio.timeout(0.01):
                await asyncio.sleep(10)
        except TimeoutError:
            return "timed out"
        return "slept"

    async def frame():
        task = eager_start(callback())
        while not task.done():
            await asyncio.sleep(0.005)
        return task.result()

    assert _run(frame()) == "timed out"


def test_a_context_variable_set_in_the_first_step_stays_in_the_eager_task(
    eager_start,
):
    level = contextvars.ContextVar("level", default="frame")

    async def callback():
        level.set("callback")
        await asyncio.sleep(0)
        return level.get()

    async def frame():
        task = eager_start(callback())
        in_the_frame = level.get()
        return in_the_frame, await task

    assert _run(frame()) == ("frame", "callback")


def test_an_eager_task_that_stops_the_program_goes_no_further(eager_start):
    steps = []

    async def callback():
        globals_list.program_state = ProgramState.STOPPED
        await asyncio.sleep(0)
        steps.append("after the stop")

    async def frame():
        task = eager_start(callback())
        await asyncio.sleep(0.01)
        return task

    assert _run(frame()).cancelled()
    assert steps == []


def test_an_eager_task_resumes_one_loop_turn_after_a_bare_await(eager_start):
    order = []

    async def callback():
        await asyncio.sleep(0)
        order.append("callback")

    async def frame():
        eager_start(callback())
        for turn in range(3):
            order.append(f"turn {turn}")
            await asyncio.sleep(0)

    _run(frame())

    assert order == ["turn 0", "callback", "turn 1", "turn 2"]


def test_a_cancellation_in_the_first_step_ends_only_the_eager_task(eager_start):
    async def callback():
        cancelled = asyncio.get_running_loop().create_future()
        cancelled.cancel()
        await cancelled

    async def frame():
        task = eager_start(callback())
        await asyncio.sleep(0)
        return task

    assert _run(frame()).cancelled()


def test_an_error_after_a_caught_timeout_does_not_carry_the_timeout(eager_start):
    async def callback():
        try:
            async with asyncio.timeout(0.01):
                await asyncio.sleep(10)
        except TimeoutError:
            pass
        raise ValueError("typo after the timeout")

    async def frame():
        task = eager_start(callback())
        while not task.done():
            await asyncio.sleep(0.005)
        return task.exception()

    error = _run(frame())

    assert str(error) == "typo after the timeout"
    assert error.__context__ is None


def test_a_forgotten_eager_task_is_collected_quietly(eager_start, monkeypatch):
    unraisable = []
    monkeypatch.setattr(sys, "unraisablehook", unraisable.append)

    async def callback():
        await asyncio.Event().wait()

    async def frame():
        eager_start(callback())
        await asyncio.sleep(0)

    _run(frame())
    gc.collect()

    assert unraisable == []


def test_without_asyncios_task_internals_a_by_hand_start_is_a_plain_task(
    monkeypatch,
):
    monkeypatch.setattr(play.loop, "_HAS_EAGER_TASK_FACTORY", False)
    monkeypatch.setattr(play.loop, "_CAN_START_BY_HAND", False)
    steps = []

    async def callback():
        steps.append("first step")
        await asyncio.sleep(0)
        return "done"

    async def frame():
        task = play.loop.start_task(callback())
        steps.append("frame goes on")
        return await task

    assert _run(frame()) == "done"
    assert steps == ["frame goes on", "first step"]
