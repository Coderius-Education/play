"""Game functions and utilities."""

import asyncio as _asyncio
import logging as _logging
import os as _os
import threading as _threading

import pygame

from ..callback import callback_manager, CallbackType
from ..core import game_loop as _game_loop
from ..globals import globals_list
from ..io.keypress import keyboard_state
from ..loop import get_loop as _get_loop
from ..physics import set_physics_simulation_steps as _set_physics_simulation_steps
from ..utils import color_name_to_rgb as _color_name_to_rgb

_program_started = False  # pylint: disable=invalid-name
_initial_pid = _os.getpid()  # pylint: disable=invalid-name
_warn_timer = None  # pylint: disable=invalid-name


def _warn_if_not_started():
    """Print a warning if the user forgot to call play.start_program()."""
    if not _program_started:
        print(
            "\nWARNING: It looks like you forgot to call play.start_program() at the end "
            "of your program.\nAdd this line at the very bottom of your file:\n\n"
            "    play.start_program()\n"
        )


def _schedule_start_program_warning():
    """Schedule a delayed warning check. Called when callbacks or sprites are registered."""
    global _warn_timer
    if _program_started or _warn_timer is not None:
        return
    _warn_timer = _threading.Timer(0.5, _warn_if_not_started)
    _warn_timer.start()


def _cancel_warning():
    """Cancel the pending warning timer."""
    global _warn_timer
    if _warn_timer is not None:
        _warn_timer.cancel()
        _warn_timer = None


callback_manager.on_first_callback = _schedule_start_program_warning
globals_list.on_first_sprite = _schedule_start_program_warning


def start_program():
    """
    Calling this function starts your program running.

    play.start_program() should almost certainly go at the very end of your program.
    """
    global _program_started
    if _program_started:
        raise RuntimeError(
            "You've already started the program! Calling play.start_program() "
            "twice can cause errors. Check to make sure it's only called once "
            "at the very bottom of your file."
        )

    _program_started = True
    _cancel_warning()
    callback_manager.run_callbacks(CallbackType.WHEN_PROGRAM_START)

    _get_loop().create_task(_game_loop())
    try:
        _get_loop().run_forever()
    finally:
        logger = _logging.getLogger("asyncio")
        logger.setLevel(_logging.CRITICAL)
        if _os.getpid() == _initial_pid:
            pygame.quit()


def stop_program():
    """
    Calling this function stops your program running.

    play.stop_program() should almost certainly go at the very end of your program.
    """
    _get_loop().stop()
    if _os.getpid() == _initial_pid:
        pygame.display.quit()
        pygame.quit()


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
