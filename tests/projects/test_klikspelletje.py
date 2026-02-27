"""Klikspelletje — realistic full-game project test.

A target circle bounces around the screen at high speed.  Each time it is
clicked it teleports to a new position and the player scores a point.
The game ends when the player reaches the target score.

Because we can't rely on a human clicking, the test simulates mouse clicks
by posting pygame events when the mouse is positioned over the target.

This test verifies:
- high-speed sprite movement with wall bouncing
- sprite click detection (when_clicked)
- teleporting a sprite on click
- score tracking and game-over condition
"""

from tests.conftest import post_mouse_motion, post_mouse_down, post_mouse_up

max_frames = 500
target_score = 3


def test_klikspelletje():
    import play
    from play.io.screen import screen

    score = [0]

    # --- sprites -----------------------------------------------------------
    target = play.new_circle(color="red", x=0, y=0, radius=30)
    score_text = play.new_text(words="Score: 0", x=0, y=260, font_size=30)

    # --- physics -----------------------------------------------------------
    target.start_physics(
        obeys_gravity=False,
        x_speed=240,
        y_speed=160,
        friction=0,
        mass=10,
        bounciness=1.0,
    )

    # --- click handling ----------------------------------------------------
    @target.when_clicked
    def target_clicked():
        score[0] += 1
        score_text.words = f"Score: {score[0]}"
        target.x = 0
        target.y = 0
        if score[0] >= target_score:
            play.stop_program()

    # --- simulated clicks + safety timeout ---------------------------------
    @play.when_program_starts
    async def simulate_clicks():
        for frame in range(max_frames):
            await play.animate()

            if score[0] >= target_score:
                return

            # Every 30 frames, simulate a click on the target's current
            # position.  Convert play coordinates (centred origin) to pygame
            # screen coordinates (top-left origin).
            # Both the motion and the button-down event use the same
            # coordinates to avoid a 1-frame drift between them.
            if frame % 30 == 10:
                sx = int(target.x + screen.width / 2)
                sy = int(-target.y + screen.height / 2)
                post_mouse_motion(sx, sy)
                post_mouse_down(sx, sy)
            if frame % 30 == 13:
                sx = int(target.x + screen.width / 2)
                sy = int(-target.y + screen.height / 2)
                post_mouse_up(sx, sy)

        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert (
        score[0] >= target_score
    ), f"expected score to reach {target_score}, but got {score[0]}"


if __name__ == "__main__":
    test_klikspelletje()
