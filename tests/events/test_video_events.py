"""Tests for video events and the built-in controls."""

import time

import pytest

import play
from play.core.mouse_loop import mouse_state
from play.core.sprites_loop import update_sprites
from play.io.keypress import keyboard_state
from play.io.mouse import mouse
from play.objects.video import Video


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def make_video(path, clock, **kwargs):
    return Video(path, _time_fn=clock, **kwargs)


def wait_for_frames(video, count=2, timeout=5.0):
    """Give the decoding thread time to fill its queue.

    _tick never blocks on the decoder, so without this a loaded machine can
    reach the assertions before a single frame has been handed over.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if video._player.decoder.queue.qsize() >= count:
            return True
        time.sleep(0.01)
    return False


def pump():
    """Let the callbacks that were fired actually run.

    Callbacks are scheduled as tasks on play's own event loop, so the loop has
    to be given a couple of turns before they have run.
    """
    import asyncio

    import play.loop

    loop = play.loop.get_loop()
    for _ in range(3):
        loop.run_until_complete(asyncio.sleep(0))


def run_frame(do_events=True):
    """Run one pass of the sprite loop on play's event loop."""
    import play.loop

    return play.loop.get_loop().run_until_complete(update_sprites(do_events=do_events))


def point_on(video, local_x, local_y):
    """Put the mouse at a pixel position inside the video."""
    mouse.x = local_x - video.width / 2
    mouse.y = video.height / 2 - local_y


##### events #####


