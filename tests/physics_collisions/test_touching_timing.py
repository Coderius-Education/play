"""When when_touching and when_stopped_touching run, with physics in sub-steps (#230)."""

import asyncio

import pytest

import play
from play.callback.collision_callbacks import WallSide
from play.core.sprites_loop import handle_new_contacts

FRAMES = 90
SIM_STEPS = [1, 3, 10, 20]


def _assert_contact_rules(events):
    """Check a log of "touching", "stopped" and "frame end" against the rules."""
    open_contact = False
    called_this_frame = False
    for index, event in enumerate(events):
        if event == "touching":
            assert not (
                open_contact and called_this_frame
            ), f"two calls for one contact in one frame, event {index}"
            open_contact = called_this_frame = True
        elif event == "stopped":
            assert open_contact, f"stopped without touching, event {index}"
            open_contact = called_this_frame = False
        else:
            assert (
                not open_contact or called_this_frame
            ), f"a frame with the contact but no call, event {index}"
            called_this_frame = False


def _resting_box():
    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    box = play.new_box(y=-180, width=20, height=20)
    box.start_physics(bounciness=0)
    return box, floor


def _sliding_box():
    floor = play.new_box(y=-200, width=700, height=20)
    floor.start_physics(can_move=False, friction=0.5)
    box = play.new_box(x=-300, y=-180, width=20, height=20)
    box.start_physics(x_speed=200, bounciness=0, friction=0.5)
    return box, floor


def _dropped_ball():
    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    ball = play.new_circle(y=-100, radius=10)
    ball.start_physics(y_speed=-600, bounciness=0.8)
    return ball, floor


def _ball_squeezed_at(speed):
    def build():
        wall = play.new_box(x=-380, width=20, height=600)
        wall.start_physics(can_move=False)
        paddle = play.new_box(x=-330, width=20, height=100)
        paddle.start_physics(can_move=False)
        ball = play.new_circle(x=-355, radius=10)
        ball.start_physics(x_speed=-speed, obeys_gravity=False)
        return ball, paddle

    return build


def _two_moving_balls():
    left = play.new_circle(x=-60, radius=15)
    right = play.new_circle(x=60, radius=15)
    left.start_physics(x_speed=400, obeys_gravity=False)
    right.start_physics(x_speed=-400, obeys_gravity=False)
    return left, right


SPRITE_PAIRS = {
    "resting box": _resting_box,
    "sliding box": _sliding_box,
    "dropped ball": _dropped_ball,
    "two moving balls": _two_moving_balls,
    "squeezed ball, 1 bounce a frame": _ball_squeezed_at(1500),
    "squeezed ball, 3 bounces a frame": _ball_squeezed_at(6000),
}


def _run_frames(log):
    frames = [0]

    @play.repeat_forever
    def end_of_frame():
        log.append("frame end")
        frames[0] += 1
        if frames[0] == FRAMES:
            play.stop_program()

    play.start_program()


@pytest.mark.parametrize("sim_steps", SIM_STEPS)
@pytest.mark.parametrize("scenario", SPRITE_PAIRS)
def test_sprite_contacts_follow_the_rules(scenario, sim_steps):
    play.set_physics_simulation_steps(sim_steps)
    sprite, other = SPRITE_PAIRS[scenario]()
    log = []
    sprite.when_touching(other)(lambda: log.append("touching"))
    sprite.when_stopped_touching(other)(lambda: log.append("stopped"))

    _run_frames(log)

    _assert_contact_rules(log)


@pytest.mark.parametrize("sim_steps", SIM_STEPS)
@pytest.mark.parametrize("speed", [300, 3000, 20000])
def test_wall_contacts_follow_the_rules(speed, sim_steps):
    play.set_physics_simulation_steps(sim_steps)
    ball = play.new_circle(x=350, radius=10)
    ball.start_physics(x_speed=speed, obeys_gravity=False)
    log = []
    ball.when_touching_wall(lambda: log.append("touching"), wall=WallSide.RIGHT)
    ball.when_stopped_touching_wall(lambda: log.append("stopped"), wall=WallSide.RIGHT)

    _run_frames(log)

    _assert_contact_rules(log)


