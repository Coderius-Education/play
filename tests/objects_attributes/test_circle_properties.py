"""What changing a circle's properties does to the circle on screen."""

import pygame
import pytest

import play

RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)


def colour_at(sprite, x, y):
    """The RGB of the sprite's own picture at pixel (x, y)."""
    return tuple(sprite.image.get_at((x, y)))[:3]


def test_a_new_circle_colour_is_drawn_on_the_next_frame():
    circle = play.new_circle(color="red", radius=20)
    assert colour_at(circle, 20, 20) == RED

    circle.color = "blue"
    circle.update()

    assert circle.color == "blue"
    assert colour_at(circle, 20, 20) == BLUE


@pytest.mark.parametrize("prop", ["color", "border_color"])
def test_a_mistyped_circle_colour_is_refused_where_it_is_set(prop):
    circle = play.new_circle(color="red", border_color="red")

    with pytest.raises(ValueError, match="blu"):
        setattr(circle, prop, "blu")

    assert getattr(circle, prop) == "red"


def test_the_border_is_a_ring_in_its_own_colour():
    circle = play.new_circle(
        color="white", radius=20, border_color="red", border_width=5
    )

    assert colour_at(circle, 2, 20) == RED
    assert colour_at(circle, 20, 2) == RED
    assert colour_at(circle, 20, 20) == WHITE


def test_a_circle_border_set_later_is_drawn_too():
    circle = play.new_circle(color="white", radius=20)
    assert colour_at(circle, 2, 20) == WHITE

    circle.border_width = 5
    circle.border_color = "blue"
    circle.update()

    assert (circle.border_width, circle.border_color) == (5, "blue")
    assert colour_at(circle, 2, 20) == BLUE
    assert colour_at(circle, 20, 20) == WHITE


def test_a_new_radius_changes_what_is_drawn_and_what_can_be_touched():
    circle = play.new_circle(radius=50)
    assert not circle.is_touching((90, 0))

    circle.radius = 100
    circle.update()

    assert circle.radius == 100
    assert circle.image.get_size() == (200, 200)
    assert circle.is_touching((90, 0))


def test_a_cloned_circle_looks_exactly_like_the_original():
    circle = play.new_circle(
        color="green",
        x=-40,
        y=25,
        radius=30,
        border_color="red",
        border_width=6,
        transparency=60,
        size=150,
        angle=90,
    )

    clone = circle.clone()

    assert clone is not circle
    assert clone.rect == circle.rect
    assert pygame.image.tobytes(clone.image, "RGBA") == pygame.image.tobytes(
        circle.image, "RGBA"
    )
