import pytest

# play.timer waits in real time, and this test counts the frames drawn
# meanwhile, so the loop has to run at real speed.
pytestmark = pytest.mark.real_clock


def test_frames_go_on_while_when_program_starts_waits_for_a_timer():
    import play

    ball = play.new_circle(radius=20)
    ball.start_physics(obeys_gravity=False)
    frames = [0]
    end_of_the_wait = []

    @play.when_program_starts
    async def start():
        ball.physics.x_speed = 300
        await play.timer(seconds=0.2)
        end_of_the_wait.append((frames[0], ball.x))
        ball.physics.x_speed = 60

    @play.repeat_forever
    def count():
        frames[0] += 1
        if end_of_the_wait and frames[0] == end_of_the_wait[0][0] + 10:
            play.stop_program()

    play.start_program()

    frames_waited, x_after_the_wait = end_of_the_wait[0]
    assert frames_waited >= 2
    assert x_after_the_wait == pytest.approx(5 * frames_waited, abs=5)
    assert ball.x - x_after_the_wait == pytest.approx(10, abs=1)
