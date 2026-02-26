"""Pong with start menu — realistic full-game project test.

The game shows a title screen with a "Start" button.  The player clicks
the button to begin.  After one player wins, a "Game Over" screen appears
with the final score.

This is how students typically structure their games: a menu state, a
playing state, and a game-over state — all managed through sprite
visibility (hide / show) and a state variable.

This test verifies:
- sprite.hide() / sprite.show() for menu and game-over screens
- when_clicked on a text button to transition between states
- the full menu → play → game-over lifecycle
- text.words updates for title, button, and score display
"""

from tests.conftest import post_mouse_down, post_mouse_motion, post_mouse_up
from tests.projects.conftest import assert_pong_winner

max_frames = 5000
winning_score = 3


def test_pong_start_menu():
    import play
    from play.callback.collision_callbacks import WallSide
    from play.io.screen import screen

    score_left = [0]
    score_right = [0]
    state = ["menu"]
    state_transitions = []

    # --- menu sprites (visible at start) ------------------------------------
    title_text = play.new_text(words="PONG", x=0, y=80, font_size=60)
    start_button = play.new_text(words="Start", x=0, y=-20, font_size=40)

    # --- game sprites (hidden at start) ------------------------------------
    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)
    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)

    # --- game-over sprites (hidden at start) --------------------------------
    gameover_text = play.new_text(words="", x=0, y=40, font_size=50)

    ball.hide()
    paddle_left.hide()
    paddle_right.hide()
    score_text.hide()
    gameover_text.hide()

    # --- physics (started but ball is hidden so paused) ---------------------
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

    # --- start button click: menu → playing --------------------------------
    @start_button.when_clicked
    def on_start_clicked():
        if state[0] != "menu":
            return
        state[0] = "playing"
        state_transitions.append("menu→playing")
        title_text.hide()
        start_button.hide()
        ball.show()
        paddle_left.show()
        paddle_right.show()
        score_text.show()

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- scoring (custom because of game-over state) -----------------------
    def end_game():
        state[0] = "gameover"
        state_transitions.append("playing→gameover")
        ball.hide()
        paddle_left.hide()
        paddle_right.hide()
        winner = "Left" if score_left[0] >= winning_score else "Right"
        gameover_text.words = f"{winner} wins!  {score_left[0]} - {score_right[0]}"
        gameover_text.show()

    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_right[0] >= winning_score:
            end_game()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 300
        ball.physics.y_speed = 40

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_left[0] >= winning_score:
            end_game()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = -300
        ball.physics.y_speed = -40

    # --- driver: click start, wait for game to finish ----------------------
    @play.when_program_starts
    async def driver():
        for _ in range(10):
            await play.animate()

        sx = int(screen.width / 2 + start_button.x)
        sy = int(screen.height / 2 - start_button.y)
        post_mouse_motion(sx, sy)
        await play.animate()
        post_mouse_down(sx, sy)
        await play.animate()
        post_mouse_up(sx, sy)
        await play.animate()

        for _ in range(max_frames):
            if state[0] == "gameover":
                for _ in range(5):
                    await play.animate()
                play.stop_program()
                return
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert (
        "menu→playing" in state_transitions
    ), "game should have transitioned from menu to playing"
    assert (
        "playing→gameover" in state_transitions
    ), "game should have transitioned from playing to gameover"
    assert_pong_winner(score_left, score_right, winning_score)
    assert gameover_text.is_shown, "game-over text should be visible at the end"
    assert ball.is_hidden, "ball should be hidden after game over"


if __name__ == "__main__":
    test_pong_start_menu()
