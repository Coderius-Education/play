"""Global registry for the currently focused TextInput widget."""

import pygame

from ..globals import globals_list


def focus(widget):
    """Shift keyboard focus to *widget*, blurring whatever was focused before."""
    prev = globals_list.focused_text_input
    if prev is not None and prev is not widget:
        prev._is_focused = False
        prev._should_recompute = True
    globals_list.focused_text_input = widget
    widget._is_focused = True
    widget._should_recompute = True
    pygame.key.start_text_input()


def clear_focus():
    """Remove keyboard focus from the currently focused TextInput (if any)."""
    widget = globals_list.focused_text_input
    if widget is not None:
        widget._is_focused = False
        widget._should_recompute = True
        globals_list.focused_text_input = None
        pygame.key.stop_text_input()


def dispatch_text(text):
    """Forward a TEXTINPUT event's text to the focused widget."""
    widget = globals_list.focused_text_input
    if widget is not None:
        widget._handle_text_input(text)


def dispatch_keydown(event):
    """Forward a KEYDOWN event to the focused widget (backspace, enter, escape)."""
    widget = globals_list.focused_text_input
    if widget is not None:
        widget._handle_keydown(event)
