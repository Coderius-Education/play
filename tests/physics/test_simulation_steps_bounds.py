import pytest
import play
from play.globals import globals_list


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_set_physics_simulation_steps_positive():
    """Setting simulation steps to a positive integer should work."""
    play.set_physics_simulation_steps(10)
    assert globals_list.num_sim_steps == 10


def test_set_physics_simulation_steps_one():
    """Setting simulation steps to 1 (minimum sensible value) should work."""
    play.set_physics_simulation_steps(1)
    assert globals_list.num_sim_steps == 1


def test_set_physics_simulation_steps_zero():
    """Setting simulation steps to 0 is accepted (no validation exists).
    This documents current behavior — 0 steps means no physics updates per frame."""
    play.set_physics_simulation_steps(0)
    assert globals_list.num_sim_steps == 0


def test_set_physics_simulation_steps_negative():
    """Setting simulation steps to a negative value is accepted (no validation exists).
    This documents current behavior."""
    play.set_physics_simulation_steps(-1)
    assert globals_list.num_sim_steps == -1
