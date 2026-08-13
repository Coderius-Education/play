"""Root conftest for pytest.

Provides shared fixtures and helpers for all tests. Module-level imports
of play trigger pygame.init() which starts background threads; the
clean_play_state fixture reinitialises pygame and resets all play globals
between tests to prevent state bleed.
"""

import logging
import os
import sys as _sys
import time
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords or "stress" in str(item.path):
            item.add_marker(skip_slow)


# ---------------------------------------------------------------------------
# Shared mouse-event helpers (used by tests/events/ and tests/projects/)
# ---------------------------------------------------------------------------


# A frame runs update() on every sprite once per physics sub-step, not once:
# simulate_physics() calls update_sprites() for every step but the last, and
# game_loop calls it once more. Mirroring that here is what makes a widget
# whose click action is not idempotent fail in a unit test instead of only in
# a real game. Kept in step with Globals.num_sim_steps.
UPDATES_PER_FRAME = 10


def click_at(x, y, *widgets, hold=False):
    """Simulate a full mouse click at play-coordinates ``(x, y)``.

    Mirrors the real event path: moves the mouse, resolves exclusive click
    ownership (an open dropdown menu claims clicks that land on it), runs
    ``update()`` on the given widgets in layer order (lowest first, like the
    real sprite loop) once per sub-step, then clears the frame's mouse state.

    Pass ``hold=True`` to leave the mouse button pressed after the click
    (e.g. to start a slider drag).
    """
    from play.io.mouse import mouse
    from play.core.mouse_loop import mouse_state

    mouse.x, mouse.y = x, y
    mouse._is_clicked = True
    mouse_state.click_happened = True
    mouse_state.resolve_click_owner()
    for _ in range(UPDATES_PER_FRAME):
        for widget in sorted(widgets, key=lambda w: w._layer):
            widget.update()
    mouse_state.clear()
    if not hold:
        mouse._is_clicked = False


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


def count_color(surface, rgb):
    """Count pixels in *surface* whose RGB matches *rgb* (alpha ignored).

    Used by widget render tests to assert that drawing responds to state
    (e.g. a progress bar shows more fill pixels at a higher value), instead of
    only checking that an image exists.
    """
    import pygame

    target = pygame.Color(*rgb[:3]) if not isinstance(rgb, pygame.Color) else rgb
    tr, tg, tb = target.r, target.g, target.b
    w, h = surface.get_width(), surface.get_height()
    total = 0
    for x in range(w):
        for y in range(h):
            c = surface.get_at((x, y))
            if c.r == tr and c.g == tg and c.b == tb and c.a != 0:
                total += 1
    return total


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

        try:
            pygame.quit()
        except Exception:
            pass
    except ImportError:
        pass


COLLISION_HANDLER_ERRORS = []
_RECORDER_INSTALLED = []


