import pytest
import play
from play.physics import physics_space, set_gravity, set_physics_simulation_steps
from play.globals import globals_list


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_physics_direct_init_and_properties():
    box = play.new_box(color="red", x=0, y=0, width=50, height=50)

    # Defaults checking
    assert box.physics.can_move is True
    assert box.physics.stable is True
    assert box.physics.obeys_gravity is False
    assert box.physics.bounciness == 1.0

    # can_move
    box.physics.can_move = False
    assert box.physics.can_move is False
    # should trigger _make_pymunk and recreate as static

    # speed
    box.physics.x_speed = 10
    assert box.physics.x_speed == 10
    box.physics.y_speed = -20
    assert box.physics.y_speed == -20

    # bounciness
    box.physics.bounciness = 0.5
    assert box.physics.bounciness == 0.5

    # mass
    box.physics.can_move = True
    box.physics.stable = False
    box.physics.obeys_gravity = True
    box.physics.mass = 50
    assert box.physics.mass == 50

    # obeys_gravity
    box.physics.obeys_gravity = True
    assert box.physics.obeys_gravity is True

    # turn gravity off
    box.physics.obeys_gravity = False
    assert box.physics.obeys_gravity is False


def test_physics_direct_stable_recreation():
    circle = play.new_circle(color="blue", x=0, y=0, radius=20)
    circle.start_physics(can_move=True, stable=False)

    assert circle.physics.stable is False

    # Changing stable toggles moment infinity vs calculation
    circle.physics.stable = True
    assert circle.physics.stable is True


def test_physics_direct_pause_unpause():
    box = play.new_box(color="red", x=0, y=0, width=50, height=50)

    # Initial state is unpaused
    assert box.physics._is_paused is False

    box.physics.pause()
    assert box.physics._is_paused is True

    # Pausing again does nothing and returns early
    box.physics.pause()

    box.physics.unpause()
    assert box.physics._is_paused is False

    # Unpausing again does nothing and returns early
    box.physics.unpause()


def test_physics_direct_clone():
    box = play.new_box(color="red", x=0, y=0, width=50, height=50)
    box.physics.x_speed = 100
    box.physics.bounciness = 0.8

    cloned_physics = box.physics.clone(box)
    assert cloned_physics.x_speed == 100
    assert cloned_physics.bounciness == 0.8
    assert cloned_physics.can_move == box.physics.can_move


def test_physics_direct_global_setters():
    set_gravity(vertical=-50, horizontal=10)
    assert physics_space.gravity == (10, -50)

    set_gravity(vertical=-200)  # leaving horizontal alone
    assert physics_space.gravity == (10, -200)

    set_physics_simulation_steps(3)
    assert globals_list.num_sim_steps == 3
    set_physics_simulation_steps(10)  # Reset global state

    # Reset gravity to defaults so it doesn't bleed into other tests
    set_gravity(vertical=-100, horizontal=0)
