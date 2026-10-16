"""A bound method such as box.hide can be a callback: its self is not counted as an argument."""

import pygame

import play
from tests.conftest import post_key_down


def test_a_bound_method_can_be_a_key_callback():
    box = play.new_box()
    play.when_key_pressed("space")(box.hide)
    frames = []

    @play.when_program_starts
    async def press():
        await play.animate()
        post_key_down(pygame.K_SPACE)

    @play.repeat_forever
    def stop_later():
        frames.append(1)
        if len(frames) == 10:
            play.stop_program()

    play.start_program()

    assert box.is_hidden
