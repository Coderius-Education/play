import play
from play.callback.collision_callbacks import WallSide
from play.io.screen import screen


def test_a_box_placed_on_the_floor_touches_it_from_the_first_frame_until_it_jumps():
    box = play.new_box(y=screen.bottom, width=40, height=40)
    box.start_physics(obeys_gravity=False)
    log = []
    frames = [0]

    @box.when_touching_wall(wall=WallSide.BOTTOM)
    def on_floor(wall):
        log.append(("touching", wall, frames[0]))

    @box.when_stopped_touching_wall(wall=WallSide.BOTTOM)
    def off_floor(wall):
        log.append(("stopped", wall, frames[0]))

    @play.repeat_forever
    def jump_later():
        frames[0] += 1
        if frames[0] == 3:
            box.physics.y_speed = 300
        if frames[0] == 30:
            play.stop_program()

    play.start_program()

    assert log[0] == ("touching", WallSide.BOTTOM, 0)
    assert [event for event, _, _ in log].count("stopped") == 1
    assert log[-1][:2] == ("stopped", WallSide.BOTTOM)
    assert {wall for _, wall, _ in log} == {WallSide.BOTTOM}
