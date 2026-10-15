"""Game functions and utilities."""

import asyncio as _asyncio
import logging as _logging
import os as _os

import pygame

from play.callback import callback_manager, CallbackType
from play.core import game_loop as _game_loop
from play import loop as _play_loop
from play.globals import globals_list, ProgramState
from play.io.keypress import keyboard_state
from play.loop import get_loop as _get_loop, stop_loop as _stop_loop
from play.physics import set_physics_simulation_steps as _set_physics_simulation_steps
from play.objects.video.video import close_all_videos as _close_all_videos
from play.utils import color_name_to_rgb as _color_name_to_rgb
from play.utils.async_helpers import hint_forgotten_awaits as _hint_forgotten_awaits


def start_program():
    """
    Calling this function starts your program running.

    play.start_program() should almost certainly go at the very end of your program.
    """
    if globals_list.program_state is not ProgramState.NOT_STARTED:
        raise RuntimeError(
            "You've already started the program! Calling play.start_program() "
            "twice can cause errors. Check to make sure it's only called once "
            "at the very bottom of your file."
        )

    globals_list.program_state = ProgramState.RUNNING
    globals_list.should_auto_start = False

    if _play_loop.RUNS_IN_BROWSER:
        _get_loop().create_task(
            _run_in_browser(), name=_play_loop.TASK_NAME_PREFIX + "start_program"
        )
        return

    try:
        with _hint_forgotten_awaits():
            _run_until_stopped(_start_then_loop())
    finally:
        _clean_up()
        if _os.getpid() == globals_list.initial_pid:
            pygame.quit()


async def _start_then_loop():
    """Run the when_program_starts callbacks, then start the frames."""
    callback_manager.run_callbacks(CallbackType.WHEN_PROGRAM_START)
    # The yield lets each callback set up before the first frame renders.
    await _asyncio.sleep(0)
    _play_loop.create_task(_game_loop())


async def _run_in_browser():
    """Run the program on the page's event loop, then stop its sounds once it has stopped."""
    with _hint_forgotten_awaits():
        await _start_then_loop()
        while not _program_has_stopped():
            await _asyncio.sleep(0)
    if pygame.mixer.get_init():
        pygame.mixer.stop()


def _clean_up():
    """Silence asyncio's shutdown messages and close any videos."""
    _logging.getLogger("asyncio").setLevel(_logging.CRITICAL)
    _close_all_videos()


def _program_has_stopped():
    """Whether play.stop_program() or an error has stopped the program."""
    return globals_list.program_state is ProgramState.STOPPED


def _run_until_stopped(start):
    """Run *start*, then frames until the program stops, also when it stops during *start*."""
    try:
        _get_loop().run_until_complete(start)
    except RuntimeError:
        if not _program_has_stopped():
            raise
    if not _program_has_stopped():
        _get_loop().run_forever()


def stop_program():
    """
    Calling this function stops your program running.

    play.stop_program() should almost certainly go at the very end of your program.
    """
    _stop_loop()


async def animate():
    """
    Wait for the next frame to be drawn.
    """
    await _asyncio.sleep(0)


def set_backdrop(color):
    """Set the backdrop color or image for the game.
    :param color: The color or image to set as the backdrop.
    """
    globals_list.backdrop = _color_name_to_rgb(color)
    globals_list.backdrop_type = "color"


def set_backdrop_image(image):
    """Set the backdrop image for the game.
    :param image: The image to set as the backdrop.
    """
    globals_list.backdrop = pygame.image.load(image)
    globals_list.backdrop_type = "image"


async def timer(seconds=1.0):
    """Wait a number of seconds. Used with the await keyword like this:
    :param seconds: The number of seconds to wait.
    :return: True after the number of seconds has passed.
    """
    await _asyncio.sleep(seconds)
    return True


def key_is_pressed(*keys):
    """
    Returns True if any of the given keys are pressed.

    Example:

        @play.repeat_forever
        async def do():
            if play.key_is_pressed('up', 'w'):
                print('up or w pressed')
    """
    for key in keys:
        if key in keyboard_state.pressed:
            return True
    return False


def set_physics_simulation_steps(num_steps: int) -> None:
    """
    Set the number of simulation steps for the physics engine.
    :param num_steps: The number of simulation steps.
    """
    _set_physics_simulation_steps(num_steps)


# Register start_program on globals_list so auto_start.py can call it without
# importing this module (which would create a cyclic import via play.core).
globals_list.start_program_fn = start_program
