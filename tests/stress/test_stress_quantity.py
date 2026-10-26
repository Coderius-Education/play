import time

import pytest

import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


@pytest.mark.slow(120)
@pytest.mark.xdist_group("stress")
def test_a_thousand_boxes_fall_straight_down_and_the_bottom_row_lands_on_the_floor():
    columns, rows = 40, 25
    boxes = []
    for i in range(columns * rows):
        box = play.new_box(
            color="red",
            x=-390 + (i % columns) * 20,
            y=280 - (i // columns) * 20,
            width=10,
            height=10,
        )
        box.start_physics(bounciness=0.5, mass=1)
        boxes.append(box)
    start = [(box.x, box.y) for box in boxes]

    floor = play.new_box(color="black", y=-220, width=800, height=20)
    floor.start_physics(can_move=False)
    resting_y = floor.y + 10 + 5

    frames_run = [0]

    @play.repeat_forever
    def simulation_loop():
        frames_run[0] += 1
        if frames_run[0] == 30:
            play.stop_program()

    start_time = time.time()
    play.start_program()
    duration = time.time() - start_time

    assert frames_run[0] == 30
    assert duration < 120.0, f"Stress test took too long! Duration: {duration}s"
    for box, (x, y) in zip(boxes, start):
        assert box.x == pytest.approx(x, abs=0.5)
        assert resting_y - 0.5 <= box.y < y
    assert all(box.y < resting_y + 2 for box in boxes[-columns:])
