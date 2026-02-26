"""Pong with high-score persistence — realistic full-game project test.

The game loads the previous high score from a database file on startup,
displays it, and saves a new high score when the winner's score exceeds
the stored record.  This is a common student pattern: tracking and
persisting best scores across game sessions.

This test verifies:
- play.new_database() creates / opens a JSON database
- database.get_data() reads stored values (with fallback)
- database.set_data() writes values and persists to disk
- high-score text updates when the record is beaten
- the database file is actually written to disk
"""

import os
import tempfile

max_frames = 3000
winning_score = 3


def test_pong_highscore():
    import play
    from play.callback.collision_callbacks import WallSide

    # Use a temp file so we don't pollute the project directory
    db_fd, db_path = tempfile.mkstemp(suffix=".json")
    os.close(db_fd)
    os.remove(db_path)  # let new_database create it fresh

    try:
        score_left = [0]
        score_right = [0]
        highscore_updated = [False]

        # --- database ----------------------------------------------------------
        db = play.new_database(db_filename=db_path)
        db.set_data("high_score", 0)
        old_high = db.get_data("high_score", fallback=0)

        # --- sprites -----------------------------------------------------------
        ball = play.new_circle(color="black", x=0, y=0, radius=10)

        paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
        paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

        score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)
        highscore_text = play.new_text(
            words=f"High Score: {old_high}", x=0, y=230, font_size=20
        )

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

        # --- scoring with high-score tracking ----------------------------------
        def check_highscore():
            winner_score = max(score_left[0], score_right[0])
            current_high = db.get_data("high_score", fallback=0)
            if winner_score > current_high:
                db.set_data("high_score", winner_score)
                highscore_text.words = f"High Score: {winner_score}"
                highscore_updated[0] = True

        @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
        def right_player_scores():
            score_right[0] += 1
            score_text.words = f"{score_left[0]} - {score_right[0]}"
            check_highscore()
            if score_right[0] >= winning_score:
                play.stop_program()
                return
            ball.x = 0
            ball.y = 0
            ball.physics.x_speed = 300
            ball.physics.y_speed = 40

        @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
        def left_player_scores():
            score_left[0] += 1
            score_text.words = f"{score_left[0]} - {score_right[0]}"
            check_highscore()
            if score_left[0] >= winning_score:
                play.stop_program()
                return
            ball.x = 0
            ball.y = 0
            ball.physics.x_speed = -300
            ball.physics.y_speed = -40

        # --- safety timeout ----------------------------------------------------
        @play.when_program_starts
        async def safety_timeout():
            for _ in range(max_frames):
                await play.animate()
            play.stop_program()

        play.start_program()

        # --- assertions --------------------------------------------------------
        total_score = score_left[0] + score_right[0]
        assert (
            total_score >= winning_score
        ), f"expected at least {winning_score} total points, got {total_score}"
        assert score_left[0] >= winning_score or score_right[0] >= winning_score

        assert highscore_updated[
            0
        ], "high score should have been updated (started at 0)"

        # verify the database file was actually written
        assert os.path.exists(db_path), "database file should exist on disk"
        stored = db.get_data("high_score", fallback=0)
        assert (
            stored >= winning_score
        ), f"stored high score should be >= {winning_score}, got {stored}"

    finally:
        # clean up temp database file
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    test_pong_highscore()
