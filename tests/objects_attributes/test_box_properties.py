"""Tests for Box sprite properties."""

import pytest
import sys

sys.path.insert(0, ".")


def test_box_color_getter():
    """Test getting box color."""
    import play

    box = play.new_box(color="red")
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.color)
        play.stop_program()

    play.start_program()

    assert result[0] == "red"


def test_box_color_setter():
    """Test setting box color."""
    import play

    box = play.new_box(color="red")
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        box.color = "blue"
        result.append(box.color)
        play.stop_program()

    play.start_program()

    assert result[0] == "blue"


def test_box_border_color():
    """Test box border_color property."""
    import play

    box = play.new_box(border_color="green", border_width=2)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.border_color)
        box.border_color = "yellow"
        result.append(box.border_color)
        play.stop_program()

    play.start_program()

    assert result[0] == "green"
    assert result[1] == "yellow"


def test_box_border_width():
    """Test box border_width property."""
    import play

    box = play.new_box(border_width=5)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.border_width)
        box.border_width = 10
        result.append(box.border_width)
        play.stop_program()

    play.start_program()

    assert result[0] == 5
    assert result[1] == 10


def test_box_border_radius():
    """Test box border_radius property."""
    import play

    box = play.new_box(border_radius=15)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.border_radius)
        box.border_radius = 20
        result.append(box.border_radius)
        play.stop_program()

    play.start_program()

    assert result[0] == 15
    assert result[1] == 20


def test_box_width_setter():
    """Test setting box width after creation."""
    import play

    box = play.new_box(width=100)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.width)
        box.width = 200
        result.append(box.width)
        play.stop_program()

    play.start_program()

    assert result[0] == 100
    assert result[1] == 200


def test_box_height_setter():
    """Test setting box height after creation."""
    import play

    box = play.new_box(height=50)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.height)
        box.height = 100
        result.append(box.height)
        play.stop_program()

    play.start_program()

    assert result[0] == 50
    assert result[1] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
