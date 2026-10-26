"""Tests for top-level API functions."""

import pytest


def test_set_backdrop_color_fills_the_screen():
    """Test setting backdrop color."""
    import play
    from play.globals import globals_list

    result = []

    @play.when_program_starts
    async def check():
        play.set_backdrop("red")
        await play.animate()
        await play.animate()
        result.append(globals_list.backdrop)
        result.append(tuple(globals_list.display.get_at((1, 1))))
        play.stop_program()

    play.start_program()

    assert result == [(255, 0, 0, 255), (255, 0, 0, 255)]


def test_set_backdrop_rgb():
    """Test setting backdrop with RGB tuple."""
    import play
    from play.globals import globals_list

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        play.set_backdrop((100, 150, 200))
        result.append(globals_list.backdrop)
        play.stop_program()

    play.start_program()

    assert result[0] == (100, 150, 200)


def test_key_is_pressed_only_while_the_key_is_held():
    import pygame
    import play
    from tests.conftest import post_key_down, post_key_up

    result = []

    @play.when_program_starts
    async def check():
        result.append(play.key_is_pressed("space"))
        post_key_down(pygame.K_SPACE)
        for _ in range(10):
            await play.animate()
        result.append(play.key_is_pressed("space"))
        result.append(play.key_is_pressed("a", "space"))
        result.append(play.key_is_pressed("a"))
        post_key_up(pygame.K_SPACE)
        for _ in range(3):
            await play.animate()
        result.append(play.key_is_pressed("space"))
        play.stop_program()

    play.start_program()

    assert result == [False, True, True, False, False]


def test_set_physics_simulation_steps():
    """Test setting physics simulation steps."""
    import play
    from play.globals import globals_list

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(globals_list.num_sim_steps)
        play.set_physics_simulation_steps(20)
        result.append(globals_list.num_sim_steps)
        play.stop_program()

    play.start_program()

    assert result[0] == 10  # default
    assert result[1] == 20


def test_timer_waits_the_given_number_of_seconds():
    import time
    import play

    result = []

    @play.when_program_starts
    async def check():
        started = time.monotonic()
        result.append(await play.timer(0.1))
        result.append(time.monotonic() - started)
        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] >= 0.1 - time.get_clock_info("monotonic").resolution


def test_animate_waits_for_the_next_frame():
    import play

    frames = [0]
    result = []

    @play.repeat_forever
    def count():
        frames[0] += 1

    @play.when_program_starts
    async def check():
        before = frames[0]
        for _ in range(10):
            await play.animate()
        result.append(frames[0] - before)
        play.stop_program()

    play.start_program()

    assert result[0] in (9, 10)


def test_set_gravity():
    """Test setting gravity."""
    import play
    from play.physics import set_gravity, physics_space

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        set_gravity(-500)
        result.append(physics_space.gravity)
        play.stop_program()

    play.start_program()

    assert result[0][1] == -500  # vertical gravity


def test_set_gravity_horizontal():
    """Test setting horizontal gravity."""
    import play
    from play.physics import set_gravity, physics_space

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        set_gravity(-500, 100)
        result.append(physics_space.gravity)
        play.stop_program()

    play.start_program()

    assert result[0][0] == 100  # horizontal gravity
    assert result[0][1] == -500  # vertical gravity


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
