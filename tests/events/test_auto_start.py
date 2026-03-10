"""Tests for auto-starting when user forgets to call play.start_program()."""

import sys
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
    """Test that creating a real Sprite subclass sets _should_auto_start."""
    from play.api import utils
    from play.globals import globals_list
    import play

    utils._program_started = False
    utils._should_auto_start = False
    globals_list.on_first_sprite = utils._schedule_auto_start

    box = play.new_box()

    assert utils._should_auto_start is True
    assert globals_list.on_first_sprite is None

    box.remove()
    globals_list.on_first_sprite = utils._schedule_auto_start
    utils._should_auto_start = False
    utils._program_started = False


def test_schedule_installs_trace_on_main_frame():
    """Test that _schedule_auto_start installs a frame trace."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = False

    # Save and clear the real trace (e.g. pytest-cov) to get a known-None baseline
    # so the assertion below is meaningful rather than trivially true.
    real_trace = sys.gettrace()
    sys.settrace(None)
    original_trace = sys.gettrace()  # now guaranteed None

    # Call from a function whose caller is __main__ (this test module)
    utils._schedule_auto_start()

    assert utils._should_auto_start is True
    # A new global trace was installed (original_trace is None, so this is a strict check)
    assert sys.gettrace() is not original_trace
    # Clean up — restore real trace so coverage tools are not disrupted
    sys.settrace(real_trace)
    utils._should_auto_start = False
    utils._program_started = False


def test_schedule_preserves_existing_trace():
    """Test that _schedule_auto_start preserves an existing sys.settrace."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = False

    real_original_trace = sys.gettrace()  # capture real trace (e.g. pytest-cov) first
    custom_trace = lambda frame, event, arg: custom_trace  # noqa: E731
    sys.settrace(custom_trace)

    utils._schedule_auto_start()

    # The global trace should still be the custom one (preserved, not replaced)
    assert sys.gettrace() is custom_trace

    # Clean up — restore real original trace so coverage tools are not disrupted
    sys.settrace(real_original_trace)
    utils._should_auto_start = False
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
