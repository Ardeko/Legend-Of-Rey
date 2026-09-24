"""Uyanan surunun avi - Bolum 15 "Sessizlik" (25.09.2026).

Arda: *"Sessiz gecmeye calistigimiz bolumde sessiz yurume imkansiz.
Orayi daha kolay ve ipuclu yapalim. Hizli gecersek oyuncuyu
cezalandiran bir sey de yok."*

Iki yarim vardi. Sessiz yurume `Action.SNEAK` ile cozuldu (klavyede
yavas yurumenin yolu yoktu). Bu modul oteki yarim: kosmanin bedeli.

## Bir uyanan, bir av

Uyanan dusman eskiden yerinde bir tehdit oluyordu ve 0.45 hizla
kovaliyordu - kosan oyuncu (2.0) onu geride birakiyordu. Artik:

    ciglik      `CRY_DELAY_FRAMES` sonra `NOISE_CRY` - yanindakiler kalkar
    hiz         `HUNT_CHASE_SPEED` (kosunun %80'i) - kacilir ama zor
    iz          `HUNT_LOSE_RANGE` - kolay birakmiyor
    adim sesi   `NOISE_HUNT` - onundeki uyuyanlari o uyandiriyor

Sonuc: kosarak gecen oyuncu, arkasinda buyuyen ve onunde uyanan bir
suruyle karsilasiyor. Dar koridorda can kaybediyor. **Sessiz
yuruyen oyuncu bunlarin hicbirini gormuyor.**

## Neden dusmana degil sahneye

`Enemy` her bolumde ayni dusman; avlanma B15'in kurali. Sahne uyanan
dusmani buraya veriyor (`on_herd_wake`), bu modul onun hizini ve iz
mesafesini degistiriyor - sinifa bir "B15 modu" bayragi eklemek her
dusmani bu bolumun bilgisiyle kirletirdi.
"""
from __future__ import annotations

from collections.abc import Callable

from src.config import (
    CRY_DELAY_FRAMES, ENEMY_APPROACH_SPEED, HUNT_CHASE_SPEED,
    HUNT_LOSE_RANGE, HUNT_NOISE_EVERY, NOISE_CRY, NOISE_HUNT,
)

# `Enemy._approach` hizi `move_speed * speed_scale * APPROACH / 0.5`
# ile kuruyor. Hedef kovalama hizindan `move_speed`e geri donus.
# `speed_scale` (zorluk: dusman hizi %75/%100) KORUNUYOR - erisilebilirlik
# ayari avda da gecerli.
_MOVE_FOR_HUNT = HUNT_CHASE_SPEED * 0.5 / ENEMY_APPROACH_SPEED

Emit = Callable[[float, float, float], None]


class HerdHunt:
    """Uyananlarin cigligi ve kovalamasi."""

    def __init__(self) -> None:
        # [x, y, kalan kare] - cigligin atilacagi yer ve zaman.
        self.cries: list[list[float]] = []
        self.hunters: list = []
        self.frames = 0

    @property
    def started(self) -> bool:
        return bool(self.hunters)

    def on_wake(self, enemy) -> bool:
        """Uyanan bir dusman ava katiliyor. Ilk kez katildiysa True."""
        if enemy in self.hunters or getattr(enemy, "dead", False):
            return False
        self.hunters.append(enemy)
        enemy.move_speed = _MOVE_FOR_HUNT
        enemy.lose_range = HUNT_LOSE_RANGE
        self.cries.append([enemy.body.center_x, enemy.body.center_y,
                           CRY_DELAY_FRAMES])
        return True

    def update(self, emit: Emit) -> list[tuple[float, float]]:
        """Bir kare: sirasi gelen cigliklar ve avcilarin adim sesleri.

        Atilan cigliklarin yerlerini dondurur (sahne ses/parcacik icin).
        """
        self.frames += 1
        fired: list[tuple[float, float]] = []
        for cry in self.cries:
            cry[2] -= 1
            if cry[2] <= 0:
                emit(cry[0], cry[1], NOISE_CRY)
                fired.append((cry[0], cry[1]))
        self.cries = [cry for cry in self.cries if cry[2] > 0]

        self.hunters = [h for h in self.hunters if not h.dead]
        if self.frames % HUNT_NOISE_EVERY == 0:
            for hunter in self.hunters:
                if abs(hunter.body.vx) > 0.3:
                    emit(hunter.body.center_x, hunter.body.center_y,
                         NOISE_HUNT)
        return fired
