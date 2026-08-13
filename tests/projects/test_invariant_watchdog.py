"""Tests for the watchdog that guards every other project test.

A checker that cannot fail is worse than no checker: it reports green over
whatever it was supposed to catch. Each test here breaks one invariant on
purpose and asserts the watchdog notices, so the 44 project tests it runs
against are actually being guarded.
"""

import play
from play.globals import globals_list
from play.physics import physics_space
from tests.projects.conftest import check_frame_invariants


def test_clean_state_reports_nothing():
    """The baseline must be quiet, or every other assertion here is vacuous."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(obeys_gravity=False)

    assert check_frame_invariants({}) == []


def test_detects_paused_sprite_left_in_the_space():
    """A paused body still collides — the user stopped it and it kept hitting things."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(obeys_gravity=False)

    # Flag it paused without taking it out of the space, which is the state a
    # bug in pause()/_remove() bookkeeping would leave behind.
    box.physics._is_paused = True

    violations = check_frame_invariants({})
    assert any(
        "paused but its body is still simulated" in v for v in violations
    ), violations


def test_detects_running_sprite_missing_from_the_space():
    """Physics that claims to be running but is not simulated goes silently dead."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(obeys_gravity=False)

    physics_space.remove(box.physics._pymunk_body, box.physics._pymunk_shape)

    violations = check_frame_invariants({})
    assert any("no body in the space" in v for v in violations), violations

    physics_space.add(box.physics._pymunk_body, box.physics._pymunk_shape)


def test_detects_body_leaked_by_a_removed_sprite():
    """A body outliving its sprite is a collider the user can no longer reach."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(obeys_gravity=False)

    known = {}
    assert check_frame_invariants(known) == []
    assert known, "the sprite should have been recorded while it was alive"

    # Drop it from the group the way remove() does, but skip the physics
    # teardown — exactly what a missing physics._remove() call would leave.
    globals_list.sprites_group.remove(box)

    violations = check_frame_invariants(known)
    assert any("still simulated" in v for v in violations), violations

    physics_space.remove(box.physics._pymunk_body, box.physics._pymunk_shape)


def test_detects_non_finite_position():
    """NaN positions are how a physics blow-up shows up before anything crashes."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.x = float("nan")

    violations = check_frame_invariants({})
    assert any("non-finite position" in v for v in violations), violations

    box.x = 0


def test_a_real_removal_is_not_flagged():
    """Sprite.remove() does the right thing, so it must stay quiet.

    Guards the other direction: an invariant that fires on correct code gets
    disabled by the next person who trips over it.
    """
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(obeys_gravity=False)

    known = {}
    check_frame_invariants(known)
    box.remove()

    assert check_frame_invariants(known) == []
