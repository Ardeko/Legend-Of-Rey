"""Karakterin golgesi sprite'la ucmaz; ayagin altindaki gercek zemine duser.

Yalnizca goruntu: carpisma veya oyuncunun grounded bayragi degismez.
Atlas golgesiz uretilir; botlar ve silahlar kirpilmaz. Sinematikler kendi
zeminlerini yonettigi icin varsayilan atlas golgesini korur.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.world.tilemap import PLATFORM, SOLID_TILES

if TYPE_CHECKING:
    from src.entities.actor import Actor
    from src.world.tilemap import TileMap

MAX_HEIGHT = TILE_SIZE * 4
SHADOW_HEIGHT = 4
SHADOW_MIN_WIDTH = 8
SHADOW_MAX_WIDTH = 32
ALPHA_LEVELS = 16
_cache: dict[tuple[int, int, palette.RGB], pygame.Surface] = {}


def clear_cache() -> None:
    _cache.clear()


def _supports(tilemap: TileMap, column: int, row: int) -> bool:
    """Harita kenarinin gorunmez duvari veya tasin ici zemin sayilmaz."""
    return (0 <= column < tilemap.width and 0 <= row < tilemap.height
            and (tilemap.at(column, row) in SOLID_TILES
                 or tilemap.at(column, row) == PLATFORM)
            and tilemap.at(column, row - 1) not in SOLID_TILES)


def _receiver(actor: Actor) -> tuple[float, float, float] | None:
    """Ayagin altindaki ilk yuzey ve onun yatay sinirlari."""
    body, scene = actor.body, actor.scene
    tilemap = getattr(scene, "tilemap", None)
    if tilemap is None:
        return None
    column = math.floor(body.center_x / TILE_SIZE)
    start = math.ceil((body.bottom - 1.0) / TILE_SIZE)
    for row in range(max(0, start), min(tilemap.height,
                                      start + MAX_HEIGHT // TILE_SIZE + 1)):
        if not _supports(tilemap, column, row):
            continue
        left = right = column
        # En genis golge iki karoyu asmaz; sonsuz zemin taranmaz.
        while left > column - 2 and _supports(tilemap, left - 1, row):
            left -= 1
        while right < column + 2 and _supports(tilemap, right + 1, row):
            right += 1
        return row * TILE_SIZE, left * TILE_SIZE, (right + 1) * TILE_SIZE
    return None


def _image(width: int, level: int) -> pygame.Surface:
    colour = palette.color("ink")
    key = (width, level, colour)
    image = _cache.get(key)
    if image is None:
        image = pygame.Surface((width, SHADOW_HEIGHT), pygame.SRCALPHA)
        # Bir elips: yumusak kenar ve ayagin altinda daha koyu temas.
        pygame.draw.ellipse(image, (*colour, 72 * level // ALPHA_LEVELS),
                            image.get_rect())
        pygame.draw.ellipse(image, (*colour, 128 * level // ALPHA_LEVELS),
                            (2, 1, max(2, width - 4), 2))
        image = image.convert_alpha()
        _cache[key] = image
    return image


def draw(surface: pygame.Surface, actor: Actor, offset: tuple[int, int],
         opacity: float = 1.0) -> None:
    """Yuksekte daralan/solan golge; cukurun ustune piksel tasmaz."""
    if opacity <= 0.0:
        return
    receiver = _receiver(actor)
    if receiver is None:
        return
    ground, left, right = receiver
    height = max(0.0, ground - actor.body.bottom)
    if height >= MAX_HEIGHT:
        return
    strength = 1.0 - height / MAX_HEIGHT
    level = round(ALPHA_LEVELS * strength * strength * min(1.0, opacity))
    if level <= 0:
        return
    width = max(SHADOW_MIN_WIDTH, min(SHADOW_MAX_WIDTH,
                round(actor.body.width * (1.25 - 0.35 * height / MAX_HEIGHT))))
    image = _image(width, level)
    world_x = round(actor.body.center_x) - width // 2
    clip_left = max(0, round(left - world_x))
    clip_right = min(width, round(right - world_x))
    ox, oy = offset
    surface.blit(image, (world_x + clip_left - ox, round(ground) - 1 - oy),
                 (clip_left, 0, clip_right - clip_left, SHADOW_HEIGHT))
