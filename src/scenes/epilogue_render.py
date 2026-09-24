"""Epilog cizimleri - ip, isik huzmesi, yarigin izi, ates, duvar resmi.

Sahne mantigi yok; `village_backdrop.py` ile ayni ilke: fonksiyonlar
saf, `frame` disaridan geliyor. Her sey paletten ve koddan
(`CLAUDE.md` 6) - yeni PNG yok.

## Cemo'nun resmi

B2'de ve B13'te duvara kazinmis bir isaret vardi: bes noktalik bir
"cati" (`chapter13.py:_draw_mark`). B13'te Rey onu tanidi: *"Evde her
yere bunu cizerdi."* Epilogda Cemo evinin duvarina **ayni isareti**
ciziyor, sonra yanina herkesi: Rey, Ardo, kendisi, Emre abi ve en
buyuk figur olarak "bagiran amca" (Kalachev). Tebesir - koyu ahsap
duvarda komur gorunmezdi.

Figurler piksel birimi dikdortgen listesi; kucuk halleri duvarda
(1x), buyugu jenerigin arkasinda (tam sayi buyutme, `smoothscale`
yok - `CLAUDE.md` 4).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE

# --- Ip ----------------------------------------------------------------------
ROPE_KNOT_STEP = 14

_beam_cache: dict[tuple[int, int, int], pygame.Surface] = {}


def draw_light_beam(surface: pygame.Surface, offset: tuple[int, int],
                    x0: int, x1: int, top_y: int, floor_y: int) -> None:
    """Kuyunun agzindan inen gun isigi - asagi dogru genisleyen huzme.

    Bir kez uretilip saklaniyor; her karede yalnizca blit.
    """
    ox, oy = offset
    top_w = max(8, x1 - x0)
    height = max(8, floor_y - top_y)
    spread = 40
    key = (top_w, height, spread)
    beam = _beam_cache.get(key)
    if beam is None:
        beam = pygame.Surface((top_w + spread * 2, height), pygame.SRCALPHA)
        for row in range(height):
            ratio = row / height
            half = top_w * 0.5 + spread * ratio
            centre = (top_w + spread * 2) * 0.5
            alpha = int(46 * (1.0 - ratio * 0.6))
            beam.fill((*palette.color("gold"), alpha),
                      (int(centre - half), row, int(half * 2), 1))
            core = half * 0.45
            beam.fill((*palette.color("bone"), alpha // 2),
                      (int(centre - core), row, int(core * 2), 1))
        _beam_cache[key] = beam
    surface.blit(beam, (x0 - spread - ox, top_y - oy))


def draw_rope(surface: pygame.Surface, offset: tuple[int, int], x: int,
              top_y: int, bottom_y: int, frame: int, tug: float = 0.0) -> None:
    """Jet'in ipi: duz bir cizgi ve araliklarla dugumler.

    `tug` (0..1) yukaridan cekildiginde sallanma genligi - Jet cevap
    verdiginde ip gerilip dalgalaniyor, sonra duruluyor.
    """
    ox, oy = offset
    rope = palette.color("earth")
    knot = palette.color("earth_dark")
    for y in range(top_y, bottom_y):
        depth = (y - top_y) / max(1, bottom_y - top_y)
        sway = math.sin(frame * 0.25 + y * 0.08) * 3.0 * tug * depth
        surface.fill(rope, (int(round(x + sway)) - ox, y - oy, 1, 1))
        if (y - top_y) % ROPE_KNOT_STEP == 0 and y > top_y:
            surface.fill(knot, (int(round(x + sway)) - 1 - ox, y - oy, 3, 2))


def draw_rope_post(surface: pygame.Surface, offset: tuple[int, int],
                   post_x: int, hole_x: int, hole_w: int, ground_y: int) -> None:
    """Koyun dogusunda kuyunun agzi ve ipin bagli oldugu kazik."""
    ox, oy = offset
    # Kuyunun agzi - zeminde karanlik bir yarik, kenari tas.
    surface.fill(palette.color("void"), (hole_x - ox, ground_y - oy, hole_w, 4))
    surface.fill(palette.color("stone_dark"),
                 (hole_x - 1 - ox, ground_y - 1 - oy, hole_w + 2, 1))
    # Kazik.
    surface.fill(palette.color("earth_dark"), (post_x - ox, ground_y - 16 - oy, 3, 16))
    surface.fill(palette.color("earth"), (post_x - ox, ground_y - 17 - oy, 3, 1))
    # Ip: kaziktan kuyuya sarkan kavis.
    start = (post_x + 1, ground_y - 13)
    end = (hole_x + hole_w // 2, ground_y + 2)
    points = []
    for step in range(9):
        t = step / 8
        x = start[0] + (end[0] - start[0]) * t
        sag = math.sin(t * math.pi) * 4.0
        y = start[1] + (end[1] - start[1]) * t + sag
        points.append((int(round(x)) - ox, int(round(y)) - oy))
    pygame.draw.lines(surface, palette.color("earth"), False, points)


# --- Yarigin izi -------------------------------------------------------------
def draw_scar(surface: pygame.Surface, offset: tuple[int, int], x: int,
              width: int, ground_y: int) -> None:
    """B1'de Cemo'yu yutan yarik - kapanmis, ama izi toprakta.

    Mor artik yok; bir iki piksel **sonmus** mor (`violet_dark`) kaliyor.
    Tohum deterministik (`random` yok): her acilista ayni iz.
    """
    ox, oy = offset
    for dx in range(width):
        depth = 1 + (dx * 7 + dx // 3) % 3
        surface.fill(palette.color("void"), (x + dx - ox, ground_y - oy, 1, depth))
        if dx % 5 == 0:
            surface.fill(palette.color("ink"), (x + dx - ox, ground_y - 1 - oy, 1, 1))
        if dx % 11 == 4:
            surface.fill(palette.color("violet_dark"),
                         (x + dx - ox, ground_y + depth - oy, 1, 1))


# --- Ates --------------------------------------------------------------------
def draw_bonfire(surface: pygame.Surface, x: int, base_y: int, frame: int,
                 size: int = 1) -> None:
    """Meydan atesi. B8'in ates basi - bu kez koyde ve kalabalik.

    Alev satir satir: her satirin genisligi yukari dogru daraliyor,
    sinus ile sallaniyor. Dis kat kor, ic kat altin.
    """
    log = palette.color("earth_dark")
    surface.fill(log, (x - 9 * size, base_y - 2 * size, 18 * size, 2 * size))
    surface.fill(palette.color("earth"), (x - 7 * size, base_y - 4 * size, 14 * size, 2 * size))
    layers = (("ember", 18, 9), ("ember_light", 13, 6), ("gold", 8, 3))
    for tone, height, half in layers:
        flicker = math.sin(frame * 0.31 + height) * 2.0
        h = int((height + flicker) * size)
        colour = palette.color(tone)
        for row in range(h):
            ratio = row / max(1, h)
            w = max(1, int(half * size * (1.0 - ratio) ** 0.8))
            sway = int(round(math.sin(frame * 0.2 + row * 0.35) * ratio * 2 * size))
            surface.fill(colour, (x - w + sway, base_y - 4 * size - row, w * 2, 1))


# --- Cemo'nun duvar resmi ----------------------------------------------------
# Her figur: (x ofseti, [(dx, dy, w, h), ...]). dy tabana gore (negatif
# yukari). Sira = cizim sirasi: once isaret, sonra insanlar.
MARK = [(i * 2, -6 + abs(2 - i) * 2, 2, 2) for i in range(5)]
# Rey: tek yana dokulen sac ve ucgen etek. Ilk hali iki yana simetrik
# sac teliyle ciziliyordu; dolu kafa + altindaki bosluklu satir 3x'te
# bir KAFATASI gibi okundu (goz cukurlari, cene). Oyunun son goruntusu.
REY_FIGURE = [(2, -14, 3, 3), (1, -13, 1, 6), (3, -11, 1, 2), (0, -10, 7, 1),
              (2, -9, 3, 1), (1, -8, 5, 1), (1, -7, 5, 1), (0, -6, 7, 1),
              (2, -5, 1, 5), (4, -5, 1, 5)]
ARDO_FIGURE = [(3, -16, 3, 3), (1, -13, 7, 1), (4, -13, 1, 7), (1, -12, 1, 4),
               (7, -12, 1, 4), (9, -15, 1, 9), (3, -6, 1, 6), (5, -6, 1, 6)]
CEMO_FIGURE = [(1, -8, 3, 3), (2, -5, 1, 3), (0, -4, 5, 1), (1, -2, 1, 2),
               (3, -2, 1, 2)]
JET_FIGURE = [(2, -14, 3, 3), (1, -14, 5, 1), (3, -11, 1, 6), (1, -10, 5, 1),
              (6, -9, 2, 2), (2, -5, 1, 5), (4, -5, 1, 5)]
# En buyuk figur: "en cok o bagirdi". Kocaman kafa, ağzı acik, yaninda
# uc bagirma cizgisi, kollari havada.
KALACHEV_FIGURE = [(3, -18, 5, 1), (3, -15, 5, 1), (3, -17, 1, 2), (7, -17, 1, 2),
                   (5, -16, 1, 1), (9, -18, 2, 1), (9, -16, 3, 1), (9, -14, 2, 1),
                   (5, -14, 1, 8), (2, -13, 7, 1), (2, -16, 1, 3), (8, -16, 1, 3),
                   (4, -6, 1, 6), (6, -6, 1, 6)]
# **Kapinin iki yanina.** Cemo cocuk boyunda: kapinin ustune uzanamaz,
# resim onun boyunda, kapinin solunda ve saginda. Solda isaret, Rey ve
# Ardo; sagda kendisi, Emre abi ve bagiran amca. Jenerikteki buyuk hali
# ayni iki yarim, arada kapi yok.
DRAWING_LEFT = ((0, MARK), (11, REY_FIGURE), (19, ARDO_FIGURE))
DRAWING_RIGHT = ((0, CEMO_FIGURE), (8, JET_FIGURE), (17, KALACHEV_FIGURE))
LEFT_WIDTH = 30
RIGHT_WIDTH = 31
DRAWING_HEIGHT = 19
STROKE_COUNT = sum(len(strokes)
                   for half in (DRAWING_LEFT, DRAWING_RIGHT)
                   for _x, strokes in half)
# Resim kapidan bu kadar uzak ve zeminden bu kadar yukarida (1x piksel).
DRAWING_GAP = 3
DRAWING_LIFT = 3


def door_size(house: tuple) -> tuple[int, int]:
    """Evin kapisi - `village_backdrop._draw_house` ile ayni olcu."""
    _tx, _ty, tw, th, _kind = house
    width, height = tw * TILE_SIZE, th * TILE_SIZE
    return max(5, width // 5), max(8, height // 2)


def drawing_halves(door_left: int, door_right: int,
                   scale: int = 1) -> tuple[int, int]:
    """Resmin iki yarisinin sol x'leri: kapinin solunda ve saginda."""
    gap = DRAWING_GAP * scale
    return door_left - gap - LEFT_WIDTH * scale, door_right + gap


