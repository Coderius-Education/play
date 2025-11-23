"""Tests for utility functions."""
import pytest
import sys
sys.path.insert(0, ".")


def test_clamp_within_range():
    """Test clamp function with value within range."""
    from play.utils import clamp

    assert clamp(5, 0, 10) == 5
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10


def test_clamp_below_min():
    """Test clamp function with value below minimum."""
    from play.utils import clamp

    assert clamp(-5, 0, 10) == 0
    assert clamp(-100, 0, 10) == 0


def test_clamp_above_max():
    """Test clamp function with value above maximum."""
    from play.utils import clamp

    assert clamp(15, 0, 10) == 10
    assert clamp(100, 0, 10) == 10


def test_clamp_with_floats():
    """Test clamp function with float values."""
    from play.utils import clamp

    assert clamp(5.5, 0.0, 10.0) == 5.5
    assert clamp(-1.5, 0.0, 10.0) == 0.0
    assert clamp(15.5, 0.0, 10.0) == 10.0


def test_position_creation():
    """Test creating a Position object."""
    from play.utils import _Position

    pos = _Position(100, 200)
    assert pos.x == 100
    assert pos.y == 200


def test_position_getitem():
    """Test Position indexing."""
    from play.utils import _Position

    pos = _Position(100, 200)
    assert pos[0] == 100
    assert pos[1] == 200


def test_position_getitem_invalid_index():
    """Test Position indexing with invalid index."""
    from play.utils import _Position

    pos = _Position(100, 200)
    with pytest.raises(IndexError):
        _ = pos[2]


def test_position_setitem():
    """Test setting Position values by index."""
    from play.utils import _Position

    pos = _Position(100, 200)
    pos[0] = 150
    pos[1] = 250
    assert pos.x == 150
    assert pos.y == 250


def test_position_setitem_invalid_index():
    """Test setting Position with invalid index."""
    from play.utils import _Position

    pos = _Position(100, 200)
    with pytest.raises(IndexError):
        pos[2] = 300


def test_position_iter():
    """Test iterating over Position."""
    from play.utils import _Position

    pos = _Position(100, 200)
    x, y = pos
    assert x == 100
    assert y == 200


def test_position_len():
    """Test length of Position."""
    from play.utils import _Position

    pos = _Position(100, 200)
    assert len(pos) == 2


def test_color_name_to_rgb_valid():
    """Test color_name_to_rgb with valid color names."""
    from play.utils import color_name_to_rgb

    # Test basic colors
    red = color_name_to_rgb("red")
    assert red[0] == 255
    assert red[1] == 0
    assert red[2] == 0
    assert red[3] == 255  # default transparency

    blue = color_name_to_rgb("blue")
    assert blue[0] == 0
    assert blue[1] == 0
    assert blue[2] == 255


def test_color_name_to_rgb_with_transparency():
    """Test color_name_to_rgb with custom transparency."""
    from play.utils import color_name_to_rgb

    red = color_name_to_rgb("red", transparency=128)
    assert red[3] == 128


def test_color_name_to_rgb_variants():
    """Test color_name_to_rgb with different naming variants."""
    from play.utils import color_name_to_rgb

    # All these should work
    color1 = color_name_to_rgb("lightblue")
    color2 = color_name_to_rgb("light blue")
    color3 = color_name_to_rgb("light-blue")

    # All should produce the same result
    assert color1[:3] == color2[:3] == color3[:3]


def test_color_name_to_rgb_tuple_passthrough():
    """Test that tuples are passed through unchanged."""
    from play.utils import color_name_to_rgb

    color_tuple = (255, 128, 0)
    result = color_name_to_rgb(color_tuple)
    assert result == color_tuple


def test_color_name_to_rgb_invalid():
    """Test color_name_to_rgb with invalid color name."""
    from play.utils import color_name_to_rgb

    with pytest.raises(ValueError, match="You gave a color name we didn't understand"):
        color_name_to_rgb("not_a_real_color_12345")


def test_color_name_to_rgb_case_insensitive():
    """Test that color names are case insensitive."""
    from play.utils import color_name_to_rgb

    red1 = color_name_to_rgb("RED")
    red2 = color_name_to_rgb("red")
    red3 = color_name_to_rgb("Red")

    assert red1[:3] == red2[:3] == red3[:3]
