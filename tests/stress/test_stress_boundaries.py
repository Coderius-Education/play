import pytest
import play
import pygame


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


@pytest.mark.xdist_group("stress")
def test_a_circle_too_big_to_draw_fails_with_a_size_error():
    with pytest.raises((MemoryError, pygame.error)) as exc_info:
        play.new_circle(color="red", x=0, y=0, radius=1000000)

    msg = str(exc_info.value).lower()
    assert (
        "too large" in msg or "memory" in msg or "dimensions" in msg
    ), f"Expected a memory/size error message, got: {exc_info.value}"


def test_a_sprite_far_off_screen_keeps_moving_without_crashing():
    box = play.new_box(color="red", x=1e10, y=1e10, width=50, height=50)
    box.start_physics(x_speed=60, mass=1, obeys_gravity=False)
    frames_run = [0]

    @play.repeat_forever
    def simulation_loop():
        frames_run[0] += 1
        if frames_run[0] == 10:
            play.stop_program()

    play.start_program()

    assert frames_run[0] == 10
    assert box.x - 1e10 == pytest.approx(10, abs=0.01)
    assert box.y == 1e10
