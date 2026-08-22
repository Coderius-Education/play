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

    assert video.playing is True


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
    assert video.image is not None


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
