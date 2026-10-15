"""In the browser (pygbag, Pyodide) the page owns the event loop and keeps it running."""

import asyncio

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
        while len(asyncio.all_tasks()) > 1:
            await asyncio.sleep(0)

    page_loop.run_until_complete(page())


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
