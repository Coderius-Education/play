"""Tests for the Video object."""

import time

import pytest

import play
from play.core.mouse_loop import mouse_state
from play.io.keypress import keyboard_state
from play.io.mouse import mouse
from play.objects.video.video import Video, _live_videos


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


def count_colour(surface, rgb):
    """How many visible pixels of *surface* have exactly this RGB."""
    width, height = surface.get_size()
    pixels = (surface.get_at((x, y)) for x in range(width) for y in range(height))
    return sum(1 for p in pixels if p.a and tuple(p)[:3] == rgb)


def point_on(video, local_x, local_y):
    """Put the mouse at a pixel position inside the video."""
    mouse.x = local_x - video.width / 2
    mouse.y = video.height / 2 - local_y


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
    with pytest.raises(FileNotFoundError, match="no_such_clip.mp4"):
        play.new_video("no_such_clip.mp4")


def test_new_video_passes_on_its_settings(video_file):
    video = play.new_video(
        video_file, width=128, volume=0.5, speed=2.0, loop=True, muted=True, layer=4
    )

    assert isinstance(video, Video)
    assert video.file_name == video_file
    assert (video.width, video.height) == (128, 96)
    assert (video.volume, video.speed, video.loop, video.muted) == (
        0.5,
        2.0,
        True,
        True,
    )
    assert video.layer == 4


def test_a_speed_of_zero_or_less_warns_and_plays_at_normal_speed(
    video_file, fake_clock, caplog
):
    with caplog.at_level("WARNING", logger="play"):
        video = make_video(video_file, fake_clock, speed=0)

    assert any("speed must be greater than 0" in r.message for r in caplog.records)
    assert video.speed == 1.0


def test_a_volume_out_of_range_when_made_is_clamped(video_file, fake_clock):
    assert make_video(video_file, fake_clock, volume=5).volume == 1.0
    assert make_video(video_file, fake_clock, volume=-1).volume == 0.0


def test_a_long_video_warns_that_its_sound_uses_memory(
    video_file, fake_clock, monkeypatch, caplog
):
    from play.objects.video import video as video_module

    real_probe = video_module.probe

    def probe_six_minutes(path):
        info = real_probe(path)
        info.duration = 360.0
        return info

    monkeypatch.setattr(video_module, "probe", probe_six_minutes)
    with caplog.at_level("WARNING", logger="play"):
        make_video(video_file, fake_clock)

    assert any("6 minutes long" in r.getMessage() for r in caplog.records)


def test_a_short_video_does_not_warn_about_memory(video_file, fake_clock, caplog):
    with caplog.at_level("WARNING", logger="play"):
        make_video(video_file, fake_clock)

    assert not any("minutes long" in r.getMessage() for r in caplog.records)


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


def test_there_is_no_sound_to_play_past_the_end_of_the_sound_track(
    video_file, fake_clock
):
    video = make_video(video_file, fake_clock)
    if video._pcm_slice(0.0) is None:
        pytest.skip("no mixer in this environment")

    assert video._pcm_slice(video.length * 10) is None


def test_with_no_free_sound_channel_the_video_plays_without_sound(
    video_file, fake_clock, monkeypatch, caplog
):
    import pygame

    video = make_video(video_file, fake_clock)
    if video._pcm_slice(0.0) is None:
        pytest.skip("no mixer in this environment")
    monkeypatch.setattr(pygame.mixer, "find_channel", lambda *args: None)

    with caplog.at_level("WARNING", logger="play"):
        video.play()
    fake_clock.advance(0.5)

    assert any("No free sound channels" in r.message for r in caplog.records)
    assert video.playing is True
    assert video.time == pytest.approx(0.5, abs=0.01)


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
    deadline = time.monotonic() + 5.0
    while video._player.current_time < 0.5 - 1e-3 and time.monotonic() < deadline:
        video._tick()
        time.sleep(0.01)
    video.update()

    video._tick()

    assert video._should_recompute is False


