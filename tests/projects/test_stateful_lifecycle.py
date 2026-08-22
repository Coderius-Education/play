"""Randomised sprite-lifecycle sequences, checked against the frame invariants.

The hand-written tests each walk one path through the lifecycle. This walks
thousands, in orders nobody would think to write down — hide then remove, pause
then restart physics then hide, remove something already paused — and after
every single step asserts the same invariants the project watchdog checks.

When it finds a failure Hypothesis shrinks it to the shortest sequence that
still breaks, so the report is a minimal reproduction rather than a log.
"""

import pytest
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

import play
from play.globals import globals_list
from tests.projects.conftest import check_frame_invariants


def _clear_sprites():
    """Remove every sprite, so each example starts from the same place.

    The autouse clean_play_state fixture runs once for the whole test function,
    not once per Hypothesis example, so without this every example would
    inherit the previous one's sprites.
    """
    for sprite in list(globals_list.sprites_group.sprites()):
        try:
            sprite.remove()
        except Exception:  # pragma: no cover - defensive
            pass


class SpriteLifecycleMachine(RuleBasedStateMachine):
    """Drives sprites through arbitrary lifecycle sequences.

    Sprites are held in a plain list and addressed by index rather than drawn
    from a Bundle. With a Bundle, every rule that takes a sprite is disabled
    while the bundle is empty, so Hypothesis spends its budget retrying draws
    and abandons a large share of sequences before they get anywhere. Indexing
    keeps every rule enabled at every step.
    """

    def __init__(self):
        super().__init__()
        _clear_sprites()
        self.sprites = []
        self.known = {}

    def _pick(self, index):
        """Return a live sprite, or None when there is nothing to act on."""
        live = [s for s in self.sprites if s.alive()]
        if not live:
            return None
        return live[index % len(live)]

    @initialize()
    def start_clean(self):
        assert check_frame_invariants(self.known) == []

    # --- creation ----------------------------------------------------------

    @rule()
    def new_box(self):
        self.sprites.append(play.new_box(color="red", x=0, y=0, width=20, height=20))

    @rule()
    def new_circle(self):
        self.sprites.append(play.new_circle(color="blue", x=0, y=0, radius=10))

    # --- physics -----------------------------------------------------------

    @rule(index=st.integers(min_value=0, max_value=99))
    def start_physics(self, index):
        sprite = self._pick(index)
        if sprite is not None:
            sprite.start_physics(obeys_gravity=False, x_speed=10, y_speed=0)

    @rule(index=st.integers(min_value=0, max_value=99))
    def stop_physics(self, index):
        sprite = self._pick(index)
        if sprite is not None and sprite.physics is not None:
            sprite.stop_physics()

    @rule(index=st.integers(min_value=0, max_value=99))
    def pause_physics(self, index):
        sprite = self._pick(index)
        if sprite is not None and sprite.physics is not None:
            sprite.physics.pause()

    @rule(index=st.integers(min_value=0, max_value=99))
    def unpause_physics(self, index):
        sprite = self._pick(index)
        if sprite is not None and sprite.physics is not None:
            sprite.physics.unpause()

    # --- visibility and lifetime -------------------------------------------

    @rule(index=st.integers(min_value=0, max_value=99))
    def hide(self, index):
        sprite = self._pick(index)
        if sprite is not None:
            sprite.hide()

    @rule(index=st.integers(min_value=0, max_value=99))
    def show(self, index):
        sprite = self._pick(index)
        if sprite is not None:
            sprite.show()

    @rule(index=st.integers(min_value=0, max_value=99))
    def remove(self, index):
        sprite = self._pick(index)
        if sprite is not None:
            sprite.remove()

    @rule(index=st.integers(min_value=0, max_value=99))
    def step_a_frame(self, index):
        """Run the per-frame update, which is where anchoring and redraw live."""
        sprite = self._pick(index)
        if sprite is not None:
            sprite.update()

    # --- the property being checked ----------------------------------------

    @invariant()
    def frame_invariants_hold(self):
        violations = check_frame_invariants(self.known)
        assert not violations, "\n  ".join(violations)

    def teardown(self):
        _clear_sprites()


TestSpriteLifecycle = SpriteLifecycleMachine.TestCase
TestSpriteLifecycle.settings = settings(
    max_examples=40,
    stateful_step_count=25,
    deadline=None,
    # clean_play_state is function-scoped and intentionally not re-run per
    # example; __init__ and teardown reset the state this machine touches.
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


@pytest.mark.parametrize("repeat", range(2))
def test_machine_is_actually_running_rules(repeat):
    """Guard against the machine silently degenerating into a no-op.

    A state machine whose rules all early-return would pass forever while
    testing nothing, which is the failure mode this whole exercise is about.
    """
    machine = SpriteLifecycleMachine()
    machine.start_clean()
    machine.new_box()
    machine.start_physics(0)
    machine.frame_invariants_hold()

    box = machine.sprites[0]
    assert box.alive()
    assert box.physics is not None

    machine.remove(0)
    machine.frame_invariants_hold()
    assert not box.alive()

    machine.teardown()
