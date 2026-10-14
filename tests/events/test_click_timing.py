"""Sprite and button clicks through the real game loop, however long the button is held."""

import pytest

import play
from play.io.screen import screen
from tests.conftest import post_mouse_down, post_mouse_motion, post_mouse_up


def _screen_xy(x, y):
    return int(screen.width / 2 + x), int(screen.height / 2 - y)


@pytest.mark.parametrize(
    "frames_held", [0, 1, 5], ids=["same frame", "1 frame", "held"]
)
def test_a_click_reaches_sprites_and_buttons_once(frames_held):
    box = play.new_box(x=-150, width=100, height=100)
    button = play.new_button("Go", x=150)
    clicks = {"box": 0, "button": 0}

    @box.when_clicked
    def on_box():
        clicks["box"] += 1

    @button.when_clicked
    def on_button():
        clicks["button"] += 1

    @play.when_program_starts
    async def driver():
        for x in (-150, 150):
            pos = _screen_xy(x, 0)
            post_mouse_motion(*pos)
            await play.animate()
            await play.animate()
            post_mouse_down(*pos)
            if frames_held == 0:
                post_mouse_up(*pos)
            for _ in range(frames_held):
                await play.animate()
            if frames_held:
                post_mouse_up(*pos)
            for _ in range(5):
                await play.animate()
        play.stop_program()

    play.start_program()

    assert clicks == {"box": 1, "button": 1}
