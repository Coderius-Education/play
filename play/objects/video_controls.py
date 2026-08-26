"""Drawing of the built-in control bar shown on top of a Video.

Kept apart from the Video object itself so that the playback logic and the
look of the controls stay easy to read on their own.
"""

import pygame


def _format_time(seconds):
    """Format seconds as m:ss, the way a video player shows it."""
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def _font(video):
    player = video._player
    if player.font is None:
        try:
            if not pygame.font.get_init():
                pygame.font.init()
            player.font = pygame.font.SysFont(None, max(11, video._bar_height() // 3))
        except Exception:  # pylint: disable=broad-except  # pragma: no cover
            player.font = False
    return player.font or None


def _played_fraction(video):
    """How far through the video playback is, from 0.0 to 1.0.

    Clamped because a video whose file carries no duration reports a length of
    zero and runs its clock on regardless, which would otherwise divide by the
    1e-6 floor and produce a number in the tens of thousands.
    """
    return min(max(video.time / max(video.length, 1e-6), 0.0), 1.0)


def _controls_state(video):
    """A small key describing how the control bar should look right now.

    Re-rendering only when this changes keeps the bar cheap to draw.
    """
    player = video._player
    return (
        int(player.controls_alpha),
        player.state == "playing",
        int(video.time),
        round(_played_fraction(video), 3),
        player.muted,
        round(player.volume, 2),
        video._width,
        video._height,
    )


def _track_y(bar_h):
    """The height of the slider line, leaving room for the time underneath."""
    return max(2, int(bar_h * 0.36))


def render(video):
    """Draw the control bar onto its own see-through surface."""
    key = _controls_state(video)
    player = video._player
    if key == player.controls_key and player.controls_surface is not None:
        return player.controls_surface

    bar_h = video._bar_height()
    surface = pygame.Surface((video._width, bar_h), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 150))

    _draw_play_button(video, surface, bar_h)
    _draw_scrubber(video, surface, bar_h)
    _draw_volume(video, surface, bar_h)
    _draw_time(video, surface, bar_h)

    surface.set_alpha(int(player.controls_alpha))
    player.controls_surface = surface
    player.controls_key = key
    return surface


def _draw_play_button(video, surface, bar_h):
    pad = max(3, bar_h // 4)
    inner = bar_h - 2 * pad
    if video._player.state == "playing":
        bar_w = max(2, inner // 3)
        pygame.draw.rect(surface, (255, 255, 255), (pad, pad, bar_w, inner))
        pygame.draw.rect(
            surface, (255, 255, 255), (bar_h - pad - bar_w, pad, bar_w, inner)
        )
    else:
        pygame.draw.polygon(
            surface,
            (255, 255, 255),
            [(pad, pad), (pad, pad + inner), (pad + inner, pad + inner // 2)],
        )


def _draw_scrubber(video, surface, bar_h):
    area = video._scrub_area()
    left, width = area.left, area.width
    mid = _track_y(bar_h)
    track_h = max(2, bar_h // 12)
    pygame.draw.rect(
        surface, (120, 120, 120), (left, mid - track_h // 2, width, track_h)
    )
    fraction = _played_fraction(video)
    pygame.draw.rect(
        surface,
        (230, 60, 60),
        (left, mid - track_h // 2, int(width * fraction), track_h),
    )
    pygame.draw.circle(
        surface,
        (255, 255, 255),
        (left + int(width * fraction), mid),
        max(3, bar_h // 6),
    )


def _draw_volume(video, surface, bar_h):
    if not video._volume_width():
        return
    mute = video._mute_area()
    mid = _track_y(bar_h)
    size = max(3, bar_h // 5)
    pygame.draw.polygon(
        surface,
        (255, 255, 255),
        [
            (mute.left + 4, mid - size // 2),
            (mute.left + 4 + size, mid - size),
            (mute.left + 4 + size, mid + size),
            (mute.left + 4, mid + size // 2),
        ],
    )
    if video._player.muted:
        pygame.draw.line(
            surface,
            (255, 80, 80),
            (mute.left + 4, mid + size),
            (mute.left + 4 + size + 4, mid - size),
            2,
        )

    area = video._volume_area()
    track_h = max(2, bar_h // 12)
    pygame.draw.rect(
        surface,
        (120, 120, 120),
        (area.left, mid - track_h // 2, area.width, track_h),
    )
    level = 0.0 if video._player.muted else video._player.volume
    pygame.draw.rect(
        surface,
        (255, 255, 255),
        (area.left, mid - track_h // 2, int(area.width * level), track_h),
    )


def _draw_time(video, surface, bar_h):
    font = _font(video)
    if font is None or video._width < 150:
        return
    label = f"{_format_time(video.time)} / {_format_time(video.length)}"
    text = font.render(label, True, (255, 255, 255))
    area = video._scrub_area()
    top = min(_track_y(bar_h) + max(4, bar_h // 8), bar_h - text.get_height())
    surface.blit(text, (area.left, top))
