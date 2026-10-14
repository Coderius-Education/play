"""This module contains the mouse loop."""

import pygame

from play.callback import callback_manager, CallbackType
from play.globals import globals_list
from play.io.mouse import mouse
from play.io.screen import screen


class MouseState:
    """Class to manage the state of the mouse."""

    click_happened = False
    click_release_happened = False
    # Widget that exclusively claimed this frame's click (e.g. an open
    # dropdown menu overlapping other widgets), or None.
    click_owner = None
    sprites_above_owner = frozenset()
    # Widgets that may claim exclusive ownership of a click. Populated by
    # widgets that draw on top of others (an open Dropdown registers here).
    click_claimants = []
    # Monotonic id for the current click; see Widget._claim_click().
    click_id = 0

    def clear(self):
        """Clear the mouse state for the next frame."""
        self.click_happened = False
        self.click_release_happened = False
        self.click_owner = None
        self.sprites_above_owner = set()

    def click_hits(self, sprite):
        """Whether *sprite* may respond to this frame's click.

        True when a click happened and no overlapping widget (such as an open
        dropdown menu) claimed it exclusively for itself."""
        return self.click_happened and (
            self.click_owner is None
            or self.click_owner is sprite
            or sprite in self.sprites_above_owner
        )

    def resolve_click_owner(self):
        """Ask registered claimants whether the current click is theirs.

        Called once per MOUSEBUTTONDOWN. An open overlay (a Dropdown menu)
        claims the click outright; otherwise the top-most interactive widget
        under the cursor takes it, so stacked widgets don't all react to one
        click. Plain sprites never become the owner; those drawn above the
        owning widget, such as an icon on a button, still receive the click.

        Called exactly once per click, from handle_mouse_events (and from the
        tests' click_at helper), so this is also where the click id advances."""
        self.click_id += 1
        self.click_claimants[:] = [w for w in self.click_claimants if w.alive()]
        claiming = [w for w in self.click_claimants if w._claims_click()]
        if claiming:
            # Registration order says nothing about what is drawn on top, so
            # pick by layer rather than taking the first claimant.
            self.click_owner = max(claiming, key=lambda w: w._layer)
            self.sprites_above_owner = set()
            return
        # sprites() is layer-ordered back-to-front, so the last hit is on top.
        # is_touching() excludes hidden sprites; a disabled one would otherwise
        # win ownership and then decline to act, losing the click.
        sprites = globals_list.sprites_group.sprites()
        widgets = [
            i
            for i, s in enumerate(sprites)
            if s._is_widget and not s._is_disabled and mouse.is_touching(s)
        ]
        if not widgets:
            self.click_owner = None
            self.sprites_above_owner = set()
            return
        self.click_owner = sprites[widgets[-1]]
        self.sprites_above_owner = {
            s
            for s in sprites[widgets[-1] + 1 :]
            if not s._is_widget and mouse.is_touching(s)
        }


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
    if event.type in (
        pygame.MOUSEMOTION,
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP,
    ):
        mouse.x, mouse.y = (event.pos[0] - screen.width / 2.0), (
            screen.height / 2.0 - event.pos[1]
        )
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_state.click_happened = True
        mouse._is_clicked = True
        mouse_state.resolve_click_owner()
    if event.type == pygame.MOUSEBUTTONUP:
        mouse_state.click_release_happened = True
        mouse._is_clicked = False


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
