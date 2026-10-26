import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


@pytest.mark.xfail(
    strict=True,
    reason="pymunk has no continuous collision detection: at 50,000 px/s and 10 "
    "sub-steps a frame the bullet moves 83 px a sub-step, past a 5 px wall and the screen edge",
)
@pytest.mark.xdist_group("stress")
def test_a_very_fast_bullet_does_not_tunnel_through_a_thin_wall():
    wall = play.new_box(color="black", x=300, y=0, width=5, height=500)
    wall.start_physics(can_move=False)
    bullet = play.new_circle(color="red", x=-300, y=0, radius=5)
    bullet.start_physics(x_speed=50000, mass=1, bounciness=0.0)
    furthest = [bullet.x]
    frames_run = [0]

    @play.repeat_forever
    def check_position():
        frames_run[0] += 1
        furthest.append(bullet.x)
        if frames_run[0] == 50:
            play.stop_program()

    play.start_program()

    assert frames_run[0] == 50
    assert max(furthest) <= wall.x + 2.5
