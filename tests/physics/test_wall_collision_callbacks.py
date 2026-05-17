"""Isolated unit tests for event-driven wall collision callbacks.

Verifies that the pymunk begin/separate handlers populate
EventComponent.touching_callbacks() and stopped_callbacks() when a
dynamic sprite contacts or leaves a screen wall.
"""

import pytest
import play
from play.physics import physics_space
from play.io.screen import screen
from play.callback.collision_callbacks import WallSide


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_when_touching_wall_callback_queued_on_contact():
    """Pymunk begin handler must call set_touching when sprite hits the bottom wall."""
    box = play.new_box(x=0, y=screen.bottom, width=40, height=40)
    box.start_physics(can_move=True, obeys_gravity=False)

    @box.when_touching_wall(wall=WallSide.BOTTOM)
    async def on_wall(wall):
        pass

    physics_space.step(1 / 60)

    assert len(box.events.touching_callbacks()) > 0


def test_when_stopped_touching_wall_callback_queued_on_separation():
    """Pymunk separate handler must call set_stopped when sprite leaves the bottom wall."""
    box = play.new_box(x=0, y=screen.bottom, width=40, height=40)
    box.start_physics(can_move=True, obeys_gravity=False)

    @box.when_stopped_touching_wall(wall=WallSide.BOTTOM)
    async def on_stop_wall(wall):
        pass

    physics_space.step(1 / 60)  # contact: begin fires

    # Drive separation with upward velocity rather than teleporting,
    # so the test doesn't rely on pymunk's teleport-detection behavior.
    box.physics.y_speed = 300
    for _ in range(10):
        physics_space.step(1 / 60)

    assert len(box.events.stopped_callbacks()) > 0
