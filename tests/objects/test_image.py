import pytest
import play
import os
import pygame
from play.objects.image import Image


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


@pytest.fixture
def mock_image_file(tmp_path):
    # Create a dummy image file using pygame
    img_path = tmp_path / "test_image.png"
    surface = pygame.Surface((50, 50))
    surface.fill((255, 0, 0))
    pygame.image.save(surface, str(img_path))
    return str(img_path)


def test_image_initialization_valid_file(mock_image_file):
    img = Image(mock_image_file, x=10, y=20, angle=45, size=50, transparency=80)
    assert img.x == 10
    assert img.y == 20
    assert img.angle == 45
    assert img.size == 50
    assert img.transparency == 80
    assert img._original_width == 50
    assert img._original_height == 50
    assert img.image is not None


def test_image_initialization_invalid_file():
    with pytest.raises(FileNotFoundError):
        Image("non_existent_file_12345.png")


def test_image_initialization_surface():
    surface = pygame.Surface((10, 10))
    img = Image(surface)
    assert img._original_width == 10
    assert img.image is not None


def test_image_filename_setter(mock_image_file, tmp_path):
    img = Image(mock_image_file)

    # Test setting new valid file
    new_path = tmp_path / "new_image.png"
    new_surface = pygame.Surface((30, 30))
    pygame.image.save(new_surface, str(new_path))

    img.image_filename = str(new_path)
    assert img._original_width == 30
    assert img.image_filename is None  # Property returns None by design

    # Test setting invalid file
    with pytest.raises(FileNotFoundError):
        img.image_filename = "invalid_path.png"


def test_image_update_transformations(mock_image_file):
    img = Image(mock_image_file)

    # Modify properties to trigger `_should_recompute` inside update
    img.size = 200
    img.angle = 90
    img.transparency = 50

    img.update()

    # Size 200 of a 50x50 image should be roughly 100x100
    assert img.rect.width == 100
    assert img.rect.height == 100
    # Original image width should remain unmodified
    assert img._original_width == 50
