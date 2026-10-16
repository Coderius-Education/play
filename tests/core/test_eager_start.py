"""A contact callback starts at once and runs up to its first await before the frame goes on."""

import asyncio

import pytest

import play.loop
from play.globals import ProgramState, globals_list


@pytest.fixture(
    params=[True, False], ids=["eager_task_factory", "by hand, as on Python 3.11"]
)
def eager_start(request, monkeypatch):
    if request.param and not play.loop._EAGER_TASKS:
        pytest.skip("eager_task_factory needs Python 3.12")
    monkeypatch.setattr(play.loop, "_EAGER_TASKS", request.param)
    return lambda coro: play.loop.create_task(coro, eager=True)


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


def test_an_error_after_the_first_await_reaches_the_eager_task(eager_start):
    async def callback():
        await asyncio.sleep(0)
        raise ValueError("typo after the await")

    async def frame():
        await eager_start(callback())

    with pytest.raises(ValueError, match="typo after the await"):
        _run(frame())


def test_cancelling_an_eager_task_cancels_the_coroutine(eager_start):
    cleaned_up = []

    async def callback():
        try:
            await asyncio.sleep(10)
        finally:
            cleaned_up.append(True)

    async def frame():
        task = eager_start(callback())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    _run(frame())

    assert cleaned_up == [True]


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
