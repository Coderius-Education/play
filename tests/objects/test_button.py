import pytest
import play
from play.io.mouse import mouse


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_button_creation():
    btn = play.new_button("OK")
    assert btn.text == "OK"
    assert btn.layer == 10
    assert btn.image is not None


def test_button_text_property_setter():
    btn = play.new_button("Start")
    btn.text = "Stop"
    assert btn.text == "Stop"
    # Setter must flag a redraw
    assert btn._should_recompute is True


def test_button_colors_stored():
    btn = play.new_button(color="blue", hover_color="darkblue")
    assert btn._base_color == "blue"
    assert btn._hover_color == "darkblue"


def test_button_alive():
    btn = play.new_button()
    assert btn.alive()


def test_button_hover_color_when_mouse_inside():
    btn = play.new_button(x=0, y=0, width=100, height=50)
    mouse.x = 0
    mouse.y = 0
    btn.update()
    assert btn._color == btn._hover_color


def test_button_base_color_when_mouse_outside():
    btn = play.new_button(x=0, y=0, width=100, height=50)
    mouse.x = 999
    mouse.y = 999
    btn.update()
    assert btn._color == btn._base_color


def test_button_image_has_nonzero_dimensions():
    btn = play.new_button(width=160, height=50)
    assert btn.image.get_width() > 0
    assert btn.image.get_height() > 0
