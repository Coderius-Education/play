"""Test that calling start_physics raises an error when callbacks are already registered."""

import pytest


def test_start_physics_raises_when_touching_registered():
    """start_physics should raise RuntimeError if when_touching callbacks exist."""
    import sys

    sys.path.insert(0, ".")
    import play

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(wall)
    async def on_touch():
        pass

    with pytest.raises(
        RuntimeError, match="already has collision callbacks registered"
    ):
        ball.start_physics(obeys_gravity=False)

    play.stop_program()


def test_start_physics_raises_when_touching_wall_registered():
    """start_physics should raise RuntimeError if when_touching_wall callbacks exist."""
    import sys

    sys.path.insert(0, ".")
    import play

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    @ball.when_touching_wall
    async def on_wall():
        pass

    with pytest.raises(
        RuntimeError, match="already has collision callbacks registered"
    ):
        ball.start_physics(obeys_gravity=False)

    play.stop_program()


def test_start_physics_raises_when_stopped_touching_registered():
    """start_physics should raise RuntimeError if when_stopped_touching callbacks exist."""
    import sys

    sys.path.insert(0, ".")
    import play

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    other = play.new_box(x=200, y=0, width=10, height=100)
    other.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_stopped_touching(other)
    async def on_stop_touch():
        pass

    with pytest.raises(
        RuntimeError, match="already has collision callbacks registered"
    ):
        ball.start_physics(obeys_gravity=False)

    play.stop_program()


def test_start_physics_raises_when_stopped_touching_wall_registered():
    """start_physics should raise RuntimeError if when_stopped_touching_wall callbacks exist."""
    import sys

    sys.path.insert(0, ".")
    import play

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    @ball.when_stopped_touching_wall
    async def on_stop_wall():
        pass

    with pytest.raises(
        RuntimeError, match="already has collision callbacks registered"
    ):
        ball.start_physics(obeys_gravity=False)

    play.stop_program()


def test_start_physics_ok_without_callbacks():
    """start_physics should succeed when no callbacks are registered."""
    import sys

    sys.path.insert(0, ".")
    import play

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    # Calling again without callbacks should work fine
    ball.start_physics(obeys_gravity=False)

    play.stop_program()


def test_stop_physics_clears_callbacks_then_restarts():
    """stop_physics should clear callbacks and successfully call start_physics."""
    import sys

    sys.path.insert(0, ".")
    import play

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    @ball.when_touching_wall
    async def on_wall():
        pass

    # stop_physics should work even with callbacks registered
    ball.stop_physics()

    play.stop_program()


def test_start_physics_raises_when_dependent_sprite_has_callback():
    """start_physics should raise RuntimeError if another sprite has a callback referencing this sprite."""
    import sys

    sys.path.insert(0, ".")
    import play

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(wall)
    async def on_touch():
        pass

    # Calling start_physics on 'wall' should fail because 'ball' has a
    # when_touching callback that references 'wall'
    with pytest.raises(RuntimeError, match="callback referencing it"):
        wall.start_physics(obeys_gravity=False, can_move=False)

    play.stop_program()


if __name__ == "__main__":
    test_start_physics_raises_when_touching_registered()
