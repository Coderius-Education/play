"""Video/audio decoding for the Video object.

This module deliberately knows nothing about pygame or about sprites: it turns a
media file into raw RGB frames and raw PCM audio.  Keeping it separate makes the
decoding logic straightforward to test on its own, and keeps the threading
concerns out of the drawing code.

PyAV (``av``) is used for decoding.  Its wheels bundle FFmpeg, so no system-wide
FFmpeg install is required.
"""

import os
import queue
import threading

from ..io.logging import play_logger as logger

_AV_IMPORT_ERROR = (
    "Playing videos needs the 'av' package, which should have been installed "
    "along with play. Install it with:\n\n    pip install av\n"
)


def _import_av():
    """Import PyAV, or raise a message a student can act on."""
    try:
        import av  # pylint: disable=import-outside-toplevel

        return av
    except ImportError as error:  # pragma: no cover - depends on the install
        raise ImportError(_AV_IMPORT_ERROR) from error


class VideoInfo:  # pylint: disable=too-few-public-methods
    """Everything we need to know about a video file before playing it."""

    def __init__(self, width, height, duration, frame_rate, has_audio):
        self.width = width
        self.height = height
        self.duration = duration
        self.frame_rate = frame_rate
        self.has_audio = has_audio


def probe(file_name):
    """Read the size, duration and frame rate of a video file.

    :param file_name: Path to the video file.
    :return: A :class:`VideoInfo`.
    """
    if not os.path.isfile(file_name):
        raise FileNotFoundError(f"Video file '{file_name}' not found.")

    av = _import_av()
    with av.open(file_name) as container:
        if not container.streams.video:
            raise ValueError(
                f"The file '{file_name}' does not contain any video. "
                "If it is a sound file, use play.new_sound() instead."
            )
        stream = container.streams.video[0]
        duration = _stream_duration(stream, container)
        frame_rate = float(stream.average_rate) if stream.average_rate else 30.0
        return VideoInfo(
            width=stream.codec_context.width,
            height=stream.codec_context.height,
            duration=duration,
            frame_rate=frame_rate,
            has_audio=bool(container.streams.audio),
        )


def _stream_duration(stream, container):
    """Best-effort duration in seconds for a stream."""
    if stream.duration is not None and stream.time_base:
        return float(stream.duration * stream.time_base)
    if container.duration is not None:
        return container.duration / 1000000.0
    return 0.0


def _mixer_formats(mixer_init):
    """Translate pygame's mixer settings into PyAV resampler settings.

    :param mixer_init: The tuple returned by ``pygame.mixer.get_init()``.
    :return: ``(format_name, layout_name, rate, channels)``.
    """
    rate, size, channels = mixer_init[0], mixer_init[1], mixer_init[2]
    # pygame reports the sample size as a signed/unsigned bit count.
    if abs(size) == 8:
        sample_format = "u8" if size > 0 else "s16"
    elif abs(size) == 32:
        sample_format = "s32"
    else:
        sample_format = "s16"
    layout = "stereo" if channels >= 2 else "mono"
    return sample_format, layout, rate, channels


def decode_audio(file_name, mixer_init):
    """Decode a file's whole audio track into one interleaved PCM buffer.

    The buffer is resampled to whatever the pygame mixer is actually running at,
    so it can be handed straight to ``pygame.mixer.Sound(buffer=...)``.

    :param file_name: Path to the video file.
    :param mixer_init: The tuple from ``pygame.mixer.get_init()``, or None.
    :return: ``bytes`` of interleaved PCM, or None when there is no audio.
    """
    if not mixer_init:
        return None

    av = _import_av()
    sample_format, layout, rate, _channels = _mixer_formats(mixer_init)

    with av.open(file_name) as container:
        if not container.streams.audio:
            return None
        stream = container.streams.audio[0]
        resampler = av.audio.resampler.AudioResampler(
            format=sample_format, layout=layout, rate=rate
        )
        chunks = []
        for frame in container.decode(stream):
            for resampled in resampler.resample(frame):
                chunks.append(resampled.to_ndarray().tobytes())
        # Flushing matters: without it the tail of the track is silently lost.
        for resampled in resampler.resample(None):
            chunks.append(resampled.to_ndarray().tobytes())

    return b"".join(chunks)


