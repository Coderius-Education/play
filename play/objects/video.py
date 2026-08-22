"""This module contains the Video class, which plays a video file on screen."""

import math as _math
import time as _time
import weakref

import numpy as np
import pygame

from .sprite import Sprite
from . import video_controls
from .video_decoder import FrameDecoder, decode_audio, probe
from ..callback import callback_manager, CallbackType
from ..callback.callback_helpers import run_async_callback
from ..io.logging import play_logger as logger
from ..io.mouse import mouse
from ..io.screen import convert_pos
from ..utils import experimental
from ..utils.async_helpers import make_async

# Videos hold a decoding thread and an open file, so they need closing even when
# the user never calls remove(). This lets the program shutdown clean them up.
_live_videos = weakref.WeakSet()

# Warn above this many seconds: the whole audio track is held in memory.
_LONG_VIDEO_SECONDS = 300

_CONTROLS_FADE_SECONDS = 0.25
_CONTROLS_HIDE_AFTER = 2.0
_SEEK_STEP = 5.0

# Interactive scrubbing seeks every dragged frame. _latch_frame's normal
# wait=True budget (0.5s) would stall the whole game loop for that long on
# every one of those frames, so scrubbing uses a much shorter budget instead.
_SCRUB_WAIT_SECONDS = 0.05

# CallbackType members that are keyed by id(video) and must be cleared when a
# video is closed, or callback_manager keeps the Video (and its buffers) alive.
_VIDEO_CALLBACK_TYPES = (
    CallbackType.WHEN_VIDEO_ENDS,
    CallbackType.WHEN_VIDEO_STARTS,
    CallbackType.WHEN_VIDEO_PLAYS,
    CallbackType.WHEN_VIDEO_PAUSES,
    CallbackType.WHEN_VIDEO_FRAME,
)


def close_all_videos():
    """Stop and close every video that is still alive."""
    for video in list(_live_videos):
        try:
            video.close()
        except Exception:  # pylint: disable=broad-except  # pragma: no cover
            logger.error("Error while closing a video", exc_info=True)


class _VideoPlayer:  # pylint: disable=too-few-public-methods
    """Holds all the state that changes while a video plays.

    This lives on a plain object rather than on the Video sprite itself on
    purpose. ``Sprite.__setattr__`` compares every assignment against the old
    value to decide whether a redraw is needed, which raises for numpy arrays and
    is needlessly expensive for large buffers written every frame.
    """

    def __init__(self, time_fn):
        self.time_fn = time_fn
        self.decoder = None
        self.pcm = None
        self.sound = None
        self.channel = None
        self.canvas = None
        self.controls_surface = None
        self.controls_key = None
        self.font = None

        self.state = "idle"  # idle | playing | paused | ended
        self.base = 0.0  # playback position when the clock last started
        self.started_at = 0.0
        self.speed = 1.0
        self.volume = 1.0
        self.muted = False
        self.loop = False
        self.started_once = False

        self.pending = None  # a decoded frame that is not due yet
        self.current_time = 0.0
        self.frame_index = -1

        self.hover = False
        self.controls_alpha = 0.0
        self.last_activity = 0.0
        self.scrubbing = False
        self.dragging_volume = False
        self.consumed_click = False


