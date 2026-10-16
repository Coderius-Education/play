"""In the browser, under pygbag, the page owns the event loop and keeps it running."""

import ast
import asyncio
import logging
import os
import subprocess
import sys
import textwrap
import types

import pygame
import pytest

import play
import play.loop
from play.api import auto_start
from play.globals import ProgramState, globals_list


@pytest.fixture
def in_the_browser(monkeypatch):
    monkeypatch.setattr(play.loop, "RUNS_IN_BROWSER", True)
    monkeypatch.setattr(play.loop, "_loop", None)
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


def test_an_error_in_a_page_task_leaves_the_program_running(in_the_browser):
    async def pages_own_task():
        raise OSError("the page's own task failed")

    def script():
        play.start_program()
        asyncio.get_running_loop().create_task(pages_own_task())

    play.repeat_forever(_stop_after(20))

    _run_page(in_the_browser, script)

    assert not globals_list.error_shown


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


def test_play_loop_works_where_asyncio_tasks_is_not_the_module_as_in_pygbag():
    script = textwrap.dedent("""
        import asyncio
        asyncio.tasks = []
        import play.loop as loop
        loop._HAS_EAGER_TASK_FACTORY = False

        async def callback():
            await asyncio.sleep(0)
            return "done"

        async def frame():
            task = loop.start_task(callback())
            loop._handle_exception(
                loop.get_loop(), {"message": loop._DESTROYED_PENDING, "task": task}
            )
            return await task

        print(loop.get_loop().run_until_complete(frame()))
        """)
    root = os.path.dirname(os.path.dirname(os.path.abspath(play.__file__)))
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": root, "PYGAME_HIDE_SUPPORT_PROMPT": "1"},
        check=False,
    )

    assert result.stdout.split() == ["done"], result.stderr
