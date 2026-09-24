"""Dovusmeyen, yuruyebilen karakter - epilogda Cemo ve Jet.

`villager.py` ve `candle_keeper.py` ile ayni gerekce: can, hasar, durum
makinesi gereksiz. `Actor`'dan turemiyor; vurus icinden gecer, sahne
onu hitbox hedefi olarak hic eklemiyor. Yercekimi de yok - epilogun
zemini duz ve karakter nerede durdugunu dogdugu yerden biliyor.

## Iki kip, tek hedef

    follow(x, facing)   her kare lideri takip: liderin **arkasinda**,
                        `gap` kadar geride durur
    walk_to(x)          senaryolu yuruyus: bir noktaya git ve dur

Ikisi de ayni `target_x`'i yaziyor; `update` yalnizca oraya yuruyor.
Uzaktaysa kosuyor - Cemo geride kalmamali, ama dibinde de durmamali.
"""
from __future__ import annotations

import math

import pygame

from src.art.animator import Animator

# Hedefe bu kadar yakin = varildi. Titremesin diye tam sifir degil.
ARRIVE = 1.5
# Bu kadar geride kalan kosar (piksel).
RUN_DISTANCE = 56.0


class Npc:
    """Oyuncunun yanindaki dovusmeyen karakter."""

    __slots__ = ("character", "x", "feet_y", "facing", "target_x", "speed",
                 "gap", "animator", "sprite_foot_y", "visible")

    def __init__(self, character: str, x: float, feet_y: float,
                 facing: int = 1, speed: float = 1.0, gap: float = 26.0) -> None:
        from src.art.animation import CHARACTERS
        self.character = character
        self.x = x
        self.feet_y = feet_y
        self.facing = facing
        self.target_x: float | None = None
        self.speed = speed
        self.gap = gap
        self.visible = True
        self.animator = Animator(character)
        self.animator.play("idle")
        self.sprite_foot_y = CHARACTERS[character].foot_y

    # --- Denetim ------------------------------------------------------------
    def follow(self, leader_x: float, leader_facing: int) -> None:
        """Liderin arkasinda dur. Lider donunce karakter de yer degistirir."""
        self.target_x = leader_x - leader_facing * self.gap

    def walk_to(self, x: float) -> None:
        self.target_x = x

    def stop(self) -> None:
        self.target_x = None

    def face(self, x: float) -> None:
        """Dururken bir noktaya don (konusulan kisiye bakmak gibi)."""
        if not self.moving and abs(x - self.x) > 2.0:
            self.facing = 1 if x > self.x else -1

    @property
    def moving(self) -> bool:
        return (self.target_x is not None
                and abs(self.target_x - self.x) > ARRIVE)

    @property
    def arrived(self) -> bool:
        return self.target_x is not None and not self.moving

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        if self.moving:
            delta = self.target_x - self.x
            fast = abs(delta) > RUN_DISTANCE
            speed = self.speed * (2.0 if fast else 1.0)
            step = math.copysign(min(speed, abs(delta)), delta)
            self.x += step
            self.facing = 1 if step > 0 else -1
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if not self.visible:
            return
        image = self.animator.render(self.facing)
        if image is None:
            return
        ox, oy = offset
        surface.blit(image,
                     (int(self.x - image.get_width() * 0.5) - ox,
                      int(self.feet_y - self.sprite_foot_y) - oy))
