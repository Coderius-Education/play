"""Shared helpers for tests/projects/ — reduces boilerplate across pong variants."""

import pytest


# ---------------------------------------------------------------------------
# Per-frame invariant watchdog
# ---------------------------------------------------------------------------

# Stop recording after this many violations. One broken invariant usually
# repeats every frame for the rest of the run, and a thousand identical lines
# buries the first one, which is the one that matters.
MAX_VIOLATIONS = 5


def _finite(value):
    return value == value and value not in (float("inf"), float("-inf"))


def check_frame_invariants(known):
    """Return a list of invariant violations for the current frame.

    These hold for any game at any moment, so every project test can check them
    on every frame for free. That is the point: a project test asserts its own
    ending, which a bug can leave intact while corrupting everything on the way
    there. ``test_platformer_keyboard`` passed for months while never touching
    its platform.

    ``known`` carries state across frames so a sprite that disappears can still
    be checked for a leaked physics body.
    """
    from play.globals import globals_list
    from play.physics import physics_space

    violations = []
    live = globals_list.sprites_group.sprites()
    body_ids = {id(b) for b in physics_space.bodies}
    shape_ids = {id(s) for s in physics_space.shapes}
    live_ids = set()

    for sprite in live:
        live_ids.add(id(sprite))

        if not (_finite(sprite.x) and _finite(sprite.y)):
            violations.append(
                f"{sprite!r} has a non-finite position ({sprite.x}, {sprite.y})"
            )

        physics = getattr(sprite, "physics", None)
        if physics is None:
            continue

        body, shape = physics._pymunk_body, physics._pymunk_shape
        known[id(sprite)] = (repr(sprite), body, shape)

        # A sprite's body belongs in the space exactly when its physics is
        # running. A body left behind after pause() still collides, which
        # reaches the user as a callback firing for something they stopped.
        if physics._is_paused:
            if id(body) in body_ids:
                violations.append(
                    f"{sprite!r} is paused but its body is still simulated"
                )
        else:
            if id(body) not in body_ids:
                violations.append(
                    f"{sprite!r} has running physics but no body in the space"
                )
            if id(shape) not in shape_ids:
                violations.append(
                    f"{sprite!r} has running physics but no shape in the space"
                )

    # A sprite that left the group must not have left a body behind: that is a
    # phantom collider the user can no longer see or reach.
    for sprite_id, (description, body, _shape) in known.items():
        if sprite_id not in live_ids and id(body) in body_ids:
            violations.append(
                f"{description} was removed but its body is still simulated"
            )

    return violations


@pytest.fixture(autouse=True)
def project_invariants(clean_play_state):
    """Check the frame invariants on every frame of every project test.

    Depends on clean_play_state so it registers after that fixture has reset
    the callback queues, otherwise this watchdog would be cleared before the
    test runs.
    """
    import play

    violations = []
    known = {}

    @play.repeat_forever
    def _watchdog():
        if len(violations) >= MAX_VIOLATIONS:
            return
        try:
            violations.extend(check_frame_invariants(known))
        except Exception as exc:  # pragma: no cover - defensive
            violations.append(f"the invariant check itself raised {exc!r}")

    yield

    assert not violations, "frame invariants broken:\n  " + "\n  ".join(
        violations[:MAX_VIOLATIONS]
    )


def setup_pong(ball_x_speed=300, ball_y_speed=40, ball_obeys_gravity=False):
    """Create the standard pong sprites and start their physics.

    Returns a namespace with: ball, paddle_left, paddle_right, score_text.
    """
    import play

    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)
    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)

    ball.start_physics(
        obeys_gravity=ball_obeys_gravity,
        x_speed=ball_x_speed,
        y_speed=ball_y_speed,
        friction=0,
        mass=10,
        bounciness=1.0,
    )
    paddle_left.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )
    paddle_right.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    return ball, paddle_left, paddle_right, score_text


def add_pong_scoring(
    ball,
    score_left,
    score_right,
    score_text,
    ball_x_speed=300,
    ball_y_speed=40,
    winning_score=1,
    on_score=None,
):
    """Register the standard wall-scoring callbacks on the ball.

    on_score(side) is called after each score (side = "left" or "right")
    but before the win-check, for tests that need extra logic (e.g.
    highscore tracking, serve delays).
    """
    import play
    from play.callback.collision_callbacks import WallSide

    # Returned to the caller rather than stored module-side: this file is
    # importable under two module names, so a module global would exist twice.
    scoring = {"won": False, "score_text": score_text}

    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if on_score:
            on_score("right")
        if score_right[0] >= winning_score:
            scoring["won"] = True
            play.stop_program()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = ball_x_speed
        ball.physics.y_speed = ball_y_speed

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if on_score:
            on_score("left")
        if score_left[0] >= winning_score:
            scoring["won"] = True
            play.stop_program()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = -ball_x_speed
        ball.physics.y_speed = -ball_y_speed

    return scoring


def new_scoring_state(score_text):
    """State for a test that writes its own scoring instead of using the helper.

    Set ``scoring["won"] = True`` just before ``play.stop_program()`` in the
    win branch, then pass this to ``assert_pong_winner``. Without it that
    assertion cannot tell a game that was won from one the safety timeout
    stopped, and both look like a pass.
    """
    return {"won": False, "score_text": score_text}


def add_safety_timeout(max_frames):
    """Register a when_program_starts safety timeout."""
    import play

    @play.when_program_starts
    async def safety_timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()


def assert_pong_winner(score_left, score_right, winning_score, scoring=None):
    """Standard assertions: someone won, and the game ended because of it.

    Without the `won` check these assertions pass identically whether the win
    condition or the safety timeout stopped the program, so a game that never
    progressed still looked like a pass.
    """
    if scoring is not None:
        assert scoring["won"], (
            "the game should have ended because someone reached "
            f"{winning_score}, not because the safety timeout expired "
            f"(scores were {score_left[0]} - {score_right[0]})"
        )
        score_text = scoring["score_text"]
        if score_text is not None:
            expected = f"{score_left[0]} - {score_right[0]}"
            assert (
                score_text.words == expected
            ), f"the scoreboard should read {expected!r}, not {score_text.words!r}"
    total = score_left[0] + score_right[0]
    assert (
        total >= winning_score
    ), f"expected at least {winning_score} total points, got {total}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score, (
        f"expected one player to reach {winning_score}, "
        f"scores were {score_left[0]} - {score_right[0]}"
    )
