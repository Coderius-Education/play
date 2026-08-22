"""Root conftest for pytest.

Provides shared fixtures and helpers for all tests. Module-level imports
of play trigger pygame.init() which starts background threads; the
clean_play_state fixture reinitialises pygame and resets all play globals
between tests to prevent state bleed.
"""

import logging
import os
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


def make_test_video(path, seconds=2.0, fps=10, width=64, height=48, audio=True):
    """Encode a small test video, so no binary file has to live in the repo.

    Every frame is a distinct shade of grey (frame ``i`` is ``i * 8``), which
    lets a test work out which frame is on screen. ``mpeg4`` is used rather than
    ``libx264`` because it ships with every FFmpeg build.

    :return: The path that was written.
    """
    import av  # imported here so collection works without av installed
    import numpy as np

    container = av.open(str(path), mode="w")
    video_stream = container.add_stream("mpeg4", rate=fps)
    video_stream.width = width
    video_stream.height = height
    video_stream.pix_fmt = "yuv420p"

    audio_stream = None
    if audio:
        audio_stream = container.add_stream("aac", rate=44100)
        audio_stream.layout = "stereo"

    for index in range(int(seconds * fps)):
        frame = np.full((height, width, 3), (index * 8) % 256, dtype=np.uint8)
        for packet in video_stream.encode(
            av.VideoFrame.from_ndarray(frame, format="rgb24")
        ):
            container.mux(packet)

    if audio_stream is not None:
        rate = 44100
        moment = np.arange(int(rate * seconds)) / rate
        tone = (np.sin(2 * np.pi * 440 * moment) * 8000).astype(np.int16)
        both = np.stack([tone, tone])
        for start in range(0, both.shape[1] - 1024, 1024):
            chunk = np.ascontiguousarray(both[:, start : start + 1024])
            audio_frame = av.AudioFrame.from_ndarray(
                chunk, format="s16p", layout="stereo"
            )
            audio_frame.sample_rate = rate
            for packet in audio_stream.encode(audio_frame):
                container.mux(packet)

    for packet in video_stream.encode():
        container.mux(packet)
    if audio_stream is not None:
        for packet in audio_stream.encode():
            container.mux(packet)
    container.close()
    return str(path)


@pytest.fixture(scope="session")
def video_file(tmp_path_factory):
    """A short test video with a sound track."""
    return make_test_video(tmp_path_factory.mktemp("video") / "clip.mp4")


@pytest.fixture(scope="session")
def silent_video_file(tmp_path_factory):
    """A short test video with no sound track."""
    return make_test_video(tmp_path_factory.mktemp("video") / "silent.mp4", audio=False)


class FakeClock:
    """A clock the tests move by hand, so playback is deterministic."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        """Move the clock forward."""
        self.now += seconds
        return self.now


@pytest.fixture
def fake_clock():
    """A hand-driven clock for video tests."""
    return FakeClock()


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

    from play.core import keyboard_state, mouse_state

    keyboard_state.pressed.clear()
    keyboard_state.pressed_this_frame.clear()
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

    # Safety timeout: automatically stop the game loop so that any test
    # whose stop_program() path never fires will fail rather than hang.
    # Tests marked @pytest.mark.slow get a longer deadline.
    marker = request.node.get_closest_marker("slow")
    _seconds = marker.args[0] if marker and marker.args else 30
    _deadline = time.monotonic() + _seconds

    @play.repeat_forever
    def _safety_stop():
        if time.monotonic() >= _deadline:
            play.stop_program()

    yield

    # Teardown: stop any video decoding threads before anything else, so they
    # don't outlive the test and keep decoding into the next one.
    from play.objects.video import close_all_videos

    close_all_videos()

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
