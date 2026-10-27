"""In the browser, under pygbag, the page owns the event loop and keeps it running."""

import ast
import asyncio
import gc
import logging
import sys
import types

import pygame
import pytest

import play
import play.loop
from play.api import auto_start
from play.globals import ProgramState, globals_list

_UNDER_A_C_TRACER = (
    sys.gettrace() is not None and getattr(sys.gettrace(), "__code__", None) is None
)


@pytest.fixture
def in_the_browser(monkeypatch):
    monkeypatch.setattr(play.loop, "RUNS_IN_BROWSER", True)
    monkeypatch.setattr(play.loop, "_loop", None)
    monkeypatch.setattr(play.loop, "_page_exception_handler", None)
    page_loop = asyncio.new_event_loop()
    yield page_loop
    page_loop.close()


def _stop_after(frames):
    counted = []

    def count():
        counted.append(1)
        if len(counted) == frames:
            play.stop_program()

    return count


def _wait_for_a_new_script():
    """Let auto-start watch the next script, as it does right after play is imported."""
    auto_start.stop_waiting_for_the_script()
    auto_start._schedule_auto_start.has_run = False


def _main_py(source, **names):
    """Return *source* as pygbag runs a main.py: a __main__ module that may await at the top."""
    code = compile(source, "main.py", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    main = {
        "__name__": "__main__",
        "asyncio": asyncio,
        "play": play,
        "stop_after": _stop_after,
        "globals_list": globals_list,
        **names,
    }
    _wait_for_a_new_script()
    return types.FunctionType(code, main)


def _run_page(page_loop, script):
    async def page():
        started = script()
        if asyncio.iscoroutine(started):
            await started
        await _until_only_the_page_is_left()

    page_loop.run_until_complete(page())


async def _until_only_the_page_is_left(steps=1000):
    for _ in range(steps):
        if len(asyncio.all_tasks()) == 1:
            return
        await asyncio.sleep(0)
    pytest.fail("play's tasks did not end")


def test_start_program_returns_at_once_and_the_page_loop_runs_the_frames(
    in_the_browser,
):
    frames = []
    first_frame_after_start_program = []

    @play.repeat_forever
    def count():
        frames.append(len(frames) + 1)
        if len(frames) == 5:
            play.stop_program()

    def script():
        play.start_program()
        first_frame_after_start_program.append(not frames)

    _run_page(in_the_browser, script)

    assert first_frame_after_start_program == [True]
    assert frames == [1, 2, 3, 4, 5]
    assert play.loop.get_loop() is in_the_browser


def test_the_display_stays_open_after_the_program_stops_in_the_browser(
    in_the_browser,
):
    play.when_program_starts(play.stop_program)

    _run_page(in_the_browser, play.start_program)

    assert pygame.display.get_init()


def test_an_error_stops_the_program_in_the_browser(in_the_browser, capsys, caplog):
    frames = []

    @play.repeat_forever
    async def broken():
        frames.append(1)
        raise ValueError("typo in the browser")

    with caplog.at_level(logging.CRITICAL, logger="play"):
        _run_page(in_the_browser, play.start_program)

    assert frames == [1]
    assert globals_list.error_shown
    shown = capsys.readouterr().err + caplog.text
    assert shown.count("ValueError: typo in the browser") == 1


def test_stopping_in_the_browser_ends_the_programs_other_callbacks(in_the_browser):
    ticks = []

    @play.when_program_starts
    async def walk():
        while True:
            ticks.append(1)
            await play.animate()

    play.repeat_forever(_stop_after(5))

    _run_page(in_the_browser, play.start_program)

    assert 0 < len(ticks) <= 6


def test_a_play_task_destroyed_while_pending_is_not_passed_to_the_page(
    in_the_browser,
):
    reported = []
    in_the_browser.set_exception_handler(
        lambda _loop, context: reported.append(context)
    )

    async def page():
        task = play.loop.create_task(asyncio.sleep(10))
        play.loop.get_loop().call_exception_handler(
            {"message": "Task was destroyed but it is pending!", "task": task}
        )
        task.cancel()

    in_the_browser.run_until_complete(page())

    assert reported == []


def test_a_failed_future_of_the_page_goes_to_the_default_handler(
    in_the_browser, monkeypatch
):
    reported = []
    monkeypatch.setattr(in_the_browser, "default_exception_handler", reported.append)

    def script():
        play.start_program()
        future = asyncio.get_running_loop().create_future()
        future.set_exception(OSError("the page's own future failed"))

    play.repeat_forever(_stop_after(5))

    _run_page(in_the_browser, script)

    assert [type(context.get("exception")) for context in reported] == [OSError]
    assert not globals_list.error_shown


def test_a_task_made_after_the_program_stopped_does_not_run_in_the_browser(
    in_the_browser,
):
    ran = []

    async def late():
        ran.append(1)

    @play.repeat_forever
    def stop_then_schedule():
        play.stop_program()
        play.loop.create_task(late())

    _run_page(in_the_browser, play.start_program)

    assert ran == []


def test_an_error_in_a_page_task_goes_to_the_handler_the_page_had(in_the_browser):
    reported = []
    in_the_browser.set_exception_handler(
        lambda _loop, context: reported.append(context)
    )

    async def pages_own_task():
        raise OSError("the page's own task failed")

    def script():
        play.start_program()
        asyncio.get_running_loop().create_task(pages_own_task())

    play.repeat_forever(_stop_after(20))

    _run_page(in_the_browser, script)

    assert [type(context.get("exception")) for context in reported] == [OSError]
    assert not globals_list.error_shown


def test_an_error_in_a_plain_callback_stops_the_program_in_the_browser(
    in_the_browser, caplog
):
    frames = []

    @play.repeat_forever
    def broken():
        frames.append(1)
        raise ValueError("typo in a plain callback")

    _run_page(in_the_browser, play.start_program)

    assert frames == [1]
    assert globals_list.error_shown
    assert caplog.text.count("ValueError: typo in a plain callback") == 1
    assert any(
        "Error in game_loop" in record.getMessage()
        and "ValueError: typo in a plain callback" in record.getMessage()
        for record in caplog.records
    )


def test_sounds_stop_once_the_program_has_stopped_in_the_browser(
    in_the_browser, monkeypatch
):
    states_when_stopped = []
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: (22050, -16, 2))
    monkeypatch.setattr(
        pygame.mixer,
        "stop",
        lambda: states_when_stopped.append(globals_list.program_state),
    )
    play.repeat_forever(_stop_after(3))

    _run_page(in_the_browser, play.start_program)

    assert states_when_stopped == [ProgramState.STOPPED]


