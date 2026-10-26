import pytest
import play
import pygame


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_a_clone_copies_what_the_sprite_has_become():
    s1 = play.new_box(color="red", x=10, y=20, width=50, height=50)
    s1.angle = 45
    s1.transparency = 50
    s1.x = -30
    s1.update()

    s2 = s1.clone()

    assert (s2.x, s2.y, s2.angle, s2.transparency) == (-30, 20, 45, 50)
    assert (s2.width, s2.height) == (50, 50)
    assert s2.rect == s1.rect
    assert pygame.image.tobytes(s2.image, "RGBA") == pygame.image.tobytes(
        s1.image, "RGBA"
    )


def test_a_clone_of_an_anchored_sprite_sits_in_the_same_place_and_layer():
    s1 = play.new_box(width=40, height=30, anchor="top-left", x=20, y=15, layer=3)
    s1.update()

    s2 = s1.clone()
    s2.update()

    assert s2.rect == s1.rect
    assert s2.layer == 3


def test_a_clone_has_a_body_of_its_own():
    s1 = play.new_box(color="red", x=10, y=20, width=50, height=50)
    s2 = s1.clone()
    assert s2.is_touching((10, 20))

    s2.x = 200

    assert s2.is_touching((200, 20))
    assert s1.is_touching((10, 20))
    assert not s1.is_touching((200, 20))


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

    s1.update()
    assert s1.rect.topleft == (
        play.screen.width / 2 + s1.left,
        play.screen.height / 2 - s1.top,
    )


def test_a_removed_sprite_is_no_longer_drawn_and_removing_it_again_is_harmless():
    s1 = play.new_box(color="blue", x=0, y=0, width=100, height=100)
    from play.globals import globals_list

    assert s1 in globals_list.sprites_group

    s1.remove()
    s1.remove()

    assert s1 not in globals_list.sprites_group
    assert not s1.is_touching((0, 0))


def test_sprite_is_touching_point():
    s1 = play.new_box(color="blue", x=0, y=0, width=100, height=100)

    assert s1.is_touching((0, 0)) is True
    assert s1.is_touching((200, 200)) is False

    # Test point touching sprite func
    from play.objects.sprite import point_touching_sprite

    assert point_touching_sprite((0, 0), s1) is True


def test_hidden_sprite_point_touch_is_symmetric():
    # Regression: hidden sprites are non-interactive on BOTH point-hit paths.
    from play.objects.sprite import point_touching_sprite

    s = play.new_box(color="blue", x=0, y=0, width=100, height=100)
    assert s.is_touching((0, 0)) is True
    s.hide()
    assert point_touching_sprite((0, 0), s) is False
    assert s.is_touching((0, 0)) is False


def test_a_removed_sprite_touches_nothing():
    from play.objects.sprite import point_touching_sprite

    coin = play.new_circle(x=10, radius=10)
    player = play.new_box(width=50, height=50)
    assert coin.is_touching(player)

    coin.remove()

    assert not coin.is_touching(player)
    assert not player.is_touching(coin)
    assert not coin.is_touching((10, 0))
    assert not point_touching_sprite((10, 0), coin)


def test_moving_a_sprite_is_seen_by_is_touching_straight_away():
    coin = play.new_circle(x=300, radius=10)
    player = play.new_box(width=50, height=50)

    coin.x = 0
    assert coin.is_touching(player)
    assert coin.is_touching((0, 0))

    coin.y = 200
    assert not coin.is_touching(player)


def test_moving_a_static_sprite_is_seen_by_is_touching_straight_away():
    wall = play.new_box(x=300, width=20, height=200)
    wall.start_physics(can_move=False)
    ball = play.new_circle(radius=10)

    wall.x = 0

    assert ball.is_touching(wall)


def test_a_hidden_or_removed_sprite_touches_no_wall():
    box = play.new_box(x=play.screen.right - 10, width=40, height=40)
    assert box.is_touching_wall()

    box.hide()
    assert box.get_touching_walls() == []
    box.show()
    assert box.is_touching_wall()

    box.remove()
    assert not box.is_touching_wall()
