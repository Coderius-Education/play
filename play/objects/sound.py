"""Handles custom music/sound being played."""

import pygame
from ..io.logging import play_logger as logger
from ..utils import experimental


@experimental
class Sound:
    def __init__(self, file_name, volume=1.0, loops=1):
        """
        Initialize the Sound object.
        :param file_name: The sound file to load.
        :param volume: The initial volume (0.0 to 1.0).
        :param loops: Number of times to loop the sound (-1 for infinite).
        """
        pygame.mixer.init()
        self.sound = None
        self.channel = None
        self.file_path = file_name
        self._volume = volume
        self.loops = loops
        self.is_paused = False
        self.load(file_name)

    def load(self, file_name):
        """Load a sound file."""
        try:
            self.sound = pygame.mixer.Sound(file_name)
            self.sound.set_volume(self._volume)
        except FileNotFoundError:
            logger.error("File not found", exc_info=True)
        logger.info("Loaded sound file")

    def play(self):
        """Play the loaded sound with the specified loop settings, or resume a paused sound."""
        if not self.sound:
            logger.warning("No sound loaded. Use the 'load' method first.")
            return

        if self.is_paused and self.channel is not None:
            self.channel.unpause()
            self.is_paused = False
            return

        # Stop any existing playback before starting a new one so we don't
        # leak an untracked channel.
        if self.channel is not None and self.channel.get_busy():
            self.channel.stop()

        self.channel = pygame.mixer.find_channel()
        if self.channel is None:
            logger.warning("No available channels to play the sound.")
            return

        self.channel.play(self.sound, loops=self.loops)

    def pause(self):
        """Pause the sound."""
        if self.channel is None:
            return
        if self.channel.get_busy():
            self.channel.pause()
            self.is_paused = True

    @property
    def length(self):
        """Returns the length of the song as a float"""
        if self.channel is None:
            return 0.0
        sound = self.channel.get_sound()
        if sound is None:
            return 0.0
        return round(sound.get_length(), 2)

    def stop(self):
        """Stop current channel"""
        if self.channel is None:
            return
        self.channel.stop()

    @property
    def volume(self):
        """Get the current volume of the sound."""
        if not self.sound:
            logger.warning("No sound loaded. Use the 'load' method first.")
            return self._volume
        return self.sound.get_volume()

    @volume.setter
    def volume(self, volume):
        """Set the volume of the sound (0.0 to 1.0)."""
        if not 0.0 <= volume <= 1.0:
            logger.warning("Volume must be between 0.0 and 1.0")
        self._volume = volume
        if self.sound:
            self.sound.set_volume(volume)

    @property
    def playing(self):
        """Check if the sound is currently playing."""
        if self.channel:
            return self.channel.get_busy()
        return False
