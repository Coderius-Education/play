"""The game loop: one physics step and one drawing per frame, until the program stops."""

import pytest

import play
from play.globals import globals_list, ProgramState


def _positions_per_frame(sprite, frames):
    """Run *frames* frames and return where *sprite* was in each."""
    positions = []

    @play.repeat_forever
    def track():
        positions.append((sprite.x, sprite.y))
        if len(positions) == frames:
            play.stop_program()

    play.start_program()
    return positions


@pytest.mark.parametrize("steps", [10, 3])
def test_a_sprite_moving_at_60_per_second_moves_1_per_frame(steps):
    play.set_physics_simulation_steps(steps)
    box = play.new_box(width=20, height=20)
    box.start_physics(x_speed=60, obeys_gravity=False)

    xs = [x for x, _ in _positions_per_frame(box, 6)]

    assert [b - a for a, b in zip(xs, xs[1:])] == pytest.approx([1] * 5)


def test_a_sprite_with_gravity_falls_faster_every_frame():
    box = play.new_box(y=100, width=20, height=20)
    box.start_physics(obeys_gravity=True)

    ys = [y for _, y in _positions_per_frame(box, 10)]
    drops = [a - b for a, b in zip(ys, ys[1:])]

    assert all(later > earlier > 0 for earlier, later in zip(drops, drops[1:]))


def test_stop_program_during_first_frame_exits():
    # Regression: loop.stop() from the very first frame was absorbed by
    # run_until_complete's own stop signal, after which run_forever() ran
    # unbounded — headless test runs hung on this.
    frames = [0]

    @play.repeat_forever
    def _stop_immediately():
        frames[0] += 1
        play.stop_program()

    play.start_program()  # a regression would hang here until the safety stop
    assert frames[0] == 1


def test_stop_program_from_when_program_starts_exits():
    ran = []

    @play.when_program_starts
    def _stop_now():
        ran.append(1)
        play.stop_program()

    play.start_program()
    assert ran == [1]


def test_start_program_after_stop_still_refuses():
    # The three lifecycle states live in one field now; a stopped program must
    # stay as unrestartable as a running one.
    @play.repeat_forever
    def _stop_immediately():
        play.stop_program()

    play.start_program()
    assert globals_list.program_state is ProgramState.STOPPED

    with pytest.raises(RuntimeError, match="already started"):
        play.start_program()


def test_a_video_stops_playing_when_the_program_ends(video_file):
    video = play.new_video(video_file)
    video.play()
    play.repeat_forever(play.stop_program)

    play.start_program()

    assert video.playing is False
