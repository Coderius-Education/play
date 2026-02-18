"""Core game loop and event handling functions."""

import pygame

from .controller_loop import (
    controller_state,
    handle_controller as _handle_controller,
    handle_controller_events as _handle_controller_events,
)
from .game_loop_wrapper import listen_to_failure
from .keyboard_loop import (
    handle_keyboard as _handle_keyboard,
    handle_keyboard_events as _handle_keyboard_events,
)
from .mouse_loop import (
    handle_mouse_loop as _handle_mouse_loop,
    handle_mouse_events as _handle_mouse_events,
    mouse_state,
)
from .physics_loop import simulate_physics
from .sprites_loop import update_sprites as _update_sprites
from ..callback import callback_manager, CallbackType
from ..globals import globals_list
from ..io.screen import screen
from ..loop import loop as _loop
from ..io.keypress import keyboard_state

_clock = pygame.time.Clock()


def _handle_pygame_events():
    """Handle pygame events in the game loop."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_q
            and (
                pygame.key.get_mods() & pygame.KMOD_META
                or pygame.key.get_mods() & pygame.KMOD_CTRL
            )
        ):
            # quitting by clicking window's close button or pressing ctrl+q / command+q
            _loop.stop()
            return False

        _handle_keyboard_events(event)
        _handle_mouse_events(event)
        _handle_controller_events(event)

    return True


@listen_to_failure()
async def game_loop():
    """The main game loop."""
    keyboard_state.clear()
    mouse_state.clear()
    controller_state.clear()

    _clock.tick(globals_list.frame_rate)

    if not _handle_pygame_events():
        return

    await _handle_keyboard()

    if mouse_state.click_happened or mouse_state.click_release_happened:
        await _handle_mouse_loop()

    if controller_state.any():
        await _handle_controller()

    #############################
    # @repeat_forever callbacks
    #############################
    callback_manager.run_callbacks(CallbackType.REPEAT_FOREVER)

    #############################
    # physics simulation
    #############################
    await simulate_physics()

    if globals_list.backdrop_type == "color":
        globals_list.display.fill(globals_list.backdrop)
    elif globals_list.backdrop_type == "image":
        globals_list.display.blit(
            globals_list.backdrop,
            (0, 0),
        )
    else:
        globals_list.display.fill((255, 255, 255))

    await _update_sprites()

    pygame.display.flip()
    _loop.create_task(game_loop())