def test_a_garbage_collection_does_not_end_the_program_in_the_browser(
    in_the_browser, monkeypatch
):
    states_when_sounds_stop = []
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: (22050, -16, 2))
    monkeypatch.setattr(
        pygame.mixer,
        "stop",
        lambda: states_when_sounds_stop.append(globals_list.program_state),
    )
    collected = []

    @play.repeat_forever
    def collect():
        collected.append(gc.collect())

    play.repeat_forever(_stop_after(3))

    _run_page(in_the_browser, play.start_program)

    assert len(collected) >= 2
    assert states_when_sounds_stop == [ProgramState.STOPPED]


def test_a_forgotten_await_gets_a_hint_in_the_browser(in_the_browser, caplog):
    @play.repeat_forever
    async def blink():
        play.timer(0.5)

    play.repeat_forever(_stop_after(10))

    with caplog.at_level(logging.WARNING, logger="play"):
        _run_page(in_the_browser, play.start_program)

    assert any("forgot" in record.getMessage() for record in caplog.records)


def test_a_top_level_await_does_not_start_the_program_early(in_the_browser):
    states = []
    main_py = _main_py(
        "play.repeat_forever(stop_after(3))\n"
        "await asyncio.sleep(0)\n"
        "states.append(globals_list.program_state)\n"
        "play.start_program()\n",
        states=states,
    )

    _run_page(in_the_browser, main_py)

    assert states == [ProgramState.NOT_STARTED]
    assert globals_list.program_state is ProgramState.STOPPED
    assert not globals_list.error_shown


def test_start_program_inside_an_async_main_is_ignored_after_auto_start(
    in_the_browser, caplog
):
    main_py = _main_py(
        "play.repeat_forever(stop_after(3))\n"
        "async def main():\n"
        "    play.start_program()\n"
        "asyncio.get_running_loop().create_task(main())\n"
    )

    _run_page(in_the_browser, main_py)

    assert globals_list.program_state is ProgramState.STOPPED
    assert "already started" not in caplog.text


def test_an_async_contact_callback_that_stops_the_program_goes_no_further(
    in_the_browser,
):
    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    ball = play.new_circle(y=-170, radius=10)
    ball.start_physics(bounciness=0)
    after_the_stop = []

    @ball.when_touching(floor)
    async def landed():
        play.stop_program()
        await play.animate()
        after_the_stop.append(1)

    _run_page(in_the_browser, play.start_program)

    assert globals_list.program_state is ProgramState.STOPPED
    assert after_the_stop == []