@experimental
class Video(Sprite):  # pylint: disable=too-many-public-methods
    """A video that plays on screen, with optional built-in controls."""

    def __init__(
        self,
        file_name,
        x=0,
        y=0,
        width=None,
        height=None,
        size=100,
        angle=0,
        transparency=100,
        volume=1.0,
        speed=1.0,
        loop=False,
        autoplay=False,
        controls=True,
        muted=False,
        _time_fn=_time.monotonic,
    ):  # pylint: disable=too-many-locals
        """Play a video file.

        :param file_name: The video file to play (for example 'clip.mp4').
        :param x: The x-coordinate of the video.
        :param y: The y-coordinate of the video.
        :param width: Width on screen. Defaults to the video's own width.
        :param height: Height on screen. Defaults to the video's own height.
        :param size: Size as a percentage.
        :param angle: The angle of the video.
        :param transparency: The transparency of the video (0-100).
        :param volume: The volume of the video's sound (0.0 to 1.0).
        :param speed: Playback speed. Note this also changes the pitch.
        :param loop: Whether to start again when the video ends.
        :param autoplay: Whether to start playing immediately.
        :param controls: Whether to show the built-in control bar on hover.
        :param muted: Whether to start muted.
        """
        info = probe(file_name)

        self._file_name = file_name
        self._info = info
        self._width, self._height = self._fit_size(info, width, height)
        self._x = x
        self._y = y
        self._size = size
        self._angle = angle
        self._transparency = transparency
        self._controls = controls
        self.rect = pygame.Rect(0, 0, self._width, self._height)

        player = _VideoPlayer(_time_fn)
        player.volume = min(max(volume, 0.0), 1.0)
        player.muted = muted
        player.loop = loop
        if speed <= 0:
            logger.warning("Video speed must be greater than 0.")
            speed = 1.0
        player.speed = speed
        player.last_activity = _time_fn()
        self._player = player

        super().__init__()

        if info.duration > _LONG_VIDEO_SECONDS:
            logger.warning(
                "'%s' is %d minutes long. Its sound is kept in memory, which "
                "may use a lot of RAM.",
                file_name,
                int(info.duration // 60),
            )

        player.canvas = pygame.Surface((info.width, info.height))
        player.pcm = decode_audio(file_name, pygame.mixer.get_init())
        player.decoder = FrameDecoder(file_name)
        player.decoder.start()

        _live_videos.add(self)

        self._latch_frame(0.0, wait=True)
        self.update()

        if autoplay:
            self.play()

    @staticmethod
    def _fit_size(info, width, height):
        """Work out the on-screen size, keeping the aspect ratio when possible."""
        native_w = max(info.width, 1)
        native_h = max(info.height, 1)
        if width is None and height is None:
            return native_w, native_h
        if width is None:
            return max(round(height * native_w / native_h), 1), max(round(height), 1)
        if height is None:
            return max(round(width), 1), max(round(width * native_h / native_w), 1)
        return max(round(width), 1), max(round(height), 1)

    ##### playback #####

    @property
    def length(self):
        """How long the video is, in seconds."""
        return self._info.duration

    @property
    def frame_rate(self):
        """How many frames per second the video was recorded at."""
        return self._info.frame_rate

    @property
    def time(self):
        """The current position in the video, in seconds."""
        return self._clock()

    @time.setter
    def time(self, seconds):
        """Jump to a position in the video."""
        self.seek(seconds)

    def _clock(self):
        """The master clock: where playback has got to, in seconds."""
        player = self._player
        if player.state != "playing":
            return player.base
        elapsed = (player.time_fn() - player.started_at) * player.speed
        return min(player.base + elapsed, self.length)

    def play(self):
        """Start playing, or carry on after a pause."""
        player = self._player
        if player.state == "playing":
            return
        if player.state == "ended":
            player.base = 0.0
            player.decoder.request_seek(0.0)
            player.pending = None

        player.started_at = player.time_fn()
        player.state = "playing"
        self._start_audio(player.base)

        if not player.started_once:
            player.started_once = True
            self._fire(CallbackType.WHEN_VIDEO_STARTS)
        self._fire(CallbackType.WHEN_VIDEO_PLAYS)
        self._should_recompute = True

    def pause(self):
        """Pause the video where it is."""
        player = self._player
        if player.state != "playing":
            return
        player.base = self._clock()
        player.state = "paused"
        self._stop_audio()
        self._fire(CallbackType.WHEN_VIDEO_PAUSES)
        self._should_recompute = True

    def toggle_play(self):
        """Pause if playing, play if not."""
        if self._player.state == "playing":
            self.pause()
        else:
            self.play()

    def stop(self):
        """Stop the video and go back to the beginning."""
        self._stop_audio()
        player = self._player
        was_playing = player.state == "playing"
        player.state = "idle"
        player.base = 0.0
        player.pending = None
        player.decoder.request_seek(0.0)
        if was_playing:
            self._fire(CallbackType.WHEN_VIDEO_PAUSES)
        self._latch_frame(0.0, wait=True)
        self._should_recompute = True

    def restart(self):
        """Go back to the beginning and play from there."""
        self.seek(0.0)
        self._player.state = "paused"
        self.play()

    def seek(self, seconds):
        """Jump to a point in the video.

        :param seconds: Where to jump to, in seconds from the start.
        """
        self._seek_to(seconds)

    def _seek_to(self, seconds, wait_seconds=0.5):
        """Do the actual seek, with a configurable wait budget for a fresh frame.

        :param wait_seconds: How long to block for a freshly-decoded frame when
            paused. Interactive scrubbing passes a much shorter budget than the
            default, since it seeks on every dragged frame and a long wait here
            would stall the whole game loop.
        """
        player = self._player
        target = min(max(float(seconds), 0.0), self.length)
        was_playing = player.state == "playing"

        self._stop_audio()
        player.base = target
        player.pending = None
        player.started_at = player.time_fn()
        player.decoder.request_seek(target)
        if player.state == "ended" and target < self.length:
            player.state = "paused"

        if was_playing:
            self._start_audio(target)
        else:
            self._latch_frame(target, wait=True, wait_seconds=wait_seconds)
        self._should_recompute = True

    @property
    def playing(self):
        """Whether the video is playing right now."""
        return self._player.state == "playing"

    @property
    def paused(self):
        """Whether the video is paused."""
        return self._player.state == "paused"

    @property
    def finished(self):
        """Whether the video has reached the end."""
        return self._player.state == "ended"

    @property
    def loop(self):
        """Whether the video starts again when it ends."""
        return self._player.loop

    @loop.setter
    def loop(self, value):
        self._player.loop = bool(value)

    @property
    def speed(self):
        """How fast the video plays. 2 is twice as fast.

        Changing the speed also changes the pitch of the sound, the way
        speeding up a tape does.
        """
        return self._player.speed

    @speed.setter
    def speed(self, value):
        if value <= 0:
            logger.warning("Video speed must be greater than 0.")
            return
        player = self._player
        now = self._clock()
        player.speed = float(value)
        player.base = now
        player.started_at = player.time_fn()
        if player.state == "playing":
            self._start_audio(now)

    ##### sound #####

    @property
    def volume(self):
        """How loud the video's sound is (0.0 to 1.0)."""
        return self._player.volume

    @volume.setter
    def volume(self, value):
        if not 0.0 <= value <= 1.0:
            logger.warning("Volume must be between 0.0 and 1.0")
        self._player.volume = min(max(float(value), 0.0), 1.0)
        self._apply_volume()
        self._should_recompute = True

    @property
    def muted(self):
        """Whether the video's sound is turned off."""
        return self._player.muted

    @muted.setter
    def muted(self, value):
        self._player.muted = bool(value)
        self._apply_volume()
        self._should_recompute = True

    def _apply_volume(self):
        player = self._player
        if player.sound is not None:
            player.sound.set_volume(0.0 if player.muted else player.volume)

    def _pcm_slice(self, offset_seconds):
        """The remaining audio from ``offset_seconds``, at the current speed."""
        player = self._player
        mixer_init = pygame.mixer.get_init()
        if not player.pcm or not mixer_init:
            return None

        rate, _size, channels = mixer_init[0], mixer_init[1], mixer_init[2]
        samples = np.frombuffer(player.pcm, dtype=np.int16)
        start = int(offset_seconds * rate) * channels
        start = min(max(start, 0), len(samples))
        tail = samples[start:]
        if tail.size == 0:
            return None

        if player.speed != 1.0:
            # Resample by walking the samples faster or slower. This shifts the
            # pitch, which is the expected "tape speed" behaviour.
            frames = tail.reshape(-1, channels)
            count = max(int(frames.shape[0] / player.speed), 1)
            index = np.minimum(
                (np.arange(count) * player.speed).astype(np.int64),
                frames.shape[0] - 1,
            )
            tail = frames[index].reshape(-1)

        return np.ascontiguousarray(tail).tobytes()

    def _start_audio(self, offset_seconds):
        """Start the sound from a position in the track."""
        self._stop_audio()
        buffer = self._pcm_slice(offset_seconds)
        if buffer is None:
            return

        player = self._player
        player.sound = pygame.mixer.Sound(buffer=buffer)
        self._apply_volume()
        channel = pygame.mixer.find_channel()
        if channel is None:
            logger.warning("No free sound channels, so this video plays without sound.")
            return
        player.channel = channel
        channel.play(player.sound)

    def _stop_audio(self):
        player = self._player
        channel = player.channel
        # pygame reuses channels, so make sure it is still ours before stopping.
        if channel is not None and channel.get_sound() is player.sound:
            channel.stop()
        player.channel = None
        player.sound = None

    ##### per-frame work #####

    def _tick(self):
        """Advance playback. Called once per frame by the game loop."""
        player = self._player
        now = player.time_fn()
        current = self._clock()

        if self._latch_frame(current):
            self._fire(CallbackType.WHEN_VIDEO_FRAME)

        if player.state == "playing" and current >= self.length - 1e-6:
            self._reach_end()

        self._tick_controls(now)

    def _reach_end(self):
        """Handle the video reaching its end."""
        player = self._player
        self._stop_audio()
        player.base = self.length
        player.state = "ended"
        self._fire(CallbackType.WHEN_VIDEO_ENDS)
        self._should_recompute = True
        if player.loop:
            self.seek(0.0)
            player.state = "paused"
            self.play()

    def _latch_frame(self, current, wait=False, wait_seconds=0.5):
        """Show the newest decoded frame that is due at ``current`` seconds.

        :param current: The playback position, in seconds.
        :param wait: Block briefly for a frame (used when seeking or starting).
        :param wait_seconds: How long ``wait`` is allowed to block for.
        :return: True if the displayed frame changed.
        """
        player = self._player
        decoder = player.decoder
        if decoder is None:
            return False

        deadline = _time.monotonic() + wait_seconds if wait else 0.0
        changed = False

        while True:
            if player.pending is None:
                item = self._next_decoded(decoder, deadline)
                if item is None:
                    break
                player.pending = item

            timestamp, payload = player.pending
            if timestamp <= current + 1e-6 or (wait and not changed):
                player.pending = None
                player.canvas.blit(
                    pygame.image.frombuffer(
                        payload, (self._info.width, self._info.height), "RGB"
                    ),
                    (0, 0),
                )
                player.current_time = timestamp
                player.frame_index += 1
                changed = True
                if wait:
                    break
            else:
                break

        if changed:
            self._should_recompute = True
        return changed

    def _next_decoded(self, decoder, deadline):
        """Take the next non-stale frame off the decoder queue."""
        while True:
            try:
                generation, timestamp, payload = decoder.queue.get_nowait()
            except Exception:  # pylint: disable=broad-except
                if deadline and _time.monotonic() < deadline:
                    _time.sleep(0.002)
                    continue
                return None
            if generation != decoder.generation:
                continue  # A seek happened after this frame was decoded.
            return timestamp, payload

    ##### controls #####

    @property
    def controls(self):
        """Whether the built-in control bar is shown."""
        return self._controls

    @controls.setter
    def controls(self, value):
        self._controls = bool(value)
        self._should_recompute = True

    def _bar_height(self):
        return max(14, min(44, int(self._height * 0.22)))

    def _tick_controls(self, now):
        """Fade the control bar in while hovered and out again afterwards."""
        player = self._player
        if not self._controls:
            if player.controls_alpha:
                player.controls_alpha = 0.0
                self._should_recompute = True
            return

        visible = player.hover or player.scrubbing or player.dragging_volume
        if not visible and now - player.last_activity < _CONTROLS_HIDE_AFTER:
            visible = True

        target = 255.0 if visible else 0.0
        if player.controls_alpha == target:
            return

        step = 255.0 / max(_CONTROLS_FADE_SECONDS * 60.0, 1.0)
        if player.controls_alpha < target:
            player.controls_alpha = min(target, player.controls_alpha + step)
        else:
            player.controls_alpha = max(target, player.controls_alpha - step)
        self._should_recompute = True

    def _local_point(self):
        """Where the mouse is inside the video, in unrotated video pixels.

        :return: An ``(x, y)`` pixel position, which may be outside the video.
        """
        dx = mouse.x - self.x
        dy = mouse.y - self.y
        radians = _math.radians(-self.angle)
        cos_a, sin_a = _math.cos(radians), _math.sin(radians)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        factor = (self._size or 100) / 100
        if factor == 0:
            return -1, -1
        return rx / factor + self._width / 2, self._height / 2 - ry / factor

    def _is_inside(self, point):
        px, py = point
        return 0 <= px < self._width and 0 <= py < self._height

    def _scrub_area(self):
        """The rectangle of the seek bar, in local pixels."""
        bar_h = self._bar_height()
        left = bar_h
        right = max(left + 10, self._width - self._volume_width() - 4)
        return pygame.Rect(left, self._height - bar_h, right - left, bar_h)

    def _volume_width(self):
        return 0 if self._width < 170 else 74

    def _volume_area(self):
        bar_h = self._bar_height()
        width = self._volume_width()
        return pygame.Rect(
            self._width - width + 22, self._height - bar_h, max(width - 26, 1), bar_h
        )

    def _button_area(self):
        bar_h = self._bar_height()
        return pygame.Rect(0, self._height - bar_h, bar_h, bar_h)

    def _mute_area(self):
        bar_h = self._bar_height()
        width = self._volume_width()
        if not width:
            return pygame.Rect(-1, -1, 0, 0)
        return pygame.Rect(self._width - width, self._height - bar_h, 22, bar_h)

    def _handle_frame_events(self):  # pylint: disable=too-many-return-statements
        """Handle mouse and keyboard input. Called once per frame.

        :return: True when the control bar used the click, so that the user's
            own when_clicked does not also fire.
        """
        # Imported here to avoid a circular import at module load.
        # pylint: disable=import-outside-toplevel
        from ..core.mouse_loop import mouse_state
        from ..io.keypress import keyboard_state

        player = self._player
        point = self._local_point()
        inside = self._is_inside(point)

        if inside != player.hover:
            player.hover = inside
            self._should_recompute = True
        if inside:
            player.last_activity = player.time_fn()

        if inside:
            self._handle_shortcuts(keyboard_state)

        if self._handle_drags(point, mouse_state):
            return True

        if not self._controls or player.controls_alpha <= 0 or not inside:
            return False

        if mouse_state.click_happened and self._start_drag(point):
            return True

        # A click on the picture itself toggles play, and still counts as a
        # click on the video for the user's own when_clicked.
        if mouse_state.click_happened and point[1] < self._height - self._bar_height():
            self.toggle_play()
        return False

    def _handle_shortcuts(self, keyboard_state):
        """Space plays/pauses, arrows seek, M mutes."""
        pressed = keyboard_state.pressed_this_frame
        if not pressed:
            return
        if pygame.K_SPACE in pressed:
            self.toggle_play()
        if pygame.K_RIGHT in pressed:
            self.seek(self.time + _SEEK_STEP)
        if pygame.K_LEFT in pressed:
            self.seek(self.time - _SEEK_STEP)
        if pygame.K_m in pressed:
            self.muted = not self.muted

    def _start_drag(self, point):
        """Begin a click on the control bar. Returns True if it was used."""
        player = self._player
        if self._button_area().collidepoint(point):
            self.toggle_play()
            return True
        if self._mute_area().collidepoint(point):
            self.muted = not self.muted
            return True
        if self._scrub_area().collidepoint(point):
            player.scrubbing = True
            self._scrub_to(point)
            return True
        if self._volume_width() and self._volume_area().collidepoint(point):
            player.dragging_volume = True
            self._volume_to(point)
            return True
        return False

    def _handle_drags(self, point, mouse_state):
        """Keep following the mouse while dragging the seek or volume bar."""
        player = self._player
        if not (player.scrubbing or player.dragging_volume):
            return False

        if player.scrubbing:
            self._scrub_to(point)
        else:
            self._volume_to(point)

        if mouse_state.click_release_happened or not mouse.is_clicked:
            player.scrubbing = False
            player.dragging_volume = False
        player.last_activity = player.time_fn()
        return True

    def _scrub_to(self, point):
        area = self._scrub_area()
        fraction = (point[0] - area.left) / max(area.width, 1)
        target = min(max(fraction, 0.0), 1.0) * self.length
        self._seek_to(target, wait_seconds=_SCRUB_WAIT_SECONDS)

    def _volume_to(self, point):
        area = self._volume_area()
        fraction = (point[0] - area.left) / max(area.width, 1)
        self.volume = min(max(fraction, 0.0), 1.0)

    ##### drawing #####

    def _render_controls(self):
        """Draw the control bar onto its own see-through surface."""
        return video_controls.render(self)

    def update(self):
        """Draw the current video frame, with the control bar on top."""
        if not self._should_recompute:
            super().update()
            return
        if self._is_hidden:
            super().update()
            return

        player = self._player
        draw_image = player.canvas
        resized = (self._width, self._height) != (self._info.width, self._info.height)
        if resized:
            draw_image = pygame.transform.smoothscale(
                draw_image, (self._width, self._height)
            )

        if self._controls and player.controls_alpha > 0:
            # The control bar is drawn at the size the video is shown at, and on
            # a copy so it isn't burnt into the frame itself.
            if not resized:
                draw_image = draw_image.copy()
            draw_image.blit(
                self._render_controls(), (0, self._height - self._bar_height())
            )

        if self._size != 100:
            new_w = max(round(self._width * self._size / 100), 1)
            new_h = max(round(self._height * self._size / 100), 1)
            draw_image = pygame.transform.scale(draw_image, (new_w, new_h))

        draw_image.set_alpha(round(self._transparency * 255 / 100))

        self.rect = draw_image.get_rect()
        pos = convert_pos(self.x, self.y)
        self.rect.x = pos[0] - self.rect.width // 2
        self.rect.y = pos[1] - self.rect.height // 2

        angle_deg = _math.degrees(self.physics._pymunk_body.angle)
        self.image = (
            pygame.transform.rotate(draw_image, angle_deg) if angle_deg else draw_image
        )
        self.rect = self.image.get_rect(center=self.rect.center)
        super().update()

    ##### size #####

    @property
    def width(self):
        """The width of the video on screen."""
        return self._width

    @width.setter
    def width(self, value):
        self._width = max(round(value), 1)
        self._player.controls_key = None
        self._should_recompute = True
        self.physics._remove()
        self.physics._make_pymunk()

    @property
    def height(self):
        """The height of the video on screen."""
        return self._height

    @height.setter
    def height(self, value):
        self._height = max(round(value), 1)
        self._player.controls_key = None
        self._should_recompute = True
        self.physics._remove()
        self.physics._make_pymunk()

    @property
    def file_name(self):
        """The video file being played."""
        return self._file_name

    ##### events #####

    def _fire(self, callback_type):
        callback_manager.run_callbacks(callback_type, callback_discriminator=id(self))

    def _register(self, callback_type, callback, arg_names=(), value_fn=None):
        """Register a user callback for one of the video events.

        The callback manager calls wrappers without arguments, so anything the
        user's function asks for is read from ``value_fn`` at the moment the
        event fires.
        """
        async_callback = make_async(callback)

        async def wrapper():
            wrapper.is_running = True
            try:
                values = (value_fn(),) if value_fn is not None else ()
                await run_async_callback(async_callback, [], list(arg_names), *values)
            finally:
                wrapper.is_running = False

        wrapper.is_running = False
        callback_manager.add_callback(callback_type, wrapper, id(self))
        return callback

    # @decorator
    def when_video_ends(self, func):
        """Run a function when the video reaches the end.

        Example:

            video = play.new_video('clip.mp4')

            @video.when_video_ends
            def done():
                print('finished!')
        """
        return self._register(CallbackType.WHEN_VIDEO_ENDS, func)

    # @decorator
    def when_video_starts(self, func):
        """Run a function the first time the video starts playing."""
        return self._register(CallbackType.WHEN_VIDEO_STARTS, func)

    # @decorator
    def when_video_plays(self, func):
        """Run a function every time the video starts or carries on playing."""
        return self._register(CallbackType.WHEN_VIDEO_PLAYS, func)

    # @decorator
    def when_video_pauses(self, func):
        """Run a function every time the video is paused."""
        return self._register(CallbackType.WHEN_VIDEO_PAUSES, func)

    # @decorator
    def when_video_frame_changes(self, func):
        """Run a function each time a new frame of the video is shown.

        The function may take a ``time`` parameter, which is how far into the
        video the new frame is, in seconds.
        """
        return self._register(
            CallbackType.WHEN_VIDEO_FRAME,
            func,
            ["time"],
            value_fn=lambda: self._player.current_time,
        )

    ##### housekeeping #####

    def close(self):
        """Stop playing and let go of the video file."""
        player = getattr(self, "_player", None)
        if player is None:
            return
        self._stop_audio()
        if player.decoder is not None:
            player.decoder.stop()
            player.decoder = None
        player.state = "idle"
        _live_videos.discard(self)
        # Otherwise callback_manager keeps this Video (and its decoded-frame
        # canvas and in-memory audio buffer) alive forever via the closures
        # registered in _register().
        for callback_type in _VIDEO_CALLBACK_TYPES:
            callback_manager.remove_callbacks(callback_type, id(self))

    def remove(self):
        """Remove the video from the screen and stop playing it."""
        self.close()
        super().remove()

    def clone(self):
        """Make a copy of this video."""
        return self.__class__(
            self._file_name,
            width=self._width,
            height=self._height,
            volume=self._player.volume,
            speed=self._player.speed,
            loop=self._player.loop,
            controls=self._controls,
            muted=self._player.muted,
            **self._common_properties(),
        )
