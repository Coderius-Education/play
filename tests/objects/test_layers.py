import pygame
import pytest
import play
from play.globals import globals_list

YELLOW_JPG = "tests/objects_attributes/yellow.jpg"


@pytest.mark.parametrize(
    "make, layer",
    [
        (lambda: play.new_box(), 0),
        (lambda: play.new_text("hello"), 0),
        (lambda: play.new_circle(), 0),
        (lambda: play.new_image(YELLOW_JPG), 0),
        (lambda: play.new_button(), 10),
    ],
    ids=["box", "text", "circle", "image", "button"],
)
def test_default_layer(make, layer):
    sprite = make()

    assert sprite.layer == layer
    assert globals_list.sprites_group.get_layer_of_sprite(sprite) == layer


def test_a_custom_layer_is_the_layer_the_sprite_is_drawn_in():
    box = play.new_box(layer=3)

    assert box.layer == 3
    assert globals_list.sprites_group.get_layer_of_sprite(box) == 3


def test_layer_setter_moves_sprite_in_group():
    box = play.new_box(layer=0)
    box.layer = 7
    assert globals_list.sprites_group.get_layer_of_sprite(box) == 7


def test_a_higher_layer_is_drawn_on_top_whatever_the_order_of_creation():
    play.new_box(color="red", width=50, height=50, layer=5)
    play.new_box(color="blue", width=50, height=50, layer=0)
    frames = [0]
    centre = []

    @play.repeat_forever
    def look():
        frames[0] += 1
        if frames[0] == 2:
            centre.append(tuple(pygame.display.get_surface().get_at((400, 300)))[:3])
            play.stop_program()

    play.start_program()

    assert centre == [(255, 0, 0)]


def test_layer_setter_after_remove_does_not_raise():
    # Regression: LayeredUpdates.change_layer raises for non-members.
    box = play.new_box(layer=0)
    box.remove()
    box.layer = 3
    assert box.layer == 3
    assert box not in globals_list.sprites_group
