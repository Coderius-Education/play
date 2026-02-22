"""Tests for Circle sprite properties."""

import pytest



def test_circle_color_getter():
    """Test getting circle color."""
    import play

    circle = play.new_circle(color="red")
    circle.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(circle.color)
        play.stop_program()

    play.start_program()

    assert result[0] == "red"


def test_circle_color_setter():
    """Test setting circle color."""
    import play

    circle = play.new_circle(color="red")
    circle.start_physics()

    result = []

    @play.when_program_starts
    def check():
        circle.color = "blue"
        result.append(circle.color)
        play.stop_program()

    play.start_program()

    assert result[0] == "blue"


def test_circle_radius_getter():
    """Test getting circle radius."""
    import play

    circle = play.new_circle(radius=50)
    circle.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(circle.radius)
        play.stop_program()

    play.start_program()

    assert result[0] == 50


def test_circle_radius_setter():
    """Test setting circle radius."""
    import play

    circle = play.new_circle(radius=50)
    circle.start_physics()

    result = []

    @play.when_program_starts
    def check():
        circle.radius = 100
        result.append(circle.radius)
        play.stop_program()

    play.start_program()

    assert result[0] == 100


def test_circle_border_color():
    """Test circle border_color property."""
    import play

    circle = play.new_circle(border_color="green", border_width=2)
    circle.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(circle.border_color)
        circle.border_color = "yellow"
        result.append(circle.border_color)
        play.stop_program()

    play.start_program()

    assert result[0] == "green"
    assert result[1] == "yellow"


def test_circle_border_width():
    """Test circle border_width property."""
    import play

    circle = play.new_circle(border_width=5)
    circle.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(circle.border_width)
        circle.border_width = 10
        result.append(circle.border_width)
        play.stop_program()

    play.start_program()

    assert result[0] == 5
    assert result[1] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
