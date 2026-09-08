"""Hayalet - `docs/korku.md` 5.3, "Zindan Hatirliyor".

Oldugun yerde bir hayalet kalir ve **yalnizca Yanki acikken** gorunur.

## Son anini TEKRAR OYNAMIYOR

`docs/derinlestirme.md` 3.4 Hollow Knight'in Shade'i gibi "son anlarini
tekrar oynar" diyordu. Uygulamada reddedildi: tekrar oynayan bir
hayalet bir **kayit** olur, izlenir ve gecilir.

Bunun yerine hayalet hicbir sey yapmiyor. Duruyor. Sen odaya girince
basini cevirip **seni izliyor.**

Fark su: bir kayit sana gecmisi gosterir, bakan bir sey sana kendini
gosterir. Ikincisi rahatsiz edici olan.

## Neden dovusmuyor, neden altin vermiyor

Ikisi de `derinlestirme.md`de vardi. Ikisi de eklenmedi cunku ikisi de
hayaleti bir **sisteme** cevirir: dovusulen sey dusman, altin veren sey
odul. Hayalet ne dusman ne odul - bir hatirlatma.

## Yanki acikken gorunmesi bedelin bir parcasi

Yanki'yi acmanin bedeli zaten var (ekran kararir, hasar artar). Buna
bir tane daha ekleniyor: **gormek istemedigin seyi de goruyorsun.**
Kapaliyken hayalet yok; oyuncu onu gormemeyi secebiliyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.systems import horror

FADE_FRAMES = 30
# Bu mesafede oyuncu hayaleti "fark etmis" sayiliyor - ses bir kez.
NOTICE_RANGE = 150.0


class Ghost:
    """Oldugun yerde kalan sey. Sahne tutar, olum sonrasi tasinir."""

    __slots__ = ("x", "feet_y", "width", "height", "facing", "fade",
                 "noticed", "_bob")

    def __init__(self, x: float, feet_y: float,
                 width: int = 10, height: int = 22) -> None:
        self.x = float(x)
        self.feet_y = float(feet_y)
        self.width = width
        self.height = height
        self.facing = -1
        self.fade = 0.0
        self.noticed = False
        self._bob = 0.0

    # --- Dongu --------------------------------------------------------------
    def update(self, game, scene) -> None:
        echo = getattr(scene, "echo", None)
        visible = (echo is not None and echo.active
                   and horror.atmosphere(game.settings))

        step = 1.0 / FADE_FRAMES
        self.fade = max(0.0, min(1.0, self.fade + (step if visible else -step)))
        self._bob += 0.024

        player = getattr(scene, "player", None)
        if player is None or not visible:
            return
        # **Seni izliyor.** Govde durur, bakis doner.
        self.facing = 1 if player.body.center_x > self.x else -1

        if not self.noticed:
            distance = abs(player.body.center_x - self.x)
            if distance < NOTICE_RANGE and self.fade > 0.5:
                self.noticed = True
                game.play_sound("ghost_seen", bus="volume_echo",
                                volume=horror.loudness(game.settings))

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if self.fade <= 0.02:
            return
        ox, oy = offset
        drift = math.sin(self._bob) * 1.2
        x = int(self.x - self.width * 0.5) - ox
        y = int(self.feet_y - self.height + drift) - oy

        colour = palette.color("violet")
        body = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        body.fill((*colour, int(150 * self.fade)))
        # Iki goz - baktigi yon govdeden okunmuyor, gozlerden okunuyor.
        eye = palette.color("violet_bright")
        eye_y = 3
        near = 2 if self.facing > 0 else self.width - 4
        far = near + (2 if self.facing > 0 else -2)
        for ex in (near, far):
            if 0 <= ex < self.width:
                body.fill((*eye, int(230 * self.fade)), (ex, eye_y, 1, 2))
        surface.blit(body, (x, y))

    def debug_line(self) -> str:
        return f"hayalet x={self.x:.0f} gorunurluk {self.fade:.2f}"