@pytest.mark.skipif(
    _UNDER_A_C_TRACER,
    reason="auto-start cannot see the script end under a C trace function, such as coverage's on 3.11",
)
def test_a_script_with_top_level_awaits_starts_once_it_ends(in_the_browser):
    states = []
    main_py = _main_py(
        "play.repeat_forever(stop_after(3))\n"
        "await asyncio.sleep(0)\n"
        "await asyncio.sleep(0)\n"
        "states.append(globals_list.program_state)\n",
        states=states,
    )

    _run_page(in_the_browser, main_py)

    assert states == [ProgramState.NOT_STARTED]
    assert globals_list.program_state is ProgramState.STOPPED


def test_a_second_start_program_in_the_browser_is_reported(in_the_browser, caplog):
    play.repeat_forever(_stop_after(3))

    def script():
        play.start_program()
        play.start_program()

    with caplog.at_level(logging.WARNING, logger="play"):
        _run_page(in_the_browser, script)

    assert "already started" in caplog.text


def test_a_debugger_still_sees_a_top_level_await_pause(in_the_browser):
    main_py = _main_py(
        "play.when_program_starts(lambda: None)\nawait asyncio.sleep(0)\n"
    )
    returns = []

    def local_trace(frame, event, _arg):
        if event == "return":
            returns.append(frame.f_code.co_name)
        return local_trace

    def debugger(frame, _event, _arg):
        return local_trace if frame.f_code is main_py.__code__ else None

    previous = sys.gettrace()
    sys.settrace(debugger)
    try:
        in_the_browser.run_until_complete(main_py())
    finally:
        sys.settrace(previous)

    assert returns == ["<module>", "<module>"]


def test_an_awaited_reset_in_the_browser_lets_play_s_tasks_end_then_a_new_program_runs(
    in_the_browser,
):
    ended = []
    frames = []

    @play.when_program_starts
    async def walk():
        try:
            while True:
                await play.animate()
        finally:
            ended.append("finally starts")
            for _ in range(5):
                await play.animate()
            ended.append("finally ends")

    async def page():
        play.start_program()
        for _ in range(5):
            await asyncio.sleep(0)
        await play.reset_program()
        ended.append("reset done")
        play.repeat_forever(_stop_after(3))
        play.repeat_forever(lambda: frames.append(1))
        play.start_program()
        await _until_only_the_page_is_left()

    in_the_browser.run_until_complete(page())

    assert ended == ["finally starts", "finally ends", "reset done"]
    assert frames == [1, 1, 1]


def test_a_reset_from_inside_the_program_in_the_browser_is_refused(in_the_browser):
    refused = []

    @play.repeat_forever
    def restart():
        try:
            play.reset_program()
        except RuntimeError as error:
            refused.append(str(error))
        play.stop_program()

    _run_page(in_the_browser, play.start_program)

    assert len(refused) == 1
    assert "inside a running play program" in refused[0]


@pytest.mark.skipif(
    _UNDER_A_C_TRACER,
    reason="auto-start cannot see the script end under a C trace function, such as coverage's on 3.11",
)
def test_a_playground_run_that_failed_before_starting_does_not_stop_the_next_from_starting(
    in_the_browser,
):
    frames = []
    failing_run = _main_py(
        "play.new_circle()\n"
        "play.when_program_starts(lambda: None)\n"
        "raise NameError('a typo after new_circle')\n"
    )
    names = {"frames": frames, "stop_after": _stop_after}
    code = compile(
        "play.repeat_forever(stop_after(3))\n"
        "play.repeat_forever(lambda: frames.append(1))\n",
        "main.py",
        "exec",
    )
    next_run = types.FunctionType(code, {"__name__": "__main__", "play": play, **names})

    async def page():
        with pytest.raises(NameError):
            failing_run()
        await play.reset_program()
        next_run()
        await _until_only_the_page_is_left()

    in_the_browser.run_until_complete(page())

    assert frames == [1, 1, 1]


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_a_task_that_will_not_end_in_the_browser_is_closed_quietly_and_the_next_program_runs(
    in_the_browser, monkeypatch, caplog
):
    monkeypatch.setattr(play.loop, "_SECONDS_TO_END", 0.05)
    frames = []

    @play.when_program_starts
    async def stubborn():
        while True:
            try:
                await play.timer(0.01)
            except BaseException:
                pass

    async def page():
        play.start_program()
        for _ in range(5):
            await asyncio.sleep(0)
        await play.reset_program()
        play.repeat_forever(_stop_after(3))
        play.repeat_forever(lambda: frames.append(1))
        play.start_program()
        for _ in range(20):
            await asyncio.sleep(0)

    with caplog.at_level(logging.INFO, logger="play"):
        in_the_browser.run_until_complete(page())

    assert frames == [1, 1, 1]
    assert not [r for r in caplog.records if r.levelno >= logging.INFO]


