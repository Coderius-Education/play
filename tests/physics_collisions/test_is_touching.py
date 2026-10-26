import play


def _ball_and_block():
    """A bouncy ball moving right towards an immovable block."""
    ball = play.new_circle(color="black", radius=20)
    block = play.new_box(color="black", x=200)
    ball.start_physics(
        obeys_gravity=False, x_speed=60, friction=0, mass=10, bounciness=1.0
    )
    block.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )
    return ball, block


def _run_frames(frames):
    """Run the game loop for *frames* frames, then stop it."""
    counted = [0]

    @play.repeat_forever
    def stop_later():
        counted[0] += 1
        if counted[0] == frames:
            play.stop_program()

    play.start_program()


def test_a_ball_bouncing_off_a_block_touches_it_once_and_is_touching_it_then():
    ball, block = _ball_and_block()
    touching = []

    @ball.when_touching(block)
    def detect_collision():
        touching.append(ball.is_touching(block))

    _run_frames(200)

    assert touching == [True]


def test_a_ball_bouncing_off_a_block_stops_touching_it_once_and_is_clear_of_it_then():
    ball, block = _ball_and_block()
    touching = []

    @ball.when_stopped_touching(block)
    def detect_separation():
        touching.append(ball.is_touching(block))

    _run_frames(200)

    assert touching == [False]


def test_teleporting_a_ball_away_in_when_touching_ends_the_contact():
    ball, block = _ball_and_block()
    log = []

    @ball.when_touching(block)
    def teleport():
        log.append("touching")
        ball.x = 0

    @ball.when_stopped_touching(block)
    def left():
        log.append("stopped")

    _run_frames(200)

    assert log == ["touching", "stopped"]
    assert ball.x < 0
