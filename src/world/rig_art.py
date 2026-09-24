"""Inis kafesinin ray, zincir, makara ve fren cizimi."""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.world.rig import Rig

CAGE_HEIGHT = 58
LINK_SPACING = 7


def draw_rails(surface: pygame.Surface, offset: tuple[int, int], rig: Rig) -> None:
    ox, oy = offset
    for side in (round(rig.left) - 7 - ox, round(rig.right) + 5 - ox):
        surface.fill(palette.color("ink"), (side - 2, 0, 7, surface.get_height()))
        surface.fill(palette.color("stone_dark"), (side, 0, 3, surface.get_height()))
        surface.fill(palette.color("stone"), (side, 0, 1, surface.get_height()))
        for world_y in range((oy // 48) * 48, oy + surface.get_height(), 48):
            y = world_y - oy
            surface.fill(palette.color("stone_darkest"), (side - 4, y, 11, 5))
            for dx in (-3, 4):
                surface.set_at((side + dx, y + 1), palette.color("stone_light"))


def _wheel(surface: pygame.Surface, x: int, y: int, turn: float) -> None:
    pygame.draw.circle(surface, palette.color("ink"), (x, y), 7)
    pygame.draw.circle(surface, palette.color("stone"), (x, y), 6, 2)
    for spoke in range(4):
        angle = turn + spoke * math.pi / 2
        end = (x + round(math.cos(angle) * 4), y + round(math.sin(angle) * 4))
        pygame.draw.line(surface, palette.color("stone_light"), (x, y), end)
    surface.set_at((x, y), palette.color("gold"))


def draw(surface: pygame.Surface, offset: tuple[int, int], rig: Rig, frame: int) -> None:
    ox, oy = offset
    left, top = round(rig.left) - ox, round(rig.y) - oy
    width = round(rig.width)
    roof = top - CAGE_HEIGHT
    if top < -12 or roof > surface.get_height() + 12:
        return
    # Zincirler tavana kadar surer; gorunmeyen 400 piksel cizilmez.
    for side in (left + 3, left + width - 4):
        for y in range(-(round(rig.y) % LINK_SPACING), max(0, roof), LINK_SPACING):
            pygame.draw.rect(surface, palette.color("stone"), (side - 1, y, 3, 5), 1)
            surface.set_at((side - 1, y + 1), palette.color("stone_light"))
        _wheel(surface, side, roof + 2, rig.y / 11)
    surface.fill(palette.color("stone_darkest"), (left - 3, roof + 7, width + 6, 5))
    surface.fill(palette.color("stone_light"), (left - 3, roof + 7, width + 6, 1))
    for post in (left, left + width - 3):
        surface.fill(palette.color("ink"), (post - 1, roof + 12, 5, CAGE_HEIGHT - 5))
        surface.fill(palette.color("stone"), (post, roof + 12, 2, CAGE_HEIGHT - 5))
        for y in (roof + 15, top - 4):
            surface.set_at((post, y), palette.color("gold"))
    # Kalin kirisin ustunde ayri tahtalar; basinilan yuzey gercek y'de.
    surface.fill(palette.color("earth_dark"), (left - 2, top, width + 4, 8))
    for x in range(left, left + width, 10):
        surface.fill(palette.color("earth"), (x, top, 9, 4))
        surface.fill(palette.color("flesh"), (x, top, 8, 1))
        surface.set_at((x + 2, top + 2), palette.color("ink"))
    surface.fill(palette.color("stone_dark"), (left - 2, top + 6, width + 4, 3))
    pygame.draw.lines(surface, palette.color("stone"), False,
                      ((left + 4, top + 9), (left + width // 2, top + 17),
                       (left + width - 4, top + 9)), 2)
    # Bel hizasinda acik korkuluk: yuzu/ust govdeyi ortmez.
    surface.fill(palette.color("stone_dark"), (left + 2, top - 12, width - 4, 2))
    pivot = (left + 13, top - 15)
    handle = (pivot[0] + (8 if rig.braking else -5), pivot[1] - 9)
    pygame.draw.line(surface, palette.color("stone_light"), pivot, handle, 2)
    pygame.draw.circle(surface, palette.color("gold" if rig.braking else "earth"), handle, 2)
    if rig.braking and rig.speed > 0.05:
        for side in (left - 3, left + width + 2):
            reach = 2 + frame % 3
            pygame.draw.line(surface, palette.color("ember_light"),
                             (side, top + 3), (side + reach, top + 6), 1)
