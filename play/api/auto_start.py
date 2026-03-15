"""Auto-start logic for running the game loop when the user forgets start_program()."""

import sys as _sys

from ..callback import callback_manager
from ..globals import globals_list
from ..utils import run_once as _run_once


def _make_main_return_trace(existing_trace, existing_f_trace):
    """Create a frame-trace function for the __main__ frame.

    Fires start_program() when the frame returns, then restores the previous
    global trace. Wraps any existing frame trace so debuggers/coverage survive.
    """

    def _on_main_return(_frame, event, _arg):  # pylint: disable=unused-argument
        if event == "return":
            if globals_list.should_auto_start and not globals_list.program_started:
                from .utils import (  # pylint: disable=import-outside-toplevel
                    start_program,
                )

                try:
                    start_program()
                except RuntimeError as exc:
                    if "already started" not in str(exc):
                        raise
            if existing_trace is None:
                _sys.settrace(None)
            if existing_f_trace is not None:
                existing_f_trace(_frame, event, _arg)
            return None  # CPython ignores the return value on 'return' events
        if event == "exception":
            # An unhandled exception is propagating through __main__ — don't
            # auto-start since the script has crashed.  Clean up the trace and
            # pass the event to any existing tracer.
            if existing_trace is None:
                _sys.settrace(None)
            if existing_f_trace is not None:
                return existing_f_trace(_frame, event, _arg)
            return None
        # Return value of existing_f_trace is intentionally discarded: we
        # always keep _on_main_return as the local trace so we can detect
        # the 'return' event.  In practice, coverage tools (e.g. pytest-cov)
        # return themselves, so they are not disrupted.
        if existing_f_trace is not None:
            existing_f_trace(_frame, event, _arg)
        return _on_main_return

    return _on_main_return


@_run_once
def _schedule_auto_start():
    """Set up auto-start when the user's script finishes.

    Walks the call stack to find the __main__ frame and installs a trace
    that fires start_program() when that frame returns. This runs on the
    main thread before the interpreter shutdown — required for pygame on Windows.

    Preserves any existing sys.settrace (debuggers, coverage, etc.) by
    wrapping the frame trace instead of replacing the global trace.
    """
    globals_list.should_auto_start = True

    # CPython-specific: _getframe() is an implementation detail but fine here
    # since pygame targets CPython.
    frame = _sys._getframe()  # pylint: disable=protected-access
    while frame is not None:
        if frame.f_globals.get("__name__") == "__main__":
            existing_trace = _sys.gettrace()
            if existing_trace is None:
                _sys.settrace(lambda *_args: None)
            frame.f_trace = _make_main_return_trace(existing_trace, frame.f_trace)
            frame.f_trace_lines = False
            break
        frame = frame.f_back
    # If no __main__ frame was found (e.g. interactive REPL, embedded context),
    # should_auto_start is True but no trace is installed — start_program()
    # won't fire automatically and the user must call it explicitly.


callback_manager.on_first_callback = _schedule_auto_start


def _cleanup_auto_start():
    """Reset all auto-start state and remove any installed frame trace.

    Used by test fixtures to prevent state leakage between tests.
    """
    globals_list.program_started = False
    globals_list.should_auto_start = False
    _schedule_auto_start.has_run = False
    callback_manager.on_first_callback = _schedule_auto_start

    frame = _sys._getframe()  # pylint: disable=protected-access
    while frame is not None:
        if frame.f_globals.get("__name__") == "__main__":
            frame.f_trace = None
            break
        frame = frame.f_back
