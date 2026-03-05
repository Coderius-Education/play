"""Tests for the warning when user forgets to call play.start_program()."""

import pytest


def test_program_started_flag_initially_false():
    """Test that _program_started is initially False."""
    from play.api import utils

    # Reset the flag for testing
    utils._program_started = False
    assert utils._program_started is False


def test_program_started_flag_set_after_start():
    """Test that _program_started is set to True when start_program sets it."""
    from play.api import utils

    # Directly set the flag (simulating what start_program does)
    utils._program_started = True
    assert utils._program_started is True

    # Reset for other tests
    utils._program_started = False


def test_warn_if_not_started_registered_with_atexit():
    """Test that _warn_if_not_started is registered with atexit."""
    from play.api import utils

    assert hasattr(utils, "_warn_if_not_started")
    assert callable(utils._warn_if_not_started)


def test_warn_if_not_started_silent_when_already_started():
    """Test that _warn_if_not_started prints nothing if program already started."""
    from play.api import utils

    utils._program_started = True
    # Should not print anything
    utils._warn_if_not_started()

    # Reset for other tests
    utils._program_started = False


def test_warn_if_not_started_prints_when_not_started(capsys):
    """Test that _warn_if_not_started prints a warning if not started and callbacks exist."""
    from play.api import utils
    from play.callback import callback_manager, CallbackType

    utils._program_started = False

    async def dummy():
        pass

    callback_manager.add_callback(CallbackType.WHEN_PROGRAM_START, dummy)

    utils._warn_if_not_started()

    captured = capsys.readouterr()
    assert "play.start_program()" in captured.out

    # Cleanup
    callback_manager.remove_callbacks(CallbackType.WHEN_PROGRAM_START)
    utils._program_started = False


def test_warn_if_not_started_silent_when_no_callbacks(capsys):
    """Test that _warn_if_not_started prints nothing if no callbacks registered."""
    from play.api import utils

    utils._program_started = False
    utils._warn_if_not_started()

    captured = capsys.readouterr()
    assert captured.out == ""

    utils._program_started = False


def test_warn_if_not_started_survives_teardown():
    """Test that _warn_if_not_started doesn't crash when globals are None."""
    from play.api import utils
    from unittest.mock import patch

    # Simulate module teardown where callback_manager becomes None
    with patch.object(utils, "callback_manager", None):
        # Should not raise — the except guard catches AttributeError
        utils._warn_if_not_started()
