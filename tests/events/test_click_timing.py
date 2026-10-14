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


def _click_once_at(x, y, frames_held=2):
    @play.when_program_starts
    async def driver():
        pos = _screen_xy(x, y)
        post_mouse_motion(*pos)
        await play.animate()
        await play.animate()
        post_mouse_down(*pos)
        for _ in range(frames_held):
            await play.animate()
        post_mouse_up(*pos)
        for _ in range(5):
            await play.animate()
        play.stop_program()

    play.start_program()


def test_overlapping_sprites_all_get_the_click_and_the_release():
    card = play.new_box(width=200, height=100)
    label = play.new_text(words="Card")
    log = []

    def logger(text):
        def callback():
            log.append(text)

        return callback

    for name, sprite in (("card", card), ("label", label)):
        sprite.when_clicked(logger(f"{name} clicked"))
        sprite.when_click_released(logger(f"{name} released"))

    _click_once_at(0, 0)

    assert sorted(log) == [
        "card clicked",
        "card released",
        "label clicked",
        "label released",
    ]


def test_a_sprite_drawn_on_a_button_gets_the_click_and_one_below_does_not():
    background = play.new_box(width=300, height=200, layer=0)
    button = play.new_button(text="", width=200, height=60, layer=10)
    icon = play.new_text(words="PLAY >", layer=50)
    log = []
    background.when_clicked(lambda: log.append("background"))
    button.when_clicked(lambda: log.append("button"))
    icon.when_clicked(lambda: log.append("icon"))

    _click_once_at(0, 0)

    assert sorted(log) == ["button", "icon"]
