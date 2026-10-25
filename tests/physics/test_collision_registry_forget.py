"""collision_registry.forget(), which start_physics() and remove() use to drop a shape's callbacks."""


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
