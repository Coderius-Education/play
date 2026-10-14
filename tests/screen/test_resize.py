"""Tests for play.screen.resize method."""

import pytest


def test_screen_resize_before_sprites():
    """Test resizing screen before creating sprites."""
    import play

    play.screen.resize(1800, 900)

    assert play.screen.width == 1800
    assert play.screen.height == 900


def test_screen_resize_updates_boundaries():
    """Test that resize updates screen boundary properties."""
    import play

    play.screen.resize(800, 600)

    assert play.screen.top == 300
    assert play.screen.bottom == -300
    assert play.screen.left == -400
    assert play.screen.right == 400


def test_screen_resize_updates_size_tuple():
    """Test that resize updates the size property."""
    import play

    play.screen.resize(1000, 500)

    assert play.screen.size == (1000, 500)


def test_screen_resize_after_sprites_raises_error():
    """Test that resizing after creating sprites raises RuntimeError."""
    import play

    play.new_circle()

    with pytest.raises(RuntimeError) as exc_info:
        play.screen.resize(1200, 800)

    assert "Screen must be resized before creating sprites" in str(exc_info.value)
    assert "1 sprite" in str(exc_info.value)


def test_screen_resize_after_multiple_sprites_shows_plural():
    """Test error message uses plural when multiple sprites exist."""
    import play

    play.new_circle()
    play.new_box()
    play.new_text("test")

    with pytest.raises(RuntimeError) as exc_info:
        play.screen.resize(1200, 800)

    assert "3 sprites" in str(exc_info.value)


def test_screen_resize_with_different_dimensions():
    """Test resizing to various dimensions."""
    import play

    test_dimensions = [
        (400, 300),
        (1920, 1080),
        (640, 480),
        (1024, 768),
    ]

    for width, height in test_dimensions:
        play.screen.resize(width, height)
        assert play.screen.width == width
        assert play.screen.height == height
        assert play.screen.size == (width, height)


def test_screen_resize_square_dimensions():
    """Test resizing to square dimensions."""
    import play

    play.screen.resize(500, 500)

    assert play.screen.width == 500
    assert play.screen.height == 500
    assert play.screen.left == -250
    assert play.screen.right == 250
    assert play.screen.top == 250
    assert play.screen.bottom == -250


def test_screen_resize_very_wide():
    """Test resizing to very wide dimensions."""
    import play

    play.screen.resize(2000, 400)

    assert play.screen.width == 2000
    assert play.screen.height == 400
    assert play.screen.left == -1000
    assert play.screen.right == 1000


def test_screen_resize_very_tall():
    """Test resizing to very tall dimensions."""
    import play

    play.screen.resize(400, 2000)

    assert play.screen.width == 400
    assert play.screen.height == 2000
    assert play.screen.top == 1000
    assert play.screen.bottom == -1000


def _wall_edges():
    """Where the four walls are, as (min x, max x, min y, max y)."""
    from play.globals import globals_list

    xs = [p.x for w in globals_list.walls for p in (w.a, w.b)]
    ys = [p.y for w in globals_list.walls for p in (w.a, w.b)]
    return min(xs), max(xs), min(ys), max(ys)


def test_resize_moves_the_walls_to_the_new_edges():
    import play

    play.screen.resize(400, 300)

    assert _wall_edges() == (-200, 200, -150, 150)


def test_a_ball_bounces_off_the_edge_after_a_resize():
    import play

    play.screen.resize(400, 300)
    ball = play.new_circle(radius=10)
    ball.start_physics(x_speed=400, y_speed=0, obeys_gravity=False)
    furthest = [0]
    frames = [0]

    @play.repeat_forever
    def watch():
        furthest[0] = max(furthest[0], ball.x)
        frames[0] += 1
        if frames[0] == 60:  # a second: long enough to reach the old wall
            play.stop_program()

    play.start_program()

    assert furthest[0] <= play.screen.right


def test_setting_width_and_height_resizes_the_window_and_walls():
    import pygame
    import play

    play.screen.width = 400
    play.screen.height = 300

    assert pygame.display.get_surface().get_size() == (400, 300)
    assert _wall_edges() == (-200, 200, -150, 150)


def test_setting_resizable_takes_effect_straight_away(monkeypatch):
    import pygame
    import play

    flags = []
    real_set_mode = pygame.display.set_mode

    def set_mode(size, mode_flags=0, *args, **kwargs):
        flags.append(mode_flags)
        return real_set_mode(size, mode_flags, *args, **kwargs)

    monkeypatch.setattr(pygame.display, "set_mode", set_mode)

    play.screen.resizable = True

    assert flags and flags[-1] & pygame.RESIZABLE
