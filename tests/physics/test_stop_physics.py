import play


def _y_per_frame(ball, frames, stop_at):
    """The ball's rounded y per frame, stopping its physics at frame *stop_at*."""
    y_values = [round(ball.y)]
    counted = [0]

    @play.repeat_forever
    def record():
        counted[0] += 1
        y_values.append(round(ball.y))
        if counted[0] == stop_at:
            ball.stop_physics()
        if counted[0] == frames:
            play.stop_program()

    play.start_program()
    return y_values


def test_a_moving_sprite_stops_where_it_is_when_physics_stops():
    ball = play.new_circle(color="gray", radius=50)
    ball.start_physics(y_speed=60, obeys_gravity=False)

    y_values = _y_per_frame(ball, 75, stop_at=25)

    assert y_values == list(range(26)) + [25] * 50


def test_a_falling_sprite_stays_in_the_air_once_physics_stops():
    ball = play.new_circle(y=100, radius=50)
    ball.start_physics(obeys_gravity=True)

    y_values = _y_per_frame(ball, 60, stop_at=30)

    assert y_values[31] < 90
    assert y_values[31:] == [y_values[31]] * 30
