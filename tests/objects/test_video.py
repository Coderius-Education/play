"""Tests for the Video object."""

import time

import pytest

import play
from play.objects.video import Video


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def make_video(path, clock, **kwargs):
    """Build a Video driven by a hand-controlled clock."""
    return Video(path, _time_fn=clock, **kwargs)


def wait_for_frames(video, count=2, timeout=5.0):
    """Give the decoding thread time to fill its queue."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if video._player.decoder.queue.qsize() >= count:
            return True
        time.sleep(0.01)
    return False


def grey_of(video):
    """The grey level of the frame currently on screen."""
    return video._player.canvas.get_at((10, 10))[0]


##### construction #####


def test_uses_native_size_by_default(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    assert video.width == 64
    assert video.height == 48
    assert video.length == pytest.approx(2.0, abs=0.1)
    assert video.frame_rate == pytest.approx(10.0)


def test_width_alone_keeps_the_shape(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=128)

    assert video.width == 128
    assert video.height == 96


def test_height_alone_keeps_the_shape(video_file, fake_clock):
    video = make_video(video_file, fake_clock, height=96)

    assert (video.width, video.height) == (128, 96)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        play.new_video("no_such_clip.mp4")


def test_new_video_is_exported(video_file):
    video = play.new_video(video_file)

    assert isinstance(video, Video)
    assert video.file_name == video_file


def test_shows_first_frame_without_autoplay(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    assert video.playing is False
    assert video.paused is False
    # Frame 0 is black; a later frame would be lighter.
    assert grey_of(video) < 10


def test_autoplay_starts_playing(video_file, fake_clock):
    video = make_video(video_file, fake_clock, autoplay=True)

    # Autoplay is deferred to the first frame so that callbacks registered
    # right after construction still see the start events.
    assert video.playing is False
    video._tick()
    assert video.playing is True


def test_autoplay_can_be_cancelled_before_the_first_frame(video_file, fake_clock):
    video = make_video(video_file, fake_clock, autoplay=True)

    video.stop()
    video._tick()
    assert video.playing is False


##### playback #####


def test_play_pause_and_resume(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.play()
    assert video.playing is True

    fake_clock.advance(0.5)
    video.pause()
    assert video.paused is True
    assert video.time == pytest.approx(0.5, abs=0.01)

    # Time stands still while paused.
    fake_clock.advance(1.0)
    assert video.time == pytest.approx(0.5, abs=0.01)

    video.play()
    fake_clock.advance(0.25)
    assert video.time == pytest.approx(0.75, abs=0.01)


def test_toggle_play(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.toggle_play()
    assert video.playing is True
    video.toggle_play()
    assert video.playing is False


def test_clock_advances_and_shows_later_frames(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    wait_for_frames(video, 4)

    fake_clock.advance(0.5)
    video._tick()

    assert video._player.current_time > 0.0
    assert grey_of(video) > 10


def test_seek_jumps_to_the_right_frame(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.seek(1.5)

    assert video.time == pytest.approx(1.5, abs=0.01)
    assert video._player.current_time == pytest.approx(1.5, abs=0.11)
    # Frame 15 was encoded as grey 120.
    assert grey_of(video) == pytest.approx(120, abs=12)


def test_time_setter_seeks(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.time = 1.0

    assert video.time == pytest.approx(1.0, abs=0.01)


def test_seek_is_clamped(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.seek(-5)
    assert video.time == 0.0

    video.seek(9999)
    assert video.time == pytest.approx(video.length)


def test_stop_returns_to_the_start(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(1.0)
    video.stop()

    assert video.time == 0.0
    assert video.playing is False


def test_restart_plays_from_the_beginning(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(1.0)
    video.restart()

    assert video.time == pytest.approx(0.0, abs=0.01)
    assert video.playing is True


def test_reaching_the_end_finishes(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()

    fake_clock.advance(video.length + 0.1)
    video._tick()

    assert video.finished is True
    assert video.playing is False


def test_loop_starts_again(video_file, fake_clock):
    video = make_video(video_file, fake_clock, loop=True)
    video.play()

    fake_clock.advance(video.length + 0.1)
    video._tick()

    assert video.finished is False
    assert video.playing is True
    assert video.time == pytest.approx(0.0, abs=0.05)


def test_play_after_finishing_starts_over(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(video.length + 0.1)
    video._tick()

    video.play()

    assert video.playing is True
    assert video.time == pytest.approx(0.0, abs=0.05)


def test_speed_scales_the_clock(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.speed = 2.0
    video.play()

    fake_clock.advance(0.5)

    assert video.time == pytest.approx(1.0, abs=0.01)


def test_speed_must_be_positive(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.speed = 0

    assert video.speed == 1.0


##### sound #####


def test_volume_is_clamped_and_applied(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.volume = 0.5
    assert video.volume == 0.5

    video.volume = 5
    assert video.volume == 1.0


def test_muting(video_file, fake_clock):
    video = make_video(video_file, fake_clock, volume=0.8)
    video.play()

    video.muted = True
    assert video.muted is True
    if video._player.sound is not None:
        assert video._player.sound.get_volume() == pytest.approx(0.0)

    video.muted = False
    if video._player.sound is not None:
        assert video._player.sound.get_volume() == pytest.approx(0.8, abs=0.02)


def test_playing_a_video_with_no_sound(silent_video_file, fake_clock):
    video = make_video(silent_video_file, fake_clock)
    video.play()
    fake_clock.advance(0.5)
    video._tick()

    assert video.playing is True
    assert video._player.pcm is None
    assert video._player.sound is None


##### drawing #####


def test_new_frame_marks_the_video_for_redrawing(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    wait_for_frames(video, 4)
    video.update()
    assert video._should_recompute is False

    fake_clock.advance(0.5)
    video._tick()

    assert video._should_recompute is True


def test_no_redraw_when_the_clock_has_not_moved(video_file, fake_clock):
    # Controls are switched off so that their fade-in does not ask for redraws
    # of its own; this is only about frames.
    video = make_video(video_file, fake_clock, controls=False)
    video.play()
    fake_clock.advance(0.5)

    # Let the decoder catch up, so every frame due at 0.5s has been shown.
    for _ in range(5):
        video._tick()
        video.update()
        time.sleep(0.02)

    video._tick()

    assert video._should_recompute is False


def test_update_can_run_many_times_per_frame(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(0.5)
    video._tick()

    for _ in range(10):
        video.update()

    assert video.image is not None
    assert video._should_recompute is False


def test_size_and_angle_are_applied(video_file, fake_clock):
    video = make_video(video_file, fake_clock, size=50)
    video.update()

    assert video.image.get_width() == pytest.approx(32, abs=1)

    video.angle = 90
    video.update()
    # A quarter turn swaps the picture's width and height.
    assert video.image.get_size() == (24, 32)


def test_hit_area_follows_the_video_size(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=200, height=100)

    assert video.physics._pymunk_shape.point_query((0, 0)).distance <= 0
    # Well outside a 200x100 box centred on the origin.
    assert video.physics._pymunk_shape.point_query((400, 0)).distance > 0


def test_hidden_video_keeps_playing(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    video.hide()

    fake_clock.advance(0.5)
    video._tick()

    assert video.playing is True
    assert video.time == pytest.approx(0.5, abs=0.01)


##### housekeeping #####


def test_close_stops_the_decoder(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.close()

    assert video._player.decoder is None


def test_remove_stops_the_decoder(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    decoder = video._player.decoder
    video.remove()

    assert decoder.is_alive() is False
    assert video._player.decoder is None


def test_close_is_safe_to_call_twice(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.close()
    video.close()


def test_clone_makes_another_video(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=128, volume=0.5, loop=True)

    clone = video.clone()

    assert clone.width == 128
    assert clone.volume == 0.5
    assert clone.loop is True
    assert clone is not video


##### control bar drawing #####


def test_control_bar_is_drawn_over_the_frame(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255

    surface = video._render_controls()

    assert surface.get_width() == 320
    assert surface.get_height() == video._bar_height()


def test_control_bar_is_reused_until_something_changes(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255

    first = video._render_controls()
    second = video._render_controls()
    assert first is second

    video.muted = True
    assert video._render_controls() is not first


def test_control_bar_is_reused_when_the_duration_is_unknown(
    video_file, fake_clock, monkeypatch
):
    # A video with no duration metadata reports length 0 and runs its clock on
    # regardless. The cache key divides time by the length, so without a clamp
    # every frame produced a fresh key and the whole bar was redrawn each time.
    from play.objects import video as video_module

    real_probe = video_module.probe

    def probe_without_duration(path):
        info = real_probe(path)
        info.duration = 0.0
        return info

    monkeypatch.setattr(video_module, "probe", probe_without_duration)
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255
    video.play()

    # Take the baseline after the first frame: the played fraction genuinely
    # moves from 0 to its clamped ceiling once, and that redraw is correct.
    fake_clock.advance(1 / 60)
    video._tick()
    first = video._render_controls()

    for _ in range(4):
        fake_clock.advance(1 / 60)
        video._tick()
        assert video._render_controls() is first


def test_control_bar_fades_in_while_hovered(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 0.0
    video._player.hover = True

    video._tick_controls(fake_clock.now)

    assert video._player.controls_alpha > 0


def test_control_bar_fades_out_once_the_mouse_has_gone(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255.0
    video._player.hover = False
    fake_clock.advance(10)

    video._tick_controls(fake_clock.now)

    assert video._player.controls_alpha < 255


def test_no_control_bar_when_controls_are_off(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240, controls=False)
    video._player.controls_alpha = 255.0
    video._player.hover = True

    video._tick_controls(fake_clock.now)

    assert video._player.controls_alpha == 0.0


def test_drawing_works_on_a_very_small_video(video_file, fake_clock):
    # The control bar has to degrade gracefully rather than crash.
    video = make_video(video_file, fake_clock, width=48, height=32)
    video._player.controls_alpha = 255

    video._render_controls()
    video.update()

    assert video.image is not None


def test_a_resized_video_fills_the_whole_picture(video_file, fake_clock):
    # Regression: the frame used to be drawn at its own size in the corner of a
    # larger black canvas instead of being scaled up to fill it.
    video = make_video(video_file, fake_clock, width=320, height=240, controls=False)
    video.seek(1.5)
    video.update()

    assert video.image.get_size() == (320, 240)
    # Frame 15 was encoded as grey 120, and should cover the whole picture.
    for spot in [(10, 10), (160, 120), (310, 230)]:
        assert video.image.get_at(spot)[0] == pytest.approx(120, abs=15)


def test_the_control_bar_sits_inside_the_video(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255
    video.update()

    bar_top = 240 - video._bar_height()
    # The bar darkens the bottom strip, so it must be darker than the picture.
    picture = video.image.get_at((160, bar_top - 20))[0]
    bar = video.image.get_at((300, 236))[0]
    assert bar < picture + 5


##### missing metadata #####


def test_unknown_duration_does_not_end_instantly(video_file, fake_clock, monkeypatch):
    # Some streams carry no duration; probe() then reports 0.0. The clock used
    # to clamp to that, so the video "ended" on its very first frame.
    from play.objects import video as video_module

    real_probe = video_module.probe

    def probe_without_duration(path):
        info = real_probe(path)
        info.duration = 0.0
        return info

    monkeypatch.setattr(video_module, "probe", probe_without_duration)
    video = make_video(video_file, fake_clock)

    video.play()
    fake_clock.advance(0.5)
    video._tick()

    assert video.playing is True
    assert video.finished is False
    assert video.time == pytest.approx(0.5, abs=0.01)


##### resizing and the other setters #####


def test_resizing_rebuilds_the_hit_shape(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=200, height=100)

    video.width = 400
    video.height = 300

    assert (video.width, video.height) == (400, 300)
    # The pymunk hit-shape must follow the new size, not keep the old one.
    assert video.physics._pymunk_shape.point_query((195, 145)).distance <= 0
    assert video.physics._pymunk_shape.point_query((400, 0)).distance > 0
    # The cached control bar was drawn for the old size and must be redrawn.
    assert video._player.controls_key is None


def test_controls_can_be_toggled_at_runtime(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.controls = False
    assert video.controls is False

    video.controls = 1  # coerced, the way a beginner might write it
    assert video.controls is True


def test_loop_setter_coerces_to_bool(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.loop = 1
    assert video.loop is True
    video.loop = 0
    assert video.loop is False


def test_speed_change_while_playing_keeps_the_position(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(0.5)

    video.speed = 2.0

    # Changing speed re-bases the clock: the position must not jump.
    assert video.time == pytest.approx(0.5, abs=0.01)
    fake_clock.advance(0.25)
    assert video.time == pytest.approx(1.0, abs=0.01)


def test_play_twice_and_pause_twice_are_no_ops(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.play()
    fake_clock.advance(0.5)
    video.play()  # already playing: must not re-base the clock
    assert video.time == pytest.approx(0.5, abs=0.01)

    video.pause()
    video.pause()  # already paused: nothing to do
    assert video.paused is True
    assert video.time == pytest.approx(0.5, abs=0.01)


##### contracts the mutation round showed were unpinned #####


def test_stop_on_an_idle_video_fires_no_pause_event(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    fired = []

    video.when_video_pauses(lambda: fired.append(True))
    video.stop()

    import asyncio
    import play.loop

    for _ in range(3):
        play.loop.get_loop().run_until_complete(asyncio.sleep(0))
    assert fired == [], "stopping an idle video must not report a pause"


def test_seek_while_playing_keeps_playing(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()

    video.seek(1.0)

    assert video.playing is True
    fake_clock.advance(0.25)
    assert video.time == pytest.approx(1.25, abs=0.01)


def test_fractional_speed_is_accepted(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.speed = 0.5

    assert video.speed == 0.5
    video.play()
    fake_clock.advance(1.0)
    assert video.time == pytest.approx(0.5, abs=0.01)


def test_speed_change_while_paused_starts_no_audio(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    video.pause()

    video.speed = 2.0

    assert video._player.sound is None, "a paused video must stay silent"


def test_speed_resamples_the_audio(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    normal = video._pcm_slice(0.0)
    if normal is None:
        pytest.skip("no mixer in this environment")

    video._player.speed = 2.0
    double = video._pcm_slice(0.0)

    assert double is not None
    assert len(double) == pytest.approx(len(normal) / 2, rel=0.05)


def test_controls_are_never_burnt_into_the_frame(video_file, fake_clock):
    # Native size: update() must draw the bar on a copy. Without the copy the
    # bar lands on the shared canvas and pollutes every later frame.
    video = make_video(video_file, fake_clock)  # native 64x48
    video._player.controls_alpha = 255
    video._should_recompute = True

    before = video._player.canvas.get_at((5, 44))[:3]
    video.update()
    after = video._player.canvas.get_at((5, 44))[:3]

    assert after == before, "the control bar leaked onto the frame canvas"


def test_a_closed_video_stays_inert(video_file, fake_clock):
    video = make_video(video_file, fake_clock, autoplay=True)
    frames = []
    video.when_video_frame_changes(lambda: frames.append(True))

    video.close()
    video._tick()

    import asyncio
    import play.loop

    for _ in range(3):
        play.loop.get_loop().run_until_complete(asyncio.sleep(0))
    assert video.playing is False, "close() must cancel a pending autoplay"
    assert frames == [], "a closed video must not report new frames"


@pytest.mark.parametrize(
    "poke",
    [
        lambda v: v.play(),
        lambda v: v.toggle_play(),
        lambda v: v.seek(0.5),
        lambda v: v.stop(),
        lambda v: v.restart(),
        lambda v: v.pause(),
    ],
    ids=["play", "toggle_play", "seek", "stop", "restart", "pause"],
)
def test_playback_calls_on_a_closed_video_do_nothing(video_file, fake_clock, poke):
    # close() lets go of the decoder, so the picture can never change again.
    # play() used to start the audio anyway and report playing=True, and
    # seek/stop/restart raised AttributeError on the decoder that was gone.
    video = make_video(video_file, fake_clock)
    video.close()

    poke(video)

    assert video.playing is False
    assert video._player.sound is None, "a closed video must not make a sound"


def test_a_removed_video_falls_silent(video_file, fake_clock):
    # remove() is how a sprite leaves the game; the sound has to go with it,
    # and must not come back if the video is played again afterwards.
    video = make_video(video_file, fake_clock)
    video.play()
    assert video.playing is True

    video.remove()
    assert video._player.sound is None

    video.play()
    assert video.playing is False
    assert video._player.sound is None


@pytest.mark.parametrize(
    "poke",
    [
        lambda v: v.play(),
        lambda v: (v.play(), v.pause()),
        lambda v: v.stop(),
        lambda v: setattr(v, "volume", 0.3),
        lambda v: setattr(v, "muted", True),
        lambda v: setattr(v, "controls", False),
        lambda v: setattr(v, "width", 100),
        lambda v: setattr(v, "height", 90),
    ],
    ids=["play", "pause", "stop", "volume", "muted", "controls", "width", "height"],
)
def test_state_changes_mark_the_video_for_redrawing(video_file, fake_clock, poke):
    video = make_video(video_file, fake_clock)
    video.update()
    video._should_recompute = False

    poke(video)

    assert video._should_recompute is True


def test_width_and_height_setters_floor_at_one(video_file, fake_clock):
    video = make_video(video_file, fake_clock)

    video.width = 0
    video.height = -5

    assert video.width == 1
    assert video.height == 1


def test_out_of_range_video_volume_warns(video_file, fake_clock, caplog):
    video = make_video(video_file, fake_clock)

    with caplog.at_level("WARNING", logger="play"):
        video.volume = 0.5
    assert not caplog.records, "a valid volume must not warn"

    with caplog.at_level("WARNING", logger="play"):
        video.volume = 5

    assert any("Volume must be between" in r.message for r in caplog.records)
    assert video.volume == 1.0


def test_reaching_the_end_marks_the_video_for_redrawing(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(video.length + 0.1)
    video._should_recompute = False

    video._tick()

    assert video.finished is True
    assert video._should_recompute is True, "the end state must trigger a redraw"


def test_seek_after_finishing_un_ends_the_video(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(video.length + 0.1)
    video._tick()
    assert video.finished is True

    video.seek(1.0)

    assert video.finished is False
    assert video.paused is True
    assert video.time == pytest.approx(1.0, abs=0.01)
