"""This module contains the Image class, which is a subclass of the Sprite class."""

import os
import pygame

from .sprite import Sprite
from ..io.screen import convert_pos


class Image(Sprite):
    def __init__(self, image, x=0, y=0, angle=0, size=100, transparency=100):
        if isinstance(image, str):
            if not os.path.isfile(image):
                raise FileNotFoundError(f"Image file '{image}' not found.")
            # Keep the original, loaded image safe from modifications.
            self._source_image = pygame.image.load(image)
        else:
            self._source_image = image

        # Initialize the parent sprite with this image.
        super().__init__(image=self._source_image)

        self._original_width = self._source_image.get_width()
        self._original_height = self._source_image.get_height()
        self._x = x
        self._y = y
        self._angle = angle
        self._size = size
        self._transparency = transparency
        self.rect = self._source_image.get_rect()
        self.start_physics(can_move=False)
        self.update()

    def update(self):
        """Update the image's position, size, angle, and transparency."""
        if self._should_recompute:
            # Generate the display image from the original source
            draw_image = pygame.transform.scale(
                self._source_image,
                (
                    self._original_width * self._size // 100,
                    self._original_height * self._size // 100,
                ),
            )
            draw_image = pygame.transform.rotate(draw_image, self.angle)
            alpha_value = round(self.transparency * 2.55)
            draw_image.set_alpha(alpha_value)

            # Set the generated image as the sprite's current image
            self.image = draw_image
            self.rect = draw_image.get_rect()
            pos = convert_pos(self.x, self.y)
            self.rect.center = pos

        # Allow the parent class to handle hiding, collisions, etc.
        super().update()

    # The custom image property is removed to use the parent Sprite's property.
    # This ensures that the image managed by the Pygame sprite group is the
    # one generated in the update method.

    @property
    def image_filename(self):
        """Return the image filename. This is a dummy property since we store the surface."""
        return None

    @image_filename.setter
    def image_filename(self, image: str):
        """Set the image from a file."""
        if not os.path.isfile(image):
            raise FileNotFoundError(f"Image file '{image}' not found.")
        self._source_image = pygame.image.load(image)
        self._original_width = self._source_image.get_width()
        self._original_height = self._source_image.get_height()
        self._should_recompute = True
        self.update()