def test_several_bounces_in_one_frame_each_run_when_touching():
    play.set_physics_simulation_steps(10)
    ball, paddle = _ball_squeezed_at(6000)()
    log = []
    ball.when_touching(paddle)(lambda: log.append("touching"))
    ball.when_stopped_touching(paddle)(lambda: log.append("stopped"))

    _run_frames(log)

    calls_per_frame = " ".join(log).split("frame end")
    assert max(frame.count("touching") for frame in calls_per_frame) >= 2
    _assert_contact_rules(log)


@pytest.mark.parametrize("sim_steps", [3, 10])
def test_when_touching_runs_at_the_moment_of_contact(sim_steps):
    play.set_physics_simulation_steps(sim_steps)
    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    ball = play.new_circle(y=0, radius=10)
    ball.start_physics(y_speed=-3000, bounciness=1)
    seen = []

    @ball.when_touching(floor)
    def landed():
        seen.append((ball.is_touching(floor), ball.y))

    _run_frames([])

    assert seen
    for touching, y in seen:
        assert touching
        assert y < -170


@pytest.mark.parametrize("taken_away_by", ["hide", "remove"])
def test_a_sprite_taken_away_in_the_same_sub_step_gets_no_when_touching(
    taken_away_by,
):
    trigger = play.new_box(x=-100, y=-100, width=60, height=20)
    floor = play.new_box(x=100, y=-100, width=60, height=20)
    ball = play.new_box(x=-100, y=0, width=20, height=20)
    coin = play.new_box(x=100, y=0, width=20, height=20)
    trigger.start_physics(can_move=False)
    floor.start_physics(can_move=False)
    ball.start_physics(y_speed=-300, obeys_gravity=False)
    coin.start_physics(y_speed=-300, obeys_gravity=False)
    calls_after = []

    @ball.when_touching(trigger)
    def take_the_coin_away():
        if taken_away_by == "hide":
            coin.hide()
        else:
            coin.remove()

    @coin.when_touching(floor)
    def landed():
        calls_after.append(coin.is_hidden or not coin.alive())

    _run_frames([])

    assert True not in calls_after


def test_a_contact_left_pending_while_hidden_does_not_run_after_show():
    coin = play.new_box()
    floor = play.new_box(y=-100)
    calls = []

    async def landed():
        calls.append(1)

    coin.events.set_touching("floor", landed, floor)
    coin.hide()
    asyncio.run(handle_new_contacts())
    coin.show()
    asyncio.run(handle_new_contacts())

    assert calls == []


def _offsets_from_bodies():
    return [
        (sprite.x - sprite.physics._pymunk_body.position.x)
        + (sprite.y - sprite.physics._pymunk_body.position.y)
        for sprite in play.globals.globals_list.sprites_group.sprites()
        if sprite.physics.can_move
    ]


@pytest.mark.parametrize("left_first", [True, False])
def test_callbacks_see_every_sprite_where_its_body_is(left_first):
    play.set_physics_simulation_steps(10)
    floor = play.new_box(y=-200, width=700, height=20)
    floor.start_physics(can_move=False)
    resting = play.new_box(y=-180, width=20, height=20)
    resting.start_physics(bounciness=0)
    if left_first:
        left, right = play.new_circle(x=-60, radius=15), play.new_circle(
            x=60, radius=15
        )
    else:
        right, left = play.new_circle(x=60, radius=15), play.new_circle(
            x=-60, radius=15
        )
    left.start_physics(x_speed=900, obeys_gravity=False)
    right.start_physics(x_speed=-900, obeys_gravity=False)
    offsets = []
    left.when_touching(right)(lambda: offsets.extend(_offsets_from_bodies()))
    resting.when_touching(floor)(lambda: offsets.extend(_offsets_from_bodies()))

    _run_frames([])

    assert offsets
    assert max(abs(offset) for offset in offsets) < 1e-9


@pytest.mark.parametrize("sim_steps", [1, 10])
def test_sprites_are_synced_once_per_frame_when_nothing_touches(sim_steps, monkeypatch):
    play.set_physics_simulation_steps(sim_steps)
    for x in (-200, 0, 200):
        play.new_circle(x=x, radius=10).start_physics(y_speed=50, obeys_gravity=False)
    syncs = []
    original = play.core.sprites_loop.update_sprite_physics

    def counting_sync(sprite):
        syncs.append(sprite)
        original(sprite)

    monkeypatch.setattr(play.core.sprites_loop, "update_sprite_physics", counting_sync)

    _run_frames([])

    assert len(syncs) == 3 * FRAMES
