"""Game over, then play again — the follow-up every student writes.

Nothing else in the suite restarts a game. That matters because a replay is
where state-reset bugs live: a score that never zeroes, sprites left hidden,
or callbacks registered a second time so every click counts twice.

This is also the only place that asserts anything was actually *drawn*. Every
other project test reads internal counters, so a regression that stopped
blitting sprites entirely would pass all of them.
"""

from tests.conftest import (
    count_color,
    post_mouse_motion,
    post_mouse_down,
    post_mouse_up,
)
from tests.projects.conftest import add_safety_timeout

max_frames = 600
WINNING_SCORE = 2


def test_game_over_then_play_again():
    import play
    from play.io.screen import screen
    from play.globals import globals_list
    from play.utils import color_name_to_rgb

    score = [0]
    rounds_played = [0]
    seen = {}

    target = play.new_box(color="red", x=0, y=0, width=120, height=120)
    game_over_text = play.new_text(words="", x=0, y=200, font_size=40)
    game_over_text.hide()

    # Registered once, before the program starts. A replay must not add a
    # second copy: that is the classic restart bug, and it shows up as the
    # score jumping by 2 per click in round two.
    @target.when_clicked
    def on_target_clicked():
        score[0] += 1
        if score[0] >= WINNING_SCORE:
            target.hide()
            game_over_text.words = "Game over!"
            game_over_text.show()

    def start_new_round():
        score[0] = 0
        rounds_played[0] += 1
        game_over_text.hide()
        target.show()

    @play.when_program_starts
    async def driver():
        async def click_target():
            pos = (int(screen.width / 2), int(screen.height / 2))
            post_mouse_motion(*pos)
            await play.animate()
            post_mouse_down(*pos)
            await play.animate()
            post_mouse_up(*pos)
            await play.animate()

        red = color_name_to_rgb("red")
        for _ in range(5):
            await play.animate()

        # The target is on screen and actually drawn.
        seen["red_pixels_at_start"] = count_color(globals_list.display, red)

        # --- round one: play to game over ---------------------------------
        for _ in range(WINNING_SCORE):
            await click_target()
        seen["round1_score"] = score[0]
        seen["round1_hidden"] = target.is_hidden
        await play.animate()
        seen["red_pixels_after_game_over"] = count_color(globals_list.display, red)

        # A click while the target is hidden must not score.
        await click_target()
        seen["score_while_hidden"] = score[0]

        # --- replay --------------------------------------------------------
        start_new_round()
        for _ in range(3):
            await play.animate()
        seen["score_after_reset"] = score[0]
        seen["visible_again"] = not target.is_hidden
        seen["red_pixels_after_replay"] = count_color(globals_list.display, red)

        # One click in round two must score exactly one point. Two would mean
        # the click callback got registered twice.
        await click_target()
        seen["score_after_one_click"] = score[0]

        # --- round two plays through to game over too ----------------------
        while score[0] < WINNING_SCORE:
            await click_target()
        seen["round2_hidden"] = target.is_hidden
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    # --- the game is actually drawn ---------------------------------------
    assert seen["red_pixels_at_start"] > 0, "the target should be drawn on screen"
    assert (
        seen["red_pixels_after_game_over"] == 0
    ), "hiding the target should stop it being drawn"
    assert (
        seen["red_pixels_after_replay"] > 0
    ), "showing the target again should put it back on screen"

    # --- round one ---------------------------------------------------------
    assert seen["round1_score"] == WINNING_SCORE
    assert seen["round1_hidden"] is True, "game over should hide the target"
    assert (
        seen["score_while_hidden"] == WINNING_SCORE
    ), "a hidden target must not accept clicks"

    # --- the replay actually reset ----------------------------------------
    assert seen["score_after_reset"] == 0, "starting a new round should zero the score"
    assert seen["visible_again"] is True, "a new round should show the target again"
    assert seen["score_after_one_click"] == 1, (
        "one click should score one point; scoring 2 means the click callback "
        "was registered a second time by the replay"
    )
    assert seen["round2_hidden"] is True, "round two should reach game over too"
    assert rounds_played[0] == 1
