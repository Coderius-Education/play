"""An ``async def`` in repeat_forever runs once per frame, like a plain ``def``."""

import play

FRAMES = 60


def _run_frames(frames=FRAMES):
    count = [0]

    @play.repeat_forever
    def stop_after_frames():
        count[0] += 1
        if count[0] == frames:
            play.stop_program()

    play.start_program()


def test_an_async_repeat_forever_runs_every_frame():
    runs = [0]

    @play.repeat_forever
    async def count():
        runs[0] += 1

    _run_frames()

    assert runs[0] >= FRAMES - 1


def test_an_async_repeat_forever_that_waits_a_frame_still_runs_every_frame():
    runs = [0]

    @play.repeat_forever
    async def count():
        await play.animate()
        runs[0] += 1

    _run_frames()

    assert runs[0] >= FRAMES - 2


def test_an_async_repeat_forever_moves_a_sprite_as_fast_as_a_plain_one():
    sync_box = play.new_box(y=100)
    async_box = play.new_box(y=-100)

    @play.repeat_forever
    def move_sync():
        sync_box.x += 1

    @play.repeat_forever
    async def move_async():
        async_box.x += 1

    _run_frames()

    assert abs(async_box.x - sync_box.x) <= 1


def test_an_async_repeat_forever_never_runs_twice_at_once():
    active = [0]
    overlaps = [0]

    @play.repeat_forever
    async def slow():
        active[0] += 1
        if active[0] > 1:
            overlaps[0] += 1
        for _ in range(3):
            await play.animate()
        active[0] -= 1

    _run_frames()

    assert overlaps[0] == 0
