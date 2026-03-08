"""Root conftest for pytest.

Provides shared fixtures and helpers for all tests. Module-level imports
of play trigger pygame.init() which starts background threads; the
clean_play_state fixture reinitialises pygame and resets all play globals
between tests to prevent state bleed.
"""

import logging
import os
import pytest

# ---------------------------------------------------------------------------
# Shared mouse-event helpers (used by tests/events/ and tests/projects/)
# ---------------------------------------------------------------------------


def post_mouse_motion(screen_x, screen_y):
    """Post a MOUSEMOTION event to position the simulated cursor."""
    import pygame

    event = pygame.event.Event(
        pygame.MOUSEMOTION,
        {"pos": (screen_x, screen_y), "rel": (0, 0), "buttons": (0, 0, 0)},
    )
    pygame.event.post(event)


def post_mouse_down(screen_x, screen_y):
    """Post a MOUSEBUTTONDOWN event at the given screen coordinates."""
    import pygame

    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": (screen_x, screen_y), "button": 1}
    )
    pygame.event.post(event)


def post_mouse_up(screen_x, screen_y):
    """Post a MOUSEBUTTONUP event at the given screen coordinates."""
    import pygame

    event = pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"pos": (screen_x, screen_y), "button": 1}
    )
    pygame.event.post(event)


def post_key_down(pygame_key):
    """Post a KEYDOWN event for the given pygame key constant."""
    import pygame

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame_key}))


def post_key_up(pygame_key):
    """Post a KEYUP event for the given pygame key constant."""
    import pygame

    pygame.event.post(pygame.event.Event(pygame.KEYUP, {"key": pygame_key}))


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def pytest_collection_finish(session):
    """Quit pygame after the collection phase.

    Module-level imports of play trigger pygame.init() which starts background
    threads.  Calling pygame.quit() here tears down those threads so they do
    not interfere with the test run that follows.
    """
    try:
        import pygame

        if pygame.get_init():
            pygame.quit()
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def clean_play_state():
    """Flush play globals, physics, callbacks, and groups before every test.
    This prevents state bleed across tests and resolves random hanging test loops.
    """
    import asyncio

    import pygame

    import play
    import play.loop

    # Headless Execution Fixes: properly initialize Pygame
    pygame.init()
    pygame.display.init()
    pygame.font.init()

    try:
        pygame.display.set_mode((800, 600))
        from play.io.screen import screen

        screen.update_display()
    except Exception as e:
        logging.warning("Failed to initialize pygame display: %s", e)

    old_loop = play.loop.get_loop()
    if old_loop and not old_loop.is_closed():
        # Cancel any leftover tasks and close their coroutines to prevent
        # "coroutine was never awaited" warnings during garbage collection.
        for task in asyncio.all_tasks(loop=old_loop):
            task.cancel()
            coro = task.get_coro()
            if coro is not None:
                coro.close()
        old_loop.stop()
        old_loop.close()
    # Reset so get_loop() creates a new properly configured loop on the next
    # call (with exception handler, debug mode, etc.).
    play.loop._creator_pid = None

    from play.physics import physics_space
    from play.callback import callback_manager

    # Clean play globals
    play.globals.globals_list.reset()

    import play.core.sprites_loop

    play.core.sprites_loop._clicked_sprite_id = None

    import play.api.utils

    play.api.utils._program_started = False
    play.api.utils._initial_pid = -1
    play.api.utils._cancel_auto_start()
    callback_manager.on_first_callback = play.api.utils._schedule_auto_start
    play.globals.globals_list.on_first_sprite = play.api.utils._schedule_auto_start

    play.globals.globals_list.gravity.vertical = -100
    play.globals.globals_list.gravity.horizontal = 0
    physics_space.gravity = (0, -100)
    from play.io.screen import screen

    screen.width = 800
    screen.height = 600
    screen.update_display()

    # Clean Pymunk physics spaces
    for body in list(physics_space.bodies):
        physics_space.remove(body)
    for shape in list(physics_space.shapes):
        physics_space.remove(shape)
    for constraint in list(physics_space.constraints):
        physics_space.remove(constraint)

    from play.io.screen import create_walls

    create_walls()

    import play.core

    play.core._clock = pygame.time.Clock()

    # Clean callback queues
    callback_manager.callbacks.clear()

    from play.callback.collision_callbacks import collision_registry

    collision_registry.callbacks = {True: {}, False: {}}
    collision_registry.shape_registry.clear()

    from play.core import keyboard_state, mouse_state

    keyboard_state.pressed.clear()
    mouse_state.click_happened = False
    mouse_state.click_release_happened = False

    from play.io.mouse import mouse

    mouse.x = 0
    mouse.y = 0
    mouse._is_clicked = False

    # Final event queue flush — the only clear that matters
    if pygame.display.get_init():
        pygame.event.pump()
        pygame.event.clear()

    yield
