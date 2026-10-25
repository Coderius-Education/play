"""Comprehensive tests for all 7 bug fixes from issue #122."""

import math

import pytest


def _picture(tmp_path, width, height):
    import pygame

    path = tmp_path / "picture.png"
    pygame.image.save(pygame.Surface((width, height)), str(path))
    return str(path)


def test_an_image_turns_with_its_physics_body(tmp_path):
    import play

    image = play.new_image(image=_picture(tmp_path, 40, 30), x=100, y=100)
    image.update()
    assert image.rect.size == (40, 30)

    image.physics._pymunk_body.angle = math.radians(90)
    image._should_recompute = True
    image.update()

    assert image.rect.size == (30, 40)


@pytest.mark.parametrize(
    "picture_size, size, expected",
    [((40, 30), 50, (20, 15)), ((3, 3), 10, (1, 1)), ((25, 25), 218, (54, 54))],
)
def test_an_image_size_is_rounded_and_never_below_one_pixel(
    tmp_path, picture_size, size, expected
):
    import play

    image = play.new_image(image=_picture(tmp_path, *picture_size), size=size)

    assert (image.width, image.height) == expected


def test_two_keyboard_states_do_not_share_their_keys():
    """Test that KeyboardState instances don't share pressed/released lists."""
    from play.io.keypress import KeyboardState

    # Create two instances
    kb1 = KeyboardState()
    kb2 = KeyboardState()

    # Modify one instance
    kb1.pressed.add("a")
    kb1.released.add("b")

    # Verify the other instance is not affected
    assert "a" not in kb2.pressed
    assert "b" not in kb2.released

    # Verify they have separate lists
    assert kb1.pressed is not kb2.pressed
    assert kb1.released is not kb2.released


def test_a_plain_async_function_can_repeat_forever():
    import play

    runs = []

    async def simple_callback():
        runs.append(1)
        if len(runs) == 3:
            play.stop_program()

    play.repeat_forever(simple_callback)
    play.start_program()

    assert runs == [1, 1, 1]


def test_a_nan_physics_coordinate_is_ignored_and_the_other_one_still_follows():
    import asyncio

    import play
    from play.core.sprites_loop import update_sprites

    sprite = play.new_box(x=100, y=100)
    sprite.physics._pymunk_body.position = (float("nan"), 70)

    asyncio.run(update_sprites())

    assert (sprite.x, sprite.y) == (100, 70)


def test_a_cloned_box_keeps_its_rounded_corners():
    """Test that Box.clone() includes border_radius parameter."""
    import play

    # Create a box with border_radius
    box1 = play.new_box(x=100, y=100, width=50, height=50, border_radius=15)

    # Clone it
    box2 = box1.clone()

    # Verify border_radius is preserved
    assert box2.border_radius == box1.border_radius
    assert box2.border_radius == 15
