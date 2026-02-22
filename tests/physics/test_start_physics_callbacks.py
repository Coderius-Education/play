"""Test that calling start_physics again preserves callbacks without duplicating them."""

import pytest


def test_when_touching_callbacks_not_duplicated():
    """Calling start_physics a second time should not duplicate when_touching callbacks."""

    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    touch_count = [0]

    @ball.when_touching(wall)
    async def on_touch():
        touch_count[0] += 1

    callbacks_before = list(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball)) or []
    )
    count_before = len(callbacks_before)

    # Call start_physics again
    ball.start_physics(obeys_gravity=False)

    callbacks_after = list(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball)) or []
    )
    count_after = len(callbacks_after)

    assert (
        count_before == count_after
    ), f"when_touching callbacks changed from {count_before} to {count_after} after start_physics"

    play.stop_program()


def test_when_touching_wall_callbacks_not_duplicated():
    """Calling start_physics a second time should not duplicate when_touching_wall callbacks."""

    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    @ball.when_touching_wall
    async def on_wall():
        pass

    callbacks_before = list(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING_WALL, id(ball)) or []
    )
    count_before = len(callbacks_before)

    ball.start_physics(obeys_gravity=False)

    callbacks_after = list(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING_WALL, id(ball)) or []
    )
    count_after = len(callbacks_after)

    assert (
        count_before == count_after
    ), f"when_touching_wall callbacks changed from {count_before} to {count_after} after start_physics"

    play.stop_program()


def test_when_stopped_touching_callbacks_not_duplicated():
    """Calling start_physics a second time should not duplicate when_stopped_touching callbacks."""

    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    other = play.new_box(x=200, y=0, width=10, height=100)
    other.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_stopped_touching(other)
    async def on_stop_touch():
        pass

    callbacks_before = list(
        callback_manager.get_callback(CallbackType.WHEN_STOPPED_TOUCHING, id(ball))
        or []
    )
    count_before = len(callbacks_before)

    ball.start_physics(obeys_gravity=False)

    callbacks_after = list(
        callback_manager.get_callback(CallbackType.WHEN_STOPPED_TOUCHING, id(ball))
        or []
    )
    count_after = len(callbacks_after)

    assert (
        count_before == count_after
    ), f"when_stopped_touching callbacks changed from {count_before} to {count_after} after start_physics"

    play.stop_program()


def test_when_stopped_touching_wall_callbacks_not_duplicated():
    """Calling start_physics a second time should not duplicate when_stopped_touching_wall callbacks."""

    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    @ball.when_stopped_touching_wall
    async def on_stop_wall():
        pass

    callbacks_before = list(
        callback_manager.get_callback(CallbackType.WHEN_STOPPED_TOUCHING_WALL, id(ball))
        or []
    )
    count_before = len(callbacks_before)

    ball.start_physics(obeys_gravity=False)

    callbacks_after = list(
        callback_manager.get_callback(CallbackType.WHEN_STOPPED_TOUCHING_WALL, id(ball))
        or []
    )
    count_after = len(callbacks_after)

    assert (
        count_before == count_after
    ), f"when_stopped_touching_wall callbacks changed from {count_before} to {count_after} after start_physics"

    play.stop_program()


def test_multiple_start_physics_calls_preserve_callbacks():
    """Calling start_physics 3 times should still have the same callback count as after the first."""

    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    other = play.new_box(x=200, y=0, width=10, height=100)
    other.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(other)
    async def on_touch():
        pass

    @ball.when_touching_wall
    async def on_wall():
        pass

    touching_before = len(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball)) or []
    )
    wall_before = len(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING_WALL, id(ball)) or []
    )

    # Call start_physics two more times
    ball.start_physics(obeys_gravity=False)
    ball.start_physics(obeys_gravity=False)

    touching_after = len(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball)) or []
    )
    wall_after = len(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING_WALL, id(ball)) or []
    )

    assert (
        touching_before == touching_after
    ), f"when_touching callbacks changed from {touching_before} to {touching_after} after 3x start_physics"
    assert (
        wall_before == wall_after
    ), f"when_touching_wall callbacks changed from {wall_before} to {wall_after} after 3x start_physics"

    play.stop_program()


def test_other_sprite_start_physics_preserves_dependent_callbacks():
    """When sprite B calls start_physics, callbacks registered by sprite A
    referencing B should be re-registered with B's new physics shape."""

    import play
    from play.callback import callback_manager, CallbackType

    bal = play.new_circle(x=0, y=0, radius=20)
    bal.start_physics(obeys_gravity=False)

    batje = play.new_box(x=200, y=0, width=10, height=100)
    batje.start_physics(obeys_gravity=False, can_move=False)

    @bal.when_touching(batje)
    async def on_touch():
        pass

    @bal.when_stopped_touching(batje)
    async def on_stop_touch():
        pass

    touching_before = len(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(bal)) or []
    )
    stopped_before = len(
        callback_manager.get_callback(CallbackType.WHEN_STOPPED_TOUCHING, id(bal)) or []
    )

    # Call start_physics on the OTHER sprite (batje)
    batje.start_physics(obeys_gravity=False, can_move=False)

    touching_after = len(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(bal)) or []
    )
    stopped_after = len(
        callback_manager.get_callback(CallbackType.WHEN_STOPPED_TOUCHING, id(bal)) or []
    )

    assert touching_before == touching_after, (
        f"when_touching callbacks changed from {touching_before} to {touching_after} "
        f"after other sprite called start_physics"
    )
    assert stopped_before == stopped_after, (
        f"when_stopped_touching callbacks changed from {stopped_before} to {stopped_after} "
        f"after other sprite called start_physics"
    )

    play.stop_program()


if __name__ == "__main__":
    test_when_touching_callbacks_not_duplicated()
