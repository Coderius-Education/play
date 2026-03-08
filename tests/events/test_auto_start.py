"""Tests for auto-starting when user forgets to call play.start_program()."""

from unittest.mock import patch


def test_schedule_auto_start_creates_thread():
    """Test that _schedule_auto_start creates a background thread."""
    from play.api import utils

    utils._program_started = False
    utils._auto_start_thread = None

    utils._schedule_auto_start()
    assert utils._auto_start_thread is not None

    utils._cancel_auto_start()
    utils._program_started = False


def test_schedule_auto_start_skipped_when_already_started():
    """Test that _schedule_auto_start does nothing if already started."""
    from play.api import utils

    utils._program_started = True
    utils._auto_start_thread = None

    utils._schedule_auto_start()
    assert utils._auto_start_thread is None

    utils._program_started = False


def test_schedule_auto_start_not_duplicated():
    """Test that _schedule_auto_start only creates one thread."""
    from play.api import utils

    utils._program_started = False
    utils._auto_start_thread = None

    utils._schedule_auto_start()
    first_thread = utils._auto_start_thread
    utils._schedule_auto_start()
    assert utils._auto_start_thread is first_thread

    utils._cancel_auto_start()
    utils._program_started = False


def test_start_program_cancels_auto_start():
    """Test that start_program() clears the auto-start thread reference."""
    from play.api import utils

    utils._program_started = False
    utils._auto_start_thread = None

    utils._schedule_auto_start()
    assert utils._auto_start_thread is not None

    with patch.object(utils, "_get_loop"):
        utils.start_program()

    assert utils._auto_start_thread is None

    utils._program_started = False


def test_callback_triggers_auto_start_schedule():
    """Test that adding a callback triggers the auto-start schedule."""
    from play.api import utils
    from play.callback import callback_manager, CallbackType

    utils._program_started = False
    utils._auto_start_thread = None
    callback_manager.on_first_callback = utils._schedule_auto_start

    async def dummy():
        pass

    callback_manager.add_callback(CallbackType.WHEN_PROGRAM_START, dummy)
    assert utils._auto_start_thread is not None
    assert callback_manager.on_first_callback is None

    utils._cancel_auto_start()
    callback_manager.remove_callbacks(CallbackType.WHEN_PROGRAM_START)
    callback_manager.on_first_callback = utils._schedule_auto_start
    utils._program_started = False


def test_sprite_triggers_auto_start_schedule():
    """Test that creating a sprite triggers the auto-start schedule."""
    from play.api import utils
    from play.globals import globals_list
    import pygame

    utils._program_started = False
    utils._auto_start_thread = None
    globals_list.on_first_sprite = utils._schedule_auto_start

    sprite = pygame.sprite.Sprite()
    globals_list.sprites_group.add(sprite)
    if globals_list.on_first_sprite is not None:
        globals_list.on_first_sprite()
        globals_list.on_first_sprite = None

    assert utils._auto_start_thread is not None

    utils._cancel_auto_start()
    sprite.kill()
    globals_list.on_first_sprite = utils._schedule_auto_start
    utils._program_started = False
