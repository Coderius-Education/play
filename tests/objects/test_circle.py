import pytest
import play
import pygame


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_circle_initialization():
    circle = play.new_circle(
        color="blue",
        x=30,
        y=40,
        radius=25,
        border_color="red",
        border_width=3,
        transparency=90,
    )

    assert circle.x == 30
    assert circle.y == 40
    assert circle.radius == 25
    assert circle.color == "blue"
    assert circle.border_color == "red"
    assert circle.border_width == 3
    assert circle.transparency == 90


def test_circle_setters_and_rendering():
    circle = play.new_circle(color="black", x=0, y=0, radius=50)

    # Trigger missing setter lines
    circle.radius = 100
    assert circle.radius == 100

    circle.color = "yellow"
    assert circle.color == "yellow"

    circle.border_color = "green"
    assert circle.border_color == "green"

    circle.border_width = 8
    assert circle.border_width == 8

    # Trigger lines 78-79 scale logic
    circle.size = 150

    # Force the render branch
    circle.update()

    # radius is 100, scaled to 150%, diameter should be 300
    assert circle.rect.width == 300
    assert circle.rect.height == 300


def test_a_scaled_circle_keeps_an_even_diameter():
    # The radius is rounded and doubled, so the centre stays on a whole pixel.
    # Rounding the diameter instead gave 5 here, with a half-pixel centre.
    small = play.new_circle(radius=5, size=50)
    small.update()
    assert small.image.get_size() == (4, 4)

    odd = play.new_circle(radius=21, size=50)
    odd.update()
    assert odd.image.get_size() == (20, 20)


def test_a_tiny_but_positive_circle_is_still_a_dot():
    # Only size <= 0 means "nothing": a radius that rounds to zero is floored
    # at one, so the circle stays a 2x2 dot rather than vanishing.
    tiny = play.new_circle(radius=20, size=1)
    tiny.update()
    assert tiny.image.get_size() == (2, 2)
