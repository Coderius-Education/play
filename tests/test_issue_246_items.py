"""The remaining small findings of #246."""

import pygame

import play
from play.callback.collision_callbacks import WallSide
from play.globals import globals_list
from play.io.screen import remove_wall, screen

IMAGE = "tests/objects_attributes/yellow.jpg"


def test_an_image_clone_keeps_its_place_size_angle_and_picture():
    image = play.new_image(
        image=IMAGE, x=-100, y=100, size=50, angle=45, transparency=50
    )

    clone = image.clone()

    assert (clone.x, clone.y) == (-100, 100)
    assert (clone.size, clone.angle, clone.transparency) == (50, 45, 50)
    assert clone.image_filename == IMAGE
    clone.size = 100
    clone.angle = 0
    clone.update()
    assert clone.rect.size == image._source_image.get_size()


def test_a_click_without_mouse_motion_lands_where_it_was_made():
    box = play.new_box(x=150, y=100, width=60, height=60)
    clicked = []
    box.when_clicked(lambda: clicked.append(1))
    pos = (int(screen.width / 2 + 150), int(screen.height / 2 - 100))

    @play.when_program_starts
    async def click():
        await play.animate()
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
        await play.animate()
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))
        for _ in range(3):
            await play.animate()
        play.stop_program()

    play.start_program()

    assert clicked == [1]


def test_remove_wall_takes_the_side_its_index_names():
    remove_wall(0)
    remove_wall(1)

    sides = {wall.wall_side for wall in globals_list.walls}
    assert sides == {WallSide.LEFT, WallSide.RIGHT}


def test_a_sound_without_an_audio_device_warns_instead_of_crashing(monkeypatch, caplog):
    def no_device():
        raise pygame.error("Audio target 'nosuchdriver' not available")

    monkeypatch.setattr(pygame.mixer, "init", no_device)

    sound = play.new_sound("missing.wav")

    assert sound.sound is None
    assert any("no audio device" in record.getMessage() for record in caplog.records)
