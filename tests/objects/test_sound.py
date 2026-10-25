"""Tests for the Sound object."""

import math
import struct
import time
import wave

import pytest

import play
from play.objects.sound import Sound


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def write_tone(path, seconds):
    """Write a 440 Hz tone as a WAV file, with the stdlib."""
    rate = 22050
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


@pytest.fixture(scope="session")
def sound_file(tmp_path_factory):
    """A two-second tone."""
    return write_tone(tmp_path_factory.mktemp("sound") / "tone.wav", 2.0)


@pytest.fixture(scope="session")
def blip_file(tmp_path_factory):
    """A tone of a twentieth of a second, short enough to wait for."""
    return write_tone(tmp_path_factory.mktemp("sound") / "blip.wav", 0.05)


def busy_channels():
    """How many mixer channels are sounding right now."""
    import pygame

    channels = range(pygame.mixer.get_num_channels())
    return sum(pygame.mixer.Channel(i).get_busy() for i in channels)


def wait_until_silent(sound, timeout=2.0):
    """Wait for a sound to finish playing on its own."""
    deadline = time.monotonic() + timeout
    while sound.playing and time.monotonic() < deadline:
        time.sleep(0.01)
    return not sound.playing


##### loading #####


def test_loads_and_knows_its_length(sound_file):
    sound = Sound(sound_file)

    assert sound.sound is not None
    # The length is known as soon as the file is loaded, before playing.
    assert sound.length == pytest.approx(2.0, abs=0.1)


def test_new_sound_passes_on_its_settings(sound_file):
    sound = play.new_sound(sound_file, volume=0.5, loops=3)

    assert isinstance(sound, Sound)
    assert sound.length == pytest.approx(2.0, abs=0.1)
    assert sound.volume == pytest.approx(0.5, abs=0.02)
    assert sound.loops == 3


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

    sound.volume = 5
    assert sound.volume == 1.0


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
    import pygame

    sound = Sound(sound_file)
    pygame.mixer.stop()

    sound.play()
    if sound.channel is None:
        pytest.skip("no free mixer channel in this environment")

    sound.play()

    # The old playback is stopped first, so nothing keeps sounding twice.
    assert sound.playing is True
    assert busy_channels() == 1

    sound.stop()


def test_pause_and_stop_before_playing_are_safe(sound_file):
    sound = Sound(sound_file)

    sound.pause()
    sound.stop()

    assert sound.playing is False
    assert sound.is_paused is False


def test_play_after_pause_and_stop_starts_from_scratch(sound_file):
    # stop() must clear the paused flag: without that, play() tried to
    # unpause the stopped channel and nothing sounded.
    sound = Sound(sound_file)

    sound.play()
    if sound.channel is None:
        pytest.skip("no free mixer channel in this environment")
    sound.pause()
    sound.stop()

    sound.play()

    assert sound.is_paused is False
    assert sound.playing is True
    sound.stop()


def test_out_of_range_volume_warns(sound_file, caplog):
    sound = Sound(sound_file)

    with caplog.at_level("WARNING", logger="play"):
        sound.volume = 5

    assert any("Volume must be between" in r.message for r in caplog.records)
    assert sound.volume == 1.0


def test_a_looping_sound_keeps_playing_after_a_single_one_has_ended(blip_file):
    once = Sound(blip_file)
    forever = Sound(blip_file, loops=-1)
    once.play()
    forever.play()
    if once.channel is None or forever.channel is None:
        pytest.skip("no free mixer channel in this environment")

    assert wait_until_silent(once)
    time.sleep(0.2)

    assert forever.playing is True
    forever.stop()


def test_pausing_a_finished_sound_does_not_stop_it_from_playing_again(blip_file):
    sound = Sound(blip_file)
    sound.play()
    if sound.channel is None:
        pytest.skip("no free mixer channel in this environment")
    assert wait_until_silent(sound)

    sound.pause()
    sound.play()

    assert sound.is_paused is False
    assert sound.playing is True


def test_with_no_free_channel_play_warns_and_stays_silent(
    sound_file, monkeypatch, caplog
):
    import pygame

    sound = Sound(sound_file)
    monkeypatch.setattr(pygame.mixer, "find_channel", lambda *args: None)

    with caplog.at_level("WARNING", logger="play"):
        sound.play()

    assert any("No available channels" in r.message for r in caplog.records)
    assert sound.playing is False
