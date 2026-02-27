import pytest
import play
import pygame


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_stress_extreme_sizes():
    """
    Stress test: Extraordinary sizes.
    Attempting to allocate a Pygame surface of size 1,000,000 x 1,000,000 pixels.
    Ensures that if Pygame raises a memory error, the test explicitly documents the behavior.
    """
    # We anticipate that calling `new_circle` (which creates the Pygame surface during
    # initialization) will fail. We catch the exact error Pygame throws (often a memory error)
    with pytest.raises((MemoryError, pygame.error)) as exc_info:
        # Extremely large radius (2,000,000 diameter)
        box = play.new_circle(color="red", x=0, y=0, radius=1000000)

    msg = str(exc_info.value).lower()
    assert (
        "too large" in msg or "memory" in msg or "dimensions" in msg
    ), f"Expected a memory/size error message, got: {exc_info.value}"


def test_stress_extreme_coordinates():
    """
    Stress test: Extraordinary coordinate locations.
    Placing objects at x=1e10, y=1e10.
    """
    box = play.new_box(color="red", x=1e10, y=1e10, width=50, height=50)
    box.start_physics(x_speed=100, mass=1, obeys_gravity=False)

    # Run 10 frames to ensure floating-point overflow or rendering at extreme
    # camera-translation offsets doesn't crash the integer casting in Pygame rects.
    frames_run = [0]

    @play.repeat_forever
    def simulation_loop():
        frames_run[0] += 1
        if frames_run[0] >= 10:
            play.stop_program()

    # If this runs without raising an OverflowError when computing display blits, it passes!
    play.start_program()
    assert frames_run[0] >= 10
