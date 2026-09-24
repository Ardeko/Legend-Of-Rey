"""Koylu - Bolum 1'in koyunu yasayan bir yer yapan pasif NPC.

Arda'nin istegi (23.08.2026): *"ilk basta etrafta koyluler dolasabilir.
Olaylar patlak verdiginde koyluler evlerine kacsin."*

Bu bir dekor detayindan fazlasi. Prologun butun anlatimi "sakin koy →
yarik aciliyor → Cemo cekiliyor" uzerine kurulu; koy hic yasamiyorsa
kaybedilen sey de soyut kaliyor. Koyluler kacinca oyuncu **kaybi
cevresinde** goruyor, sadece Cemo'da degil.

## Uc durum, tek yon

    WANDER   iki nokta arasinda agir agir gider gelir, arada durur
    FLEE     en yakin evine kosar (panik - normalden hizli)
    INSIDE   eve girdi, artik cizilmiyor

Gecis **tek yonlu**: kacan koylu geri donmez. Yarik kapansa bile koy bir
daha dolmaz - kaybin kalici oldugunu mekanin kendisi soyluyor.

## ...ta ki oyunun sonuna kadar (24.09.2026, epilog "Eve Donus")

B1'in "koy bir daha dolmaz" cumlesi bilincliydi ve on sekiz bolum
boyunca dogru kaldi. Epilogda koy **tekrar doluyor**: can calininca
koyluler kapilarindan cikip oyuncuya donuyor. Iki yeni durum:

    EMERGE   kapidan cikar, kendi yerine yurur (kademeli: `delay`)
    GREET    disarida, oyuncuya donuk bekler - konusulabilir

B1'in akisi degismedi: `inside=False` ile dogan koylu eskisi gibi
WANDER -> FLEE -> INSIDE yolunu izliyor.

## `Actor`'dan turemiyor

`candle_keeper.py` ile ayni gerekce: can, hasar, durum makinesi
gereksiz. Vurus icinden gecer, hicbir sey olmaz - sahne onu hitbox hedefi
olarak hic eklemiyor. Yercekimi de yok; koyluler duz zeminde yuruyor ve
zeminin nerede oldugunu dogduklari yerden biliyorlar.

## `random` yok

Her koylunun ritmi kendi `seed`'inden turuyor (`cave_backdrop`'un
deterministik hash+sinus deseniyle ayni ruh). Ayni sahne her acilista
ayni sekilde yasiyor - kare kare degisen bir koy "gurultu" gibi okunur.
"""
from __future__ import annotations

import math

import pygame

from src.art.animator import Animator

WANDER = "wander"
FLEE = "flee"
INSIDE = "inside"
EMERGE = "emerge"
GREET = "greet"

# Kapidan cikip yerine yuruyen koylunun hizi - kosmuyor, merakla geliyor.
EMERGE_SPEED = 0.45
# Yerine bu kadar yaklasinca durup doner.
STAND_REACH = 1.2

# Hizlar (piksel/kare). Kacis gezinmenin ~3 kati - panik okunur olmali.
WANDER_SPEED = 0.22
FLEE_SPEED = 0.72
# Gezinme yaricapi: dogdugu noktadan bu kadar uzaga gider.
WANDER_RANGE = 26.0
# Kapiya bu kadar yaklasinca iceri girmis sayilir.
DOOR_REACH = 6.0
# Kacmadan once bu kadar kare donup bakar - "ne oldu?" ani. Hepsi ayni
# karede donup kacsaydi bir suru gibi okunurdu; kademeli tepki panigi
# gercek yapiyor.
STARTLE_FRAMES = 18