def _install_collision_error_recorder():
    """Make exceptions raised inside collision handlers fail the test.

    pymunk calls these across a cffi boundary, which catches whatever they
    raise, prints a traceback to stderr and carries on. The suite sees a clean
    pass. That silence is total: mutating the guards in _handle_collision to
    raise KeyError on every wall collision left all 29 collision tests passing.
    Nothing in that function can be verified while its failures are invisible.

    Re-registers the handlers wrapped, rather than patching the registry, since
    pymunk is holding the bound methods captured in its constructor.
    """
    if _RECORDER_INSTALLED:
        return
    from play.callback.collision_callbacks import collision_registry
    from play.physics import physics_space

    def _wrap(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - recorded, then re-raised
                COLLISION_HANDLER_ERRORS.append(f"{type(exc).__name__}: {exc}")
                raise

        return wrapper

    begin = _wrap(collision_registry._handle_collision)
    separate = _wrap(collision_registry._handle_end_collision)
    try:
        physics_space.on_collision(begin=begin, separate=separate)
    except AttributeError:
        handler = physics_space.add_default_collision_handler()
        handler.begin = begin
        handler.separate = separate
    _RECORDER_INSTALLED.append(True)


def pytest_sessionfinish(session, exitstatus):
    """Disarm auto-start once the session is over.

    Creating a sprite arms auto_start, which runs the game loop as the
    interpreter shuts down — the intended kindness for a student who forgot
    play.start_program(). clean_play_state disarms it at the *start* of each
    test, so the last test's arming survives the session: pytest prints its
    summary, then sits through a phantom game until that test's safety-stop
    deadline expires. That is the 30 seconds a single-file run spends after
    reporting every test as passed.

    Only bites without xdist; its workers exit before the trace can fire,
    which is why CI never sees it.

    Looked up in sys.modules rather than imported: under xdist the tests run
    in workers and this also runs in the controller, which otherwise never
    imports play. Importing it there is not free — `python -c "import play"`
    segfaults at interpreter shutdown all on its own — so an unconditional
    import here turns a clean exit into a 139.
    """
    auto_start = _sys.modules.get("play.api.auto_start")
    if auto_start is None:
        return
    auto_start._cleanup_auto_start()


@pytest.fixture(autouse=True)
def clean_play_state(request):
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

    _install_collision_error_recorder()
    COLLISION_HANDLER_ERRORS.clear()

    # Clean play globals
    play.globals.globals_list.reset()

    import play.core.sprites_loop

    play.core.sprites_loop._clicked_sprite_id = None

    import play.api.auto_start

    play.api.auto_start._cleanup_auto_start()
    play.globals.globals_list.initial_pid = -1

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

    from play.objects import text_input_registry as _ti_registry

    _ti_registry.reset()

    from play.core import keyboard_state, mouse_state

    keyboard_state.pressed.clear()
    keyboard_state.pressed_this_frame.clear()
    mouse_state.click_happened = False
    mouse_state.click_release_happened = False
    mouse_state.click_owner = None
    mouse_state.click_claimants.clear()

    from play.io.mouse import mouse

    mouse.x = 0
    mouse.y = 0
    mouse._is_clicked = False

    # Final event queue flush — the only clear that matters
    if pygame.display.get_init():
        pygame.event.pump()
        pygame.event.clear()

    # Safety timeout: automatically stop the game loop so that any test
    # whose stop_program() path never fires will fail rather than hang.
    # Tests marked @pytest.mark.slow get a longer deadline.
    marker = request.node.get_closest_marker("slow")
    _seconds = marker.args[0] if marker and marker.args else 30
    _deadline = time.monotonic() + _seconds
    _timed_out = {"fired": False}

    @play.repeat_forever
    def _safety_stop():
        if time.monotonic() >= _deadline:
            _timed_out["fired"] = True
            play.stop_program()

    yield

    # Teardown: remove all pymunk bodies/shapes so C destructors don't race
    # with interpreter shutdown and cause a segfault on process exit.
    for body in list(physics_space.bodies):
        try:
            physics_space.remove(body)
        except Exception:
            pass
    for shape in list(physics_space.shapes):
        try:
            physics_space.remove(shape)
        except Exception:
            pass
    for constraint in list(physics_space.constraints):
        try:
            physics_space.remove(constraint)
        except Exception:
            pass

    # The safety stop is an emergency brake, not an ending. A test that reaches
    # it did not stop itself, which usually means the behaviour it describes
    # never happened — and its assertions passed anyway, since "the game ended"
    # looks identical either way. Failing here by default is what stops that
    # from being silent; a test that genuinely has no ending of its own can say
    # so with @pytest.mark.allow_safety_timeout.
    assert (
        not COLLISION_HANDLER_ERRORS
    ), "a collision handler raised, and pymunk swallowed it:\n  " + "\n  ".join(
        COLLISION_HANDLER_ERRORS[:5]
    )

    if _timed_out["fired"] and not request.node.get_closest_marker(
        "allow_safety_timeout"
    ):
        pytest.fail(
            f"the {_seconds}s safety timeout stopped this test — it never "
            "reached an ending of its own. Mark it with "
            "@pytest.mark.allow_safety_timeout if that is intended."
        )
