"""Tests for random utility functions."""

import pytest

import play
from play.io.screen import screen

DRAWS = 500


def test_random_number_default():
    """Test random_number with default parameters."""
    for _ in range(10):
        num = play.random_number()
        assert 0 <= num <= 100


def test_random_number_custom_range():
    """Test random_number with custom range."""
    for _ in range(10):
        num = play.random_number(50, 150)
        assert 50 <= num <= 150


def test_whole_number_bounds_give_whole_numbers_and_both_ends_can_come_up():
    numbers = [play.random_number(1, 10) for _ in range(DRAWS)]

    assert all(type(num) is int for num in numbers)
    assert set(numbers) == set(range(1, 11))


@pytest.mark.parametrize("lowest, highest", [(1.0, 10.0), (1, 10.0), (1.5, 2)])
def test_a_decimal_bound_gives_decimals_rounded_to_two_places(lowest, highest):
    numbers = [play.random_number(lowest, highest) for _ in range(DRAWS)]

    assert all(type(num) is float for num in numbers)
    assert all(lowest <= num <= highest for num in numbers)
    assert all(num == round(num, 2) for num in numbers)
    assert len(set(numbers)) > highest - lowest + 1


def test_random_number_negative_range():
    """Test random_number with negative numbers."""
    for _ in range(10):
        num = play.random_number(-50, -10)
        assert -50 <= num <= -10


def test_random_number_zero_range():
    """Test random_number with same min and max."""
    assert play.random_number(42, 42) == 42
    assert play.random_number(4.2, 4.2) == 4.2


def test_random_color_gives_three_channels_covering_the_full_range():
    colors = [play.random_color() for _ in range(5000)]

    assert all(len(color) == 3 for color in colors)
    assert all(type(c) is int and 0 <= c <= 255 for color in colors for c in color)
    for channel in range(3):
        values = [color[channel] for color in colors]
        assert (min(values), max(values)) == (0, 255)


def test_a_random_color_can_be_given_to_a_sprite():
    box = play.new_box(color=play.random_color())
    box.update()

    assert box.image.get_at(box.image.get_rect().center)[:3] == tuple(box.color)


def test_random_position_defaults_to_anywhere_on_the_screen():
    positions = [play.random_position() for _ in range(DRAWS)]

    assert all(screen.left <= x <= screen.right for x, _ in positions)
    assert all(screen.bottom <= y <= screen.top for _, y in positions)
    xs = [x for x, _ in positions]
    ys = [y for _, y in positions]
    assert min(xs) < screen.left / 2 and max(xs) > screen.right / 2
    assert min(ys) < screen.bottom / 2 and max(ys) > screen.top / 2


def test_random_position_follows_a_resized_screen():
    screen.resize(200, 100)

    positions = [play.random_position() for _ in range(DRAWS)]

    assert all(-100 <= x <= 100 and -50 <= y <= 50 for x, y in positions)
    assert max(x for x, _ in positions) > 50


def test_random_position_custom_bounds():
    """Test random_position with custom bounds."""
    for _ in range(10):
        pos = play.random_position(x_min=0, x_max=100, y_min=0, y_max=100)
        assert 0 <= pos.x <= 100
        assert 0 <= pos.y <= 100


def test_random_position_keeps_x_and_y_bounds_apart():
    for _ in range(10):
        pos = play.random_position(x_min=500, x_max=600, y_min=-20, y_max=-10)
        assert 500 <= pos.x <= 600
        assert -20 <= pos.y <= -10


def test_random_position_indexing():
    """Test that random_position returns indexable object."""
    pos = play.random_position(x_min=0, x_max=100, y_min=0, y_max=100)
    assert pos[0] == pos.x
    assert pos[1] == pos.y


def test_random_position_unpacking():
    """Test that random_position can be unpacked."""
    pos = play.random_position(x_min=0, x_max=100, y_min=0, y_max=100)
    x, y = pos
    assert x == pos.x
    assert y == pos.y


def test_random_position_negative_bounds():
    """Test random_position with negative bounds."""
    for _ in range(10):
        pos = play.random_position(x_min=-100, x_max=-50, y_min=-100, y_max=-50)
        assert -100 <= pos.x <= -50
        assert -100 <= pos.y <= -50


def test_random_number_raises_when_lowest_is_above_highest():
    with pytest.raises(ValueError, match=r"random_number\(1, 10\)"):
        play.random_number(10, 1)
    with pytest.raises(ValueError, match="lowest number first"):
        play.random_number(4.5, 1.5)