class FrameDecoder:
    """Decodes video frames on a background thread into a bounded queue.

    Frames are handed over as ``(timestamp_seconds, rgb_bytes)`` so that the
    expensive colour conversion happens off the main thread while the cheap
    surface creation stays on it (pygame surfaces should not be built from a
    worker thread).
    """

    def __init__(self, file_name, max_queued=5):
        self._av = _import_av()
        self.file_name = file_name
        self.queue = queue.Queue(maxsize=max_queued)
        self.eof = threading.Event()

        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._seek_to = None
        self._generation = 0
        self._thread = None

    @property
    def generation(self):
        """The current seek generation; frames from older generations are stale."""
        with self._lock:
            return self._generation

    def start(self):
        """Start the decoding thread."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name=f"play-video-{os.path.basename(self.file_name)}"
        )
        self._thread.daemon = True
        self._thread.start()

    def request_seek(self, seconds):
        """Ask the decoder to jump to a point in the file.

        Bumps the generation counter so already-queued frames can be discarded.
        """
        with self._lock:
            self._seek_to = max(0.0, seconds)
            self._generation += 1
        self._drain()

    def stop(self, timeout=1.0):
        """Stop the decoding thread and wait briefly for it to finish."""
        self._stop.set()
        self._drain()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._thread = None

    def is_alive(self):
        """Whether the decoding thread is still running."""
        return self._thread is not None and self._thread.is_alive()

    def _drain(self):
        """Empty the queue so a blocked producer can make progress."""
        while True:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                return

    def _take_seek_request(self):
        with self._lock:
            seek_to, self._seek_to = self._seek_to, None
            return seek_to, self._generation

    def _run(self):  # pylint: disable=too-many-branches
        """Decode frames until stopped, honouring seek requests as they arrive."""
        try:
            container = self._av.open(self.file_name)
        except Exception:  # pylint: disable=broad-except  # pragma: no cover
            logger.error("Could not open video file for decoding", exc_info=True)
            self.eof.set()
            return

        try:
            stream = container.streams.video[0]
            stream.thread_type = "AUTO"
            generation = self.generation
            frames = container.decode(stream)

            while not self._stop.is_set():
                seek_to, generation = self._take_seek_request()
                if seek_to is not None:
                    frames = self._seek(container, stream, seek_to)
                    self.eof.clear()

                try:
                    frame = next(frames)
                except StopIteration:
                    self.eof.set()
                    # Idle until a seek arrives or we are told to stop.
                    if self._wait_for_work():
                        continue
                    return
                except Exception:  # pylint: disable=broad-except  # pragma: no cover
                    logger.error("Error while decoding video", exc_info=True)
                    self.eof.set()
                    return

                timestamp = float(frame.time) if frame.time is not None else 0.0
                payload = frame.to_ndarray(format="rgb24").tobytes()
                self._put(timestamp, payload, generation)
        finally:
            container.close()

    def _seek(self, container, stream, seconds):
        """Seek and return a fresh frame generator positioned at ``seconds``.

        ``container.seek`` lands on the closest preceding keyframe, so frames
        before the requested point are decoded and thrown away.
        """
        offset = int(seconds / stream.time_base)
        container.seek(offset, stream=stream, backward=True, any_frame=False)
        stream.codec_context.flush_buffers()
        frames = container.decode(stream)
        return self._skip_until(frames, seconds)

    @staticmethod
    def _skip_until(frames, seconds):
        """Yield frames from ``seconds`` onwards, discarding earlier ones."""
        for frame in frames:
            if frame.time is None or frame.time >= seconds - 1e-4:
                yield frame
                break
        yield from frames

    def _wait_for_work(self):
        """Block until a seek is requested or we are stopped.

        :return: True if there is a seek to handle, False if we should exit.
        """
        while not self._stop.is_set():
            with self._lock:
                if self._seek_to is not None:
                    return True
            if self._stop.wait(0.02):
                break
        return False

    def _put(self, timestamp, payload, generation):
        """Put a frame on the queue, giving up if a seek or stop intervenes."""
        while not self._stop.is_set():
            with self._lock:
                if generation != self._generation:
                    return  # Stale: a seek happened while we were decoding.
            try:
                self.queue.put((generation, timestamp, payload), timeout=0.05)
                return
            except queue.Full:
                continue
