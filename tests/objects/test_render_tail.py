"""The shared render tail: Sprite._finalize_image and Sprite._place_image.

Box, Circle, Text, Image, Video and the widgets all finish drawing through
these two, so a mistake there shows up everywhere at once.
"""

import pygame
import pytest

import play
from play.io.screen import convert_pos
from play.objects.image import Image


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


SPRITES = {
    "box, even size": lambda **kw: play.new_box(width=40, height=20, **kw),
    "box, odd size": lambda **kw: play.new_box(width=41, height=21, **kw),
    "circle": lambda **kw: play.new_circle(radius=15, **kw),
    "text": lambda **kw: play.new_text("Hi there", **kw),
    "image": lambda **kw: Image(pygame.Surface((21, 13)), **kw),
    "button": lambda **kw: play.new_button("Go", **kw),
}


@pytest.mark.parametrize("make", SPRITES.values(), ids=SPRITES.keys())
@pytest.mark.parametrize("x, y", [(0, 0), (13, -7)])
@pytest.mark.parametrize("angle", [0, 30], ids=["upright", "turned"])
def test_a_sprite_is_drawn_centred_on_its_position(make, x, y, angle):
    # Upright and turned sprites take different paths through _place_image.
    sprite = make(x=x, y=y)
    sprite.angle = angle
    sprite.update()
    assert sprite.rect.center == convert_pos(x, y)
    assert sprite.rect.size == sprite.image.get_size()


def test_a_text_made_at_an_angle_is_drawn_at_that_angle():
    # Text draws itself once before Sprite.__init__ builds its physics body,
    # using its own angle; nothing redraws it afterwards until something
    # changes, so that first drawing is what the student sees.
    upright = play.new_text("Hi there").image
    turned = play.new_text("Hi there", angle=45).image

    assert turned.get_size() == pygame.transform.rotate(upright, 45).get_size()


def test_an_image_never_changes_the_surface_it_was_given():
    # set_alpha goes on a scaled copy, even at size 100.
    source = pygame.Surface((21, 13))
    image = Image(source, transparency=40)
    image.update()

    assert image.image is not source
    assert source.get_alpha() is None
