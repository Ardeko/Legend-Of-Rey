"""Kare sonrasi parlaklik - oynanisi degistirmez, ekrani ayarlar.

Neden `postfx`'ten AYRI: vinyet ve renk derecelendirmesi bolumun
atmosferi; parlaklik oyuncunun monitoru. Ikisini tek kaydiricida
toplamak Bolum 3'un mesale karanligini da acardi - yanlis katman.
Bu yuzden sahne + postfx tamamen cizildikten SONRA, imlec ve
hata ayiklamadan ONCE uygulanir.

Neden 1.0 atlanir: varsayilan "tasarlandigi gibi". Kaydirici
0.75-1.25 cunku oyun karanlik tasarlandi; bazi ekranlar daha koyu,
bazi oyuncular acmak ister. 0-1 araligi yalnizca KARARTIRDI.

Neden carpma, ekleme degil: `BLEND_RGB_ADD` her piksele ayni
miktari ekler ve siyahlari gri sise cevirir. Gercek parlaklik
carpimdir. pygame'in MULT karistirmasi 1.0'i asamaz; acmak icin
numpy (zaten calisma zamani bagimliligi, CLAUDE.md 4).
"""
from __future__ import annotations

import numpy as np
import pygame

from src.config import (
    BRIGHTNESS_DEFAULT, BRIGHTNESS_MAX, BRIGHTNESS_MIN, BRIGHTNESS_STEP,
    INTERNAL_HEIGHT, INTERNAL_WIDTH,
)

# 1.0'a bu kadar yakinsa "tasarlandigi gibi" - kaydirici adiminin yarisindan
# kucuk, yani bir tik uzakta bile uygulanir.
_IDENTITY = BRIGHTNESS_STEP * 0.25

_overlays: dict[int, pygame.Surface] = {}


def clamp(value: float) -> float:
    """Kayitli eski 0-1 degerlerini de yeni araliga ceker."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return BRIGHTNESS_DEFAULT
    return max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, number))


def clear_cache() -> None:
    """Ekran bicimi degisince `convert()` yuzeyleri bayatlar."""
    _overlays.clear()


def _dim_overlay(level: int) -> pygame.Surface:
    cached = _overlays.get(level)
    if cached is not None:
        return cached
    layer = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
    layer.fill((level, level, level))
    layer = layer.convert()
    _overlays[level] = layer
    return layer


def apply(target: pygame.Surface, brightness: float) -> None:
    """Tuvale parlaklik uygular. 1.0 ise hic dokunmaz."""
    factor = clamp(brightness)
    if abs(factor - BRIGHTNESS_DEFAULT) <= _IDENTITY:
        return
    if factor < BRIGHTNESS_DEFAULT:
        level = max(0, min(255, int(round(factor * 255.0))))
        target.blit(_dim_overlay(level), (0, 0),
                    special_flags=pygame.BLEND_RGB_MULT)
        return
    pixels = pygame.surfarray.pixels3d(target)
    lifted = np.clip(pixels.astype(np.float32) * factor, 0, 255)
    pixels[...] = lifted.astype(np.uint8)
    del pixels
