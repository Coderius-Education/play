"""Tests for auto-starting when user forgets to call play.start_program()."""

from unittest.mock import patch


def test_auto_start_flag_set_by_callback():
    """Test that adding a callback sets _should_auto_start."""
    from play.api import utils
    from play.callback import callback_manager, CallbackType

    utils._program_started = False
    utils._should_auto_start = False
    callback_manager.on_first_callback = utils._schedule_auto_start

    async def dummy():
        pass

    callback_manager.add_callback(CallbackType.WHEN_PROGRAM_START, dummy)
    assert utils._should_auto_start is True
    assert callback_manager.on_first_callback is None

    callback_manager.remove_callbacks(CallbackType.WHEN_PROGRAM_START)
    callback_manager.on_first_callback = utils._schedule_auto_start
    utils._should_auto_start = False
    utils._program_started = False


def test_auto_start_flag_set_by_sprite():
    """Test that creating a sprite sets _should_auto_start."""
    from play.api import utils
    from play.globals import globals_list
    import pygame

    utils._program_started = False
    utils._should_auto_start = False
    globals_list.on_first_sprite = utils._schedule_auto_start

    sprite = pygame.sprite.Sprite()
    globals_list.sprites_group.add(sprite)
    if globals_list.on_first_sprite is not None:
        globals_list.on_first_sprite()
        globals_list.on_first_sprite = None

    assert utils._should_auto_start is True

    sprite.kill()
    globals_list.on_first_sprite = utils._schedule_auto_start
    utils._should_auto_start = False
    utils._program_started = False


def test_auto_start_calls_start_program():
    """Test that _auto_start_if_needed calls start_program when flag is set."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = True

    with patch.object(utils, "start_program") as mock_start:
        utils._auto_start_if_needed()
        mock_start.assert_called_once()

    utils._should_auto_start = False
    utils._program_started = False


def test_auto_start_skipped_when_already_started():
    """Test that _auto_start_if_needed does nothing if already started."""
    from play.api import utils

    utils._program_started = True
    utils._should_auto_start = True

    with patch.object(utils, "start_program") as mock_start:
        utils._auto_start_if_needed()
        mock_start.assert_not_called()

    utils._should_auto_start = False
    utils._program_started = False


def test_auto_start_skipped_when_flag_not_set():
    """Test that _auto_start_if_needed does nothing if no callbacks/sprites were registered."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = False

    with patch.object(utils, "start_program") as mock_start:
        utils._auto_start_if_needed()
        mock_start.assert_not_called()

    utils._program_started = False


def test_start_program_clears_auto_start_flag():
    """Test that start_program() clears _should_auto_start."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = True

    with patch.object(utils, "_get_loop"):
        utils.start_program()

    assert utils._should_auto_start is False

    utils._program_started = False
