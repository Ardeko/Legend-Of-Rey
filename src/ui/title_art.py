"""Ana menunun oyulmus metal amblemi; piksel izgara ustunde ozel harfler.

Oyun adi iki dilde de marka olarak LEGEND OF REY; alt ad cevrilir.
Serifler, ic bosluklar ve pahlar logo icin cizilir, arayuz fontu buyutulmez.
Yuzeyler dil/palet degisince bir kez hazirlanir; karelerde yalnizca blit.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.ui import text

WIDTH, HEIGHT = 176, 84
WORD_Y = 21
SHEEN_PERIOD = 600
SHEEN_FRAMES = 180


def _letter(char: str) -> pygame.Surface:
    """16x22 tasarim izgara: belirgin serif, acik goz, genis capraz bacak."""
    image = pygame.Surface((16, 22), pygame.SRCALPHA)
    colour = (*palette.color("bone"), 255)
    if char == "R":
        points = [(0, 0), (10, 0), (13, 2), (14, 5), (14, 7),
                  (12, 10), (8, 11), (14, 20), (15, 20), (15, 21),
                  (10, 21), (5, 12), (4, 12), (4, 20), (7, 20),
                  (7, 21), (0, 21), (0, 20), (1, 20), (1, 1), (0, 1)]
        pygame.draw.polygon(image, colour, points)
        pygame.draw.polygon(image, (0, 0, 0, 0),
                            [(5, 2), (9, 2), (11, 4), (11, 7), (9, 9), (5, 9)])
    elif char == "E":
        points = [(0, 0), (14, 0), (14, 4), (13, 4), (12, 2),
                  (5, 2), (5, 9), (10, 9), (11, 7), (12, 7),
                  (12, 13), (11, 13), (10, 11), (5, 11), (5, 19),
                  (12, 19), (14, 16), (15, 16), (15, 21), (0, 21),
                  (0, 20), (2, 20), (2, 1), (0, 1)]
        pygame.draw.polygon(image, colour, points)
    else:  # Y
        points = [(0, 0), (7, 0), (7, 1), (5, 1), (9, 9),
                  (12, 2), (10, 1), (10, 0), (15, 0), (15, 1),
                  (14, 2), (10, 11), (10, 20), (13, 20), (13, 21),
                  (3, 21), (3, 20), (6, 20), (6, 11), (1, 1), (0, 1)]
        pygame.draw.polygon(image, colour, points)
    return image


def _word_mask() -> pygame.mask.Mask:
    word = pygame.Surface((54, 22), pygame.SRCALPHA)
    for index, letter in enumerate("REY"):
        word.blit(_letter(letter), (index * 19, 0))
    # Harfler yatayda genis, dikeyde sikistirilmis degil: 3x2 tasarim
    # olcegi, iki eksende de tam piksel. Filtre / smoothscale kullanilmaz.
    word = pygame.transform.scale(word, (162, 44))
    return pygame.mask.from_surface(word)


def _tint(mask: pygame.mask.Mask, colour: str,
          alpha: int = 255) -> pygame.Surface:
    return mask.to_surface(setcolor=(*palette.color(colour), alpha),
                           unsetcolor=(0, 0, 0, 0)).convert_alpha()


class TitleArt:
    def __init__(self, subtitle: str) -> None:
        self.image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        mask = _word_mask()
        x = (WIDTH - mask.get_size()[0]) // 2
        shadow = _tint(mask, "void")
        self.image.blit(shadow, (x + 2, WORD_Y + 3))
        # Uc piksel derinlik ve bir piksellik ust-sol keski isigi.
        self.image.blit(_tint(mask, "earth_dark"), (x + 1, WORD_Y + 2))
        face = _tint(mask, "bone")
        shade = _tint(mask, "flesh_light")
        face.blit(shade, (0, 27), (0, 27, 162, 17))
        # Bronz yuzeye dogru sekiz siralik doku gecisi: duz iki renk
        # bandi harfi ortadan kesiyormus gibi okunmasin.
        for row in range(20, 27):
            for column in range(mask.get_size()[0]):
                if mask.get_at((column, row)) and (column + row * 2) % 8 < row - 19:
                    face.set_at((column, row), palette.color("flesh_light"))
        top = mask.copy()
        top.erase(mask, (1, 1))
        face.blit(_tint(top, "bone"), (0, 0))
        bottom = mask.copy()
        bottom.erase(mask, (-1, -1))
        face.blit(_tint(bottom, "earth"), (0, 0))
        self.image.blit(face, (x, WORD_Y))
        # Ust kucuk harfler genis aralikli: isim tek bakista okunur.
        text.draw(self.image, "LEGEND OF", WIDTH // 2, 3,
                  color=palette.color("bone"), align="center", tracking=2)
        self._ornaments(subtitle)
        self.image = self.image.convert_alpha()
        self.sheen = _tint(mask, "bone", 65)
        self.word_x = x

    def _ornaments(self, subtitle: str) -> None:
        """Kolye tasina gonderme yapan elmaslar ve sakin ayiricilar."""
        dim = palette.color("stone_dark")
        for left, right in ((2, 40), (WIDTH - 41, WIDTH - 3)):
            pygame.draw.line(self.image, dim, (left, 8), (right, 8))
        for x in (2, WIDTH - 3):
            pygame.draw.polygon(self.image, palette.color("violet"),
                                [(x, 6), (x + 2, 8), (x, 10), (x - 2, 8)])
        text.draw(self.image, subtitle, WIDTH // 2, 72,
                  color=palette.color("stone_light"), align="center", tracking=3)
        width = text.text_width(subtitle, tracking=3)
        gap = (WIDTH - width) // 2 - 8
        for left, right in ((17, gap), (WIDTH - gap, WIDTH - 18)):
            if right > left:
                pygame.draw.line(self.image, palette.color("violet_dark"),
                                 (left, 77), (right, 77))

    def draw(self, target: pygame.Surface, position: tuple[int, int],
             frame: int, *, animate: bool = True) -> None:
        target.blit(self.image, position)
        phase = frame % SHEEN_PERIOD
        if animate and phase < SHEEN_FRAMES:
            # On saniyede bir dar, dusuk kontrastli metal yansimasi.
            # Butun baslik yanip sonmez; fotosensitivite ayari bunu kapatir.
            column = phase * self.sheen.get_width() // SHEEN_FRAMES
            target.blit(self.sheen,
                        (position[0] + self.word_x + column, position[1] + WORD_Y),
                        (column, 0, 3, self.sheen.get_height()))
