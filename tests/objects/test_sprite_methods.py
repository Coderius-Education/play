"""Tests for sprite methods: distance_to, is_touching, and the plain Sprite."""

import pygame
import pytest

import play
from play.objects.sprite import Sprite


def test_distance_to_a_point():
    sprite = play.new_box(x=10, y=0)

    assert sprite.distance_to(13, 4) == 5.0
    assert sprite.distance_to(10, 0) == 0.0


def test_distance_to_a_sprite_is_the_same_both_ways():
    box = play.new_box(x=10, y=0)
    circle = play.new_circle(x=13, y=4)

    assert box.distance_to(circle) == 5.0
    assert circle.distance_to(box) == 5.0


def test_distance_to_a_number_without_y_explains_what_is_missing():
    sprite = play.new_box()

    with pytest.raises(ValueError, match="requires a y argument"):
        sprite.distance_to(30)


def test_sprites_that_overlap_are_touching_and_far_apart_ones_are_not():
    box = play.new_box(x=0, y=0, width=50, height=50)
    near = play.new_box(x=40, y=0, width=50, height=50)
    far = play.new_box(x=300, y=300, width=50, height=50)

    assert box.is_touching(near)
    assert near.is_touching(box)
    assert not box.is_touching(far)


def test_a_plain_sprite_gets_the_defaults():
    sprite = Sprite(x=12, y=-5)

    assert (sprite.x, sprite.y) == (12, -5)
    assert sprite.angle == 0
    assert sprite.transparency == 100
    assert sprite.is_hidden is False


def test_a_plain_sprite_clones_with_its_picture():
    picture = pygame.Surface((10, 10))
    sprite = Sprite(image=picture)

    clone = sprite.clone()

    assert clone is not sprite
    assert clone.image is picture


def test_changing_a_sprite_redraws_the_sprites_that_watch_it():
    watcher = play.new_box()
    target = play.new_box()
    watcher.when_touching(target)(lambda: None)
    watcher._should_recompute = False

    target.x = 50

    assert watcher._should_recompute is True
