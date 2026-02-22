"""Tests for random utility functions."""

import pytest


def test_random_number_default():
    """Test random_number with default parameters."""
    import play

    for _ in range(10):
        num = play.random_number()
        assert 0 <= num <= 100


def test_random_number_custom_range():
    """Test random_number with custom range."""
    import play

    for _ in range(10):
        num = play.random_number(50, 150)
        assert 50 <= num <= 150


def test_random_number_integers():
    """Test that random_number returns integers when given integers."""
    import play

    for _ in range(10):
        num = play.random_number(1, 10)
        assert isinstance(num, int)


def test_random_number_floats():
    """Test that random_number returns floats when given floats."""
    import play

    for _ in range(10):
        num = play.random_number(1.0, 10.0)
        assert isinstance(num, float)


def test_random_number_mixed_types():
    """Test random_number with mixed int and float."""
    import play

    for _ in range(10):
        num = play.random_number(1, 10.0)
        assert isinstance(num, float)


def test_random_number_negative_range():
    """Test random_number with negative numbers."""
    import play

    for _ in range(10):
        num = play.random_number(-50, -10)
        assert -50 <= num <= -10


def test_random_number_zero_range():
    """Test random_number with same min and max."""
    import play

    num = play.random_number(42, 42)
    assert num == 42


def test_random_color():
    """Test random_color returns valid RGB tuple."""
    import play

    for _ in range(10):
        color = play.random_color()
        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(0 <= c <= 255 for c in color)
        assert all(isinstance(c, int) for c in color)


def test_random_position_default():
    """Test random_position with default screen bounds."""
    import play

    for _ in range(10):
        pos = play.random_position()
        # Position should have x and y attributes
        assert hasattr(pos, "x")
        assert hasattr(pos, "y")
        # Values should be numbers
        assert isinstance(pos.x, (int, float))
        assert isinstance(pos.y, (int, float))


def test_random_position_custom_bounds():
    """Test random_position with custom bounds."""
    import play

    for _ in range(10):
        pos = play.random_position(x_min=0, x_max=100, y_min=0, y_max=100)
        assert 0 <= pos.x <= 100
        assert 0 <= pos.y <= 100


def test_random_position_indexing():
    """Test that random_position returns indexable object."""
    import play

    pos = play.random_position(x_min=0, x_max=100, y_min=0, y_max=100)
    # Should support indexing
    assert pos[0] == pos.x
    assert pos[1] == pos.y


def test_random_position_unpacking():
    """Test that random_position can be unpacked."""
    import play

    pos = play.random_position(x_min=0, x_max=100, y_min=0, y_max=100)
    x, y = pos
    assert x == pos.x
    assert y == pos.y


def test_random_position_negative_bounds():
    """Test random_position with negative bounds."""
    import play

    for _ in range(10):
        pos = play.random_position(x_min=-100, x_max=-50, y_min=-100, y_max=-50)
        assert -100 <= pos.x <= -50
        assert -100 <= pos.y <= -50
