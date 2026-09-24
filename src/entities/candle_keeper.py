"""Mum Bekcisi - konusmayan, savasmayan, ticaret yapan varlik.

`docs/bolum-03.md` Oda 3-A: *"Hollow Knight dersi - dusmanca bir dunyada
dusman olmayan varliklar, yalnizligi azaltmaz, derinlestirir."*

Bilinclu olarak `Actor`'dan turemiyor: can, hasar, durum makinesi hicbirine
ihtiyaci yok. Bir "sey" degil "biri" hissi vermesi gereken, saldirilamayan
bir sahne parcasi - vurus onun icinden gecer, hicbir sey olmaz (sahne
tarafinda hitbox hedefi olarak hic eklenmiyor).

Gozleri sprite degil: iki parcacik emitoru, kod ile uretilip titretiliyor
(docs'un actikca istedigi sey). `cave_backdrop`'un deterministik
hash+sinus deseniyle ayni ruh - `random` yok, ayni kare hep ayni titremeyi
verir.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow

BODY_WIDTH = 12
BODY_HEIGHT = 20

# --- Sprite (23.09.2026) -----------------------------------------------------
# Ilk surum iki dikdortgendi ve karanlik bolumlerde bir "kutu" gibi
# okunuyordu; gezgin dukkan olunca oyuncunun onu **uzaktan** tanimasi
# gerekti. Belgedeki tarif (`docs/bolum-03.md` Oda 3-A) harfiyen:
#
#     insan silueti, yuzu yok      kukuleta ici bos, iki alev goz
#     onunde bir tabak             altin sikkeli sig bir kap
#     biraz daha az mumla          `candles` - her gorunuste bir eksik
#
# Cuppe mor: B3'un Mor Alev'i onun odasinda. Sol-ust isik kurali:
# sol kenar ve kukuleta tepesi acik, sag kenar golgede.
SPRITE_W = 40
SPRITE_H = 26
ANCHOR_X = 13                    # govde merkezi, sprite icinde
DEFAULT_CANDLES = 5

# Her satir: (y, sol, sag) dahil. Oturan, one egik bir figur - kukuleta
# ucu hafifce ileri (saga) dusuyor.
_SILHOUETTE = (
    (0, 13, 14), (1, 12, 15), (2, 11, 16), (3, 10, 16), (4, 9, 17),
    (5, 9, 17), (6, 8, 17), (7, 8, 18), (8, 8, 18), (9, 7, 19),
    (10, 7, 19), (11, 6, 19), (12, 6, 20), (13, 6, 20), (14, 5, 20),
    (15, 5, 21), (16, 5, 21), (17, 4, 21), (18, 4, 21), (19, 4, 22),
    (20, 4, 22), (21, 3, 22), (22, 3, 23), (23, 3, 23), (24, 3, 23),
    (25, 3, 23),
)
# Kukuletanin ici - bos yuz.
_HOOD_VOID = ((4, 12, 15), (5, 11, 15), (6, 11, 16), (7, 11, 16),
              (8, 12, 15))
EYE_ROW = 6
EYES_X = (12, 15)
# Tabak: govdenin saginda, yerde.
PLATE_X, PLATE_Y, PLATE_W = 25, 23, 11
# Mumlarin yerleri (x, fitil yuksekligi) - soldan saga azaliyor.
_CANDLE_SPOTS = ((1, 7), (37, 6), (23, 5), (38, 4), (2, 4))

_body_cache: dict[int, pygame.Surface] = {}


def clear_cache() -> None:
    _body_cache.clear()


def _glow(radius: int, colour_name: str, peak: float) -> pygame.Surface:
    # `radial_glow` kendi onbellegini tutuyor (`src/art/glow.py`).
    return radial_glow(radius, palette.color(colour_name), peak=peak)


def _span_fill(surface: pygame.Surface, spans, colour) -> None:
    for y, x0, x1 in spans:
        surface.fill(colour, (x0, y, x1 - x0 + 1, 1))


def _build_body(candles: int) -> pygame.Surface:
    """Durağan kisim - **bir kez** uretilir (`CLAUDE.md` 4)."""
    image = pygame.Surface((SPRITE_W, SPRITE_H), pygame.SRCALPHA)
    outline = palette.color("ink")
    robe = palette.color("violet_dark")
    lit = palette.color("violet")
    shade = palette.color("ink_soft")
    # Kontur: silueti bir piksel sisirip koyu renkle bas.
    grown = [(y, x0 - 1, x1 + 1) for y, x0, x1 in _SILHOUETTE]
    _span_fill(image, grown, outline)
    image.fill(outline, (12, 0, 4, 1))
    _span_fill(image, _SILHOUETTE[1:], robe)
    for y, x0, x1 in _SILHOUETTE[1:]:
        image.fill(lit, (x0, y, 1, 1))                   # sol kenar isik
        image.fill(shade, (x1 - 1, y, 2, 1))             # sag kenar golge
    image.fill(lit, (12, 1, 3, 1))                        # kukuleta tepesi
    # Kivrimlar - cuppe kumas gibi okunsun, blok gibi degil.
    for x, y0 in ((9, 14), (13, 12), (17, 16)):
        image.fill(shade, (x, y0, 1, SPRITE_H - y0 - 1))
    # Kol: tabaga uzanan yen.
    image.fill(robe, (18, 15, 5, 2))
    image.fill(lit, (18, 15, 5, 1))
    image.fill(outline, (23, 15, 1, 2))
    _span_fill(image, _HOOD_VOID, palette.color("void"))
    _draw_plate(image)
    for index in range(min(candles, len(_CANDLE_SPOTS))):
        x, height = _CANDLE_SPOTS[index]
        _draw_candle_stick(image, x, height)
    if pygame.display.get_init() and pygame.display.get_surface() is not None:
        return image.convert_alpha()
    return image


def _draw_plate(image: pygame.Surface) -> None:
    """Sig kap ve icinde uc sikke - "altin koy, al" (belge)."""
    rim = palette.color("stone_light")
    base = palette.color("stone")
    image.fill(palette.color("ink"), (PLATE_X - 1, PLATE_Y, PLATE_W + 2, 3))
    image.fill(base, (PLATE_X, PLATE_Y + 1, PLATE_W, 1))
    image.fill(rim, (PLATE_X, PLATE_Y, PLATE_W, 1))
    image.fill(palette.color("stone_dark"), (PLATE_X + 1, PLATE_Y + 2, PLATE_W - 2, 1))
    for cx in (PLATE_X + 3, PLATE_X + 5, PLATE_X + 7):
        image.fill(palette.color("gold"), (cx, PLATE_Y - 1, 2, 1))
    image.fill(palette.color("ember_light"), (PLATE_X + 4, PLATE_Y - 2, 2, 1))


def _draw_candle_stick(image: pygame.Surface, x: int, height: int) -> None:
    top = SPRITE_H - height
    image.fill(palette.color("ink"), (x - 1, top - 1, 3, height + 1))
    image.fill(palette.color("bone"), (x, top, 1, height))
    image.fill(palette.color("stone_light"), (x, top + height - 1, 1, 1))


def body_image(candles: int) -> pygame.Surface:
    image = _body_cache.get(candles)
    if image is None:
        image = _build_body(candles)
        _body_cache[candles] = image
    return image


class CandleKeeper:
    """Pasif NPC. Ticaret sahne tarafindan yonetilir (`merchant.py`)."""

    __slots__ = ("x", "feet_y", "frame", "candles", "lit", "fade")

    def __init__(self, x: float, feet_y: float,
                 candles: int = DEFAULT_CANDLES) -> None:
        self.x = x
        self.feet_y = feet_y
        self.frame = 0
        self.candles = max(0, min(len(_CANDLE_SPOTS), candles))
        # Yanan mum sayisi - mumun **cubugu** kalir, alevi soner
        # (epilog: son mumu kendisi sonduruyor). Kayboluş: `fade` 1 -> 0.
        self.lit = self.candles
        self.fade = 1.0

    def candle_point(self, index: int = 0) -> tuple[float, float]:
        """Bir mumun alevinin dunya konumu - sonme dumani oradan cikar."""
        x, height = _CANDLE_SPOTS[index]
        return (self.x - ANCHOR_X + x,
                self.feet_y - height - 2)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - BODY_WIDTH // 2 - 4),
                           int(self.feet_y - BODY_HEIGHT - 4),
                           BODY_WIDTH + 8, BODY_HEIGHT + 8)

    def update(self) -> None:
        self.frame += 1

    # --- Cizim ----------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if self.fade <= 0.0:
            return
        ox, oy = offset
        left = int(self.x) - ox - ANCHOR_X
        top = int(self.feet_y) - oy - SPRITE_H
        body = body_image(self.candles)
        if self.fade < 1.0:
            # Kayboluyor: karanliga karisir gibi. Kopya kucuk (40x26) ve
            # yalnizca kayboluşun ~1 saniyesinde uretiliyor.
            body = body.copy()
            body.set_alpha(int(255 * self.fade))
        # Golge: karakterin altinda tek elips (`CLAUDE.md` 6).
        if self.fade > 0.5:
            pygame.draw.ellipse(surface, palette.color("ink"),
                                (left + 2, top + SPRITE_H - 2, 24, 4))
        surface.blit(body, (left, top))
        self._draw_flames(surface, left, top)
        self._draw_eyes(surface, left, top + EYE_ROW)

    def _draw_flames(self, surface: pygame.Surface, left: int, top: int) -> None:
        """Mum alevleri - 8 FPS adimli titreme, `random` yok."""
        step = self.frame // 8
        for index in range(min(self.lit, self.candles)):
            x, height = _CANDLE_SPOTS[index]
            fx = left + x
            fy = top + SPRITE_H - height - 2
            lean = (step + index) % 3 - 1 if (step + index) % 4 == 0 else 0
            surface.fill(palette.color("ember"), (fx + lean, fy, 1, 2))
            surface.fill(palette.color("gold"), (fx, fy + 1, 1, 1))
            surface.blit(_glow(6, "ember_dark", 0.55), (fx - 6, fy - 5),
                         special_flags=pygame.BLEND_RGB_ADD)

    def _draw_eyes(self, surface: pygame.Surface, left: int, eye_y: int) -> None:
        """Iki titreyen mum alevi - sprite degil, kod uretimi (belge)."""
        for side, ex in zip((-1, 1), EYES_X):
            jitter = math.sin(self.frame * 0.22 + side * 1.7) * 0.6
            x = left + ex
            y = int(eye_y + jitter)
            if self.fade > 0.3:
                surface.fill(palette.color("gold"), (x, y, 1, 1))
            peak = (0.5 + 0.1 * math.sin(self.frame * 0.3 + side)) * self.fade
            glow = _glow(7, "ember", peak)
            surface.blit(glow, (x - 7, y - 7), special_flags=pygame.BLEND_RGB_ADD)
