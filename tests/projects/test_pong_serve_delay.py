"""Pong with serve delay — realistic full-game project test.

After each point the ball speed is set to zero while a countdown runs
(using await play.animate() frame loops).  A countdown text shows
"3… 2… 1… Go!" before the ball launches again.

This test verifies:
- await play.animate() for frame-by-frame delays
- text.words updates during the countdown
- setting physics speed to 0 and back works correctly
- countdown runs in the correct order (3 → 2 → 1 → Go!)
- the game still completes normally after repeated serve delays
"""

from tests.projects.conftest import (
    setup_pong,
    assert_pong_winner,
)

max_frames = 5000
winning_score = 3
countdown_frames = 10


def test_pong_serve_delay():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    serves = [0]
    countdown_values = []
    serve_direction = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong()

    countdown_text = play.new_text(words="", x=0, y=0, font_size=50)

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- scoring (custom: freezes ball and requests serve) -----------------
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_right[0] >= winning_score:
            play.stop_program()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 0
        ball.physics.y_speed = 0
        serve_direction[0] = 1

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_left[0] >= winning_score:
            play.stop_program()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 0
        ball.physics.y_speed = 0
        serve_direction[0] = -1

    # --- main loop: countdown + serve + safety timeout ---------------------
    @play.when_program_starts
    async def driver():
        for _ in range(max_frames):
            await play.animate()

            if serve_direction[0] != 0:
                direction = serve_direction[0]
                serve_direction[0] = 0

                for n in [3, 2, 1]:
                    countdown_text.words = str(n)
                    countdown_values.append(n)
                    for _ in range(countdown_frames):
                        await play.animate()

                countdown_text.words = "Go!"
                countdown_values.append(0)

                ball.physics.x_speed = 300 * direction
                ball.physics.y_speed = 40 * direction
                serves[0] += 1

                await play.animate()
                countdown_text.words = ""

        play.stop_program()

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert serves[0] > 0, "at least one serve with countdown should have happened"
    assert len(countdown_values) > 0, "countdown text should have been updated"
    # Verify countdown ran in order: 3, 2, 1, 0 (Go!)
    first_sequence = countdown_values[:4]
    assert first_sequence == [
        3,
        2,
        1,
        0,
    ], f"countdown should run 3→2→1→Go!, got {first_sequence}"


if __name__ == "__main__":
    test_pong_serve_delay()