def test_update_can_run_many_times_per_frame(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(0.5)
    video._tick()

    for _ in range(10):
        video.update()

    assert video.image.get_size() == (64, 48)
    assert video._should_recompute is False


def test_a_video_at_a_negative_size_shows_nothing_instead_of_crashing(
    video_file, fake_clock
):
    video = make_video(video_file, fake_clock, size=-10)
    video.update()
    assert video.image.get_size() == (0, 0)


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


def test_closing_twice_does_not_crash_and_leaves_the_video_closed(
    video_file, fake_clock
):
    video = make_video(video_file, fake_clock)
    video.play()

    video.close()
    video.close()

    assert video.playing is False
    assert video._player.decoder is None
    assert video not in _live_videos


def test_clone_makes_another_video(video_file, fake_clock):
    video = make_video(
        video_file,
        fake_clock,
        width=128,
        volume=0.5,
        speed=2.0,
        loop=True,
        controls=False,
        muted=True,
    )

    clone = video.clone()

    assert clone is not video
    assert (clone.width, clone.height) == (128, 96)
    assert (clone.volume, clone.speed, clone.loop) == (0.5, 2.0, True)
    assert (clone.controls, clone.muted) == (False, True)


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
    from play.objects.video import video as video_module

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


def test_a_very_small_video_still_draws_its_control_bar(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=48, height=32)
    video.seek(1.5)
    video._player.controls_alpha = 255
    video._should_recompute = True

    video.update()

    assert video.image.get_size() == (48, 32)
    assert video._bar_height() == 14
    picture = video.image.get_at((24, 5))[0]
    bar = video.image.get_at((40, 30))[0]
    assert bar < picture - 20


def test_a_narrow_video_has_no_mute_button_so_its_bar_seeks_to_the_end(
    video_file, fake_clock
):
    video = make_video(video_file, fake_clock, width=160, height=120)
    video._player.controls_alpha = 255

    point_on(video, 155, 115)
    mouse._is_clicked = True
    mouse_state.click_happened = True
    video._handle_frame_events()

    assert video.muted is False
    assert video.volume == 1.0
    assert video.time > 0.9 * video.length


@pytest.mark.xfail(
    strict=True,
    reason="_local_point reads size 0 as 100, so an invisible video still takes keys",
)
def test_a_video_at_size_zero_does_not_take_the_keyboard(video_file, fake_clock):
    import pygame

    video = make_video(video_file, fake_clock, size=0)
    point_on(video, video.width / 2, video.height / 2)

    keyboard_state.pressed_this_frame.add(pygame.K_SPACE)
    video._handle_frame_events()

    assert video.playing is False


def test_the_time_label_is_drawn_even_after_the_font_module_was_shut_down(
    video_file, fake_clock
):
    import pygame

    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255
    pygame.font.quit()

    bar = video._render_controls()

    label = bar.subsurface((video._scrub_area().left + 10, 24, 50, 20))
    assert count_colour(label, (255, 255, 255)) > 0


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
    from play.objects.video import video as video_module

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


def test_a_video_in_the_browser_says_videos_do_not_play_there(video_file, monkeypatch):
    monkeypatch.setattr(play.loop, "RUNS_IN_BROWSER", True)

    with pytest.raises(ImportError, match="can't be played in the browser"):
        play.new_video(video_file)


def test_the_time_never_runs_past_the_end(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()

    fake_clock.advance(video.length + 5)

    assert video.time == pytest.approx(video.length)


def test_seeking_a_finished_video_to_its_end_leaves_it_finished(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    fake_clock.advance(video.length + 0.1)
    video._tick()

    video.seek(video.length)

    assert video.finished is True


def test_the_sound_starts_where_the_picture_is(video_file, fake_clock):
    import pygame

    video = make_video(video_file, fake_clock)
    whole = video._pcm_slice(0.0)
    if whole is None:
        pytest.skip("no mixer in this environment")
    rate, size, channels = pygame.mixer.get_init()
    one_second = rate * channels * abs(size) // 8

    from_one_second = video._pcm_slice(1.0)

    assert len(whole) - len(from_one_second) == pytest.approx(one_second, rel=0.01)


def test_pausing_a_video_leaves_a_sound_that_took_over_its_channel_alone(
    video_file, fake_clock
):
    import pygame

    video = make_video(video_file, fake_clock)
    video.play()
    channel = video._player.channel
    if channel is None:
        pytest.skip("no free mixer channel in this environment")
    other = pygame.mixer.Sound(buffer=bytes(44100 * 4))
    channel.play(other)

    video.pause()

    assert channel.get_busy()
    assert channel.get_sound() is other
    channel.stop()


def test_closing_a_video_lets_go_of_its_callbacks(video_file, fake_clock):
    from play.callback import callback_manager, CallbackType

    video = make_video(video_file, fake_clock)
    video.when_video_ends(lambda: None)
    video.when_video_frame_changes(lambda time: None)

    video.close()

    for event in (CallbackType.WHEN_VIDEO_ENDS, CallbackType.WHEN_VIDEO_FRAME):
        assert not callback_manager.get_callback(event, id(video))


@pytest.mark.parametrize(
    "seconds, shown", [(0, "0:00"), (5, "0:05"), (65, "1:05"), (600, "10:00")]
)
def test_the_control_bar_shows_time_as_minutes_and_seconds(seconds, shown):
    from play.objects.video.video_controls import _format_time

    assert _format_time(seconds) == shown


def white_in(surface, rect):
    """How many pure white pixels a part of the control bar has."""
    return count_colour(surface.subsurface(rect), (255, 255, 255))


def test_the_button_shows_play_when_stopped_and_pause_while_playing(
    video_file, fake_clock
):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255
    middle = video._bar_height() // 2

    stopped = video._render_controls()
    assert stopped.get_at((middle, middle))[:3] == (255, 255, 255)

    video.play()
    playing = video._render_controls()
    assert playing.get_at((middle, middle))[:3] != (255, 255, 255)


def test_muting_empties_the_volume_bar(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255
    volume_bar = video._volume_area()
    track = (volume_bar.left, 0, volume_bar.width, video._bar_height())
    loud = white_in(video._render_controls(), track)

    video.muted = True

    assert white_in(video._render_controls(), track) < loud / 4


def test_a_narrow_video_has_no_room_for_the_time(video_file, fake_clock):
    narrow = make_video(video_file, fake_clock, width=140, height=240)
    wide = make_video(video_file, fake_clock, width=320, height=240)
    for video in (narrow, wide):
        video._player.controls_alpha = 255
    label = (narrow._scrub_area().left + 10, 24, 50, 20)

    assert white_in(narrow._render_controls(), label) == 0
    assert white_in(wide._render_controls(), label) > 0
