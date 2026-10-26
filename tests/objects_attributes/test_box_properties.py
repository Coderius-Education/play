"""What changing a box's properties does to the box on screen."""

import pygame
import pytest

import play
from tests.conftest import color_at

RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)


def test_a_new_box_colour_is_drawn_on_the_next_frame():
    box = play.new_box(color="red", width=20, height=20)
    assert color_at(box, 10, 10) == RED

    box.color = "blue"
    box.update()

    assert box.color == "blue"
    assert color_at(box, 10, 10) == BLUE


@pytest.mark.parametrize("prop", ["color", "border_color"])
def test_a_mistyped_box_colour_is_refused_where_it_is_set(prop):
    box = play.new_box(color="red", border_color="red")

    with pytest.raises(ValueError, match="blu"):
        setattr(box, prop, "blu")

    assert getattr(box, prop) == "red"


def test_the_border_is_drawn_in_its_own_colour_on_every_side():
    box = play.new_box(
        color="white", width=40, height=30, border_color="red", border_width=5
    )

    for x, y in [(2, 15), (37, 15), (20, 2), (20, 27)]:
        assert color_at(box, x, y) == RED, (x, y)
    for x, y in [(6, 15), (33, 15), (20, 6), (20, 23)]:
        assert color_at(box, x, y) == WHITE, (x, y)


def test_a_box_border_set_later_is_drawn_too():
    box = play.new_box(color="white", width=40, height=30)
    assert color_at(box, 2, 15) == WHITE

    box.border_width = 5
    box.border_color = "blue"
    box.update()

    assert (box.border_width, box.border_color) == (5, "blue")
    assert color_at(box, 2, 15) == BLUE
    assert color_at(box, 20, 15) == WHITE


@pytest.mark.parametrize("border_width", [0, 3])
def test_a_border_radius_rounds_the_corners(border_width):
    box = play.new_box(
        color="red", width=40, height=40, border_radius=12, border_width=border_width
    )
    assert box.image.get_at((0, 0)).a == 0
    assert box.image.get_at((20, 20)).a == 255

    box.border_radius = 0
    box.update()

    assert box.border_radius == 0
    assert box.image.get_at((0, 0)).a == 255


def test_the_inside_of_a_bordered_box_is_rounded_as_well():
    box = play.new_box(
        color="white",
        width=60,
        height=60,
        border_color="red",
        border_width=3,
        border_radius=15,
    )

    assert color_at(box, 4, 4) != WHITE


@pytest.mark.parametrize(
    "prop, point",
    [("width", (90, 0)), ("height", (0, 90))],
)
def test_resizing_a_box_changes_what_is_drawn_and_what_can_be_touched(prop, point):
    box = play.new_box(width=100, height=100)
    assert not box.is_touching(point)

    setattr(box, prop, 200)
    box.update()

    assert getattr(box, prop) == 200
    assert box.image.get_size() == ((200, 100) if prop == "width" else (100, 200))
    assert box.is_touching(point)


def test_a_cloned_box_looks_exactly_like_the_original():
    box = play.new_box(
        color="green",
        x=40,
        y=-30,
        width=60,
        height=40,
        border_color="red",
        border_width=4,
        border_radius=9,
        transparency=70,
        size=150,
        angle=20,
    )

    clone = box.clone()

    assert clone is not box
    assert clone.rect == box.rect
    assert pygame.image.tobytes(clone.image, "RGBA") == pygame.image.tobytes(
        box.image, "RGBA"
    )
