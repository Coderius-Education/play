import pygame
import pytest
import play
from play.io.mouse import mouse
from play.utils import color_name_to_rgb
from tests.conftest import count_color


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_a_new_button_shows_its_label_at_layer_10():
    btn = play.new_button("OK", text_color="red")
    assert btn.text == "OK"
    assert btn.layer == 10
    assert count_color(btn.image, color_name_to_rgb("red")) > 0


def test_changing_the_text_redraws_the_label():
    btn = play.new_button("Start")
    btn.update()
    before = pygame.image.tobytes(btn.image, "RGBA")
    btn.text = "Stop"
    assert btn.text == "Stop"
    btn.update()
    assert pygame.image.tobytes(btn.image, "RGBA") != before


def test_changing_the_text_colour_redraws_the_label():
    btn = play.new_button("Start", text_color="red")
    btn.update()
    btn.text_color = "green"
    btn.update()
    assert count_color(btn.image, color_name_to_rgb("green")) > 0
    assert count_color(btn.image, color_name_to_rgb("red")) == 0


@pytest.mark.parametrize(
    "mouse_xy, shown, not_shown",
    [((0, 0), "darkblue", "blue"), ((999, 999), "blue", "darkblue")],
    ids=["hovered", "resting"],
)
def test_a_button_shows_its_hover_colour_only_under_the_mouse(
    mouse_xy, shown, not_shown
):
    btn = play.new_button(
        x=0, y=0, width=100, height=50, color="blue", hover_color="darkblue"
    )
    mouse.x, mouse.y = mouse_xy
    btn.update()
    assert count_color(btn.image, color_name_to_rgb(shown)) > 0
    assert count_color(btn.image, color_name_to_rgb(not_shown)) == 0


@pytest.mark.parametrize("size, expected", [(100, (160, 50)), (50, (80, 25))])
def test_a_button_is_drawn_at_its_width_and_height_times_its_size(size, expected):
    btn = play.new_button(width=160, height=50, size=size)
    assert btn.image.get_size() == expected
