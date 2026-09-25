"""Size and physics-setting changes reshape the pymunk objects in place.

Until now every such change removed the body and shape from the space and
built new ones, copying the collision_type and sensor flag across by hand so
callbacks kept working. pymunk can resize a shape and retype a body where
they are, so the objects, and everything keyed on them, simply survive.
"""

import pymunk
import pytest

import play
from play.callback.collision_callbacks import WallSide
from play.globals import globals_list
from play.io.screen import rebuild_walls, remove_wall, screen
from play.physics import physics_space, set_gravity

ANYTHING = pymunk.ShapeFilter()


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _hit(point, distance=0):
    info = physics_space.point_query_nearest(point, distance, ANYTHING)
    return info.shape if info else None


# ── sizes ─────────────────────────────────────────────────────────────────────


def test_resizing_keeps_the_same_body_and_shape():
    box = play.new_box(width=40, height=20)
    box.start_physics(can_move=True, stable=False)
    body, shape = box.physics._pymunk_body, box.physics._pymunk_shape

    box.size = 50

    assert box.physics._pymunk_body is body
    assert box.physics._pymunk_shape is shape
    assert shape.bb == pymunk.BB(-10, -5, 10, 5)
    assert body.moment == pytest.approx(pymunk.moment_for_box(10, (20, 10)))


def test_a_circle_resizes_its_radius():
    circle = play.new_circle(radius=20)
    circle.start_physics(can_move=True, stable=False)
    shape = circle.physics._pymunk_shape

    circle.size = 50

    assert circle.physics._pymunk_shape is shape
    assert shape.radius == 10
    assert circle.physics._pymunk_body.moment == pytest.approx(
        pymunk.moment_for_circle(10, 0, 10)
    )


def test_a_box_width_change_reshapes_the_hit_box():
    box = play.new_box(width=40, height=20)
    box.start_physics()
    shape = box.physics._pymunk_shape

    box.width = 80

    assert box.physics._pymunk_shape is shape
    assert shape.bb == pymunk.BB(-40, -10, 40, 10)


def test_the_space_sees_the_new_size():
    # A shape changed in place has to be re-indexed, or point queries and
    # collisions keep using its old extent.
    circle = play.new_circle(x=0, y=0, radius=10)
    circle.start_physics()
    assert _hit((25, 0)) is None

    circle.size = 300

    assert _hit((25, 0)) is circle.physics._pymunk_shape


def test_resizing_a_hidden_sprite_stays_out_of_the_space():
    box = play.new_box(width=40, height=20)
    box.start_physics()
    body = box.physics._pymunk_body
    box.hide()
    assert body not in physics_space.bodies

    box.size = 50

    assert body not in physics_space.bodies
    box.show()
    assert body in physics_space.bodies
    assert box.physics._pymunk_shape.bb == pymunk.BB(-10, -5, 10, 5)


def test_a_negative_size_does_not_trip_pymunk():
    # pymunk refuses a zero moment on a dynamic body in a space. A circle
    # shrunk below nothing becomes a point and keeps the moment it had.
    circle = play.new_circle(radius=20)
    circle.start_physics(can_move=True, stable=False)

    circle.size = -10

    assert circle.physics._pymunk_shape.radius == 0
    assert circle.physics._pymunk_body.moment > 0
    physics_space.step(1 / 60)


# ── physics settings ──────────────────────────────────────────────────────────


def test_toggling_can_move_retypes_the_same_body():
    box = play.new_box()
    box.start_physics(can_move=True, stable=False, x_speed=30)
    body = box.physics._pymunk_body

    box.physics.can_move = False
    assert box.physics._pymunk_body is body
    assert body.body_type == pymunk.Body.STATIC

    box.physics.can_move = True
    assert box.physics._pymunk_body is body
    assert body.body_type == pymunk.Body.DYNAMIC
    assert body.mass == 10
    assert body.moment == pytest.approx(pymunk.moment_for_box(10, (100, 200)))
    assert body.velocity == (30, 0)


def test_toggling_stable_switches_the_moment_in_place():
    box = play.new_box()
    box.start_physics(can_move=True, stable=False)
    body = box.physics._pymunk_body
    assert body.moment < float("inf")

    box.physics.stable = True
    assert box.physics._pymunk_body is body
    assert body.moment == float("inf")

    box.physics.stable = False
    assert body.moment == pytest.approx(pymunk.moment_for_box(10, (100, 200)))


def test_stable_without_gravity_becomes_kinematic_in_place():
    set_gravity(-100)
    box = play.new_box()
    box.start_physics(can_move=True, stable=False, obeys_gravity=False)
    body = box.physics._pymunk_body
    assert body.body_type == pymunk.Body.DYNAMIC

    box.physics.stable = True
    assert box.physics._pymunk_body is body
    assert body.body_type == pymunk.Body.KINEMATIC

    box.physics.stable = False
    assert body.body_type == pymunk.Body.DYNAMIC
    assert body.mass == 10


def test_collision_bookkeeping_needs_no_copying():
    ball = play.new_circle(radius=20)
    wall = play.new_box(x=200, y=0, width=10, height=100)

    @ball.when_touching(wall)
    def on_touch():
        pass

    shape = ball.physics._pymunk_shape
    ball.physics.sensor = True
    collision_type = shape.collision_type

    ball.size = 50
    ball.physics.can_move = False
    ball.physics.can_move = True
    ball.physics.stable = True

    assert ball.physics._pymunk_shape is shape
    assert shape.collision_type == collision_type
    assert shape.sensor is True


def test_nothing_leaks_across_many_changes():
    box = play.new_box(width=40, height=20)
    box.start_physics(can_move=True, stable=False)
    bodies, shapes = len(physics_space.bodies), len(physics_space.shapes)

    for i in range(1, 6):
        box.size = 100 + i
        box.width = 40 + i
        box.height = 20 + i
        box.physics.can_move = i % 2 == 0
        box.physics.stable = i % 3 == 0

    assert (len(physics_space.bodies), len(physics_space.shapes)) == (bodies, shapes)


# ── walls ─────────────────────────────────────────────────────────────────────


def test_rebuilt_walls_are_the_same_segments_moved():
    before = list(globals_list.walls)
    types = [wall.collision_type for wall in before]

    screen.width, screen.height = 1024, 768
    rebuild_walls()

    assert globals_list.walls == before
    assert [wall.collision_type for wall in globals_list.walls] == types
    top, bottom, left, right = globals_list.walls
    assert (top.a, top.b) == ((-512, 384), (512, 384))
    assert (bottom.a, bottom.b) == ((-512, -384), (512, -384))
    assert (left.a, left.b) == ((-512, -384), (-512, 384))
    assert (right.a, right.b) == ((512, -384), (512, 384))


def test_the_space_sees_the_moved_walls():
    old_bottom = screen.bottom
    screen.width, screen.height = 1024, 768
    rebuild_walls()

    assert _hit((0, screen.bottom), 1) is globals_list.walls[1]
    assert _hit((0, old_bottom), 1) is None


def test_a_removed_wall_comes_back_on_rebuild():
    # As it always has: rebuild_walls() restores the full set, in index order.
    remove_wall(0)
    assert len(globals_list.walls) == 3

    rebuild_walls()

    assert [wall.wall_side for wall in globals_list.walls] == [
        WallSide.TOP,
        WallSide.BOTTOM,
        WallSide.LEFT,
        WallSide.RIGHT,
    ]
