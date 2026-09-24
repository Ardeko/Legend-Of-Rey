"""B14 jumpscare'inin cizimi - sizan karartma, hamle, kesme, gozler.

Zamanlama `src/systems/jumpscare.py`'de (ne zaman), bu modul yalnizca
**nasil gorundugunu** biliyor. Iki ayri soru: tabloyu degistirmek
cizimi, cizimi degistirmek tabloyu bozmamali.

## Kurallar

* **Tam sayi olcek yok, istenen boyutta cizim** - yuz her boyda ayri
  uretiliyor (`horror_face`), `smoothscale` hic yok (`CLAUDE.md` 4).
* **Parlama tek kare** ve `flash_limit` acikken hic yok
  (fotosensitivite). Olay atlanmiyor, sunum degisiyor.
* **Titreme sarsinti ayarina bagli**: sarsintiyi kapatan oyuncu yuzu
  titrerken gormuyor (`CLAUDE.md` 10).
"""
from __future__ import annotations

import math

import pygame

from src.art import horror_face, palette
from src.art.glow import radial_glow
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.systems.jumpscare import FACE_HEIGHTS

# Yuz ekranin altina biraz tasiyor - "ekrana sigdirilmis" degil,
# ekrandan buyuk.
BOTTOM_OVERFLOW = 0.08
# Hamlenin basinda yuz oyuncunun baktigi yanda, bu kadar ileride.
START_AHEAD = 40
# Titreme genligi (piksel) - sarsinti acikken.
JITTER = 2
# Sizan karartmanin en koyu hali (0..255).
CREEP_ALPHA = 200

_vignette: pygame.Surface | None = None
_black: pygame.Surface | None = None


def _get_black() -> pygame.Surface:
    """Tam ekran koyu perde - her karede yeniden uretilmiyor."""
    global _black
    if _black is None:
        _black = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT)).convert()
        _black.fill(palette.color("void"))
    return _black


def _get_vignette() -> pygame.Surface:
    """Kenarlari koyu, ortasi acik bir perde. Bir kez uretiliyor.

    Dis elipsten ice dogru saydamlasan halkalar; SRCALPHA yuzeye cizim
    alfayi **yaziyor** (harmanlamiyor), ice cizilen halka dsini eziyor.
    """
    global _vignette
    if _vignette is None:
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              pygame.SRCALPHA)
        void = palette.color("void")
        veil.fill((*void, 255))
        rings = 14
        for index in range(rings):
            t = index / (rings - 1)
            alpha = int(255 * (1.0 - t) ** 1.7)
            rect = pygame.Rect(0, 0, int(INTERNAL_WIDTH * (1.25 - 0.55 * t)),
                               int(INTERNAL_HEIGHT * (1.35 - 0.60 * t)))
            rect.center = (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2)
            pygame.draw.ellipse(veil, (*void, alpha), rect)
        _vignette = veil.convert_alpha()
    return _vignette


def _ease_out(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def face_rect(scare, player_x: float, facing: int) -> pygame.Rect:
    """Yuzun bu karedeki ekran dikdortgeni (hamle dahil)."""
    height = scare.face_height
    width = int(height * horror_face.ASPECT)
    start = player_x + facing * START_AHEAD
    centre = start + (INTERNAL_WIDTH / 2 - start) * _ease_out(scare.lunge)
    top = INTERNAL_HEIGHT - height + int(height * BOTTOM_OVERFLOW)
    return pygame.Rect(int(centre - width / 2), top, width, height)


def final_eyes() -> tuple[tuple[int, int], tuple[int, int]]:
    """Hamlenin sonundaki goz konumlari - kesmeden sonra orada kaliyor."""
    height = FACE_HEIGHTS[-1]
    width = int(height * horror_face.ASPECT)
    left = INTERNAL_WIDTH // 2 - width // 2
    top = INTERNAL_HEIGHT - height + int(height * BOTTOM_OVERFLOW)
    (lx, ly), (rx, ry) = horror_face.eye_points(height)
    return (left + lx, top + ly), (left + rx, top + ry)


def draw(surface: pygame.Surface, scare, player_x: float, facing: int,
         flash: float, shake_on: bool, frame: int) -> None:
    """Jumpscare'in bu karesi. `player_x` oyuncunun EKRAN x'i."""
    creep = scare.creep
    if creep > 0.0:
        veil = _get_vignette()
        veil.set_alpha(int(CREEP_ALPHA * creep ** 1.5))
        surface.blit(veil, (0, 0))
        return

    if scare.visible:
        _draw_face(surface, scare, player_x, facing, shake_on, frame)
        if flash > 0.0:
            white = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
            white.fill(palette.color("white_flash"))
            white.set_alpha(int(235 * flash))
            surface.blit(white, (0, 0))
        return

    if scare.blackout:
        surface.fill(palette.color("void"))
        return

    glow = scare.afterglow
    if glow > 0.0:
        _draw_afterglow(surface, glow)


def _draw_face(surface, scare, player_x: float, facing: int,
               shake_on: bool, frame: int) -> None:
    # Arka plan geri cekiliyor: yuz dunyanin onunde degil, onun yerine.
    veil = _get_vignette()
    veil.set_alpha(230)
    surface.blit(veil, (0, 0))
    dim = _get_black()
    dim.set_alpha(150)
    surface.blit(dim, (0, 0))

    rect = face_rect(scare, player_x, facing)
    if shake_on:
        # Deterministik titreme: rastgele degil, kareye bagli - ayni
        # anda iki kez oynansa ayni gorunur.
        rect.x += int(round(math.sin(frame * 2.3) * JITTER))
        rect.y += int(round(math.cos(frame * 3.1) * JITTER))
    surface.blit(horror_face.face(rect.height), rect.topleft)


def _draw_afterglow(surface, glow: float) -> None:
    """Karanlikta iki goz. Yuz gitti; bakis kaldi.

    Karanlik **cekiliyor**, tam siyah kalmiyor: oyuncu B14'un ortasinda,
    kor birakilirsa dovuste vurulurdu (`docs/korku.md` kural 1:
    oynanisi durdurmaz). Dunya geri gelirken gozler bir sure daha orada.
    """
    veil = _get_black()
    veil.set_alpha(int(255 * glow))
    surface.blit(veil, (0, 0))
    colour = palette.color("danger")
    halo = radial_glow(9, colour, peak=0.9 * glow)
    for x, y in final_eyes():
        surface.blit(halo, (x - 9, y - 9), special_flags=pygame.BLEND_RGB_ADD)
        if glow > 0.35:
            surface.set_at((x, y), palette.color("white_flash"))
