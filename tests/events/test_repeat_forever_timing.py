"""An ``async def`` in repeat_forever runs once per frame, like a plain ``def``."""

import play

FRAMES = 60


def _frames_in_which(register_body):
    frame = [0]
    recorded = []

    @play.repeat_forever
    def count_frames():
        frame[0] += 1
        if frame[0] == FRAMES:
            play.stop_program()

    register_body(lambda: recorded.append(frame[0]))
    play.start_program()
    return recorded


def test_an_async_repeat_forever_runs_in_every_frame():
    def register(record):
        @play.repeat_forever
        async def body():
            record()

    assert _frames_in_which(register) == list(range(1, FRAMES))


def test_an_async_repeat_forever_that_waits_a_frame_still_runs_in_every_frame():
    def register(record):
        @play.repeat_forever
        async def body():
            await play.animate()
            record()

    assert _frames_in_which(register) == list(range(2, FRAMES))


def test_an_async_repeat_forever_that_waits_three_frames_starts_every_third_frame():
    def register(record):
        @play.repeat_forever
        async def body():
            record()
            for _ in range(3):
                await play.animate()

    assert _frames_in_which(register) == list(range(1, FRAMES, 3))
