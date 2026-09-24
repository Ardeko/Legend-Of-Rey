"""Koy arka plani - Bolum 1'in dekoru.

`cave_backdrop.py`'nin magara icin yaptiginin koy karsiligi: sahne
mantigini degil, yalnizca **cizimi** tutuyor. Ayrildi cunku
`chapter01.py` 732 satira cikmisti - CLAUDE.md 11'in 400 satir siniri.

Dort parallax katmani: gokyuzu -> ay -> uzak tepeler -> koy. Ilk halinde
yalnizca yildizlar ve evler vardi; aradaki bosluk "gokyuzu" degil
"hiclik" gibi okunuyordu (ayni tuzak magara arka planinda da yasanmisti,
DEVIR.md 4 madde 19). Ay ve tepe siluetleri o boslugu MESAFEYE ceviriyor.

Butun fonksiyonlar saf: durum tutmuyorlar, `frame` disaridan geliyor.

## Safak (24.09.2026 - epilog "Eve Donus")

Ayni koy oyunun sonunda **sabah** goruluyor (`time_of_day="dawn"`).
Gece surumu bayt bayt ayni kaliyor; safak yalnizca parametre. Gokyuzu
gradyani bir kez uretilip saklaniyor (`CLAUDE.md` 4: her karede
yeniden uretme) - karede yalnizca gunes ve duman ciziliyor.

Epilog koye iki yapi ekliyor: **han** (Kalachev'in parasini biraktigi
yer) ve **can cercevesi** (koy cani). Ikisi de `scenery` listesinden
geliyor; B1 kendi listesini degistirmeden kullanmaya devam ediyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE
from src.world.rooms.chapter01 import SCENERY

NIGHT = "night"
DAWN = "dawn"

# Safak gogu: ustten ufka bantlar. (baslangic satiri, renk). Ufuk 128;
# gunes tepelerin arkasindan doguyor, sicak renkler ufka yakin.
DAWN_BANDS: tuple[tuple[int, str], ...] = (
    (0, "abyss"),
    (26, "abyss_light"),
    (54, "stone_light"),
    (80, "flesh_light"),
    (102, "ember_light"),
    (118, "gold"),
)
# Bant gecislerinde dama deseni - duz sinir "cizgi" gibi okunuyor,
# iki satirlik dama piksel art'in gradyani.
DAWN_DITHER_ROWS = 3
# Gunes: dogu (sag) ufukta, tepelerin arkasindan yari cikmis.
SUN_X_RATIO = 0.80
SUN_Y = 116
SUN_RADIUS = 8
# Baca catinin egiminden bu kadar yukselir (piksel).
CHIMNEY_RISE = 6

_dawn_sky: pygame.Surface | None = None


def _draw_stars(surface: pygame.Surface, ox: float, frame: int) -> None:
    """Yildizlar - bir kismi nabiz atiyor, hepsi ayni parlaklikta degil."""
    for i in range(70):
        x = int(i * 97 - ox * 0.10) % INTERNAL_WIDTH
        y = (i * 53) % 118
        if i % 7 == 0:
            # Titreyen yildiz: sabit bir yildiz alani "doku" gibi
            # okunuyordu, birkac tanesinin nabzi onu gokyuzu yapiyor.
            twinkle = math.sin(frame * 0.04 + i) > 0.2
            tone = "white_flash" if twinkle else "stone_dark"
        else:
            tone = "bone" if i % 5 == 0 else "stone_dark"
        surface.fill(palette.color(tone), (x, y, 1, 1))

def _draw_moon(surface: pygame.Surface, ox: float) -> None:
    """Ay - neredeyse sabit (cok uzak) ve hafif haleli."""
    mx = int(INTERNAL_WIDTH * 0.78 - ox * 0.04)
    my = 34
    if mx < -24 or mx > INTERNAL_WIDTH + 24:
        return
    halo = radial_glow(20, palette.color("abyss_light"), peak=0.22)
    surface.blit(halo, (mx - 20, my - 20),
                 special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.circle(surface, palette.color("bone"), (mx, my), 7)
    # Hilal: ust uste ikinci daire gokyuzu renginde - dolunay yerine
    # hilal, siluete kimlik veriyor.
    pygame.draw.circle(surface, palette.color("abyss_dark"),
                       (mx + 4, my - 2), 6)

def _draw_hills(surface: pygame.Surface, ox: float,
                tones: tuple[str, str] = ("abyss", "ink_soft")) -> None:
    """Uzak tepe siluetleri - iki kademe, ikisi de tek renk.

    Tek renk bilincli: ayrinti verirsek yakinda sanilir. Uzaklik
    ayrintinin YOKLUGU ile anlatilir. Safakta tonlar aciliyor: parlak
    ufkun onunde tepeler yine siluet ama gece kadar kara degil.
    """
    horizon = 128
    far, near = tones
    for layer, (speed, tone, amp, step) in enumerate((
            (0.22, far, 16.0, 0.020),
            (0.35, near, 11.0, 0.034))):
        base_y = horizon + layer * 9
        shift = ox * speed
        for x in range(INTERNAL_WIDTH):
            world = x + shift
            h = (math.sin(world * step) * amp
                 + math.sin(world * step * 2.3 + layer) * amp * 0.35)
            top = int(base_y - h)
            if top < INTERNAL_HEIGHT:
                surface.fill(palette.color(tone),
                             (x, top, 1, INTERNAL_HEIGHT - top))


def paint_bands(surface: pygame.Surface,
                bands: tuple[tuple[int, str], ...], bottom: int) -> None:
    """Bantlari doldurur; sinirlari `DAWN_DITHER_ROWS` satirlik dama.

    Safak gogu iki yerde ciziliyor - koyde ve dikey yolculugun varisinda.
    Yolculukta dama yokken bantlar duz serit gibi okunuyordu; gecis iki
    yerde ayni kalsin diye tek fonksiyon. Uretimde bir kez cagrilir.
    """
    width = surface.get_width()
    for index, (top, tone) in enumerate(bands):
        end = bands[index + 1][0] if index + 1 < len(bands) else bottom
        surface.fill(palette.color(tone), (0, top, width, end - top))
    for index in range(1, len(bands)):
        boundary, tone = bands[index]
        colour = palette.color(tone)
        for row in range(boundary - DAWN_DITHER_ROWS, boundary):
            # Sinira yaklastikca alttaki renk artiyor: 1/4, 1/2, 3/4.
            step = 4 - (row - (boundary - DAWN_DITHER_ROWS))
            for x in range(row % 2, width, max(2, step)):
                surface.set_at((x, row), colour)


def _build_dawn_sky() -> pygame.Surface:
    """Safak gradyani - bir kez uretilir, sonra yalnizca blit edilir.

    Her bant bir sonrakine `DAWN_DITHER_ROWS` satirlik dama ile geciyor.
    Piksel piksel `set_at` her karede pahali olurdu (480x15 cagri);
    bir kez yapmak bedava.
    """
    sky = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
    paint_bands(sky, DAWN_BANDS, INTERNAL_HEIGHT)
    # Son yildizlar - gece tamamen bitmedi, en ustte birkac tane kaldi.
    for i in range(14):
        x = (i * 131 + 17) % INTERNAL_WIDTH
        y = (i * 37) % 30
        sky.set_at((x, y), palette.color("stone_light"))
    return sky.convert()


def _draw_sun(surface: pygame.Surface, ox: float) -> None:
    """Gunes - doguda, yari tepelerin arkasinda. Neredeyse sabit (uzak)."""
    sx = int(INTERNAL_WIDTH * SUN_X_RATIO - ox * 0.04)
    if sx < -40 or sx > INTERNAL_WIDTH + 40:
        return
    halo = radial_glow(30, palette.color("gold"), peak=0.35)
    surface.blit(halo, (sx - 30, SUN_Y - 30),
                 special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.circle(surface, palette.color("gold"), (sx, SUN_Y),
                       SUN_RADIUS)
    pygame.draw.circle(surface, palette.color("white_flash"), (sx, SUN_Y),
                       SUN_RADIUS - 3)


def draw(surface: pygame.Surface, offset, frame: int,
         time_of_day: str = NIGHT,
         scenery: tuple | None = None) -> None:
    """Evler, kuyu, cit. Carpisma yok - yalnizca dekor.

    Koyun koye benzemesi icin sart: duz zemin uzerinde iki platform
    "koy" degil "test odasi" gibi okunuyordu.

    `scenery` verilmezse B1'in listesi; epilog kendi listesini veriyor
    (ayni evler + han + can cercevesi).
    """
    ox, oy = offset
    dawn = time_of_day == DAWN
    for tx, ty, tw, th, kind in (scenery if scenery is not None else SCENERY):
        x = tx * TILE_SIZE - ox
        base = (ty + 1) * TILE_SIZE - oy
        width = tw * TILE_SIZE
        height = th * TILE_SIZE
        if x + width < -20 or x > INTERNAL_WIDTH + 20:
            continue                     # Gorunmeyeni cizme

        if kind == "house":
            _draw_house(surface, frame, x, base, width, height, dawn)
        elif kind == "inn":
            _draw_house(surface, frame, x, base, width, height, dawn)
            _draw_inn_sign(surface, frame, x, base, width, height)
        elif kind == "well":
            _draw_well(surface, frame, x, base, width, height)
        elif kind == "bellframe":
            _draw_bellframe(surface, x, base, width, height)
        else:
            _draw_fence(surface, frame, x, base, width, height)

def _draw_house(surface: pygame.Surface, frame: int, x: int, base: int,
                width: int, height: int, dawn: bool = False) -> None:
    """Ev: govde + saclik yapan cati + kapi + isikli pencere + baca.

    **Kapi sart oldu** (23.08.2026): koyluler `door_x`'e kosuyor ve
    oraya girip kayboluyor. Gorunur bir kapi olmadan bu hareket
    "duvara girdi" gibi okunuyordu.

    Safakta pencereler **titremiyor** ve sonuk: geceden kalan mum,
    icerde biri uyanik ama disari cikmamis.
    """
    top = base - height
    surface.fill(palette.color("ink_soft"), (x, top, width, height))
    # Yatay tahta cizgileri - duz dolgu "kutu" gibi okunuyordu.
    for row in range(top + 3, base, 4):
        surface.fill(palette.color("void"), (x + 1, row, width - 2, 1))

    # Cati: govdeden iki piksel TASAR (saclik). Tam govde genisliginde
    # biten cati, evi ustten kesilmis bir kutu yapiyordu.
    roof_h = max(4, height // 3)
    for i in range(roof_h):
        t = i / max(1, roof_h - 1)
        inset = int((width * 0.5 + 2) * t)
        tone = "earth" if i < 2 else "earth_dark"
        surface.fill(palette.color(tone),
                     (x - 2 + inset, top - i, width + 4 - inset * 2, 1))

    # Kapi - koylunun kactigi yer. Govdenin ortasinda, zemine oturur.
    door_w = max(5, width // 5)
    door_h = max(8, height // 2)
    dx = x + width // 2 - door_w // 2
    surface.fill(palette.color("earth_dark"),
                 (dx, base - door_h, door_w, door_h))
    surface.fill(palette.color("void"), (dx, base - door_h, door_w, 1))
    surface.fill(palette.color("gold"),
                 (dx + door_w - 2, base - door_h // 2, 1, 1))   # kol

    # Isikli pencere - koyde hayat var. Titriyor: mum isigi.
    win_y = top + max(3, height // 3)
    if dawn:
        lit, other = "ember_dark", "ember_dark"
    else:
        flicker = 1 if (frame // 17 + x) % 5 else 0
        lit = "ember" if flicker else "ember_dark"
        other = "ember" if not flicker else "ember_dark"
    surface.fill(palette.color(lit), (x + 3, win_y, 3, 3))
    if width > 40:
        surface.fill(palette.color(other), (x + width - 6, win_y, 3, 3))

    # Baca + duman - hareket eden tek dekor ogesi, koyu "canli" yapar.
    # Baca catinin EGIMINE oturuyor (24.09.2026): sabit yukseklikte
    # cizildiginde catidan ~14 piksel kopuk, havada asili duruyordu.
    # Gece koyu gokyuzunde gorunmuyordu; safagin acik gokyuzunde goruldu.
    chimney_x = x + width - max(6, width // 4)
    roof_y = top - _roof_row_at(chimney_x + 3, x, width, roof_h)
    chimney_top = roof_y - CHIMNEY_RISE
    surface.fill(palette.color("stone_darkest"),
                 (chimney_x, chimney_top, 4, roof_y - chimney_top + 1))
    _draw_smoke(surface, frame, chimney_x + 2, chimney_top - 1, dawn)


def _roof_row_at(column: int, x: int, width: int, roof_h: int) -> int:
    """Catinin bu sutunu ortten en ust satiri (0 = saclik satiri).

    `_draw_house`'taki cati dongusuyle ayni hesap - baca buna oturuyor.
    """
    row = 0
    for i in range(roof_h):
        t = i / max(1, roof_h - 1)
        inset = int((width * 0.5 + 2) * t)
        if x - 2 + inset <= column < x + width + 2 - inset:
            row = i
    return row


def _draw_smoke(surface: pygame.Surface, frame: int, x: int, y: int,
                dawn: bool = False) -> None:
    """Bacadan yukselen duman - yukari cikarken saga savrulur ve soner.

    Safakta acik gokyuzunun onunde koyu duman "is" gibi okunuyordu;
    sabah dumani acik gri.
    """
    near, far = (("stone_light", "stone") if dawn
                 else ("stone_dark", "stone_darkest"))
    for i in range(6):
        phase = frame * 0.035 + i * 0.9 + x * 0.11
        drift = math.sin(phase) * (1.0 + i * 0.5)
        puff_x = int(round(x + drift))
        puff_y = y - 3 - i * 4
        if puff_y < -4:
            continue
        size = 1 if i < 2 else 2
        tone = near if i < 3 else far
        surface.fill(palette.color(tone), (puff_x, puff_y, size, size))


def _draw_inn_sign(surface: pygame.Surface, frame: int, x: int, base: int,
                   width: int, height: int) -> None:
    """Han tabelasi: duvardan cikan cubuk ve asili bir tahta, ustunde kupa.

    Tabela hafifce sallaniyor - sabah ruzgari. Hanin siradan bir evden
    ayrilmasinin tek yolu bu; ayri bir bina sprite'i gerekmedi.
    """
    top = base - height
    pole_y = top + 5
    surface.fill(palette.color("earth_dark"), (x + width, pole_y, 6, 1))
    sway = int(round(math.sin(frame * 0.05 + x * 0.1)))
    sx = x + width + 1 + sway
    surface.fill(palette.color("earth_dark"), (sx + 1, pole_y + 1, 1, 2))
    surface.fill(palette.color("earth_dark"), (sx + 5, pole_y + 1, 1, 2))
    surface.fill(palette.color("earth"), (sx, pole_y + 3, 7, 6))
    surface.fill(palette.color("earth_dark"), (sx, pole_y + 8, 7, 1))
    # Kupa: govde + kulp + kopuk.
    surface.fill(palette.color("gold"), (sx + 2, pole_y + 5, 2, 3))
    surface.fill(palette.color("gold"), (sx + 4, pole_y + 6, 1, 1))
    surface.fill(palette.color("bone"), (sx + 2, pole_y + 4, 2, 1))


def _draw_bellframe(surface: pygame.Surface, x: int, base: int,
                    width: int, height: int) -> None:
    """Koy caninin iskelesi: iki direk, ust kiris, kucuk bir cati.

    Canin kendisi `src/world/resonant.py:Bell` - B9'un cani, ayni sinif.
    Iskele yalnizca onu tasiyan ahsap; carpisma yok.
    """
    top = base - height
    surface.fill(palette.color("earth_dark"), (x, top, 2, height))
    surface.fill(palette.color("earth_dark"), (x + width - 2, top, 2, height))
    surface.fill(palette.color("earth"), (x - 3, top, width + 6, 2))
    for i in range(4):
        surface.fill(palette.color("earth_dark"),
                     (x - 3 + i * 2, top - 1 - i, width + 6 - i * 4, 1))

def _draw_well(surface: pygame.Surface, frame: int, x: int, base: int,
               width: int, height: int) -> None:
    top = base - height
    surface.fill(palette.color("stone_darkest"), (x, top, width, height))
    surface.fill(palette.color("stone_dark"), (x - 2, top, width + 4, 2))
    # Direk + makara: siluete dikey bir cizgi katiyor.
    surface.fill(palette.color("earth_dark"), (x + 1, top - 9, 1, 9))
    surface.fill(palette.color("earth_dark"),
                 (x + width - 2, top - 9, 1, 9))
    surface.fill(palette.color("earth"), (x, top - 10, width, 1))
    surface.fill(palette.color("stone"), (x + width // 2, top - 8, 1, 4))

def _draw_fence(surface: pygame.Surface, frame: int, x: int, base: int,
                width: int, height: int) -> None:
    top = base - height
    for i in range(0, width, 5):
        surface.fill(palette.color("earth_dark"), (x + i, top, 1, height))
    surface.fill(palette.color("earth_dark"), (x, top + 2, width, 1))


def draw_sky(surface: pygame.Surface, ox: float, frame: int,
             time_of_day: str = NIGHT) -> None:
    """Gokyuzu katmanlari: yildizlar + ay. Koyden ONCE cizilir.

    Katman hizlari bilerek farkli: yildiz 0.10, ay 0.04 (neredeyse
    sabit - cok uzak), tepeler 0.22/0.35, koy 1.0.

    Safakta: saklanmis gradyan + gunes + acilmis tepeler.
    """
    if time_of_day == DAWN:
        global _dawn_sky
        if _dawn_sky is None:
            _dawn_sky = _build_dawn_sky()
        surface.blit(_dawn_sky, (0, 0))
        _draw_sun(surface, ox)
        _draw_hills(surface, ox, ("stone_dark", "stone_darkest"))
        return
    surface.fill(palette.color("abyss_dark"))
    _draw_stars(surface, ox, frame)
    _draw_moon(surface, ox)
    _draw_hills(surface, ox)
