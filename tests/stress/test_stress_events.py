import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


@pytest.mark.xdist_group("stress")
def test_two_hundred_overlapping_sprites_each_run_their_when_touching_in_the_first_frame():
    num_sprites = 200
    sprites = []
    first_touch = {}
    frames_run = [0]

    for _ in range(num_sprites):
        sprite = play.new_circle(color="blue", radius=50)
        sprite.start_physics(obeys_gravity=False, bounciness=0, mass=1)
        sprites.append(sprite)

    target = sprites[0]

    def watch(index):
        @sprites[index].when_touching(target)
        def touched():
            first_touch.setdefault(index, frames_run[0])

    for index in range(1, num_sprites):
        watch(index)

    @play.repeat_forever
    def simulation_loop():
        frames_run[0] += 1
        if frames_run[0] == 20:
            play.stop_program()

    play.start_program()

    assert frames_run[0] == 20
    assert first_touch == {index: 0 for index in range(1, num_sprites)}
