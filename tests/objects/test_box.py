import pytest
import play
import pygame


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_box_initialization():
    box = play.new_box(
        color="red",
        x=10,
        y=20,
        width=50,
        height=60,
        border_color="blue",
        border_width=2,
        border_radius=5,
    )

    assert box.x == 10
    assert box.y == 20
    assert box.width == 50
    assert box.height == 60
    assert box.color == "red"
    assert box.border_color == "blue"
    assert box.border_width == 2
    assert box.border_radius == 5


def test_box_setters_and_rendering():
    box = play.new_box(color="black", x=0, y=0, width=100, height=100)

    # Trigger missing lines: 95-99, 112-116, 129, 142, 155, 168
    box.width = 200
    assert box.width == 200

    box.height = 150
    assert box.height == 150

    box.color = "yellow"
    assert box.color == "yellow"

    box.border_color = "black"
    assert box.border_color == "black"

    box.border_width = 10
    assert box.border_width == 10

    box.border_radius = 5
    assert box.border_radius == 5

    # Trigger lines 68-70 scale logic
    box.size = 200

    # Call update manually to force the image rendering logic (Lines 47, 68-70)
    box.update()

    assert box.rect.width == 400  # 200 scaled by 200%
    assert box.rect.height == 300  # 150 scaled by 200%
