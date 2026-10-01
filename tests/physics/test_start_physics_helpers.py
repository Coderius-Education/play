"""Tests for the helper methods extracted from start_physics."""


def test_save_and_clear_callbacks_returns_saved():
    """_save_and_clear_callbacks should return all registered callbacks."""
    import play
    from play.callback import CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(wall)
    async def on_touch():
        pass

    @ball.when_touching_wall
    async def on_wall():
        pass

    saved = ball._save_and_clear_callbacks()

    assert len(saved[CallbackType.WHEN_TOUCHING]) == 1
    # when_touching_wall registers one callback per wall side (top, bottom, left, right)
    assert len(saved[CallbackType.WHEN_TOUCHING_WALL]) == 4
    assert len(saved[CallbackType.WHEN_STOPPED_TOUCHING]) == 0
    assert len(saved[CallbackType.WHEN_STOPPED_TOUCHING_WALL]) == 0

    play.stop_program()


def test_save_and_clear_callbacks_clears_manager():
    """After _save_and_clear_callbacks, the callback_manager should have no entries."""
    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(wall)
    async def on_touch():
        pass

    ball._save_and_clear_callbacks()

    remaining = callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball))
    assert remaining is None or len(remaining) == 0

    play.stop_program()


def test_save_and_clear_callbacks_empty_when_no_callbacks():
    """_save_and_clear_callbacks should return empty lists when nothing is registered."""
    import play

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    saved = ball._save_and_clear_callbacks()

    for callback_type in saved:
        assert len(saved[callback_type]) == 0

    play.stop_program()


def test_forget_removes_entries():
    """forget() should remove all entries for a shape's collision type."""
    import play
    from play.callback.collision_callbacks import collision_registry

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(wall)
    async def on_touch():
        pass

    shape = ball.physics._pymunk_shape
    ct = shape.collision_type

    # The registered shape carries its sprite, and has callbacks, before cleanup
    assert shape._play_sprite is ball
    assert ct in collision_registry.callbacks[True]

    collision_registry.forget(shape)

    assert shape._play_sprite is None
    for begin in [True, False]:
        assert ct not in collision_registry.callbacks[begin]

    play.stop_program()


def test_forget_removes_nested_entries():
    """forget() should also remove the sprite from nested dicts of other sprites."""
    import play
    from play.callback.collision_callbacks import collision_registry

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(wall)
    async def on_touch():
        pass

    ball_ct = ball.physics._pymunk_shape.collision_type
    wall_ct = wall.physics._pymunk_shape.collision_type

    # Verify ball_ct is nested inside wall_ct's dict before cleanup
    assert ball_ct in collision_registry.callbacks[True].get(wall_ct, {})

    collision_registry.forget(ball.physics._pymunk_shape)

    # After cleanup, ball_ct should be removed from wall_ct's nested dict too
    for begin in [True, False]:
        assert ball_ct not in collision_registry.callbacks[begin].get(wall_ct, {})

    play.stop_program()


def test_forget_removes_the_stopped_touching_side_too():
    """forget() must drop when_stopped_touching entries as well as when_touching.

    The tests above only register when_touching, so their check of the
    separate side passed whatever forget() did there.
    """
    import play
    from play.callback.collision_callbacks import collision_registry

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_stopped_touching(wall)
    async def on_stop():
        pass

    ball_ct = ball.physics._pymunk_shape.collision_type
    wall_ct = wall.physics._pymunk_shape.collision_type
    separate = collision_registry.callbacks[False]
    assert ball_ct in separate and ball_ct in separate.get(wall_ct, {})

    collision_registry.forget(ball.physics._pymunk_shape)

    assert ball_ct not in separate
    assert ball_ct not in separate.get(wall_ct, {})

    play.stop_program()


def test_forgetting_a_shape_that_was_never_registered_is_a_noop():
    """forget() on a shape with no collision callbacks should do nothing.

    Every unregistered shape has pymunk's default collision_type 0, so this
    also checks forget() cannot reach anybody else's registrations that way.
    """
    import play
    from play.callback.collision_callbacks import collision_registry

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)
    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(wall)
    async def on_touch():
        pass

    bystander = play.new_circle(x=-200, y=0, radius=20)
    before = {
        begin: {ct: dict(others) for ct, others in by_ct.items()}
        for begin, by_ct in collision_registry.callbacks.items()
    }
    assert before[True], "the pair above should be registered"

    collision_registry.forget(bystander.physics._pymunk_shape)

    assert collision_registry.callbacks == before
    assert ball.physics._pymunk_shape._play_sprite is ball

    play.stop_program()


def test_reregister_own_callbacks_restores_touching():
    """_reregister_own_callbacks should restore when_touching callbacks."""
    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    wall = play.new_box(x=200, y=0, width=10, height=100)
    wall.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(wall)
    async def on_touch():
        pass

    from play.callback.collision_callbacks import collision_registry

    saved = ball._save_and_clear_callbacks()
    collision_registry.forget(ball.physics._pymunk_shape)

    # Callbacks should be cleared now
    assert (
        len(callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball)) or [])
        == 0
    )

    ball._reregister_own_callbacks(saved)

    restored = callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball))
    assert len(restored) == 1

    play.stop_program()


def test_reregister_own_callbacks_restores_wall_callbacks():
    """_reregister_own_callbacks should restore when_touching_wall callbacks."""
    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    @ball.when_touching_wall
    async def on_wall():
        pass

    @ball.when_stopped_touching_wall
    async def on_stop_wall():
        pass

    saved = ball._save_and_clear_callbacks()
    ball._reregister_own_callbacks(saved)

    wall_cbs = callback_manager.get_callback(CallbackType.WHEN_TOUCHING_WALL, id(ball))
    stop_wall_cbs = callback_manager.get_callback(
        CallbackType.WHEN_STOPPED_TOUCHING_WALL, id(ball)
    )
    # Each wall decorator registers one callback per wall side (4 sides)
    assert len(wall_cbs) == 4
    assert len(stop_wall_cbs) == 4

    play.stop_program()


def test_reregister_dependent_callbacks_refreshes_other_sprite():
    """_reregister_dependent_callbacks should refresh when_touching callbacks from dependents."""
    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    target = play.new_box(x=200, y=0, width=10, height=100)
    target.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(target)
    async def on_touch():
        pass

    count_before = len(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball)) or []
    )

    # Call start_physics on the target sprite to trigger _reregister_dependent_callbacks
    target.start_physics(obeys_gravity=False, can_move=False)

    count_after = len(
        callback_manager.get_callback(CallbackType.WHEN_TOUCHING, id(ball)) or []
    )

    assert count_before == count_after

    play.stop_program()


def test_reregister_dependent_callbacks_refreshes_when_stopped_touching():
    """_reregister_dependent_callbacks should refresh when_stopped_touching callbacks from dependents."""
    import play
    from play.callback import callback_manager, CallbackType

    ball = play.new_circle(x=0, y=0, radius=20)
    ball.start_physics(obeys_gravity=False)

    target = play.new_box(x=200, y=0, width=10, height=100)
    target.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_stopped_touching(target)
    async def on_stop_touch():
        pass

    count_before = len(
        callback_manager.get_callback(CallbackType.WHEN_STOPPED_TOUCHING, id(ball))
        or []
    )

    # Call start_physics on the target sprite to trigger _reregister_dependent_callbacks
    target.start_physics(obeys_gravity=False, can_move=False)

    count_after = len(
        callback_manager.get_callback(CallbackType.WHEN_STOPPED_TOUCHING, id(ball))
        or []
    )

    assert count_before == count_after

    play.stop_program()
