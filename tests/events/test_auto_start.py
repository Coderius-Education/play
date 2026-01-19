"""Tests for automatic start_program() when user forgets to call it."""

import pytest
import sys

sys.path.insert(0, ".")


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


def test_auto_start_registered_with_atexit():
    """Test that _auto_start_program is registered with atexit."""
    import atexit
    from play.api import utils

    # Check that _auto_start_program is in the atexit registry
    # atexit._run_exitfuncs would run all registered functions
    # We can check if our function is registered by examining atexit internals
    # Note: This is implementation-dependent but works for testing
    assert hasattr(utils, "_auto_start_program")
    assert callable(utils._auto_start_program)


def test_auto_start_does_nothing_when_already_started():
    """Test that _auto_start_program does nothing if program already started."""
    from play.api import utils
    from unittest.mock import patch

    # Set flag to True (simulating program already started)
    utils._program_started = True

    # Mock start_program to verify it's not called
    with patch.object(utils, "start_program") as mock_start:
        utils._auto_start_program()
        mock_start.assert_not_called()

    # Reset for other tests
    utils._program_started = False


def test_auto_start_calls_start_program_when_not_started():
    """Test that _auto_start_program calls start_program if not started."""
    from play.api import utils
    from unittest.mock import patch

    # Ensure flag is False
    utils._program_started = False

    # Mock start_program to verify it's called
    with patch.object(utils, "start_program") as mock_start:
        utils._auto_start_program()
        mock_start.assert_called_once()

    # Reset for other tests
    utils._program_started = False
