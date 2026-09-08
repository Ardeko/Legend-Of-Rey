"""Kalicilik - kan lekeleri, moloz, kirik parcalar.

Bunlar bolum boyunca zeminde kalir (CLAUDE.md 7, docs/derinlestirme.md 1.7).
Ucuz bir efekt gibi gorunur ama isi baska: **oyuncuya ne yaptigini
hatirlatir.** Gecilen bir koridora donunce oradaki dovusun izini gormek,
dunyayi oyuncunun eylemlerine tepki veriyormus gibi gosterir. Parcaciklar
sonup gider, lekeler kalir; fark budur.

Cizim bedeli sabit tutuluyor: tek bir yuzeye bir kez cizilir, sonra her
karede o yuzey blit edilir. 200 lekeyi her karede tek tek cizmek kare
butcesini yerdi.
"""
from __future__ import annotations

import random

import pygame

from src.art import palette
from src.config import MAX_GROUND_DECALS


class DecalField:
    """Bir bolumun kalici zemin izleri."""

    def __init__(self, width: int, height: int) -> None:
        # Tek yuzey: lekeler uzerine cizilir ve orada kalir.
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.surface = self.surface.convert_alpha()
        self.count = 0

    def clear(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        self.count = 0

    # --- Ekleme -------------------------------------------------------------
    def splatter(self, x: float, y: float, amount: int = 8,
                 path: str = "blood", spread: float = 9.0) -> None:
        """Bir noktaya leke serpistirir.

        Rastgelelik yalnizca **gorunuste**: lekelerin nerede oldugu oynanisi
        etkilemez, o yuzden burada `random` serbest. Dovus zamanlamalarinda
        olmadigi gibi.
        """
        if self.count >= MAX_GROUND_DECALS:
            return
        for _ in range(amount):
            if self.count >= MAX_GROUND_DECALS:
                break
            offset_x = random.uniform(-spread, spread)
            offset_y = random.uniform(-spread * 0.35, spread * 0.35)
            size = random.choice((1, 1, 1, 2))
            # Yolun koyu ucundan renk al - taze kan degil, kurumus iz.
            tone = palette.path_color(path, random.uniform(0.0, 0.35))
            alpha = random.randint(90, 170)
            spot = pygame.Surface((size, size), pygame.SRCALPHA)
            spot.fill((*tone, alpha))
            self.surface.blit(spot, (int(x + offset_x), int(y + offset_y)))
            self.count += 1

    def scorch(self, x: float, y: float, radius: float = 14.0) -> None:
        """Patlama izi - Sismek'in birakti."""
        if self.count >= MAX_GROUND_DECALS:
            return
        mark = pygame.Surface((int(radius * 2), int(radius * 2)),
                              pygame.SRCALPHA)
        pygame.draw.circle(mark, (*palette.color("void"), 110),
                           (int(radius), int(radius)), int(radius))
        pygame.draw.circle(mark, (*palette.color("ember_dark"), 70),
                           (int(radius), int(radius)), int(radius * 0.6))
        self.surface.blit(mark, (int(x - radius), int(y - radius)))
        self.count += 4

    def claw(self, x: float, y: float, length: float = 13.0) -> None:
        """Uc paralel tirmik izi (`docs/korku.md` 5.5).

        Temizlenmis bir odaya donen oyuncu duvarda **onceden olmayan**
        bir iz buluyor. Oynanisa etkisi yok; fark eden urperiyor, fark
        etmeyen hicbir sey kaybetmiyor - belgenin kendi olcutu.

        Ucu **paralel ve esit araliksiz**: rastgele cizikler bir doku
        olurdu, paralel uclu bir **pence** okunuyor. Hafif egik cunku
        dik cizgiler tas dokusunun kendi cizgilerine karisiyor.
        """
        if self.count >= MAX_GROUND_DECALS:
            return
        tone = palette.color("stone_darkest")
        for index in range(3):
            offset_x = (index - 1) * 3
            # Yukaridan asagi, hafif saga egik.
            for step in range(int(length)):
                ratio = step / max(1.0, length)
                px = int(x + offset_x + ratio * 3)
                py = int(y - length + step)
                # Ucu inceliyor: iz basta derin, sonunda siliniyor.
                alpha = int(180 * (1.0 - ratio * 0.7))
                spot = pygame.Surface((1, 1), pygame.SRCALPHA)
                spot.fill((*tone, alpha))
                self.surface.blit(spot, (px, py))
        self.count += 3

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        surface.blit(self.surface, (-ox, -oy))
