"""Tests for the Sound object."""

import math
import struct
import wave

import pytest

import play
from play.objects.sound import Sound


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


@pytest.fixture(scope="session")
def sound_file(tmp_path_factory):
    """A two-second 440 Hz tone as a WAV file, written with the stdlib."""
    path = tmp_path_factory.mktemp("sound") / "tone.wav"
    rate = 22050
    seconds = 2.0
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        frames = bytearray()
        for i in range(int(rate * seconds)):
            sample = int(8000 * math.sin(2 * math.pi * 440 * i / rate))
            frames += struct.pack("<h", sample)
        out.writeframes(bytes(frames))
    return str(path)


##### loading #####


def test_loads_and_knows_its_length(sound_file):
    sound = Sound(sound_file)

    assert sound.sound is not None
    # The length is known as soon as the file is loaded, before playing.
    assert sound.length == pytest.approx(2.0, abs=0.1)


def test_new_sound_is_exported(sound_file):
    sound = play.new_sound(sound_file)

    assert isinstance(sound, Sound)
    assert sound.length == pytest.approx(2.0, abs=0.1)


def test_plays_once_by_default(sound_file):
    # pygame's loops=N means N *extra* repetitions, so the old default of 1
    # made every sound play twice. It must match new_sound's default of 0.
    assert Sound(sound_file).loops == 0


def test_missing_file_is_logged_not_raised(sound_file):
    sound = Sound("no_such_sound.wav")

    assert sound.sound is None
    sound.play()  # warns instead of crashing
    assert sound.playing is False
    assert sound.length == 0.0


def test_corrupt_file_is_logged_not_raised(tmp_path):
    path = tmp_path / "junk.wav"
    path.write_bytes(b"this is not audio")

    sound = Sound(str(path))

    assert sound.sound is None
    sound.play()
    assert sound.playing is False


##### volume #####


def test_volume_roundtrip(sound_file):
    sound = Sound(sound_file, volume=0.8)
    assert sound.volume == pytest.approx(0.8, abs=0.02)

    sound.volume = 0.25
    assert sound.volume == pytest.approx(0.25, abs=0.02)


def test_volume_is_clamped(sound_file):
    sound = Sound(sound_file)

    sound.volume = 5
    assert sound.volume == 1.0

    sound.volume = -3
    assert sound.volume == 0.0


def test_volume_survives_a_failed_load():
    sound = Sound("no_such_sound.wav", volume=0.4)

    # With nothing loaded, the property reports the wanted volume.
    assert sound.volume == pytest.approx(0.4)


##### playback #####


def test_play_pause_resume_and_stop(sound_file):
    sound = Sound(sound_file)

    sound.play()
    if sound.channel is None:
        pytest.skip("no free mixer channel in this environment")
    assert sound.playing is True

    sound.pause()
    assert sound.is_paused is True

    sound.play()  # resumes rather than restarting
    assert sound.is_paused is False
    assert sound.playing is True

    sound.stop()
    assert sound.playing is False


def test_playing_again_replaces_the_previous_playback(sound_file):
    sound = Sound(sound_file)

    sound.play()
    if sound.channel is None:
        pytest.skip("no free mixer channel in this environment")
    first_channel = sound.channel

    sound.play()

    # The old playback is stopped first, so nothing keeps sounding twice.
    assert sound.playing is True
    assert sound.channel is not None
    assert first_channel.get_sound() in (None, sound.sound)

    sound.stop()


def test_pause_and_stop_before_playing_are_safe(sound_file):
    sound = Sound(sound_file)

    sound.pause()
    sound.stop()

    assert sound.playing is False
    assert sound.is_paused is False
