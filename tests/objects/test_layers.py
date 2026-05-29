import pytest
import play
from play.globals import globals_list

YELLOW_JPG = "tests/objects_attributes/yellow.jpg"


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_box_default_layer():
    assert play.new_box().layer == 0


def test_text_default_layer():
    assert play.new_text("hello").layer == 0


def test_circle_default_layer():
    assert play.new_circle().layer == 0


def test_image_default_layer():
    assert play.new_image(YELLOW_JPG).layer == 0


def test_button_default_layer():
    assert play.new_button().layer == 10


def test_custom_layer_stored():
    box = play.new_box(layer=5)
    assert box.layer == 5


def test_sprite_added_to_correct_group_layer():
    box = play.new_box(layer=3)
    assert globals_list.sprites_group.get_layer_of_sprite(box) == 3


def test_layer_setter_moves_sprite_in_group():
    box = play.new_box(layer=0)
    box.layer = 7
    assert globals_list.sprites_group.get_layer_of_sprite(box) == 7


def test_draw_order_lower_layer_first():
    a = play.new_box(layer=0)
    b = play.new_box(layer=5)
    sprites = globals_list.sprites_group.sprites()
    assert sprites.index(a) < sprites.index(b)
