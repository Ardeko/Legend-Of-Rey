"""Silah kaidesi - tasa saplanmis bir silah, alinmayi bekliyor.

Arda, 23.09.2026: *"oyuna silah cesitliligi de ekleyelim"* - karaktere
ozel silah (B10) ve ortak yeni silah (B14) bu kaideden aliniyor.

## Neden sandik degil

Sandik bir **odul**: aciliyor ve icindeki sayi artiyor. Silah bir
**karar anı** degil ama bir **karsilasma**: oyuncu onu uzaktan goruyor,
ne oldugunu siluetinden okuyor ve yanina gidiyor. Tasa saplanmis silah
bunu hic yazi kullanmadan anlatiyor - ve alindiktan sonra bos kaide
odada kaliyor: "burada bir sey vardi."

## Silahin gorunusu oyuncununkiyle AYNI cizici

Kaidedeki silah `spritegen._draw_weapon` ile ciziliyor - oyuncunun
elindekiyle ayni fonksiyon. Kaideden alinan sey elde ayni gorunuyor;
ayri bir "ikon" cizseydik ikisi gun gelir birbirinden ayrilirdi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.combat import weapons
from src.core.input import Action

REACH_X = 18
REACH_Y = 26
SPRITE = 28

# Kaidenin halesi - silahin kimligi. Palet adlari.
GLOW = {weapons.WHISPER: "violet", weapons.SPEAR: "ember",
        weapons.SICKLE: "stone"}
MOTE = {weapons.WHISPER: "violet_bright", weapons.SPEAR: "ember_light",
        weapons.SICKLE: "stone_light"}
# Sprite'i cizmek icin silah turu -> CharSpec adi (weapon + weapon_chain).
SPEC_FOR = {weapons.WHISPER: "rey_whisper", weapons.SPEAR: "ardo_spear",
            weapons.SICKLE: "rey_sickle"}
# Alininca acilan mekanik kartinin metni. Duz dize - `tests/test_lang.py`
# hesaplanmis anahtari goremiyor.
HINT_KEYS = {weapons.WHISPER: "hint.weapon_whisper",
             weapons.SPEAR: "hint.weapon_spear",
             weapons.SICKLE: "hint.weapon_sickle"}

_image_cache: dict[str, pygame.Surface] = {}


def clear_cache() -> None:
    _image_cache.clear()


def weapon_image(key: str) -> pygame.Surface:
    """Tasa saplanmis silah: agiz asagida, kabza yukarida, hafif egik."""
    image = _image_cache.get(key)
    if image is not None:
        return image
    from src.art.animation import CHARACTERS
    from src.art.forge import Canvas
    from src.art.spritegen import _draw_weapon
    spec = CHARACTERS[SPEC_FOR.get(key, "rey_armed")]
    canvas = Canvas(SPRITE, SPRITE)
    # El (kabza) ustte; aci pi/2 = asagi. Hafif egim durgunlugu kiriyor.
    _draw_weapon(canvas, SPRITE * 0.5, 5.0, math.pi / 2 + 0.12, spec)
    canvas.outline()
    image = canvas.resolve()
    _image_cache[key] = image
    return image


class WeaponShrine:
    """Bir bolumde duran tek kaide."""

    def __init__(self, x: float, feet_y: float, weapon_key: str,
                 taken: bool) -> None:
        self.x = x
        self.feet_y = feet_y
        self.weapon_key = weapon_key
        self.taken = taken
        self.frame = 0

    def near(self, player) -> bool:
        return (abs(self.x - player.body.center_x) < REACH_X
                and abs(self.feet_y - player.body.feet[1]) < REACH_Y)

    def update(self, scene) -> None:
        self.frame += 1
        if self.taken or scene.player.dead or not self.near(scene.player):
            return
        scene.prompts.offer("weapon_shrine", self.x, self.feet_y - 30,
                            verb_key="prompt.take")
        if scene.game.input.pressed(Action.INTERACT):
            self.taken = True
            scene.take_weapon(self.weapon_key, self.x, self.feet_y - 16)

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        x = int(self.x) - ox
        base = int(self.feet_y) - oy
        if x < -40 or x > surface.get_width() + 40:
            return
        if not self.taken:
            self._draw_glow(surface, x, base)
            image = weapon_image(self.weapon_key)
            # 8 FPS'lik bir soluk alma - silah "canli", ama yerinden oynamiyor.
            lift = 1 if (self.frame // 32) % 2 else 0
            surface.blit(image, (x - SPRITE // 2, base - 10 - SPRITE + 8 - lift))
        self._draw_pedestal(surface, x, base)

    def _draw_glow(self, surface: pygame.Surface, x: int, base: int) -> None:
        name = GLOW.get(self.weapon_key, "stone")
        pulse = 0.55 + 0.15 * math.sin(self.frame * 0.05)
        glow = radial_glow(20, palette.color(name), peak=pulse)
        surface.blit(glow, (x - 20, base - 34), special_flags=pygame.BLEND_RGB_ADD)
        # Kaideden yukselen uc zerre - "burada bir sey var" uzaktan okunsun.
        for index in range(3):
            phase = (self.frame + index * 37) % 90
            px = x - 5 + index * 5 + round(math.sin((self.frame + index * 20) * 0.07))
            py = base - 12 - phase // 3
            if phase < 80:
                surface.set_at((px, py), palette.color(
                    MOTE.get(self.weapon_key, "stone_light")))

    def _draw_pedestal(self, surface: pygame.Surface, x: int, base: int) -> None:
        """Iki basamakli tas kaide; sol-ust isik, sag-alt golge."""
        outline = palette.color("ink")
        surface.fill(outline, (x - 9, base - 11, 19, 11))
        surface.fill(palette.color("stone_dark"), (x - 8, base - 10, 17, 10))
        surface.fill(palette.color("stone_light"), (x - 8, base - 10, 17, 1))
        surface.fill(palette.color("stone"), (x - 8, base - 9, 1, 9))
        surface.fill(palette.color("stone_darkest"), (x + 8, base - 9, 1, 9))
        # Ust basamak ve saplama yarigi.
        surface.fill(outline, (x - 6, base - 14, 13, 4))
        surface.fill(palette.color("stone"), (x - 5, base - 13, 11, 3))
        surface.fill(palette.color("stone_light"), (x - 5, base - 13, 11, 1))
        surface.fill(palette.color("ink"), (x - 1, base - 13, 3, 1))
        # Oyma: kaidenin yuzunde tek bir isaret - kimin silahi oldugu.
        mark = palette.color(GLOW.get(self.weapon_key, "stone") if not self.taken
                             else "stone_darkest")
        surface.fill(mark, (x - 1, base - 6, 3, 1))
        surface.fill(mark, (x, base - 7, 1, 3))
