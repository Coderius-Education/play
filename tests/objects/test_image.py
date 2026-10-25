import pytest
import pygame
from play.objects.image import Image


@pytest.fixture
def mock_image_file(tmp_path):
    img_path = tmp_path / "test_image.png"
    surface = pygame.Surface((50, 50))
    surface.fill((255, 0, 0))
    pygame.image.save(surface, str(img_path))
    return str(img_path)


def test_an_image_from_a_file_is_drawn_with_its_settings(mock_image_file):
    img = Image(mock_image_file, x=10, y=20, size=50, transparency=80)

    assert (img.x, img.y, img.size, img.transparency) == (10, 20, 50, 80)
    assert img.image_filename == mock_image_file
    assert img.image.get_size() == (25, 25)
    assert tuple(img.image.get_at((12, 12)))[:3] == (255, 0, 0)
    assert img.image.get_alpha() == 204


def test_a_missing_image_file_is_named_in_the_error():
    with pytest.raises(
        FileNotFoundError, match="Image file .non_existent_file_12345.png. not found"
    ):
        Image("non_existent_file_12345.png")


def test_an_image_can_be_made_from_a_surface():
    img = Image(pygame.Surface((10, 20)))

    assert img.image_filename is None
    assert img.image.get_size() == (10, 20)


def test_a_new_image_file_is_drawn_and_touched_at_its_own_size(
    mock_image_file, tmp_path
):
    img = Image(mock_image_file)
    new_path = tmp_path / "new_image.png"
    pygame.image.save(pygame.Surface((120, 30)), str(new_path))
    assert not img.is_touching((55, 0))

    img.image_filename = str(new_path)

    assert img.image_filename == str(new_path)
    assert img.image.get_size() == (120, 30)
    assert img.is_touching((55, 0))


def test_a_missing_new_image_file_is_refused_and_the_old_picture_stays(
    mock_image_file,
):
    img = Image(mock_image_file)

    with pytest.raises(FileNotFoundError, match="invalid_path.png"):
        img.image_filename = "invalid_path.png"

    assert img.image_filename == mock_image_file
    assert img.image.get_size() == (50, 50)


def test_growing_and_shrinking_back_does_not_wear_the_picture_down(mock_image_file):
    img = Image(mock_image_file)

    img.size = 200
    img.angle = 90
    img.update()
    assert img.image.get_size() == (100, 100)

    img.size = 10
    img.update()
    img.size = 100
    img.angle = 0
    img.update()

    assert img.image.get_size() == (50, 50)
    assert tuple(img.image.get_at((0, 0)))[:3] == (255, 0, 0)
