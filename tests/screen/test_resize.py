"""Tests for play.screen.resize method."""

import pytest


@pytest.mark.parametrize(
    "width, height",
    [(1800, 900), (1000, 500), (400, 300), (500, 500), (2000, 400), (400, 2000)],
)
def test_resizing_before_any_sprites_sets_the_size_and_the_edges(width, height):
    import pygame
    import play

    play.screen.resize(width, height)

    assert (play.screen.width, play.screen.height) == (width, height)
    assert play.screen.size == (width, height)
    assert pygame.display.get_surface().get_size() == (width, height)
    assert (play.screen.left, play.screen.right) == (-width / 2, width / 2)
    assert (play.screen.bottom, play.screen.top) == (-height / 2, height / 2)


def test_screen_resize_after_sprites_raises_error():
    """Test that resizing after creating sprites raises RuntimeError."""
    import play

    play.new_circle()

    with pytest.raises(RuntimeError) as exc_info:
        play.screen.resize(1200, 800)

    assert "Screen must be resized before creating sprites" in str(exc_info.value)
    assert "creating 1 sprite.\n" in str(exc_info.value)


def test_screen_resize_after_multiple_sprites_shows_plural():
    """Test error message uses plural when multiple sprites exist."""
    import play

    play.new_circle()
    play.new_box()
    play.new_text("test")

    with pytest.raises(RuntimeError) as exc_info:
        play.screen.resize(1200, 800)

    assert "3 sprites" in str(exc_info.value)


def _wall_edges():
    """Where the inner faces of the four walls are, as (min x, max x, min y, max y)."""
    from play.globals import globals_list

    top, bottom, left, right = globals_list.walls
    return left.bb.right, right.bb.left, bottom.bb.top, top.bb.bottom


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


def test_dragging_the_window_bigger_runs_when_resized_with_the_new_size():
    import pygame
    import play

    sizes = []

    @play.screen.when_resized
    def on_resize():
        sizes.append(play.screen.size)

    @play.when_program_starts
    async def drag():
        await play.animate()
        pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE, {"w": 1000, "h": 700}))
        for _ in range(3):
            await play.animate()
        play.stop_program()

    play.start_program()

    assert sizes == [(1000, 700)]


def test_a_resizable_screen_says_so_and_asks_for_a_resizable_window(monkeypatch):
    import pygame
    import play

    flags_asked = []
    set_mode = pygame.display.set_mode

    def spy(size, flags=0, *args, **kwargs):
        flags_asked.append(flags)
        return set_mode(size, flags, *args, **kwargs)

    monkeypatch.setattr(pygame.display, "set_mode", spy)
    play.screen.resizable = True

    assert play.screen.resizable is True
    assert flags_asked[-1] & pygame.RESIZABLE
