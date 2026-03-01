"""Pong with random serve direction — realistic full-game project test.

After each point the ball is served in a random direction using
play.random_number().  The ball also gets a random_color() on each serve.
This is how students commonly add variety to their games.

This test verifies:
- play.random_number() returns values in the expected range
- play.random_color() returns a valid RGB tuple
- random values are actually used (ball direction varies)
- the game completes normally with randomized serves
"""

from tests.projects.conftest import (
    setup_pong,
    assert_pong_winner,
)

max_frames = 1500
winning_score = 2


def test_pong_random():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    serves = [0]
    serve_angles = []
    colors_used = []

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- scoring with random serve -----------------------------------------
    def random_serve():
        y_speed = play.random_number(lowest=-100, highest=100)
        serve_angles.append(y_speed)

        color = play.random_color()
        colors_used.append(color)

        # Alternate serve direction
        direction = 1 if serves[0] % 2 == 0 else -1
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 300 * direction
        ball.physics.y_speed = y_speed
        serves[0] += 1

    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_right[0] >= winning_score:
            play.stop_program()
            return
        random_serve()

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_left[0] >= winning_score:
            play.stop_program()
            return
        random_serve()

    # --- safety timeout ----------------------------------------------------
    @play.when_program_starts
    async def timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score)
    assert serves[0] > 0, "at least one random serve should have happened"

    # Verify random_number produced values in range
    for angle in serve_angles:
        assert -100 <= angle <= 100, f"random y_speed out of range: {angle}"

    # Verify random_color produced valid RGB tuples
    for color in colors_used:
        assert len(color) == 3, f"random_color should return 3-tuple, got {color}"
        for channel in color:
            assert 0 <= channel <= 255, f"color channel out of range: {channel}"


if __name__ == "__main__":
    test_pong_random()
