"""Property-based tests for play.utils."""

import pygame
import pytest
from hypothesis import given, strategies as st

# We need pygame to be initialized for color name resolution
pygame.init()

from play.utils import clamp, color_name_to_rgb


@given(
    num=st.floats(allow_nan=False, allow_infinity=False),
    min_=st.floats(allow_nan=False, allow_infinity=False),
    max_=st.floats(allow_nan=False, allow_infinity=False),
)
def test_clamp_properties(num, min_, max_):
    """
    Test properties of the clamp function.
    """
    # Ensure min_ is less than or equal to max_ for proper clamping logic
    if min_ > max_:
        min_, max_ = max_, min_

    result = clamp(num, min_, max_)

    # 1. Result should be within bounds
    assert min_ <= result <= max_

    # 2. Idempotence: clamping twice should yield the same result
    assert clamp(result, min_, max_) == result

    # 3. If num is within bounds, it should remain unchanged
    if min_ <= num <= max_:
        assert result == num


@given(
    name=st.sampled_from(
        [
            "red",
            "blue",
            "green",
            "black",
            "white",
            "LightBlue",
            "light blue",
            "light-blue",
        ]
    ),
    transparency=st.integers(min_value=0, max_value=255),
)
def test_color_name_to_rgb_valid_strings(name, transparency):
    """
    Test color_name_to_rgb with valid string inputs and arbitrary transparencies.
    """
    result = color_name_to_rgb(name, transparency)

    assert isinstance(result, tuple)
    assert len(result) == 4

    # Check that each component is a valid color channel byte (0-255)
    for channel in result:
        assert isinstance(channel, int)
        assert 0 <= channel <= 255

    # Ensure the transparency is correctly applied to the alpha channel
    assert result[3] == transparency


@given(
    color_tuple=st.tuples(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
    )
)
def test_color_name_to_rgb_passthrough_tuples(color_tuple):
    """
    Test that providing a tuple right back out.
    """
    result = color_name_to_rgb(color_tuple)
    assert result == color_tuple


@given(st.text())
def test_color_name_to_rgb_invalid_strings(invalid_name):
    """
    Test that invalid color strings raise ValueError.
    """
    # Filter out strings that might actually be valid Pygame colors
    valid_pygame_colors = [c.lower() for c in pygame.color.THECOLORS.keys()]
    test_name = invalid_name.lower().strip().replace("-", "").replace(" ", "")

    if test_name not in valid_pygame_colors:
        with pytest.raises(
            ValueError, match="You gave a color name we didn't understand"
        ):
            color_name_to_rgb(invalid_name)
