"""Tests for the warning when user forgets to call play.start_program()."""

import time
from unittest.mock import patch


def test_warn_if_not_started_prints_warning(capsys):
    """Test that _warn_if_not_started prints a warning if not started."""
    from play.api import utils

    utils._program_started = False
    utils._warn_if_not_started()

    captured = capsys.readouterr()
    assert "play.start_program()" in captured.out

    utils._program_started = False


def test_warn_if_not_started_silent_when_already_started(capsys):
    """Test that _warn_if_not_started prints nothing if program already started."""
    from play.api import utils

    utils._program_started = True
    utils._warn_if_not_started()

    captured = capsys.readouterr()
    assert captured.out == ""

    utils._program_started = False


def test_schedule_warning_sets_timer():
    """Test that schedule_start_program_warning creates a timer."""
    from play.api import utils

    utils._program_started = False
    utils._warn_timer = None

    utils.schedule_start_program_warning()
    assert utils._warn_timer is not None

    utils._cancel_warning()
    utils._program_started = False


def test_schedule_warning_skipped_when_already_started():
    """Test that schedule_start_program_warning does nothing if already started."""
    from play.api import utils

    utils._program_started = True
    utils._warn_timer = None

    utils.schedule_start_program_warning()
    assert utils._warn_timer is None

    utils._program_started = False


def test_schedule_warning_not_duplicated():
    """Test that schedule_start_program_warning only creates one timer."""
    from play.api import utils

    utils._program_started = False
    utils._warn_timer = None

    utils.schedule_start_program_warning()
    first_timer = utils._warn_timer
    utils.schedule_start_program_warning()
    assert utils._warn_timer is first_timer

    utils._cancel_warning()
    utils._program_started = False


def test_start_program_cancels_warning():
    """Test that start_program() cancels a pending warning timer."""
    from play.api import utils

    utils._program_started = False
    utils._warn_timer = None

    utils.schedule_start_program_warning()
    assert utils._warn_timer is not None

    with patch.object(utils, "_get_loop"):
        utils.start_program()

    assert utils._warn_timer is None

    utils._program_started = False


def test_warning_fires_after_delay(capsys):
    """Test that the warning actually prints after the timer fires."""
    from play.api import utils

    utils._program_started = False
    utils._warn_timer = None

    utils.schedule_start_program_warning()
    utils._warn_timer.join(timeout=2.0)

    captured = capsys.readouterr()
    assert "play.start_program()" in captured.out

    utils._warn_timer = None
    utils._program_started = False


def test_warning_suppressed_when_start_program_called_before_delay():
    """Test that start_program() prevents the warning from printing."""
    from play.api import utils
    import io
    from contextlib import redirect_stdout

    utils._program_started = False
    utils._warn_timer = None

    utils.schedule_start_program_warning()

    with patch.object(utils, "_get_loop"):
        utils.start_program()

    # Wait long enough for the timer to have fired (if it wasn't cancelled)
    time.sleep(0.7)

    f = io.StringIO()
    with redirect_stdout(f):
        pass  # nothing should have printed
    assert "play.start_program()" not in f.getvalue()

    utils._program_started = False


def test_callback_triggers_warning_schedule():
    """Test that adding a callback triggers the warning schedule."""
    from play.api import utils
    from play.callback import callback_manager, CallbackType

    utils._program_started = False
    utils._warn_timer = None
    callback_manager.on_first_callback = utils.schedule_start_program_warning

    async def dummy():
        pass

    callback_manager.add_callback(CallbackType.WHEN_PROGRAM_START, dummy)
    assert utils._warn_timer is not None
    assert callback_manager.on_first_callback is None

    utils._cancel_warning()
    callback_manager.remove_callbacks(CallbackType.WHEN_PROGRAM_START)
    callback_manager.on_first_callback = utils.schedule_start_program_warning
    utils._program_started = False


def test_sprite_triggers_warning_schedule():
    """Test that creating a sprite triggers the warning schedule."""
    from play.api import utils
    from play.globals import globals_list
    import pygame

    utils._program_started = False
    utils._warn_timer = None
    globals_list.on_first_sprite = utils.schedule_start_program_warning

    sprite = pygame.sprite.Sprite()
    globals_list.sprites_group.add(sprite)
    if globals_list.on_first_sprite is not None:
        globals_list.on_first_sprite()
        globals_list.on_first_sprite = None

    assert utils._warn_timer is not None

    utils._cancel_warning()
    sprite.kill()
    globals_list.on_first_sprite = utils.schedule_start_program_warning
    utils._program_started = False
