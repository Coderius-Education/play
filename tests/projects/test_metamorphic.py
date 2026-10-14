"""Metamorphic tests — the same game, run under changed conditions.

Instead of asserting a specific outcome, these assert that an outcome does not
*change* when something that should not affect it changes. That catches a class
of bug an ordinary test cannot see: code which is right at the default settings
and wrong everywhere else.

The physics sub-step count is the sharpest example: anything that ran once per
sub-step would happen ten times per frame at the default and once at
``num_sim_steps=1`` — behaviour that silently depends on a setting the user is
free to change.
"""

import pytest

import play
from play.callback.collision_callbacks import WallSide
from play.globals import globals_list

SIM_STEPS = [1, 3, 10]
SCREEN_SIZES = [(800, 600), (640, 480), (1024, 768)]


def _run_scoring_game(max_frames=900):
    """Send a ball straight at the right wall and report what happened.

    Deliberately unambiguous: no gravity, no vertical speed, nothing in the
    way. Who scores is a fact about the rules, not about how finely the
    physics was integrated, so it must come out the same under every setting.
    """
    scored = []

    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=300, y_speed=0, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        scored.append("left")
        play.stop_program()

    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        scored.append("right")
        play.stop_program()

    @play.when_program_starts
    async def budget():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()
    return scored


@pytest.mark.parametrize("sim_steps", SIM_STEPS)
def test_scoring_is_independent_of_simulation_steps(sim_steps):
    """Who scores must not depend on the physics sub-step count."""
    play.set_physics_simulation_steps(sim_steps)
    assert globals_list.num_sim_steps == sim_steps

    scored = _run_scoring_game()

    assert scored, f"nobody scored at num_sim_steps={sim_steps}"
    assert scored[0] == "left", (
        f"a ball sent right must score for the left player, but at "
        f"num_sim_steps={sim_steps} it scored for {scored[0]}"
    )


@pytest.mark.parametrize("size", SCREEN_SIZES)
def test_scoring_is_independent_of_screen_size(size):
    """A wider screen means a longer flight, not a different winner."""
    from play.io.screen import screen, create_walls

    screen.width, screen.height = size
    screen.update_display()
    create_walls()

    scored = _run_scoring_game()

    assert scored, f"nobody scored at screen size {size}"
    assert scored[0] == "left", (
        f"a ball sent right must score for the left player, but at screen "
        f"size {size} it scored for {scored[0]}"
    )


@pytest.mark.parametrize("sim_steps", SIM_STEPS)
def test_callback_fires_once_per_collision_regardless_of_sim_steps(sim_steps):
    """An edge-triggered collision must not scale with the sub-step count.

    A collision callback that fired per sub-step would show a count that
    tracks the setting, so comparing across settings is what exposes it.
    """
    play.set_physics_simulation_steps(sim_steps)

    hits = []

    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    wall_hits = play.new_box(color="blue", x=200, y=0, width=20, height=400)
    ball.start_physics(
        obeys_gravity=False, x_speed=200, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    wall_hits.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_touching(wall_hits)
    def touched():
        hits.append(1)
        play.stop_program()

    @play.when_program_starts
    async def budget():
        for _ in range(600):
            await play.animate()
        play.stop_program()

    play.start_program()

    assert hits, f"the ball never reached the block at num_sim_steps={sim_steps}"
    # Stopping on the first hit means a per-sub-step dispatch would still show
    # up as more than one entry recorded within that same frame.
    assert len(hits) == 1, (
        f"the collision callback ran {len(hits)} times for one collision at "
        f"num_sim_steps={sim_steps}; it should not scale with sub-steps"
    )


@pytest.mark.parametrize("sim_steps", SIM_STEPS)
def test_a_resting_contact_fires_once_per_frame_regardless_of_sim_steps(sim_steps):
    play.set_physics_simulation_steps(sim_steps)
    floor = play.new_box(x=-200, y=-100, width=200, height=20)
    floor.start_physics(can_move=False)
    on_box = play.new_circle(x=-200, y=-80, radius=10)
    on_box.start_physics(bounciness=0)
    on_edge = play.new_circle(x=200, y=play.screen.bottom + 10, radius=10)
    on_edge.start_physics(bounciness=0)
    touching_floor = []
    touching_wall = []
    frames = [0]

    @on_box.when_touching(floor)
    def on_floor():
        touching_floor.append(frames[0])

    @on_edge.when_touching_wall
    def on_wall():
        touching_wall.append(frames[0])

    @play.repeat_forever
    def count():
        frames[0] += 1
        if frames[0] == 40:
            play.stop_program()

    play.start_program()

    for calls in (touching_floor, touching_wall):
        late = [frame for frame in calls if frame >= 20]
        assert late and len(late) == len(set(late)), (sim_steps, calls)


@pytest.mark.parametrize("sim_steps", SIM_STEPS)
def test_sprites_are_drawn_once_per_frame_regardless_of_sim_steps(sim_steps):
    from play.globals import globals_list

    play.set_physics_simulation_steps(sim_steps)
    play.new_circle()
    draws = [0]
    frames = [0]
    real_draw = globals_list.sprites_group.draw

    def draw(*args, **kwargs):
        draws[0] += 1
        return real_draw(*args, **kwargs)

    globals_list.sprites_group.draw = draw

    @play.repeat_forever
    def count():
        frames[0] += 1
        if frames[0] == 30:
            play.stop_program()

    play.start_program()

    assert draws[0] == frames[0]