class Villager:
    """Koyde dolasan, tehlike aninda evine kacan pasif NPC."""

    __slots__ = ("home_x", "x", "feet_y", "door_x", "state", "facing",
                 "frame", "seed", "animator", "sprite_foot_y", "startle",
                 "stand_x", "delay", "role")

    def __init__(self, x: float, feet_y: float, door_x: float,
                 seed: int = 0, inside: bool = False, role: str = "") -> None:
        from src.art.animation import CHARACTERS
        self.home_x = x
        self.x = door_x if inside else x
        self.feet_y = feet_y
        self.door_x = door_x          # Kacinca gidecegi kapi
        self.state = INSIDE if inside else WANDER
        self.facing = 1
        self.frame = 0
        self.seed = seed
        self.startle = 0
        # Epilog: kapidan cikinca durulacak yer ve kac kare sonra.
        self.stand_x = x
        self.delay = 0
        # Konusulunca ne diyecegi - sahne bu etiketi repliege ceviriyor.
        self.role = role
        self.animator = Animator("villager")
        self.animator.play("idle")
        self.sprite_foot_y = CHARACTERS["villager"].foot_y

    # --- Sorgular -----------------------------------------------------------
    @property
    def gone(self) -> bool:
        return self.state == INSIDE

    @property
    def hidden(self) -> bool:
        """Ekranda yok mu? Iceride ya da cikmak icin sirasini bekliyor."""
        return self.state == INSIDE or (self.state == EMERGE and self.delay > 0)

    @property
    def greeting(self) -> bool:
        """Disarida, oyuncuya donuk, konusulabilir."""
        return self.state == GREET

    @property
    def _wander_phase(self) -> float:
        """Kendi ritmi. Her koylu farkli hizda gider gelir."""
        period = 260.0 + (self.seed % 7) * 40.0
        return (self.frame + self.seed * 37) / period * math.tau

    # --- Denetim ------------------------------------------------------------
    def flee(self) -> None:
        """Tehlike! Kisa bir irkilmeden sonra eve kosar."""
        if self.state == WANDER:
            self.state = FLEE
            # Irkilme suresi koyluye gore degisiyor - hepsi ayni karede
            # donmesin (bkz. STARTLE_FRAMES).
            self.startle = STARTLE_FRAMES + (self.seed % 5) * 6

    def emerge(self, delay: int, stand_x: float | None = None) -> None:
        """Can caldi: `delay` kare sonra kapidan cik, `stand_x`'e yuru.

        Hepsi ayni karede cikarsa bir suru gibi okunurdu (FLEE'deki
        `STARTLE_FRAMES` ile ayni ders) - cagiran gecikmeyi kademeli
        veriyor.
        """
        if self.state != INSIDE:
            return
        self.state = EMERGE
        self.x = self.door_x
        self.delay = max(0, delay)
        if stand_x is not None:
            self.stand_x = stand_x

    def greet(self) -> None:
        """Dogrudan disarida baslat (oyun sonrasi koy - herkes zaten cikti)."""
        self.state = GREET
        self.x = self.stand_x
        self.delay = 0

    def face(self, x: float) -> None:
        """Disarida bekleyen koylu oyuncuya doner. Yururken dokunulmaz."""
        if self.state == GREET and abs(x - self.x) > 2.0:
            self.facing = 1 if x > self.x else -1

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        if self.state == INSIDE:
            return
        self.frame += 1
        if self.state == WANDER:
            self._update_wander()
        elif self.state == EMERGE:
            self._update_emerge()
        elif self.state == GREET:
            self.animator.play("idle")
        else:
            self._update_flee()
        self.animator.update()

    def _update_emerge(self) -> None:
        if self.delay > 0:
            self.delay -= 1
            return
        delta = self.stand_x - self.x
        if abs(delta) <= STAND_REACH:
            self.x = self.stand_x
            self.state = GREET
            self.animator.play("idle")
            return
        step = math.copysign(min(EMERGE_SPEED, abs(delta)), delta)
        self.x += step
        self.facing = 1 if step > 0 else -1
        self.animator.play("run")

    def _update_wander(self) -> None:
        target = self.home_x + math.sin(self._wander_phase) * WANDER_RANGE
        delta = target - self.x
        if abs(delta) < 0.6:
            # Ucta bekliyor - surekli yurumek "devriye" gibi okunur,
            # duraklamalar "yasiyor" gibi.
            self.animator.play("idle")
            return
        step = math.copysign(min(WANDER_SPEED, abs(delta)), delta)
        self.x += step
        self.facing = 1 if step > 0 else -1
        self.animator.play("run" if abs(step) > 0.18 else "idle")

    def _update_flee(self) -> None:
        if self.startle > 0:
            # Donup bakiyor: hedefe yuzunu cevirir ama daha kosmaz.
            self.startle -= 1
            self.facing = 1 if self.door_x > self.x else -1
            self.animator.play("idle")
            return
        delta = self.door_x - self.x
        if abs(delta) <= DOOR_REACH:
            self.state = INSIDE
            return
        step = math.copysign(FLEE_SPEED, delta)
        self.x += step
        self.facing = 1 if step > 0 else -1
        self.animator.play("run")

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if self.hidden:
            return
        image = self.animator.render(self.facing)
        if image is None:
            return
        ox, oy = offset
        surface.blit(image,
                     (int(self.x - image.get_width() * 0.5) - ox,
                      int(self.feet_y - self.sprite_foot_y) - oy))
