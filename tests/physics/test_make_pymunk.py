"""Tests for the _make_pymunk method body type selection."""

import pytest


import pymunk


def test_static_body_when_can_move_false():
    """Test that body type is STATIC when can_move=False."""
    import play

    box = play.new_box()
    box.start_physics(can_move=False)

    assert box.physics._pymunk_body.body_type == pymunk.Body.STATIC


def test_dynamic_body_when_can_move_true_stable_false():
    """Test that body type is DYNAMIC when can_move=True, stable=False."""
    import play

    box = play.new_box()
    box.start_physics(can_move=True, stable=False)

    assert box.physics._pymunk_body.body_type == pymunk.Body.DYNAMIC


def test_dynamic_body_when_obeys_gravity_true():
    """Test that body type is DYNAMIC when can_move=True, stable=True, obeys_gravity=True."""
    import play
    from play.physics import set_gravity

    set_gravity(-100)
    box = play.new_box()
    box.start_physics(can_move=True, stable=True, obeys_gravity=True)

    assert box.physics._pymunk_body.body_type == pymunk.Body.DYNAMIC


def test_kinematic_body_when_stable_no_gravity_obey():
    """Test that body type is KINEMATIC when can_move=True, stable=True, obeys_gravity=False, has_gravity=True."""
    import play
    from play.physics import set_gravity

    set_gravity(-100)
    box = play.new_box()
    box.start_physics(can_move=True, stable=True, obeys_gravity=False)

    assert box.physics._pymunk_body.body_type == pymunk.Body.KINEMATIC


def test_dynamic_body_when_no_gravity_in_world():
    """Test that body type is DYNAMIC when can_move=True, stable=True, obeys_gravity=False but world has no gravity."""
    import play
    from play.physics import set_gravity

    set_gravity(0)
    box = play.new_box()
    box.start_physics(can_move=True, stable=True, obeys_gravity=False)

    assert box.physics._pymunk_body.body_type == pymunk.Body.DYNAMIC


def test_mass_set_when_can_move_true():
    """Test that mass is set when can_move=True."""
    import play

    box = play.new_box()
    box.start_physics(can_move=True, mass=5)

    assert box.physics._pymunk_body.mass == 5


def test_moment_infinite_when_stable():
    """Test that moment is infinite when stable=True."""
    import play

    box = play.new_box()
    box.start_physics(can_move=True, stable=True)

    assert box.physics._pymunk_body.moment == float("inf")


def test_circle_shape_for_circle_sprite():
    """Test that Circle sprites get a pymunk Circle shape."""
    import play

    circle = play.new_circle(radius=25)
    circle.start_physics()

    assert isinstance(circle.physics._pymunk_shape, pymunk.Circle)
    assert circle.physics._pymunk_shape.radius == 25


def test_poly_shape_for_box_sprite():
    """Test that Box sprites get a pymunk Poly shape."""
    import play

    box = play.new_box(width=50, height=30)
    box.start_physics()

    assert isinstance(box.physics._pymunk_shape, pymunk.Poly)


def test_initial_velocity_set():
    """Test that initial velocity is set correctly."""
    import play

    box = play.new_box()
    box.start_physics(can_move=True, x_speed=100, y_speed=50)

    assert box.physics._pymunk_body.velocity == (100, 50)


def test_initial_position_set():
    """Test that initial position is set correctly."""
    import play

    box = play.new_box(x=150, y=-75)
    box.start_physics()

    assert box.physics._pymunk_body.position == (150, -75)


def test_bounciness_clamped():
    """Test that bounciness is clamped between 0 and 0.9999."""
    import play

    box = play.new_box()
    box.start_physics(bounciness=1.5)

    assert box.physics._pymunk_shape.elasticity <= 0.9999


def test_all_static_combinations():
    """Test all can_move=False combinations result in STATIC."""
    import play
    from play.physics import set_gravity

    combinations = [
        (False, False),  # stable, obeys_gravity
        (False, True),
        (True, False),
        (True, True),
    ]

    for stable, obeys_gravity in combinations:
        set_gravity(-100)
        box = play.new_box()
        box.start_physics(can_move=False, stable=stable, obeys_gravity=obeys_gravity)
        assert (
            box.physics._pymunk_body.body_type == pymunk.Body.STATIC
        ), f"Expected STATIC for can_move=False, stable={stable}, obeys_gravity={obeys_gravity}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
