"""Transparency (0 to 100) becomes the alpha (0 to 255) of what is drawn."""

import pygame
import pytest

import play

SPRITES = {
    "image": lambda **kw: play.new_image(image=pygame.Surface((20, 10)), **kw),
    "box": lambda **kw: play.new_box(**kw),
    "text": lambda **kw: play.new_text("Hi", **kw),
}


@pytest.mark.parametrize("make", SPRITES.values(), ids=SPRITES.keys())
@pytest.mark.parametrize("transparency, alpha", [(0, 0), (50, 128), (100, 255)])
def test_transparency_sets_the_alpha_of_the_drawing(make, transparency, alpha):
    assert make(transparency=transparency).image.get_alpha() == alpha


def test_a_new_transparency_is_drawn_on_the_next_frame():
    box = play.new_box()

    box.transparency = 25
    box.update()

    assert box.transparency == 25
    assert box.image.get_alpha() == 64


@pytest.mark.parametrize("wanted, kept, alpha", [(150, 100, 255), (-20, 0, 0)])
def test_a_transparency_outside_0_to_100_warns_and_is_clamped(wanted, kept, alpha):
    box = play.new_box()

    with pytest.warns(UserWarning, match="between 0 and 100"):
        box.transparency = wanted
    box.update()

    assert box.transparency == kept
    assert box.image.get_alpha() == alpha


def test_a_transparency_that_is_not_a_number_is_refused():
    box = play.new_box()

    with pytest.raises(ValueError, match="isn't a number"):
        box.transparency = "half"

    assert box.transparency == 100