def test_when_video_ends_fires(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    fired = []

    @video.when_video_ends
    def ended():
        fired.append(True)

    video.play()
    fake_clock.advance(video.length + 0.1)
    video._tick()
    pump()

    assert fired == [True]


def test_when_video_starts_fires_once(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    fired = []

    @video.when_video_starts
    def started():
        fired.append(True)

    video.play()
    video.pause()
    video.play()
    pump()

    assert fired == [True]


def test_when_video_starts_fires_with_autoplay(video_file, fake_clock):
    # The obvious student pattern: autoplay=True, then register the callback.
    # Autoplay is deferred to the first frame precisely so this works.
    video = make_video(video_file, fake_clock, autoplay=True)
    fired = []

    @video.when_video_starts
    def started():
        fired.append(True)

    video._tick()
    pump()

    assert fired == [True]


def test_when_video_plays_fires_on_every_resume(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    fired = []

    @video.when_video_plays
    def played():
        fired.append(True)

    video.play()
    video.pause()
    video.play()
    pump()

    assert len(fired) == 2


def test_when_video_pauses_fires(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    fired = []

    @video.when_video_pauses
    def paused():
        fired.append(True)

    video.play()
    video.pause()
    pump()

    assert fired == [True]


def test_when_video_frame_changes_receives_the_time(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    seen = []

    @video.when_video_frame_changes
    def changed(time):  # pylint: disable=redefined-outer-name
        seen.append(time)

    video.play()
    for _ in range(4):
        fake_clock.advance(0.2)
        video._tick()
        time.sleep(0.02)
    pump()

    assert seen, "expected at least one frame event"
    assert all(isinstance(moment, float) for moment in seen)
    assert seen == sorted(seen)


def test_module_level_video_event_decorator(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    fired = []

    @play.when_video_ends(video)
    def ended():
        fired.append(True)

    video.play()
    fake_clock.advance(video.length + 0.1)
    video._tick()
    pump()

    assert fired == [True]


##### controls #####


def test_clicking_the_play_button_starts_the_video(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255

    point_on(video, 10, video.height - 10)  # the play button
    mouse._is_clicked = True
    mouse_state.click_happened = True

    consumed = video._handle_frame_events()

    assert consumed is True
    assert video.playing is True


def test_control_bar_click_is_not_reported_as_a_click_on_the_video(
    video_file, fake_clock
):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255
    clicks = []

    @video.when_clicked
    def clicked():
        clicks.append(True)

    point_on(video, 10, video.height - 10)
    mouse._is_clicked = True
    mouse_state.click_happened = True

    assert video._handle_frame_events() is True
    assert clicks == []


def test_clicking_the_picture_toggles_play_and_still_counts_as_a_click(
    video_file, fake_clock
):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255

    point_on(video, 160, 60)  # well above the control bar
    mouse._is_clicked = True
    mouse_state.click_happened = True

    consumed = video._handle_frame_events()

    assert consumed is False  # so the user's own when_clicked still runs
    assert video.playing is True


def test_dragging_the_scrubber_seeks(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255

    area = video._scrub_area()
    point_on(video, area.left + area.width // 2, area.centery)
    mouse._is_clicked = True
    mouse_state.click_happened = True

    assert video._handle_frame_events() is True
    assert video.time == pytest.approx(video.length / 2, abs=0.15)


def test_clicking_mute_toggles_sound(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255

    area = video._mute_area()
    point_on(video, area.centerx, area.centery)
    mouse._is_clicked = True
    mouse_state.click_happened = True

    assert video._handle_frame_events() is True
    assert video.muted is True


def test_controls_ignore_clicks_outside_the_video(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255

    mouse.x, mouse.y = 5000, 5000
    mouse._is_clicked = True
    mouse_state.click_happened = True

    assert video._handle_frame_events() is False
    assert video.playing is False


def test_controls_work_on_a_rotated_video(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240, angle=90)
    video._player.controls_alpha = 255

    # The play button in local pixels, mapped through the 90 degree rotation.
    point_on(video, 10, video.height - 10)
    rotated_x, rotated_y = -mouse.y, mouse.x
    mouse.x, mouse.y = rotated_x, rotated_y
    mouse._is_clicked = True
    mouse_state.click_happened = True

    assert video._handle_frame_events() is True
    assert video.playing is True


def test_space_toggles_play_while_hovering(video_file, fake_clock):
    import pygame

    video = make_video(video_file, fake_clock, width=320, height=240)
    point_on(video, 160, 60)
    keyboard_state.pressed_this_frame.add(pygame.K_SPACE)

    video._handle_frame_events()

    assert video.playing is True


def test_arrow_keys_seek_while_hovering(video_file, fake_clock):
    import pygame

    video = make_video(video_file, fake_clock, width=320, height=240)
    video.seek(0.0)
    point_on(video, 160, 60)
    keyboard_state.pressed_this_frame.add(pygame.K_RIGHT)

    video._handle_frame_events()

    # The clip is shorter than one seek step, so it lands at the end.
    assert video.time == pytest.approx(video.length, abs=0.01)


def test_keyboard_is_ignored_when_not_hovering(video_file, fake_clock):
    import pygame

    video = make_video(video_file, fake_clock, width=320, height=240)
    mouse.x, mouse.y = 5000, 5000
    keyboard_state.pressed_this_frame.add(pygame.K_SPACE)

    video._handle_frame_events()

    assert video.playing is False


def test_controls_can_be_switched_off(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240, controls=False)
    video._player.controls_alpha = 255
    fake_clock.advance(1.0)
    video._tick()

    point_on(video, 10, video.height - 10)
    mouse._is_clicked = True
    mouse_state.click_happened = True

    assert video._handle_frame_events() is False
    assert video.playing is False


def test_shortcuts_are_off_when_controls_are_off(video_file, fake_clock):
    import pygame

    video = make_video(video_file, fake_clock, width=320, height=240, controls=False)
    point_on(video, 160, 60)
    keyboard_state.pressed_this_frame.add(pygame.K_SPACE)

    video._handle_frame_events()

    # controls=False means the game owns the keyboard; hovering the video must
    # not make Space pause it.
    assert video.playing is False


def test_a_widget_on_top_takes_the_click_away_from_the_video(video_file, fake_clock):
    video = make_video(video_file, fake_clock, width=320, height=240)
    video._player.controls_alpha = 255

    point_on(video, 160, 60)  # on the picture, above the control bar
    mouse._is_clicked = True
    mouse_state.click_happened = True
    # A widget (say a button drawn over the video) owns this click.
    mouse_state.click_owner = object()

    assert video._handle_frame_events() is False
    assert video.playing is False

    # The same click with no owner does reach the video.
    mouse_state.click_owner = None
    assert video._handle_frame_events() is False
    assert video.playing is True


##### the game loop #####


def test_the_game_loop_ticks_the_video(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    wait_for_frames(video, 4)
    fake_clock.advance(0.5)

    run_frame()

    assert video.time == pytest.approx(0.5, abs=0.01)
    assert video._player.current_time > 0.0


def test_a_hidden_video_is_still_ticked(video_file, fake_clock):
    video = make_video(video_file, fake_clock)
    video.play()
    video.hide()
    fake_clock.advance(0.5)

    run_frame()

    assert video.playing is True
    assert video.time == pytest.approx(0.5, abs=0.01)
