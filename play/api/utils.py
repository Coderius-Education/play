"""Game functions and utilities."""

import asyncio as _asyncio
import logging as _logging
import os as _os

import pygame

from play.api.auto_start import _cleanup_auto_start, stop_waiting_for_the_script
from play.callback import callback_manager, CallbackType
from play.callback.collision_callbacks import collision_registry as _collision_registry
from play.core import game_loop as _game_loop
from play.core.controller_loop import controller_state as _controller_state
from play.core.mouse_loop import mouse_state as _mouse_state
from play.core.sprites_loop import _clicked_sprites
from play import loop as _play_loop
from play.globals import globals_list, ProgramState
from play.io.keypress import keyboard_state
from play.io.controllers import controllers as _controllers
from play.io.logging import play_logger
from play.io.mouse import mouse as _mouse
from play.io.screen import screen as _screen
from play.objects.widgets import text_input_registry as _text_input_registry
from play.physics import _reset_physics
from play.physics import set_physics_simulation_steps as _set_physics_simulation_steps
from play.objects.video.video import close_all_videos as _close_all_videos
from play.utils import color_name_to_rgb as _color_name_to_rgb
from play.utils.async_helpers import hint_forgotten_awaits as _hint_forgotten_awaits

_asyncio_logger = _logging.getLogger("asyncio")
_asyncio_log_level_before_the_program = None  # pylint: disable=invalid-name
_resets = set()


def start_program():
    """
    Calling this function starts your program running.

    play.start_program() should almost certainly go at the very end of your program.
    """
    if _resets:
        raise RuntimeError(
            "play.reset_program() has not finished yet. Await it before you "
            "start the next program: await play.reset_program()"
        )
    if (
        _play_loop.RUNS_IN_BROWSER
        and globals_list.program_state is ProgramState.RUNNING
    ):
        if not globals_list.started_by_auto_start:
            play_logger.warning(
                "You've already started the program! play.start_program() only "
                "needs to be called once, at the very bottom of your file."
            )
        return
    if globals_list.program_state is not ProgramState.NOT_STARTED:
        raise RuntimeError(
            "You've already started the program! Calling play.start_program() "
            "twice can cause errors. Check to make sure it's only called once "
            "at the very bottom of your file."
        )

    globals_list.program_state = ProgramState.RUNNING
    globals_list.should_auto_start = False
    stop_waiting_for_the_script()

    if _play_loop.RUNS_IN_BROWSER:
        _play_loop.create_task(_run_in_browser())
        return

    try:
        with _hint_forgotten_awaits():
            _run_until_stopped(_start_then_loop())
    finally:
        _quiet_the_asyncio_logger()
        _close_all_videos()
        if _os.getpid() == globals_list.initial_pid:
            pygame.quit()


def _quiet_the_asyncio_logger():
    """Silence asyncio's logger after a program, remembering its level for play.reset_program()."""
    global _asyncio_log_level_before_the_program
    if _asyncio_log_level_before_the_program is None:
        _asyncio_log_level_before_the_program = _asyncio_logger.level
    _asyncio_logger.setLevel(_logging.CRITICAL)


def _put_back_the_asyncio_logger():
    """Give asyncio's logger back the level it had before play silenced it."""
    global _asyncio_log_level_before_the_program
    if _asyncio_log_level_before_the_program is not None:
        _asyncio_logger.setLevel(_asyncio_log_level_before_the_program)
        _asyncio_log_level_before_the_program = None


async def _start_then_loop():
    """Run the when_program_starts callbacks, give each a turn to set up, then start the frames."""
    callback_manager.run_callbacks(CallbackType.WHEN_PROGRAM_START)
    await _asyncio.sleep(0)
    _play_loop.create_task(_game_loop())


async def _until_cancelled():
    """Wait until the task awaiting this is cancelled."""
    await _play_loop.get_loop().create_future()


async def _run_in_browser():
    """Run the program on the page's event loop until the program stops, then stop its sounds."""
    try:
        with _hint_forgotten_awaits():
            await _start_then_loop()
            await _until_cancelled()
    finally:
        if pygame.mixer.get_init():
            pygame.mixer.stop()


def _program_has_stopped():
    """Whether play.stop_program() or an error has stopped the program."""
    return globals_list.program_state is ProgramState.STOPPED


def _run_until_stopped(start):
    """Run *start*, then frames until the program stops, also when it stops during *start*."""
    try:
        _play_loop.get_loop().run_until_complete(start)
    except RuntimeError:
        if not _program_has_stopped():
            raise
    if not _program_has_stopped():
        _play_loop.get_loop().run_forever()


def stop_program():
    """
    Calling this function stops your program running.

    play.stop_program() should almost certainly go at the very end of your program.
    """
    _play_loop.stop_loop()


class _AlreadyReset:  # pylint: disable=too-few-public-methods
    """What play.reset_program() returns on the desktop: an awaitable that is already done."""

    def __await__(self):
        return iter(())


def reset_program():
    """Put play back into the state it has right after ``import play``, once play's tasks have ended.
    :return: An awaitable that is done once play is reset. In the browser, await it before the next program;
        on the desktop it is already done when reset_program() returns.
    :raises RuntimeError: When called from inside a running play program."""
    tasks = _play_loop.stop_for_reset()
    if not _play_loop.RUNS_IN_BROWSER:
        _play_loop.end_tasks_and_close_the_loop(tasks)
        _reset_state()
        return _AlreadyReset()
    resetting = _play_loop.get_loop().create_task(_reset_in_the_browser(tasks))
    _resets.add(resetting)
    resetting.add_done_callback(_resets.discard)
    return resetting


async def _reset_in_the_browser(tasks):
    """Let play's cancelled tasks end, then put play back into its starting state."""
    await _play_loop.end_tasks(tasks)
    _reset_state()


def _reset_state():
    """Put every part of play back into the state it has right after ``import play``."""
    _close_all_videos()
    pygame.init()
    if pygame.mixer.get_init():
        pygame.mixer.stop()
    _put_back_the_asyncio_logger()
    _text_input_registry.clear_focus()
    globals_list.reset()
    _clicked_sprites.clear()
    _cleanup_auto_start()
    stop_waiting_for_the_script()
    callback_manager.callbacks.clear()
    _collision_registry.reset()
    _text_input_registry.reset()
    _reset_physics()
    _screen._reset()
    _controllers._reconnect()
    keyboard_state.pressed.clear()
    keyboard_state.clear()
    _mouse_state.clear()
    _mouse_state.click_claimants.clear()
    _controller_state.buttons_pressed.clear()
    _mouse.x = _mouse.y = 0
    _mouse._is_clicked = False
    pygame.event.clear()


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
