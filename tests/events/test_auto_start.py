"""Tests for auto-starting when user forgets to call play.start_program()."""

import subprocess
import sys
from unittest.mock import patch


def test_auto_start_flag_set_by_callback():
    """Test that adding a callback sets _should_auto_start."""
    from play.api import utils
    from play.callback import callback_manager, CallbackType

    async def dummy():
        pass

    callback_manager.add_callback(CallbackType.WHEN_PROGRAM_START, dummy)
    assert utils._should_auto_start is True


def test_auto_start_flag_set_by_sprite():
    """Test that creating a real Sprite subclass sets _should_auto_start."""
    from play.api import utils
    from play.globals import globals_list
    import play

    box = play.new_box()

    assert utils._should_auto_start is True

    box.remove()


def test_schedule_installs_trace_on_main_frame():
    """Test that _schedule_auto_start installs a frame trace."""
    from play.api import utils

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


def test_schedule_preserves_existing_trace():
    """Test that _schedule_auto_start preserves an existing sys.settrace."""
    from play.api import utils

    real_original_trace = sys.gettrace()  # capture real trace (e.g. pytest-cov) first
    custom_trace = lambda frame, event, arg: custom_trace  # noqa: E731
    sys.settrace(custom_trace)

    utils._schedule_auto_start()

    # The global trace should still be the custom one (preserved, not replaced)
    assert sys.gettrace() is custom_trace

    # Clean up — restore real original trace so coverage tools are not disrupted
    sys.settrace(real_original_trace)


def test_start_program_clears_auto_start_flag():
    """Test that start_program() clears _should_auto_start."""
    from play.api import utils

    utils._should_auto_start = True

    with patch.object(utils, "_get_loop"):
        utils.start_program()

    assert utils._should_auto_start is False


def test_auto_start_end_to_end():
    """End-to-end test: a script with a callback but no start_program() should auto-start."""
    script = (
        "import os, play\n"
        "os.environ['SDL_VIDEODRIVER'] = 'dummy'\n"
        "os.environ['SDL_AUDIODRIVER'] = 'dummy'\n"
        "@play.when_program_starts\n"
        "async def on_start():\n"
        "    os._exit(0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        timeout=10,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr.decode()
