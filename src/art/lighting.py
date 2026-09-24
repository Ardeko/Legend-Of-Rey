"""Bolum 3'un karanlik/isik katmani.

`docs/bolum-03.md` "Uygulama Notlari" bunu tarif ediyor ama kod tabaninda
hic karsiligi yoktu: **tek bir karartma yuzeyinde toplanan isik maskesi**,
her kaynak `BLEND_RGBA_SUB` ile ayni yuzeye islenir - kaynak basina ayri
gecis yok. `PlayScene.draw_foreground()` kancasindan cagrilir (aktorlerden
sonra, HUD'dan once): dunya karariyor ama arayuz her zaman tam parlaklikta
okunur.

Karanlik ≠ siyah: paletin en koyu rengi kullanilir (zaten sogukca), ve tam
opak degil - `DARKNESS_SILHOUETTE_ALPHA` kadar siluetler karanlikta bile
hafifce sizar (oyuncu tamamen kor olmasin).

`radial_glow` (art/glow.py) ile karistirilmasin: o RGB'yi **ekliyordu**
(BLEND_RGB_ADD, isik halesi ustuste bindirme). Burasi tam tersi - alfayi
**siliyor** (BLEND_RGBA_SUB, karanligi deliyor).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pygame

from src.art import palette
from src.config import DARKNESS_SILHOUETTE_ALPHA
from src.systems.light import LightState

_DARK_NAME = palette.darkest_names(1)[0]
_masks: dict[tuple[int, int], pygame.Surface] = {}


def clear_cache() -> None:
    _hole.cache_clear()
    _masks.clear()


@lru_cache(maxsize=32)
def _hole(radius: int) -> pygame.Surface:
    """Merkezde tam delik (alfa 0), kenarda tam karanlik (alfa 255).

    Yaricap kucuk bir tam sayi kumesinden geldigi icin (mesale/Mor Alev/
    mangal - hepsi sabit birkac deger) `lru_cache` her kareyi yeniden
    hesaplamayi onluyor.
    """
    radius = max(1, radius)
    size = radius * 2
    yy, xx = np.ogrid[:size, :size]
    distance = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    # Eski karesel egri, mesale yaricapinin ortasini bile karartiyordu.
    # Aydinlik cekirdek + yumusak kenar gorusu gercek yaricapa yaklastirir.
    edge = np.clip((distance - 0.30) / 0.70, 0.0, 1.0)
    falloff = 1.0 - edge * edge * (3.0 - 2.0 * edge)

    hole = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.surfarray.pixels_alpha(hole)[:, :] = (falloff * 255).astype(np.uint8)
    return hole.convert_alpha()


def render(surface: pygame.Surface, offset: tuple[int, int],
           light: LightState, visibility: float = DARKNESS_SILHOUETTE_ALPHA) -> None:
    """Karanlik maskesini olusturup `surface` uzerine isler.

    B3 ve B13 kullanir. Kaynak yokken de karanlik uygulanir; oyuncu
    zemin ve tehlike siluetlerini secebilir. LightState'in oynanis
    sorgulari degismez: golge dusmani aydinlatmak hala mesale ister.
    """
    ox, oy = offset
    width, height = surface.get_size()
    size = (width, height)
    mask = _masks.get(size)
    if mask is None:
        mask = pygame.Surface(size, pygame.SRCALPHA).convert_alpha()
        _masks[size] = mask
    dark_alpha = int(255 * (1.0 - max(0.0, min(1.0, visibility))))
    mask.fill((*palette.color(_DARK_NAME), dark_alpha))

    for source in light.all_sources():
        radius = int(source.radius)
        if radius <= 0:
            continue
        hole = _hole(radius)
        mask.blit(hole, (int(source.x - ox - radius), int(source.y - oy - radius)),
                  special_flags=pygame.BLEND_RGBA_SUB)

    surface.blit(mask, (0, 0))
