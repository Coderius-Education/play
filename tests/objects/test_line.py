"""Tests for Line object creation and properties."""
import pytest
import sys
import math
sys.path.insert(0, ".")


def test_line_creation_default():
    """Test creating a line object with default values."""
    import play

    line = play.new_line()

    assert line.x == 0
    assert line.y == 0
    assert line.color == "black"
    assert line.thickness == 1
    assert line.length == 100
    assert line.angle == 0


def test_line_creation_with_length_angle():
    """Test creating a line with length and angle."""
    import play

    line = play.new_line(
        x=50,
        y=60,
        length=200,
        angle=45,
        color="red",
        thickness=5
    )

    assert line.x == 50
    assert line.y == 60
    assert line.length == 200
    assert line.angle == 45
    assert line.color == "red"
    assert line.thickness == 5


def test_line_creation_with_endpoint():
    """Test creating a line with x1, y1 endpoint."""
    import play

    line = play.new_line(
        x=0,
        y=0,
        x1=100,
        y1=100,
        color="blue",
        thickness=3
    )

    assert line.x == 0
    assert line.y == 0
    assert line.x1 == 100
    assert line.y1 == 100
    assert line.color == "blue"
    assert line.thickness == 3


def test_line_color_setter():
    """Test setting the color property."""
    import play

    line = play.new_line(color="green")
    assert line.color == "green"

    line.color = "yellow"
    assert line.color == "yellow"


def test_line_thickness_setter():
    """Test setting the thickness property."""
    import play

    line = play.new_line(thickness=2)
    assert line.thickness == 2

    line.thickness = 10
    assert line.thickness == 10


def test_line_length_setter():
    """Test setting the length property."""
    import play

    line = play.new_line(length=100, angle=0)
    assert line.length == 100

    line.length = 200
    assert line.length == 200


def test_line_angle_setter():
    """Test setting the angle property."""
    import play

    line = play.new_line(angle=0)
    assert line.angle == 0

    line.angle = 90
    assert line.angle == 90


def test_line_endpoint_calculation():
    """Test that endpoint is calculated correctly from length and angle."""
    import play

    # Horizontal line to the right
    line = play.new_line(x=0, y=0, length=100, angle=0)
    assert abs(line.x1 - 100) < 0.1
    assert abs(line.y1 - 0) < 0.1

    # Vertical line upward (90 degrees)
    line = play.new_line(x=0, y=0, length=100, angle=90)
    assert abs(line.x1 - 0) < 0.1
    assert abs(line.y1 - 100) < 0.1


def test_line_length_angle_calculation():
    """Test that length and angle are calculated from endpoints."""
    import play

    # Horizontal line
    line = play.new_line(x=0, y=0, x1=100, y1=0)
    assert abs(line.length - 100) < 0.1
    assert abs(line.angle - 0) < 0.1

    # Diagonal line
    line = play.new_line(x=0, y=0, x1=100, y1=100)
    expected_length = math.sqrt(100**2 + 100**2)
    assert abs(line.length - expected_length) < 0.1


def test_line_x1_setter():
    """Test setting x1 property."""
    import play

    line = play.new_line(x=0, y=0, x1=100, y1=0)
    assert line.x1 == 100

    line.x1 = 200
    assert line.x1 == 200


def test_line_y1_setter():
    """Test setting y1 property."""
    import play

    line = play.new_line(x=0, y=0, x1=0, y1=100)
    assert line.y1 == 100

    line.y1 = 200
    assert line.y1 == 200


def test_line_position_setters():
    """Test setting x and y positions."""
    import play

    line = play.new_line(x=50, y=60)
    assert line.x == 50
    assert line.y == 60

    line.x = 100
    line.y = 200
    assert line.x == 100
    assert line.y == 200


def test_line_clone():
    """Test cloning a line object."""
    import play

    line1 = play.new_line(
        x=50,
        y=60,
        length=200,
        angle=45,
        color="purple",
        thickness=7
    )

    line2 = line1.clone()

    assert line2.x == line1.x
    assert line2.y == line1.y
    assert line2.length == line1.length
    assert line2.color == line1.color
    assert line2.thickness == line1.thickness

    # Verify they are different objects
    assert line1 is not line2


def test_line_hide_show():
    """Test hiding and showing line."""
    import play

    line = play.new_line()
    assert line.is_hidden == False

    line.hide()
    assert line.is_hidden == True

    line.show()
    assert line.is_hidden == False


def test_line_size_property():
    """Test size property."""
    import play

    line = play.new_line(size=100)
    assert line.size == 100

    line.size = 200
    assert line.size == 200
