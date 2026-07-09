"""Global registry for the currently focused TextInput widget and Tab-order management."""

import pygame

from ..globals import globals_list
from ..io.keypress import keyboard_state


_tab_order = []  # All registered TextInput widgets in insertion order


def register(widget):
    """Add *widget* to the Tab order (called from TextInput.__init__)."""
    if widget not in _tab_order:
        _tab_order.append(widget)


def unregister(widget):
    """Remove *widget* from the Tab order (called from TextInput.remove)."""
    try:
        _tab_order.remove(widget)
    except ValueError:
        pass


def focus(widget):
    """Shift keyboard focus to *widget*, blurring whatever was focused before."""
    prev = globals_list.focused_text_input
    if prev is not None and prev is not widget:
        prev._is_focused = False
        prev._should_recompute = True
    globals_list.focused_text_input = widget
    widget._is_focused = True
    widget._should_recompute = True
    # Clear any keys held before focus so they don't fire game callbacks while
    # the user types (e.g. holding right-arrow then clicking into a TextInput).
    keyboard_state.pressed.clear()
    keyboard_state.pressed_this_frame.clear()
    pygame.key.start_text_input()


def clear_focus():
    """Remove keyboard focus from the currently focused TextInput (if any)."""
    widget = globals_list.focused_text_input
    if widget is not None:
        widget._is_focused = False
        widget._should_recompute = True
        globals_list.focused_text_input = None
        pygame.key.stop_text_input()


def focus_next():
    """Shift keyboard focus to the next TextInput in the Tab order.

    Cycles wrap around; if no widget is focused, focuses the first one."""
    visible = [w for w in _tab_order if w.alive() and not w._is_disabled]
    if not visible:
        clear_focus()
        return
    current = globals_list.focused_text_input
    if current is None or current not in visible:
        focus(visible[0])
        return
    idx = visible.index(current)
    focus(visible[(idx + 1) % len(visible)])


def dispatch_text(text):
    """Forward a TEXTINPUT event's text to the focused widget."""
    widget = globals_list.focused_text_input
    if widget is not None:
        widget._handle_text_input(text)


def dispatch_keydown(event):
    """Forward a KEYDOWN event to the focused widget (backspace, enter, escape, arrows, tab)."""
    widget = globals_list.focused_text_input
    if widget is not None:
        widget._handle_keydown(event)


def reset():
    """Clear the Tab order. Called from conftest between tests."""
    _tab_order.clear()
