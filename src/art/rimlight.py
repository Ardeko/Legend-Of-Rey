"""Ortam kenar isigi - derinde karakterlerin golge kenari ortamin rengini alir.

Arda, 24.09.2026: *"grafikleri daha modern gercekci olarak gelistir."*

Gercekci isikta bir karakterin golge yani siyah degil, cevrenin rengini
alir: lav golunun ustunde kizil, kristal magarasinda mor. Modern piksel
sanatta buna "secici kontur" / "kenar isigi" deniyor. Burada tek piksellik
bir serit, sprite'in **sag** (golge) kenarina ekleniyor - ana isik her
zaman sol ustten (`CLAUDE.md` 6), yani kenar isigi onun karsisinda.

    derinlik < 0.45   yok     (ust katlar: klasik gorunum)
    0.45 - 0.75       mor     (kristal, Yanki)
    0.75+             kor     (lav)

**Eklemeli** (`BLEND_RGB_ADD`): kontur yerinde kaliyor, ustune isik
biniyor. Konturu boyamak stil sozlesmesini degistirirdi; eklemek yalnizca
isik ekliyor.

Ayrica bir okunurluk kazanci: koyu mor/kizil fonda karakterin sag kenari
artik fondan ayriliyor (Arda'nin 19.09 karanlik geri bildirimi).

## Onbellek

Maske islemi her kare goruntusu icin **bir kez** (Animator kareleri
kalici yuzeyler). Anahtar `id(image)` + kimlik kontrolu: ayni id'nin
baska bir yuzeye gecmesi sessizce yanlis kenar cizdirmesin.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.glow import rim_light

_CACHE_LIMIT = 800
_cache: dict[int, tuple[pygame.Surface, dict[tuple[str, int], pygame.Surface | None]]] = {}


def clear_cache() -> None:
    _cache.clear()


def for_depth(depth: float) -> tuple[str, float] | None:
    """Derinlikten (renk adi, guc). Ust katlarda `None`."""
    if depth >= 0.75:
        return ("ember", 0.6)
    if depth >= 0.45:
        return ("violet", 0.5)
    return None


def _rim(image: pygame.Surface, colour: str, level: int) -> pygame.Surface | None:
    entry = _cache.get(id(image))
    if entry is None or entry[0] is not image:
        if len(_cache) >= _CACHE_LIMIT:
            _cache.clear()
        entry = (image, {})
        _cache[id(image)] = entry
    key = (colour, level)
    if key not in entry[1]:
        rim = rim_light(image, palette.color(colour), 1, strength=level / 10.0)
        if rim is not None and pygame.display.get_init() \
                and pygame.display.get_surface() is not None:
            rim = rim.convert_alpha()
        entry[1][key] = rim
    return entry[1][key]


def draw(surface: pygame.Surface, image: pygame.Surface,
         position: tuple[int, int], light: tuple[str, float] | None,
         foot_row: int | None = None) -> None:
    """`image`in `position`a cizilmis haline kenar isigi ekler.

    `foot_row`: sprite icindeki ayak cizgisi. Altindaki satirlar (yerdeki
    golge elipsi) isik almiyor - golge bir yuzey degil.
    """
    if light is None:
        return
    colour, strength = light
    rim = _rim(image, colour, max(1, min(10, round(strength * 10))))
    if rim is None:
        return
    area = None
    if foot_row is not None:
        area = pygame.Rect(0, 0, rim.get_width(), max(0, foot_row - 1))
    surface.blit(rim, position, area, special_flags=pygame.BLEND_RGB_ADD)
