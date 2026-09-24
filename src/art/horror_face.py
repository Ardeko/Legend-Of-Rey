"""Izleyen'in yuzu - B14 jumpscare'inin tek goruntusu (25.09.2026).

Arda: *"Jumpscare'li bolum daha korkunc olsun."* Once olculdu: eski sok
32 piksellik govde sprite'ini 6x buyutuyordu - koyu zemin ustunde koyu
bir sutun ve iki kucuk mor nokta. Yuz yoktu; korkutan tek sey beyaz
parlamaydi.

## Buyutulmuyor, istenen boyutta CIZILIYOR

Yuz normalize koordinatlarda (0..1) tarif ediliyor ve her boyut icin
ayri raster ediliyor. Hamle (`jumpscare.LUNGE_FRAMES`) bes boyuttan
geciyor; buyutulmus bir sprite her adimda kirik kenarli bir bloga
donerdi. Her boyut **bir kez** uretilip saklaniyor (`CLAUDE.md` 4).

## Yuzun dili

* **Kubbeli kafatasi, uzayan cene** - insan orantisinin biraz disinda.
  Tekinsiz olan canavarlik degil, neredeyse-insan olmak.
* **Egik, asimetrik goz cukurlari**: sag goz biraz asagida ve buyuk.
  Simetri guven verir.
* **Igne ucu gozbebekleri.** Ilk deneme buyuk yuvarlak gozlerle bir
  baykus gibi okundu. Korkutan sey karanligin icinde kucuk bir isik.
  Mor halka (on bolumdur Izleyen'in rengi) ve tehlike cekirdek: kural
  bozuldu (`CLAUDE.md` 7: renk kodlu tehlike).
* **Catlaklar ve dikey agiz**: cenenin ucuna inen tirtikli bir yarik.
* Isik **sol ustten**, kontur paletin en koyu ikinci rengi (`ink`) -
  stil sozlesmesi istisnasiz (`CLAUDE.md` 6).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette

# Yuzun en/boy orani: uzun bir kafa.
ASPECT = 0.78
# Kafanin tonlari, isiktan golgeye. `_shade` her pikselin bu siradaki
# yerini hesapliyor; bant sinirlarinda dama.
_TONES = ("stone", "stone_dark", "stone_darkest", "ink_soft")

_cache: dict[int, pygame.Surface] = {}


def face(height: int) -> pygame.Surface:
    """`height` piksel boyunda yuz. Saklanmis kopya doner."""
    height = max(24, int(height))
    image = _cache.get(height)
    if image is None:
        image = _draw(height)
        _cache[height] = image
    return image


def eye_points(height: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """Iki gozbebeginin yuz yuzeyindeki konumu (sonme parlamasi icin)."""
    width = int(height * ASPECT)
    return ((int(width * 0.33), int(height * 0.43)),
            (int(width * 0.68), int(height * 0.455)))


# --- Cizim ----------------------------------------------------------------------
def _draw(height: int) -> pygame.Surface:
    width = int(height * ASPECT)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    head = _head_mask(width, height)
    _shade(surface, head, width, height)
    _cracks(surface, head, width, height)
    _eyes(surface, width, height)
    _nose(surface, width, height)
    _mouth(surface, width, height)
    _outline(surface, head, width, height)
    return surface.convert_alpha()


def _half_width(v: float) -> float:
    """Boyun `v` noktasinda kafanin yari genisligi (genisligin orani).

    Kubbeli kafatasi, disari tasan elmacik, uzayip daralan cene.
    """
    if v < 0.46:
        t = (0.46 - v) / 0.46
        return 0.43 * math.sqrt(max(0.0, 1.0 - t * t))
    if v < 0.60:
        return 0.43 + 0.035 * math.sin((v - 0.46) / 0.14 * math.pi)
    t = (v - 0.60) / 0.40
    return 0.07 + 0.36 * (1.0 - t) ** 1.15


def _head_mask(width: int, height: int) -> list[list[bool]]:
    mask = [[False] * width for _ in range(height)]
    for y in range(height):
        v = y / max(1, height - 1)
        if v > 0.985:
            continue
        half = _half_width(v)
        for x in range(width):
            if abs(x / max(1, width - 1) - 0.5) <= half:
                mask[y][x] = True
    return mask


def _shade(surface, head, width: int, height: int) -> None:
    """Hacim: isik sol ustten, kenarlar kararir. Bant sinirinda dama."""
    for y in range(height):
        v = y / height
        for x in range(width):
            if not head[y][x]:
                continue
            u = x / width
            half = max(0.05, _half_width(v))
            edge = abs(u - 0.5) / half          # 0 merkez, 1 kenar
            light = (0.55 - 0.9 * (u - 0.35) - 0.8 * (v - 0.30)
                     - 0.55 * edge ** 3)
            level = (1.0 - light) * (len(_TONES) - 1)
            index = int(level)
            # Bant sinirinda dama: ikinci ton yari yariya karisiyor.
            if level - index > 0.5 and (x + y) % 2 == 0:
                index += 1
            index = max(0, min(len(_TONES) - 1, index))
            surface.set_at((x, y), palette.color(_TONES[index]))


def _cracks(surface, head, width: int, height: int) -> None:
    """Catlaklar: alnin sagindan ve sol yanaktan inen ince cizgiler.

    Deterministik: ayni boyut her zaman ayni catlaklar (titremesin).
    """
    ink = palette.color("ink")
    starts = ((0.64, 0.10, -0.35, 0.34), (0.20, 0.50, 0.25, 0.20),
              (0.74, 0.58, 0.10, 0.16))
    for sx, sy, dx, length in starts:
        steps = max(4, int(length * height))
        x, y = sx * width, sy * height
        for step in range(steps):
            jitter = math.sin(step * 1.7 + sx * 13.0) * 0.8
            x += dx + jitter * 0.5
            y += 1.0
            ix, iy = int(x), int(y)
            if 0 <= ix < width and 0 <= iy < height and head[iy][ix]:
                surface.set_at((ix, iy), ink)


def _socket(surface, cx: float, cy: float, rx: float, ry: float,
            angle: float, colour) -> None:
    """Dondurulmus elips - goz cukuru egik dursun."""
    points = []
    for i in range(24):
        a = math.tau * i / 24
        px, py = math.cos(a) * rx, math.sin(a) * ry
        points.append((cx + px * math.cos(angle) - py * math.sin(angle),
                       cy + px * math.sin(angle) + py * math.cos(angle)))
    pygame.draw.polygon(surface, colour, points)


def _eyes(surface, width: int, height: int) -> None:
    """Egik, asimetrik, derin. Icinde igne ucu kadar gozbebegi."""
    brow = palette.color("ink")
    void = palette.color("void")
    (lx, ly), (rx, ry) = eye_points(height)
    sockets = ((lx, ly, 0.135, 0.070, 0.20), (rx, ry, 0.150, 0.085, -0.16))
    for x, y, sx, sy, tilt in sockets:
        # Kas: cukurun ustunde koyu, daha genis bir golge.
        _socket(surface, x, y - height * 0.035, sx * width * 1.08,
                sy * height * 0.75, tilt, brow)
        _socket(surface, x, y, sx * width, sy * height, tilt, void)
    size = max(1, height // 60)
    # Ikisi de ortaya - oyuncuya - bakiyor.
    for x, y in ((lx + width * 0.015, ly), (rx - width * 0.015, ry)):
        x, y = int(x), int(y)
        pygame.draw.circle(surface, palette.color("violet"), (x, y), size + 2)
        pygame.draw.circle(surface, palette.color("danger"), (x, y), size + 1)
        pygame.draw.circle(surface, palette.color("white_flash"), (x, y), size)


def _nose(surface, width: int, height: int) -> None:
    """Burun yok - kafatasi gibi ters bir yarik. Insan yuzunden bir eksik."""
    void = palette.color("void")
    top, bottom = int(height * 0.52), int(height * 0.59)
    for y in range(top, bottom):
        half = max(0, int((y - top) / max(1, bottom - top) * width * 0.035))
        for x in range(width // 2 - half, width // 2 + half + 1):
            surface.set_at((x, y), void)


def _mouth(surface, width: int, height: int) -> None:
    """Dikey yarik, iki yaninda tirtikli disler, cenenin ucuna iniyor."""
    void = palette.color("void")
    tooth = palette.color("bone")
    tooth_shade = palette.color("stone_light")
    gum = palette.color("blood_dark")
    top, bottom = int(height * 0.63), int(height * 0.95)
    span = max(1, bottom - top)
    step = max(2, height // 34)
    for y in range(top, bottom):
        t = (y - top) / span
        half = max(1, int(width * 0.095 * math.sin(math.pi * t) ** 0.8))
        centre = int(width * 0.5 + math.sin(t * 6.0) * width * 0.01)
        for x in range(centre - half, centre + half + 1):
            surface.set_at((x, y), void)
        surface.set_at((centre - half - 1, y), gum)
        surface.set_at((centre + half + 1, y), gum)
        # Disler: iki kenardan iceri sivrilen ucgenler, sirayla kayik.
        phase = (y - top) % step
        if 0.10 < t < 0.92 and half > 2:
            length = max(1, int(half * 0.7 * (1.0 - phase / step)))
            for i in range(length):
                colour = tooth if phase < step // 2 else tooth_shade
                surface.set_at((centre - half + i, y), colour)
            if (y - top + step // 2) % step == 0:
                for i in range(max(1, int(half * 0.6))):
                    surface.set_at((centre + half - i, y), tooth)


def _outline(surface, head, width: int, height: int) -> None:
    """Kontur: siyah degil, paletin en koyu IKINCI rengi (`ink`).

    Sol ust kenar isigi aliyor - orada kontur yerine ince bir parlama.
    """
    ink = palette.color("ink")
    rim = palette.color("stone_light")
    for y in range(height):
        for x in range(width):
            if not head[y][x]:
                continue
            edge = (x == 0 or x == width - 1 or y == 0 or y == height - 1
                    or not head[y][x - 1] or not head[y][x + 1]
                    or not head[y - 1][x] or not head[y + 1][x])
            if not edge:
                continue
            lit = x < width * 0.5 and y < height * 0.45
            surface.set_at((x, y), rim if lit else ink)
