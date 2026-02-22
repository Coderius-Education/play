"""Tests for top-level API functions."""

import pytest


def test_set_backdrop_color():
    """Test setting backdrop color."""
    import play
    from play.globals import globals_list

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        play.set_backdrop("red")
        result.append(globals_list.backdrop)
        play.stop_program()

    play.start_program()

    # Should be RGB tuple for red
    assert result[0] == (255, 0, 0, 255)


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


def test_key_is_pressed_false():
    """Test key_is_pressed returns False when no key pressed."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.key_is_pressed("space"))
        print("hello")
        play.stop_program()

    play.start_program()

    print(result)
    assert result[0] is False


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


def test_timer_async():
    """Test timer async function."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    async def check():
        result.append("before")
        await play.timer(0.1)
        result.append("after")
        play.stop_program()

    play.start_program()

    assert result == ["before", "after"]


def test_animate_async():
    """Test animate async function (wait for next frame)."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    async def check():
        result.append("frame1")
        await play.animate()
        result.append("frame2")
        await play.animate()
        result.append("frame3")
        play.stop_program()

    play.start_program()

    assert result == ["frame1", "frame2", "frame3"]


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
