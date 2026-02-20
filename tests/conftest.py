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

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_parent_pid = os.getpid()


def pytest_collection_finish(session):
    """Kill pygame threads in the parent after test collection.

    Module-level imports during collection trigger pygame.init(), which
    starts background threads.  Those threads make fork() unsafe.
    Quitting pygame here is safe because no tests have run yet.
    """
    try:
        import pygame

        if pygame.get_init():
            pygame.quit()
    except ImportError:
        pass


def pytest_runtest_setup(item):
    """Re-initialise pygame in forked child processes.

    After the parent quit pygame (see above), forked children need to
    restart it before running any test that uses play.
    """
    if os.getpid() != _parent_pid:
        import pygame

        pygame.init()
        from play.io.screen import screen

        screen.update_display()