def draw_door(surface: pygame.Surface, centre_x: int, ground_y: int,
              size: tuple[int, int], scale: int) -> tuple[int, int]:
    """Kapi, yakindan (jenerigin duvari). Kapinin sol ve sag x'ini dondurur.

    `_draw_house`'taki kapinin tam sayi buyutulmus hali: govde, ust
    esik, altin kol.
    """
    door_w, door_h = size[0] * scale, size[1] * scale
    left = centre_x - door_w // 2
    top = ground_y - door_h
    surface.fill(palette.color("earth_dark"), (left, top, door_w, door_h))
    surface.fill(palette.color("void"), (left, top, door_w, scale))
    surface.fill(palette.color("gold"), (left + door_w - 2 * scale,
                                         ground_y - door_h // 2, scale, scale))
    return left, left + door_w


def draw_chalk_drawing(surface: pygame.Surface, left_x: int, right_x: int,
                       base_y: int, progress: float, scale: int = 1) -> None:
    """Resmi `progress` (0..1) kadar ciz - cizgiler sirayla beliriyor.

    Iki yarim ayri x'lerde (duvarda kapi arada). `scale` tam sayi:
    buyutme `smoothscale` degil, dikdortgen carpimi.
    """
    reveal = int(round(max(0.0, min(1.0, progress)) * STROKE_COUNT))
    chalk = palette.color("bone")
    drawn = 0
    for origin, half in ((left_x, DRAWING_LEFT), (right_x, DRAWING_RIGHT)):
        for fx, strokes in half:
            for dx, dy, w, h in strokes:
                if drawn >= reveal:
                    return
                surface.fill(chalk, (origin + (fx + dx) * scale,
                                     base_y + dy * scale, w * scale, h * scale))
                drawn += 1
