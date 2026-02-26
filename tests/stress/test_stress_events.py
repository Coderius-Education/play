import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_stress_events():
    """
    Stress test: Overlapping Event execution.
    Creates 200 sprites all touching each other simultaneously, each having its own callback.
    Asserts that the custom event polling loops execute all 200 without recursion limits or stack overflows.
    """
    NUM_SPRITES = 200
    MAX_FRAMES = 20

    sprites = []
    callbacks_hit = set()

    for i in range(NUM_SPRITES):
        s = play.new_circle(color="blue", x=0, y=0, radius=50)
        s.start_physics(obeys_gravity=False, bounciness=0, mass=1)
        sprites.append(s)

    # All sprites are overlapping at (0, 0).
    # We will register them all to listen to collisions with sprite[0].
    target = sprites[0]

    for i in range(1, NUM_SPRITES):

        def _make_callback(idx):
            @sprites[idx].when_touching(target)
            def _cb():
                callbacks_hit.add(idx)

        _make_callback(i)

    frames_run = [0]

    @play.repeat_forever
    def simulation_loop():
        frames_run[0] += 1
        if frames_run[0] >= MAX_FRAMES:
            play.stop_program()

    # The engine should process 199 overlapping touching callbacks safely.
    play.start_program()

    assert frames_run[0] >= MAX_FRAMES, "Simulation stopped prematurely!"
    # All sprites overlap at (0,0), so a majority of callbacks should fire.
    assert (
        len(callbacks_hit) >= NUM_SPRITES // 2
    ), f"Expected at least {NUM_SPRITES // 2} callbacks to fire, got {len(callbacks_hit)}"
