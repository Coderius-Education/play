import pytest
import play
import time


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_stress_velocity_tunneling():
    """
    Stress test: Very high velocity to ensure discrete step logic doesn't allow tunneling.
    Spawns object at astronomical speed towards a thin wall.
    """
    MAX_FRAMES = 50

    # Very thin wall on the right
    wall = play.new_box(color="black", x=300, y=0, width=5, height=500)
    wall.start_physics(can_move=False)

    # Fast bullet on the left
    bullet = play.new_circle(color="red", x=-300, y=0, radius=5)

    # 50,000 pixels per second is astronomical.
    # With a 60 FPS loop, it's roughly ~833 pixels per frame, easily clearing the 5px wall width.
    bullet.start_physics(x_speed=50000, mass=1, bounciness=0.0)

    frames_run = [0]

    @play.repeat_forever
    def check_position():
        frames_run[0] += 1

        # Give it a few frames to run the course.
        # We assert that the x position NEVER surpasses the wall's right side (x=302.5)
        # Assuming physics prevents it, it should hit the wall and stop/bounce back.
        assert bullet.x <= 302.5, "Tunneling occurred! The bullet crossed the wall!"

        if frames_run[0] >= MAX_FRAMES:
            play.stop_program()

    play.start_program()

    # If the program survived without asserting the bullet crossed the wall,
    # the collision engine successfully prevented tunneling at 50,000 px/s!
