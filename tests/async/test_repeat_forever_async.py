"""Tests for async callbacks with await.

Verifies that the game loop keeps rendering frames while async callbacks
are suspended on an await (e.g. play.timer). Covers @repeat_forever,
@when_key_released, and other event decorators.
"""

from unittest.mock import patch


def test_frames_render_during_repeat_forever_timer():
    """pygame.display.flip() must be called between awaits in @repeat_forever.

    Regression test: if the next game_loop frame is not scheduled before
    the callback suspends, the loop freezes and no frames are rendered
    until the callback finishes — all visual changes happen invisibly.
    """
    import pygame
    import play

    flip_total = [0]
    original_flip = pygame.display.flip

    def counting_flip():
        flip_total[0] += 1
        original_flip()

    # Record flip snapshots before and after each await to prove frames rendered.
    flips_between_awaits = []

    ball = play.new_circle(color="red")

    @play.repeat_forever
    async def change_color():
        before = flip_total[0]
        ball.color = "blue"
        await play.timer(seconds=0.05)
        flips_between_awaits.append(flip_total[0] - before)

        before = flip_total[0]
        ball.color = "red"
        await play.timer(seconds=0.05)
        flips_between_awaits.append(flip_total[0] - before)

    frame_count = [0]

    @play.repeat_forever
    def stopper():
        frame_count[0] += 1
        if frame_count[0] >= 60:
            play.stop_program()

    with patch.object(pygame.display, "flip", side_effect=counting_flip):
        play.start_program()

    # The callback should have completed at least once (2 measurements per iteration).
    assert (
        len(flips_between_awaits) >= 2
    ), f"Expected at least 2 measurements, got {len(flips_between_awaits)}"
    # Each await play.timer(0.05) should have allowed at least 1 frame to render.
    assert all(f >= 1 for f in flips_between_awaits), (
        f"Expected at least 1 flip between each await, got: {flips_between_awaits}. "
        "Frames are not being rendered while the callback is suspended."
    )


def test_multiple_async_repeat_forever_callbacks():
    """Multiple async @repeat_forever callbacks should all run without blocking."""
    import play

    frame_count = [0]
    a_count = [0]
    b_count = [0]

    @play.repeat_forever
    async def callback_a():
        a_count[0] += 1
        await play.timer(seconds=0.05)

    @play.repeat_forever
    async def callback_b():
        b_count[0] += 1
        await play.timer(seconds=0.05)

    @play.repeat_forever
    def stopper():
        frame_count[0] += 1
        if frame_count[0] >= 30:
            play.stop_program()

    play.start_program()

    assert frame_count[0] >= 30
    # Both callbacks should have run at least a few times
    assert a_count[0] >= 2, f"callback_a only ran {a_count[0]} times"
    assert b_count[0] >= 2, f"callback_b only ran {b_count[0]} times"


def test_frames_render_during_when_key_released_timer():
    """Game loop must keep rendering while @when_key_released awaits play.timer().

    Regression test: event callbacks (keyboard, mouse, controller) used to be
    awaited inline, which meant any await inside them froze the game loop.
    Now they are scheduled as independent tasks via create_task.
    """
    import pygame
    import play

    flip_total = [0]
    original_flip = pygame.display.flip

    def counting_flip():
        flip_total[0] += 1
        original_flip()

    flips_during_callback = []
    key_posted = [False]

    @play.when_key_released("a")
    async def on_release(key):
        before = flip_total[0]
        await play.timer(seconds=0.1)
        flips_during_callback.append(flip_total[0] - before)

    frame_count = [0]

    @play.repeat_forever
    def driver():
        frame_count[0] += 1

        # Post a key down + key up on frame 2 to trigger when_key_released
        if frame_count[0] == 2 and not key_posted[0]:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a}))
            pygame.event.post(pygame.event.Event(pygame.KEYUP, {"key": pygame.K_a}))
            key_posted[0] = True

        if frame_count[0] >= 60:
            play.stop_program()

    with patch.object(pygame.display, "flip", side_effect=counting_flip):
        play.start_program()

    # The callback should have fired and measured flips during its await
    assert (
        len(flips_during_callback) >= 1
    ), "when_key_released callback never completed — it may not have fired"
    assert all(f >= 1 for f in flips_during_callback), (
        f"Expected at least 1 flip during await, got: {flips_during_callback}. "
        "Game loop froze while @when_key_released callback was suspended."
    )
