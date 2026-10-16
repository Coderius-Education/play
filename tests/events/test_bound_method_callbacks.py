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


def test_a_bound_method_can_be_a_contact_callback():
    ball = play.new_circle(x=-100, radius=10)
    ball.start_physics(x_speed=300, obeys_gravity=False)
    coin = play.new_circle(radius=10)
    coin.start_physics(can_move=False)
    ball.when_touching(coin)(coin.hide)
    frames = []

    @play.repeat_forever
    def stop_later():
        frames.append(1)
        if len(frames) == 60:
            play.stop_program()

    play.start_program()

    assert coin.is_hidden
