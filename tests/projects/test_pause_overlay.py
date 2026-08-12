"""Pause overlay built from widgets — realistic full-game project test.

The pattern every student hits: the game runs, you pause it, a menu of
widgets appears on top, you click one, and the game resumes.

Unlike the unit tests under tests/objects/, this drives the real frame path
(``update_sprites`` -> ``handle_sprite_click`` -> ``sprites_group.update()``)
with real pygame mouse events, which is where hidden widgets and click
ownership actually have to behave.

This test verifies:
- a hidden overlay is completely inert: clicks fall through to the game
- a visible overlay takes the click, and the sprite underneath does not
- widgets keep updating while the game is paused, so a Resume button works
- hiding the overlay again restores clicks to the game
"""

from tests.conftest import post_mouse_motion, post_mouse_down, post_mouse_up

max_frames = 400


def test_pause_overlay():
    import play
    from play.io.screen import screen

    game_clicks = [0]
    resume_clicks = [0]
    hovers = [0]
    paused = [False]
    seen = {}

    # The game world: one big sprite the overlay will sit on top of.
    player = play.new_box(color="green", x=0, y=0, width=300, height=200)

    @player.when_clicked
    def on_player_clicked():
        game_clicks[0] += 1

    # The pause overlay, hidden until the game is paused.
    resume = play.new_button("Resume", x=0, y=0, width=160, height=50)
    sound = play.new_checkbox("Sound", x=0, y=-70, size_px=24)
    resume.hide()
    sound.hide()

    @resume.when_hover
    def on_resume_hover():
        hovers[0] += 1

    @resume.when_clicked
    def on_resume_clicked():
        resume_clicks[0] += 1
        paused[0] = False
        resume.hide()
        sound.hide()

    def pause_game():
        paused[0] = True
        resume.show()
        sound.show()

    @play.when_program_starts
    async def driver():
        async def click(x, y):
            """Post a real motion/down/up sequence at play-coordinates."""
            sx = int(screen.width / 2 + x)
            sy = int(screen.height / 2 - y)
            post_mouse_motion(sx, sy)
            await play.animate()
            post_mouse_down(sx, sy)
            await play.animate()
            post_mouse_up(sx, sy)
            await play.animate()

        async def move_away():
            post_mouse_motion(5, 5)
            await play.animate()

        for _ in range(5):
            await play.animate()

        # 1. Overlay hidden — the click must reach the game, not the widgets.
        await move_away()
        await click(0, 0)
        seen["hidden"] = (game_clicks[0], resume_clicks[0], sound.checked)

        # 2. Pause. The overlay is now visible and drawn above the player.
        await move_away()
        pause_game()
        for _ in range(3):
            await play.animate()

        # 2a. The checkbox takes its click; the sprite underneath does not.
        await click(0, -70)
        seen["checkbox"] = (game_clicks[0], sound.checked)
        seen["checkbox_debug"] = {
            "hidden": sound.is_hidden,
            "pos": (sound.x, sound.y),
            "size": (sound.width, sound.height),
            "mouse": (play.mouse.x, play.mouse.y),
            "touching": play.mouse.is_touching(sound),
        }

        # 2b. The Resume button works while the game is paused, and the
        #     sprite underneath still does not see the click.
        await click(0, 0)
        seen["resume"] = (game_clicks[0], resume_clicks[0], hovers[0])

        # 3. Overlay hidden again — clicks go back to the game.
        await move_away()
        for _ in range(3):
            await play.animate()
        await click(0, 0)
        seen["after"] = (game_clicks[0], resume_clicks[0])

        play.stop_program()

    # Safety net so a broken assertion can't hang the suite.
    @play.when_program_starts
    async def safety_timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert "after" in seen, "driver did not finish; the loop stopped early"

    hidden_game, hidden_resume, hidden_checked = seen["hidden"]
    assert hidden_game == 1, "a click should reach the game while the overlay is hidden"
    assert hidden_resume == 0, "a hidden Resume button must not fire"
    assert hidden_checked is False, "a hidden checkbox must not toggle"

    checkbox_game, checked = seen["checkbox"]
    assert (
        checked is True
    ), f"the visible checkbox should have toggled: {seen['checkbox_debug']}"
    assert (
        checkbox_game == hidden_game
    ), "the sprite under a visible overlay must not receive the click"

    resume_game, resumed, hover_count = seen["resume"]
    assert resumed == 1, "the Resume button should work while the game is paused"
    assert (
        resume_game == hidden_game
    ), "the sprite under the Resume button must not receive the click"
    assert hover_count >= 1, "widgets must keep updating while the game is paused"
    assert paused[0] is False, "clicking Resume should have unpaused the game"

    after_game, after_resume = seen["after"]
    assert after_game == hidden_game + 1, "clicks should return to the game once hidden"
    assert after_resume == 1, "the re-hidden Resume button must not fire again"


if __name__ == "__main__":
    test_pause_overlay()
