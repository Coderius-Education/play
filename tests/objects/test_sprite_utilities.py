import pytest
import play
import io
import contextlib
import pygame


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_sprite_distance_to():
    s1 = play.new_circle(color="red", x=0, y=0, radius=10)
    s2 = play.new_circle(color="blue", x=30, y=40, radius=10)

    # Test distance string matching
    assert s1.distance_to(s2) == 50.0
    assert s2.distance_to(s1) == 50.0

    # Test point
    assert s1.distance_to(30, 40) == 50.0

    # Test bad arguments
    with pytest.raises(ValueError):
        s1.distance_to(30)  # Missing y


def test_sprite_clone():
    s1 = play.new_box(color="red", x=10, y=20, width=50, height=50)
    s1.angle = 45
    s1.transparency = 50

    # Clone it
    s2 = s1.clone()
    assert s2.x == 10
    assert s2.y == 20
    assert s2.angle == 45
    assert s2.transparency == 50
    assert s2.width == 50
    assert s2.height == 50


def test_sprite_hide_show():
    s1 = play.new_box(color="red", x=0, y=0, width=10, height=10)

    assert s1.is_hidden is False
    assert s1.is_shown is True

    s1.hide()
    assert s1.is_hidden is True
    assert s1.is_shown is False

    # Does not crash if already hidden
    s1.hide()

    s1.show()
    assert s1.is_hidden is False

    s1.is_hidden = True
    assert s1.is_hidden is True

    s1.is_shown = True
    assert s1.is_shown is True


def test_sprite_rect_properties():
    s1 = play.new_box(color="red", x=0, y=0, width=20, height=30)

    # Initial bounds
    assert s1.left == -10
    assert s1.right == 10
    assert s1.top == 15
    assert s1.bottom == -15

    # Modify bounds
    s1.left = 100
    assert s1.x == 110
    assert s1.left == 100
    assert s1.right == 120

    s1.right = -50
    assert s1.x == -60
    assert s1.right == -50

    s1.top = 100
    assert s1.y == 85
    assert s1.top == 100

    s1.bottom = -100
    assert s1.y == -85
    assert s1.bottom == -100

    # pygame coords
    assert isinstance(s1._pygame_x(), float)
    assert isinstance(s1._pygame_y(), float)


def test_sprite_info_output():
    s1 = play.new_circle(color="red", x=10, y=20, radius=50)
    s2 = play.new_box(color="blue", x=0, y=0, width=100, height=100)

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        s1.info()
        s2.info()

    output = stdout.getvalue()
    assert "Circle" in output
    assert "Box" in output
    assert "radius=50" in output
    assert "width=100" in output
    assert "Color: red" in output
    assert "Color: blue" in output


def test_sprite_physics_info_output():
    s1 = play.new_box(color="blue", x=0, y=0, width=100, height=100)

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        # Without physics
        s1.physics = None
        s1.physics_info()

        # With physics
        s1.start_physics(can_move=True, stable=False)
        s1.physics_info()

        # Physics stop
        s1.stop_physics()
        s1.physics_info()

    output = stdout.getvalue()
    assert "This sprite has no physics" in output
    assert "DYNAMIC" in output
    assert "KINEMATIC" in output


def test_sprite_remove():
    s1 = play.new_box(color="blue", x=0, y=0, width=100, height=100)
    from play.globals import globals_list

    assert s1 in globals_list.sprites_group

    s1.remove()
    assert s1 not in globals_list.sprites_group

    # Removing again should not crash
    s1.remove()


def test_sprite_is_touching_point():
    s1 = play.new_box(color="blue", x=0, y=0, width=100, height=100)

    assert s1.is_touching((0, 0)) is True
    assert s1.is_touching((200, 200)) is False

    # Test point touching sprite func
    from play.objects.sprite import point_touching_sprite

    assert point_touching_sprite((0, 0), s1) is True