def test_a_task_closed_by_a_reset_in_the_browser_is_no_longer_one_of_play_s_tasks(
    in_the_browser, monkeypatch
):
    monkeypatch.setattr(play.loop, "_SECONDS_TO_END", 0.05)

    @play.when_program_starts
    async def slow_to_end():
        try:
            while True:
                await play.animate()
        finally:
            await play.timer(10)

    async def page():
        play.start_program()
        for _ in range(5):
            await asyncio.sleep(0)
        await play.reset_program()
        return set(play.loop._tasks)

    assert in_the_browser.run_until_complete(page()) == set()


def test_a_second_reset_while_the_first_is_ending_lets_the_finally_blocks_end(
    in_the_browser,
):
    ended = []

    @play.when_program_starts
    async def walk():
        try:
            while True:
                await play.animate()
        finally:
            ended.append("finally starts")
            for _ in range(5):
                await play.animate()
            ended.append("finally ends")

    async def page():
        play.start_program()
        for _ in range(5):
            await asyncio.sleep(0)
        first = play.reset_program()
        await asyncio.sleep(0)
        await play.reset_program()
        await first

    in_the_browser.run_until_complete(page())

    assert ended == ["finally starts", "finally ends"]


def test_a_stop_in_one_finally_does_not_cut_another_finally_short_during_a_reset(
    in_the_browser,
):
    ended = []

    @play.when_program_starts
    async def walk():
        try:
            while True:
                await play.animate()
        finally:
            ended.append("finally starts")
            for _ in range(5):
                await play.animate()
            ended.append("finally ends")

    @play.when_program_starts
    async def quitter():
        try:
            while True:
                await play.animate()
        finally:
            await play.animate()
            play.stop_program()

    async def page():
        play.start_program()
        for _ in range(5):
            await asyncio.sleep(0)
        await play.reset_program()

    in_the_browser.run_until_complete(page())

    assert ended == ["finally starts", "finally ends"]


def test_a_reset_the_page_gives_up_on_still_leaves_play_ready_for_the_next_program(
    in_the_browser,
):
    frames = []
    ended = []

    @play.when_program_starts
    async def slow_to_end():
        try:
            while True:
                await play.animate()
        finally:
            await play.timer(0.2)
            ended.append("old finally ends")

    async def page():
        play.start_program()
        await asyncio.sleep(0.05)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(play.reset_program(), 0.05)
        play.repeat_forever(_stop_after(3))
        play.repeat_forever(lambda: frames.append(1))
        play.start_program()
        await asyncio.sleep(0.3)

    in_the_browser.run_until_complete(page())

    assert frames == [1, 1, 1]
    assert not ended


def test_a_task_play_starts_while_a_reset_ends_a_running_program_is_cancelled_straight_away(
    in_the_browser,
):
    started = []

    async def late():
        started.append("late")

    @play.when_program_starts
    async def walk():
        try:
            while True:
                await play.animate()
        finally:
            play.loop.create_task(late())
            await play.animate()

    async def page():
        play.start_program()
        for _ in range(5):
            await asyncio.sleep(0)
        await play.reset_program()
        for _ in range(5):
            await asyncio.sleep(0)

    in_the_browser.run_until_complete(page())

    assert not started


def test_a_reset_left_unfinished_on_a_closed_page_does_not_block_the_next_program(
    in_the_browser, monkeypatch
):
    frames = []

    @play.when_program_starts
    async def slow_to_end():
        try:
            while True:
                await play.animate()
        finally:
            await play.timer(10)

    async def page():
        play.start_program()
        for _ in range(5):
            await asyncio.sleep(0)
        play.reset_program()
        for _ in range(5):
            await asyncio.sleep(0)

    in_the_browser.run_until_complete(page())
    in_the_browser.close()
    monkeypatch.setattr(play.loop, "RUNS_IN_BROWSER", False)
    monkeypatch.setattr(play.loop, "_loop", None)

    play.reset_program()
    play.repeat_forever(_stop_after(3))
    play.repeat_forever(lambda: frames.append(1))
    play.start_program()
    play.reset_program()

    assert frames == [1, 1, 1]


def test_starting_the_next_program_before_the_reset_is_done_is_refused(
    in_the_browser,
):
    frames = []

    async def page():
        play.repeat_forever(lambda: None)
        play.start_program()
        await asyncio.sleep(0)
        resetting = play.reset_program()
        with pytest.raises(RuntimeError, match="Await it"):
            play.start_program()
        await resetting
        play.repeat_forever(_stop_after(3))
        play.repeat_forever(lambda: frames.append(1))
        play.start_program()
        await _until_only_the_page_is_left()

    in_the_browser.run_until_complete(page())

    assert frames == [1, 1, 1]
