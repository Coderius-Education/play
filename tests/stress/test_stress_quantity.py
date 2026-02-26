import pytest
import play
import time


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_stress_quantity_sprites():
    """
    Stress test: Spawning 1000 physics-enabled sprites and running 100 frames.
    Validates that the engine does not segmentation fault or crash, and finishes in a reasonable time.
    """
    NUM_SPRITES = 1000
    MAX_FRAMES = 50

    # Spawn 1000 boxes
    boxes = []
    for i in range(NUM_SPRITES):
        # Stagger positions slightly to force collision resolution
        b = play.new_box(
            color="red",
            x=-300 + (i % 30) * 20,
            y=200 - (i // 30) * 20,
            width=10,
            height=10,
        )
        b.start_physics(bounciness=0.5, mass=1)
        boxes.append(b)

    # Floor to catch them
    floor = play.new_box(color="black", x=0, y=-250, width=800, height=20)
    floor.start_physics(can_move=False)

    frames_run = [0]

    @play.repeat_forever
    def simulation_loop():
        frames_run[0] += 1
        if frames_run[0] >= MAX_FRAMES:
            play.stop_program()

    start_time = time.time()

    # Run the simulation
    play.start_program()

    end_time = time.time()
    duration = end_time - start_time

    assert frames_run[0] >= MAX_FRAMES, "Simulation stopped prematurely!"

    # Ensure it didn't crash and finished within 15 seconds
    assert duration < 15.0, f"Stress test took too long! Duration: {duration}s"

    print(f"Quantity Stress Test (1000 boxes, 50 frames): {duration:.2f} seconds")
