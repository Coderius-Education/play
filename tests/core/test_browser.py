"""In the browser, under pygbag, the page owns the event loop and keeps it running."""

import ast
import asyncio
import logging
import sys
import types

import pygame
import pytest

import play
import play.loop
from play.globals import globals_list


@pytest.fixture
def in_the_browser(monkeypatch):
    monkeypatch.setattr(play.loop, "RUNS_IN_BROWSER", True)
    monkeypatch.setattr(play.loop, "_loop", None)
    page_loop = asyncio.new_event_loop()
    yield page_loop
    page_loop.close()


def _run_page(page_loop, script):
    async def page():
        script()
        await _until_only_the_page_is_left()

    page_loop.run_until_complete(page())


async def _until_only_the_page_is_left(steps=1000):
    for _ in range(steps):
        if len(asyncio.all_tasks()) == 1:
            return
        await asyncio.sleep(0)


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


def test_an_error_stops_the_program_in_the_browser(in_the_browser, capsys):
    frames = []

    @play.repeat_forever
    async def broken():
        frames.append(1)
        raise ValueError("typo in the browser")

    _run_page(in_the_browser, play.start_program)

    assert frames == [1]
    assert globals_list.error_shown
    assert capsys.readouterr().err.count("ValueError: typo in the browser") == 1


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


def _stop_after(frames):
    counted = []

    def count():
        counted.append(1)
        if len(counted) == frames:
            play.stop_program()

    return count


def test_an_error_in_a_page_task_leaves_the_program_running(in_the_browser):
    async def pages_own_task():
        raise OSError("the page's own task failed")

    def script():
        play.start_program()
        asyncio.get_running_loop().create_task(pages_own_task())

    play.repeat_forever(_stop_after(20))

    _run_page(in_the_browser, script)

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

    assert states_when_stopped == [play.globals.ProgramState.STOPPED]


def test_a_forgotten_await_gets_a_hint_in_the_browser(in_the_browser, caplog):
    @play.repeat_forever
    async def blink():
        play.timer(0.5)

    play.repeat_forever(_stop_after(10))

    with caplog.at_level(logging.WARNING, logger="play"):
        _run_page(in_the_browser, play.start_program)

    assert any("forgot" in record.getMessage() for record in caplog.records)


def test_a_top_level_await_does_not_start_the_program_early(in_the_browser):
    script = compile(
        "play.repeat_forever(stop_after(3))\n"
        "await asyncio.sleep(0)\n"
        "play.start_program()\n",
        "main.py",
        "exec",
        flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
    )
    main = {
        "__name__": "__main__",
        "asyncio": asyncio,
        "play": play,
        "stop_after": _stop_after,
    }
    play.api.auto_start._schedule_auto_start.has_run = False

    async def page():
        await types.FunctionType(script, main)()
        await _until_only_the_page_is_left()

    in_the_browser.run_until_complete(page())

    assert globals_list.program_state is play.globals.ProgramState.STOPPED
    assert not globals_list.error_shown


def test_start_program_inside_an_async_main_is_ignored_after_auto_start(
    in_the_browser, caplog
):
    script = compile(
        "play.repeat_forever(stop_after(3))\n"
        "async def main():\n"
        "    play.start_program()\n"
        "asyncio.get_running_loop().create_task(main())\n",
        "main.py",
        "exec",
        flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
    )
    main = {
        "__name__": "__main__",
        "asyncio": asyncio,
        "play": play,
        "stop_after": _stop_after,
    }
    play.api.auto_start._schedule_auto_start.has_run = False

    async def page():
        types.FunctionType(script, main)()
        await _until_only_the_page_is_left()

    in_the_browser.run_until_complete(page())

    assert globals_list.program_state is play.globals.ProgramState.STOPPED
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

    assert globals_list.program_state is play.globals.ProgramState.STOPPED
    assert after_the_stop == []


def test_a_script_with_top_level_awaits_starts_once_it_ends(in_the_browser):
    script = compile(
        "play.repeat_forever(stop_after(3))\n"
        "await asyncio.sleep(0)\n"
        "await asyncio.sleep(0)\n",
        "main.py",
        "exec",
        flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
    )
    main = {
        "__name__": "__main__",
        "asyncio": asyncio,
        "play": play,
        "stop_after": _stop_after,
    }
    play.api.auto_start.stop_waiting_for_the_script()
    play.api.auto_start._schedule_auto_start.has_run = False

    async def page():
        await types.FunctionType(script, main)()
        await _until_only_the_page_is_left()

    in_the_browser.run_until_complete(page())

    assert globals_list.program_state is play.globals.ProgramState.STOPPED


def test_a_second_start_program_in_the_browser_is_reported(in_the_browser, caplog):
    play.repeat_forever(_stop_after(3))

    def script():
        play.start_program()
        play.start_program()

    with caplog.at_level(logging.WARNING, logger="play"):
        _run_page(in_the_browser, script)

    assert "already started" in caplog.text


def test_a_debugger_still_sees_a_top_level_await_pause(in_the_browser):
    script = compile(
        "play.when_program_starts(lambda: None)\nawait asyncio.sleep(0)\n",
        "main.py",
        "exec",
        flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
    )
    main = {"__name__": "__main__", "asyncio": asyncio, "play": play}
    returns = []

    def local_trace(frame, event, _arg):
        if event == "return":
            returns.append(frame.f_code.co_name)
        return local_trace

    def debugger(frame, _event, _arg):
        return local_trace if frame.f_code is script else None

    play.api.auto_start.stop_waiting_for_the_script()
    play.api.auto_start._schedule_auto_start.has_run = False
    previous = sys.gettrace()
    sys.settrace(debugger)
    try:
        in_the_browser.run_until_complete(types.FunctionType(script, main)())
    finally:
        sys.settrace(previous)

    assert returns == ["<module>", "<module>"]
