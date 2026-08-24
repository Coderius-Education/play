"""A video with widgets around and on top of it — full-game project test.

The unit tests under tests/objects/ call the video's hooks directly; this
drives the real frame path (``update_sprites`` → ``_tick`` /
``_handle_frame_events`` → click resolution) with real pygame mouse events,
which is where autoplay deferral and click ownership actually have to behave.

This test verifies:
- autoplay starts inside the loop, so ``when_video_starts`` registered after
  construction still fires
- a button drawn on top of the video takes the click; the video does not
  also toggle underneath it
- a click on the bare picture toggles play and still reaches the user's own
  ``when_clicked``
- a slider drives the video's volume through ``when_changed``
- the video reaches its end inside the loop and fires ``when_video_ends``
"""

import pytest

from tests.conftest import (
    make_test_video,
    post_mouse_motion,
    post_mouse_down,
    post_mouse_up,
)

max_frames = 700


@pytest.fixture
def short_clip(tmp_path):
    """A one-second clip, so waiting for the real end stays fast."""
    return make_test_video(tmp_path / "kiosk.mp4", seconds=1.0)


def test_video_kiosk(short_clip):
    import play
    from play.io.screen import screen

    starts = []
    ends = []
    video_clicks = [0]
    menu_clicks = [0]
    seen = {}

    # width=240/height=180 keeps the control bar (bottom ~39px) away from the
    # picture clicks below.
    video = play.new_video(short_clip, x=0, y=0, width=240, height=180, autoplay=True)

    @video.when_video_starts
    def on_start():
        starts.append(True)

    @video.when_video_ends
    def on_end():
        ends.append(True)

    @video.when_clicked
    def on_video_clicked():
        video_clicks[0] += 1

    # A widget drawn over the middle of the picture, like a pause-menu button.
    menu = play.new_button("Menu", x=0, y=0, width=100, height=40)

    @menu.when_clicked
    def on_menu_clicked():
        menu_clicks[0] += 1

    volume = play.new_slider(x=0, y=-160, width=200, value=100)

    @volume.when_changed
    def on_volume(value):
        video.volume = value / 100

    @play.when_program_starts
    async def driver():
        async def click(x, y):
            """Post a real motion/down/up sequence at play-coordinates."""
            sx = int(screen.width / 2 + x)
            sy = int(screen.height / 2 - y)
            post_mouse_motion(sx, sy)
            await play.animate()
            await play.animate()  # a second frame so the control bar fades in
            post_mouse_down(sx, sy)
            await play.animate()
            post_mouse_up(sx, sy)
            await play.animate()

        # 1. Autoplay is deferred into the loop: it must have started by now,
        #    and the callback registered after construction must have fired.
        for _ in range(5):
            await play.animate()
        seen["autoplay"] = (video.playing, list(starts))

        # 2. The button on top of the video owns its click.
        was_playing = video.playing
        await click(0, 0)
        seen["menu"] = (menu_clicks[0], video.playing == was_playing)

        # 3. A click on the bare picture (inside the video, outside the
        #    button, above the control bar) toggles play and still counts as
        #    a click on the video.
        await click(-80, 40)
        seen["picture"] = (video.playing, video_clicks[0])

        await click(-80, 40)  # toggle back so the clip can finish
        seen["resumed"] = video.playing

        # 4. The slider drives the volume. A click at a quarter of the track
        #    starts a drag there, which sets the value.
        post_mouse_motion(5, 5)
        await play.animate()
        await click(-50, -160)
        seen["volume"] = video.volume

        # 5. Let the clip play out for real and reach its end.
        for _ in range(240):
            if video.finished:
                break
            await play.animate()
        # The end callback is scheduled as a task on the loop; give it a
        # couple of frames to actually run before reading the result.
        for _ in range(3):
            await play.animate()
        seen["end"] = (video.finished, list(ends))

        play.stop_program()

    # Safety net so a broken assertion can't hang the suite.
    @play.when_program_starts
    async def safety_timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert "end" in seen, "driver did not finish; the loop stopped early"

    autoplay_playing, autoplay_starts = seen["autoplay"]
    assert autoplay_playing is True, "autoplay should have started inside the loop"
    assert autoplay_starts == [
        True
    ], "when_video_starts registered after construction must fire with autoplay"

    menu_count, video_untouched = seen["menu"]
    assert menu_count == 1, "the button on top of the video should take the click"
    assert video_untouched, "the video must not toggle under a click a widget owned"

    picture_playing, picture_clicks = seen["picture"]
    assert picture_playing is False, "a click on the picture should pause the video"
    assert picture_clicks >= 1, "the picture click still belongs to the video"

    assert seen["resumed"] is True, "a second picture click should resume playback"

    assert seen["volume"] == pytest.approx(
        0.25, abs=0.1
    ), "clicking a quarter along the slider should set the volume to match"

    finished, end_events = seen["end"]
    assert finished is True, "the clip should have reached its end inside the loop"
    assert end_events == [True], "when_video_ends should fire exactly once"
