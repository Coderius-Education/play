"""What info() and physics_info() print for a student."""

import pytest

import play
from play.objects.sprite import Sprite


def test_info_describes_a_box(capsys):
    play.new_box(color="blue", width=100, height=50).info()

    assert capsys.readouterr().out == (
        "Hi, I'm a Box!\n"
        "  Color: blue\n"
        "  Position: x=0, y=0\n"
        "  Size: width=100, height=50\n"
        "  Angle: 0°\n"
    )


def test_info_gives_a_circle_its_radius(capsys):
    play.new_circle(color="red", radius=25, x=10, y=-20, angle=30).info()

    assert capsys.readouterr().out == (
        "Hi, I'm a Circle!\n"
        "  Color: red\n"
        "  Position: x=10, y=-20\n"
        "  Size: radius=25\n"
        "  Angle: 30°\n"
    )


def test_info_says_when_a_sprite_is_hidden(capsys):
    box = play.new_box()
    box.hide()

    box.info()

    assert capsys.readouterr().out.splitlines()[-1] == "  Angle: 0° (hidden)"


def test_info_on_a_sprite_without_a_colour_says_unknown(capsys):
    Sprite().info()

    assert "  Color: unknown\n" in capsys.readouterr().out


COLLIDES_WITH_ALL = (
    "  ✓ Collides with DYNAMIC (VRIJ)\n"
    "  ✓ Collides with KINEMATIC (GESTUURD)\n"
    "  ✓ Collides with STATIC (VAST)\n"
)
COLLIDES_WITH_DYNAMIC_ONLY = (
    "  ✓ Collides with DYNAMIC (VRIJ)\n"
    "  ✗ Passes through KINEMATIC (GESTUURD)\n"
    "  ✗ Passes through STATIC (VAST)\n"
)


@pytest.mark.parametrize(
    "physics, heading, settings, collisions",
    [
        (
            {"can_move": True, "stable": False},
            "Physics: DYNAMIC (VRIJ)",
            "can_move=True,stable=False,obeys_gravity=True",
            COLLIDES_WITH_ALL,
        ),
        (
            {"can_move": True, "stable": True, "obeys_gravity": False},
            "Physics: KINEMATIC (GESTUURD)",
            "can_move=True,stable=True,obeys_gravity=False",
            COLLIDES_WITH_DYNAMIC_ONLY,
        ),
        (
            {"can_move": False},
            "Physics: STATIC (VAST)",
            "can_move=False,stable=False,obeys_gravity=True",
            COLLIDES_WITH_DYNAMIC_ONLY,
        ),
    ],
    ids=["dynamic", "kinematic", "static"],
)
def test_physics_info_names_the_body_type_and_what_it_collides_with(
    capsys, physics, heading, settings, collisions
):
    box = play.new_box()
    box.start_physics(bounciness=0.5, mass=4, **physics)

    box.physics_info()

    assert capsys.readouterr().out == (
        f"{heading}\n"
        f"{settings}\n"
        "  Speed: x=0, y=0\n"
        "  Mass: 4, Bounciness: 0.5\n"
        "\n"
        "Collision behavior:\n" + collisions
    )


def test_physics_info_after_stop_physics_shows_the_starting_body(capsys):
    box = play.new_box()
    box.start_physics(can_move=True, stable=False)

    box.stop_physics()
    box.physics_info()

    assert capsys.readouterr().out.startswith(
        "Physics: KINEMATIC (GESTUURD)\n"
        "can_move=True,stable=True,obeys_gravity=False\n"
    )
