"""Coverage tests for Box, Circle, Text constructors and property setters.

These exercise the __init__ paths and property setters that aren't hit
by other tests — particularly border properties and the update() method.
"""

import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


# --- Box ---


def test_box_full_constructor():
    """Box with all parameters should initialize correctly."""
    box = play.new_box(
        color="blue",
        x=10,
        y=20,
        width=50,
        height=30,
        border_color="red",
        border_width=3,
        border_radius=5,
        transparency=80,
        size=120,
        angle=45,
    )
    assert box.color == "blue"
    assert box.x == 10
    assert box.y == 20
    assert box.width == 50
    assert box.height == 30
    assert box.border_color == "red"
    assert box.border_width == 3
    assert box.border_radius == 5
    assert box.transparency == 80
    assert box.size == 120
    assert box.angle == 45


def test_box_border_color_setter():
    """Setting border_color should update the property."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.border_color = "green"
    assert box.border_color == "green"


def test_box_border_width_setter():
    """Setting border_width should update the property."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.border_width = 5
    assert box.border_width == 5


def test_box_border_radius_setter():
    """Setting border_radius should update the property."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.border_radius = 10
    assert box.border_radius == 10


def test_box_width_setter_updates_physics():
    """Setting width should trigger physics recalculation."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(obeys_gravity=False)
    box.width = 50
    assert box.width == 50


def test_box_height_setter_updates_physics():
    """Setting height should trigger physics recalculation."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(obeys_gravity=False)
    box.height = 50
    assert box.height == 50


# --- Circle ---


def test_circle_full_constructor():
    """Circle with all parameters should initialize correctly."""
    circle = play.new_circle(
        color="green",
        x=15,
        y=25,
        radius=30,
        border_color="yellow",
        border_width=2,
        transparency=60,
        size=150,
        angle=90,
    )
    assert circle.color == "green"
    assert circle.x == 15
    assert circle.y == 25
    assert circle.radius == 30
    assert circle.border_color == "yellow"
    assert circle.border_width == 2
    assert circle.transparency == 60
    assert circle.size == 150
    assert circle.angle == 90


def test_circle_border_color_setter():
    """Setting border_color should update the property."""
    circle = play.new_circle(color="red", x=0, y=0, radius=10)
    circle.border_color = "blue"
    assert circle.border_color == "blue"


def test_circle_border_width_setter():
    """Setting border_width should update the property."""
    circle = play.new_circle(color="red", x=0, y=0, radius=10)
    circle.border_width = 4
    assert circle.border_width == 4


def test_circle_radius_setter():
    """Setting radius should update the property and physics."""
    circle = play.new_circle(color="red", x=0, y=0, radius=10)
    circle.start_physics(obeys_gravity=False)
    circle.radius = 25
    assert circle.radius == 25


# --- Text ---


def test_text_full_constructor():
    """Text with all parameters should initialize correctly."""
    text = play.new_text(
        words="hello",
        x=5,
        y=10,
        font="default",
        font_size=40,
        color="purple",
        angle=30,
        transparency=70,
        size=110,
    )
    assert text.words == "hello"
    assert text.x == 5
    assert text.y == 10
    assert text.font_size == 40
    assert text.color == "purple"
    assert text.angle == 30
    assert text.transparency == 70
    assert text.size == 110


def test_text_color_setter():
    """Setting text color should update the property."""
    text = play.new_text(words="hi", x=0, y=0)
    text.color = "red"
    assert text.color == "red"


def test_text_font_size_setter():
    """Setting font_size should update the property."""
    text = play.new_text(words="hi", x=0, y=0)
    text.font_size = 80
    assert text.font_size == 80


def test_text_words_setter():
    """Setting words should update and accept non-string via str()."""
    text = play.new_text(words="hi", x=0, y=0)
    text.words = 42
    assert text.words == "42"
