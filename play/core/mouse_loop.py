"""This module contains the mouse loop."""

import pygame

from ..callback import callback_manager, CallbackType
from ..io.mouse import mouse
from ..io.screen import screen


class MouseState:
    """Class to manage the state of the mouse."""

    click_happened = False
    click_release_happened = False
    # Widget that exclusively claimed this frame's click (e.g. an open
    # dropdown menu overlapping other widgets), or None.
    click_owner = None
    # Widgets that may claim exclusive ownership of a click. Populated by
    # widgets that draw on top of others (an open Dropdown registers here).
    click_claimants = []

    def clear(self):
        """Clear the mouse state for the next frame."""
        self.click_happened = False
        self.click_release_happened = False
        self.click_owner = None

    def click_hits(self, sprite):
        """Whether *sprite* may respond to this frame's click.

        True when a click happened and no overlapping widget (such as an open
        dropdown menu) claimed it exclusively for itself."""
        return self.click_happened and (
            self.click_owner is None or self.click_owner is sprite
        )

    def resolve_click_owner(self):
        """Ask registered claimants whether the current click is theirs.

        Called once per MOUSEBUTTONDOWN; of the claimants whose open UI is
        under the mouse, the top-most one becomes the exclusive owner of this
        click."""
        self.click_claimants[:] = [w for w in self.click_claimants if w.alive()]
        claiming = [w for w in self.click_claimants if w._claims_click()]
        # Registration order says nothing about what is drawn on top, so pick
        # by layer rather than taking the first claimant.
        self.click_owner = max(claiming, key=lambda w: w._layer, default=None)


mouse_state = MouseState()


# pygame emits synthetic button 4/5 down+up pairs for wheel scrolling (kept for
# SDL1 compatibility). They are not clicks, and treating them as clicks lets a
# scroll toggle every widget it passes under the cursor.
_WHEEL_BUTTONS = (4, 5)


def handle_mouse_events(event):
    """Handle mouse events and update the mouse state."""
    if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        if getattr(event, "button", None) in _WHEEL_BUTTONS:
            return
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_state.click_happened = True
        mouse._is_clicked = True
        mouse_state.resolve_click_owner()
    if event.type == pygame.MOUSEBUTTONUP:
        mouse_state.click_release_happened = True
        mouse._is_clicked = False
    if event.type == pygame.MOUSEMOTION:
        mouse.x, mouse.y = (event.pos[0] - screen.width / 2.0), (
            screen.height / 2.0 - event.pos[1]
        )


async def handle_mouse_loop():
    """Handle mouse events in the game loop."""
    ####################################
    # @mouse.when_clicked callbacks
    ####################################
    if mouse_state.click_happened:
        callback_manager.run_callbacks(CallbackType.WHEN_CLICKED)

    ########################################
    # @mouse.when_click_released callbacks
    ########################################
    if mouse_state.click_release_happened:
        callback_manager.run_callbacks(CallbackType.WHEN_CLICK_RELEASED)

    ########################################
    # @mouse.while_pressed callbacks
    ########################################
    if mouse._is_clicked:
        callback_manager.run_callbacks(CallbackType.WHILE_MOUSE_PRESSED)
