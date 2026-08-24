"""Tests for the pure decoding layer, which needs no display or mixer."""

import time

import pytest

from play.objects import video_decoder


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _collect(decoder, count, timeout=5.0):
    """Pull ``count`` frames off a decoder's queue."""
    frames = []
    deadline = time.monotonic() + timeout
    while len(frames) < count and time.monotonic() < deadline:
        try:
            frames.append(decoder.queue.get(timeout=0.2))
        except Exception:  # pylint: disable=broad-except
            continue
    return frames


def test_probe_reads_video_details(video_file):
    info = video_decoder.probe(video_file)

    assert info.width == 64
    assert info.height == 48
    assert info.frame_rate == pytest.approx(10.0)
    assert info.duration == pytest.approx(2.0, abs=0.1)
    assert info.has_audio is True


def test_probe_reports_missing_audio(silent_video_file):
    assert video_decoder.probe(silent_video_file).has_audio is False


def test_probe_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        video_decoder.probe("definitely_not_here.mp4")


def test_decode_audio_matches_duration(video_file):
    pcm = video_decoder.decode_audio(video_file, (44100, -16, 2))

    # 2 bytes per sample, 2 channels.
    seconds = len(pcm) / 2 / 2 / 44100
    assert seconds == pytest.approx(2.0, abs=0.15)


def test_decode_audio_without_audio_track(silent_video_file):
    assert video_decoder.decode_audio(silent_video_file, (44100, -16, 2)) is None


def test_decode_audio_without_mixer(video_file):
    assert video_decoder.decode_audio(video_file, None) is None


def test_frames_arrive_in_order(video_file):
    decoder = video_decoder.FrameDecoder(video_file)
    decoder.start()
    try:
        frames = _collect(decoder, 4)
        assert len(frames) == 4
        timestamps = [frame[1] for frame in frames]
        assert timestamps == sorted(timestamps)
        assert timestamps[0] == pytest.approx(0.0, abs=0.01)
        # 64 x 48 pixels, 3 bytes each.
        assert len(frames[0][2]) == 64 * 48 * 3
    finally:
        decoder.stop()


def test_seek_skips_to_requested_point(video_file):
    decoder = video_decoder.FrameDecoder(video_file)
    decoder.start()
    try:
        _collect(decoder, 2)
        decoder.request_seek(1.5)
        frames = _collect(decoder, 1)

        assert frames, "expected a frame after seeking"
        generation, timestamp, _payload = frames[0]
        assert timestamp >= 1.5 - 0.01
        # The generation counter marks frames decoded before the seek as stale.
        assert generation == decoder.generation
    finally:
        decoder.stop()


def test_stop_ends_the_thread(video_file):
    decoder = video_decoder.FrameDecoder(video_file)
    decoder.start()
    _collect(decoder, 1)
    decoder.stop()

    assert decoder.is_alive() is False


##### probing edge cases #####


def test_probe_rejects_a_file_without_video(tmp_path):
    import av
    import numpy as np

    path = str(tmp_path / "audio_only.m4a")
    container = av.open(path, mode="w")
    stream = container.add_stream("aac", rate=44100)
    stream.layout = "stereo"
    tone = (np.zeros((2, 1024))).astype("int16")
    frame = av.AudioFrame.from_ndarray(
        np.ascontiguousarray(tone), format="s16p", layout="stereo"
    )
    frame.sample_rate = 44100
    for packet in stream.encode(frame):
        container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()

    with pytest.raises(ValueError, match="does not contain any video"):
        video_decoder.probe(path)


def test_stream_duration_falls_back_to_the_container():
    class FakeStream:
        duration = None
        time_base = None

    class FakeContainer:
        duration = 3_000_000  # microseconds

    assert video_decoder._stream_duration(FakeStream(), FakeContainer()) == 3.0

    class EmptyContainer:
        duration = None

    assert video_decoder._stream_duration(FakeStream(), EmptyContainer()) == 0.0


def test_mixer_formats_cover_the_sample_sizes():
    # (rate, size, channels) as pygame.mixer.get_init() reports them; a
    # negative size means signed samples.
    assert video_decoder._mixer_formats((44100, -16, 2)) == ("s16", "stereo", 44100, 2)
    assert video_decoder._mixer_formats((44100, 8, 2))[0] == "u8"
    assert video_decoder._mixer_formats((44100, -32, 2))[0] == "s32"
    assert video_decoder._mixer_formats((22050, -16, 1))[1] == "mono"


def test_seek_after_the_end_resumes_decoding(video_file):
    # After the clip fully decodes the thread idles on eof; a seek must wake
    # it up again. Looping a video depends on exactly this.
    decoder = video_decoder.FrameDecoder(video_file)
    decoder.start()
    try:
        deadline = time.monotonic() + 10.0
        while not decoder.eof.is_set() and time.monotonic() < deadline:
            decoder._drain()  # let the producer reach the end of the file
            time.sleep(0.01)
        assert decoder.eof.is_set(), "the clip should have decoded to its end"

        decoder.request_seek(0.5)
        frames = _collect(decoder, 1)

        assert frames, "a seek after eof should produce frames again"
        _generation, timestamp, _payload = frames[0]
        assert timestamp >= 0.4
    finally:
        decoder.stop()
