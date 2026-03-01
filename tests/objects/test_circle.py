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
