"""Root conftest for pytest.

Handles pygame re-initialisation after fork().  Module-level imports of
play trigger pygame.init() which starts background threads.  Those
threads do not survive fork(), causing deadlocks with pytest --forked.

Two hooks cooperate to fix this:

1. pytest_collection_finish – runs in the *parent* after all test modules
   have been collected (and thus after pygame.init() has been triggered by
   module-level imports).  Calls pygame.quit() to kill background threads
   so that subsequent fork() calls don't deadlock.

2. pytest_runtest_setup – runs in every forked *child* before each test.
   Calls pygame.init() to restart pygame cleanly.
"""

import os
import pytest
import pymunk

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_parent_pid = os.getpid()


def pytest_collection_finish(session):
    """Kill pygame threads in the parent after test collection."""
    try:
        import pygame

        if pygame.get_init():
            pygame.quit()
    except ImportError:
        pass


def pytest_runtest_setup(item):
    """Re-initialise pygame in forked child processes."""
    if os.getpid() != _parent_pid:
        import pygame

        pygame.init()
        try:
            from play.io.screen import screen

            screen.update_display()
        except ImportError:
            pass
    else:
        # If not forked, ensure pygame is initialized anyway locally
        import pygame

        if not pygame.get_init():
            pygame.init()
            try:
                from play.io.screen import screen

                screen.update_display()
            except ImportError:
                pass


@pytest.fixture(autouse=True)
def reset_play_global_state():
    """Automatically resets the global state of the 'play' framework before each test.
    This prevents test bleed and failures when running multiple tests in sequence.
    """
    try:
        from play.globals import globals_list
        from play.callback import callback_manager
        import play.physics as p_module

        # Reset globals gracefully
        globals_list.all_sprites.clear()

        # Create a fresh group
        import pygame

        globals_list.sprites_group = pygame.sprite.Group()

        globals_list.walls.clear()
        try:
            from play.io.screen import create_walls

            create_walls()
        except ImportError:
            pass
        globals_list.controllers.clear()

        # Reset Callbacks
        callback_manager.callbacks = {}

        # Reset physics space without breaking references
        if hasattr(p_module, "physics_space"):
            for shape in list(p_module.physics_space.shapes):
                p_module.physics_space.remove(shape)
            for constraint in list(p_module.physics_space.constraints):
                p_module.physics_space.remove(constraint)
            for body in list(p_module.physics_space.bodies):
                p_module.physics_space.remove(body)
            p_module.physics_space.step(0.001)  # flush

    except ImportError:
        pass

    yield

    # Try to clean up pending events from pygame
    try:
        import pygame

        if pygame.get_init():
            pygame.event.clear()
    except ImportError:
        pass
