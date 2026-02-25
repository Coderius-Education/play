"""Pong with serve delay — realistic full-game project test.

After each point the ball speed is set to zero while a countdown runs
(using await play.animate() frame loops).  A countdown text shows
"3… 2… 1… Go!" before the ball launches again.

This test verifies:
- await play.animate() for frame-by-frame delays
- text.words updates during the countdown
- setting physics speed to 0 and back works correctly
- the game still completes normally after repeated serve delays
"""

import pytest

max_frames = 5000
winning_score = 3
countdown_frames = 10  # frames per countdown step (short for testing)


def test_pong_serve_delay():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    serves = [0]
    countdown_values = []  # track that countdown text actually changes
    serve_direction = [0]  # non-zero means a serve is pending

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="black", x=0, y=0, radius=10)

    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)
    countdown_text = play.new_text(words="", x=0, y=0, font_size=50)

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=False,
        x_speed=300,
        y_speed=40,
        friction=0,
        mass=10,
        bounciness=1.0,
    )
    paddle_left.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )
    paddle_right.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- scoring (request a serve, don't do async work here) ---------------
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_right[0] >= winning_score:
            play.stop_program()
            return
        # freeze ball and request serve
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

                # countdown
                for n in [3, 2, 1]:
                    countdown_text.words = str(n)
                    countdown_values.append(n)
                    for _ in range(countdown_frames):
                        await play.animate()

                countdown_text.words = "Go!"
                countdown_values.append(0)

                # launch
                ball.physics.x_speed = 300 * direction
                ball.physics.y_speed = 40 * direction
                serves[0] += 1

                await play.animate()
                countdown_text.words = ""

        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    total_score = score_left[0] + score_right[0]
    assert (
        total_score >= winning_score
    ), f"expected at least {winning_score} total points, got {total_score}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score
    assert serves[0] > 0, "at least one serve with countdown should have happened"
    assert len(countdown_values) > 0, "countdown text should have been updated"
    assert 3 in countdown_values, "countdown should have shown '3'"
    assert 1 in countdown_values, "countdown should have shown '1'"


if __name__ == "__main__":
    test_pong_serve_delay()
