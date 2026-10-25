"""Asking play.mouse where it is: is_touching and distance_to."""

import pytest

import play
from play.io.mouse import mouse


def test_the_mouse_touches_a_sprite_it_is_over():
    box = play.new_box(x=100, y=-50, width=40, height=40)

    mouse.x, mouse.y = 110, -60

    assert mouse.is_touching(box) is True


@pytest.mark.parametrize(
    "x, y", [(-50, 100), (300, -50), (100, 200)], ids=["swapped", "right", "above"]
)
def test_the_mouse_does_not_touch_a_sprite_beside_it(x, y):
    box = play.new_box(x=100, y=-50, width=40, height=40)

    mouse.x, mouse.y = x, y

    assert mouse.is_touching(box) is False


def test_the_mouse_does_not_touch_a_hidden_sprite():
    box = play.new_box(width=40, height=40)
    box.hide()

    mouse.x, mouse.y = 0, 0

    assert mouse.is_touching(box) is False


@pytest.mark.parametrize(
    "mouse_at, point, distance",
    [((3, 4), (0, 0), 5), ((0, 0), (-6, 8), 10), ((10, 10), (10, 10), 0)],
)
def test_distance_to_measures_from_the_mouse_to_a_point(mouse_at, point, distance):
    mouse.x, mouse.y = mouse_at

    assert mouse.distance_to(*point) == pytest.approx(distance)


@pytest.mark.parametrize("point", [(None, 4), (3, None)])
def test_distance_to_needs_both_coordinates(point):
    with pytest.raises(AssertionError, match="must not be None"):
        mouse.distance_to(*point)
