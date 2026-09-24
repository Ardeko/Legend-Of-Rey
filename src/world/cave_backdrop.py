"""Yeraltinin arka plani - kaya kutlesi, katmanlar, mesaleler.

Bolum 2'de dogdu ama bolume ait degil: Bolum 3, 5, 7... hepsi yeralti.
Bolume ozel yazilsaydi her yeralti bolumu kendi arka planini yeniden icat
ederdi ve hicbiri digerine benzemezdi.

## Magarada gokyuzu yoktur

Ilk hali duz zemin uzerine ayri ayri dikdortgenler koyuyordu ve ekranda
**sehir silueti** gibi okunuyordu: duz tepeli bloklar, aralarinda bos
karanlik. Sorun bloklarda degil, aralarindaki **bosluktaydi** - bos
karanlik gokyuzu gibi okunuyor.

Simdi ekranin tamami kaya. Katmanlar birbirinin ustune biniyor, aralarinda
bosluk degil **dikis** var. Uc kademe:

    abyss_dark   en derin kaya  (parlaklik 25)
    ink          orta kademe    (16)
    void         en yakin kaya  (6) - siluet gibi koyu

Uc kademe **tek yonde** koyulasiyor. Ilk denemede orta kademe en aciktu
(abyss, 46) ve ekranin ortasina mavi bir tepe serisi cizilmis gibi
duruyordu: goz onu arka plan degil **nesne** sanıyordu. Sirali koyulasma
ayni derinligi verirken hicbir katman one ciknmiyor.

Ucunun de tile'lardan (stone_dark 64) belirgin koyu olmasi sart: oyun
alaninin arka plani, oynanan seyin arkasinda kalmali.

## Ofset **tam sayiya** yuvarlanir

Ondalik ofset piksel art dokusunu titretir (CLAUDE.md 9). Parallax
carpanlari ondalik uretmeye en yatkin yer, o yuzden burada acikca
yuvarlaniyor.

## Desen deterministik ve **adim adim** ciziliyor

`random` yok: profil bir hash + iki sinusten uretiliyor, yani kamera geri
donduğunde ayni kaya ayni yerde. Sutun sutun cizmek kare basina 480 fill
demek olurdu; `STEP` piksellik dilimler halinde ciziliyor - 16x16 tile
olceginde fark gorunmuyor, maliyet dortte bire iniyor.

Dikey kulelerde de duvar DUNYAYA baglidir: her katman kendi x/y
parallax ofsetini kullanir. Kaya dilimlerinin iki kenari da duzensiz;
tek bir ufku asagi kaydirip uzun iniste ekrani tek renge boyamayiz.
Sutunlar ve catlaklar ekrandan degil dunya izgara noktasindan baslar.
Kamera bir piksel ilerleyince doku yeniden uretilmis gibi kipirdamaz.
"""
from __future__ import annotations

import math
import random

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE

FAR_PARALLAX = 0.22
MID_PARALLAX = 0.38
NEAR_PARALLAX = 0.60
STEP = 3                         # Profil dilimi genisligi (piksel)

# Kaya dikislerinin taban yuksekligi ve dalga genligi.
# Harita 16 tile (256 piksel) yuksekliginde ve ekran 270; oyun alani
# satir 4-13 arasi, yani ekranda kabaca y=70..230. Dikisler bu bandin
# **icinde** kalmali, yoksa tavan tile'larinin arkasinda kaybolurlar.
FAR_BASE, FAR_AMP = 186, 26
MID_BASE, MID_AMP = 132, 22
NEAR_BASE, NEAR_AMP = 74, 18

STRATA_SPACING = 19              # Yatay kaya katmanlari arasi
CRACK_SPACING = 61               # Duvardaki dusey yarik araligi
MID_STRIDE, MID_DEPTH = 384, 175
NEAR_STRIDE, NEAR_DEPTH = 416, 128

# --- Derinlik (23.09.2026) ---------------------------------------------------
# Arda: *"Oyunda asagi indikce etrafa hareketli lav grafikleri gelebilir,
# ortam hafif morarabilir."*
#
# `depth` 0..1: B2 sifir, B18 bir (`depth_for`). Lav bir ESIKten sonra
# basliyor ve sikligi derinlikle artiyor - ilk gorulen tek bir uzak
# selale olmali, oyuncu "asagida bir sey var" desin. B18'de duvarlar
# damarlarla kapli.
#
# Selaleler **uzak katmanda**: uzak duvarin bir yarigindan dokulup orta
# kaya sirtinin ARKASINA iniyor; sirtin kenari alttan kor isigiyla
# aydinlaniyor - "tepelerin ardinda bir lav golu var". Ilk deneme orta
# katmandaydi ve yatay bolumlerde yakin kaya alt ucunu kesiyordu: havada
# asili kisa turuncu cubuklar gibi okundu (olculdu, B10/B14/B18).
# Parlaklik kucuk alanlarda; genis parlak yuzey yok - arka plan oynananin
# arkasinda kalmali.
LAVA_START = 0.30                # B7'den itibaren (depth 0.3125)
LAVA_FALL_SPACING = 157          # Selale adaylarinin dunya araligi (uzak katman)
LAVA_BAND = 300                  # Uzak katmanda dikey tekrar (dikey kuleler)
LAVA_MAX_LENGTH = 210
LAVA_MIN_VISIBLE = 26            # Bundan kisa gorunen selale hic cizilmez
VEIN_START = 0.43                # Magma damarlari B9'dan itibaren (0.4375)
LAVA_SCROLL_FRAMES = 3           # Akis: 3 karede bir piksel - agir, yapiskan
LAVA_TEXTURE_HEIGHT = 24
LAVA_WIDTH = 3

# --- Sis (24.09.2026) --------------------------------------------------------
# Arda: *"grafikleri daha modern gercekci olarak gelistir."* Arka plan
# katmanlari keskin sinirlarla ust uste biniyordu; gercek bir magarada
# uzak kaya HAVANIN arkasinda kalir (atmosfer perspektifi). Iki yavas sis
# seridi yakin kaya sirtlarinin ustunu yumusatiyor. Renk derinlikle
# degisiyor: mavi -> mor -> kor (altta lav var).
#
# Sis **arka planin** parcasi: karolardan ve aktorlerden once ciziliyor,
# yani oynanan hicbir sey sisin arkasinda kalmiyor.
FOG_WIDTH, FOG_HEIGHT = 512, 90
FOG_ALPHA = 58                   # en yogun yerde
FOG_LAYERS = (                   # (parallax, suruklenme px/kare, ekran y)
    (0.45, 0.10, 118),
    (0.70, 0.22, 158),
)


def depth_for(chapter: int) -> float:
    """Bolum numarasindan derinlik: B2 = 0, B18 = 1."""
    return max(0.0, min(1.0, (chapter - 2) / 16.0))


def _profile(x: int, seed: int, base: int, amp: int) -> int:
    """Bir sutundaki kaya yuksekligi. Deterministik, surekli.

    Iki farkli frekansta sinus + hash: tek sinus dalgali bir tepe gibi
    okunuyordu (cok duzenli), saf hash ise gurultu gibi (cok duzensiz).
    Ikisinin toplami kaya gibi okunuyor.
    """
    value = base
    value += amp * math.sin((x + seed) * 0.0170)
    value += amp * 0.45 * math.sin((x + seed) * 0.0413 + 1.7)
    value += ((x * 2654435761 + seed) >> 9) & 5
    return int(value)


def _slab_edges(x: int, band: int, seed: int, base: int, amp: int,
                stride: int, depth: int) -> tuple[int, int]:
    """Sonsuz kaya duvarinda bir dilimin iki dogal, dunya-sabit kenari."""
    band_seed = seed + band * 137
    top = band * stride + INTERNAL_HEIGHT - _profile(x, band_seed, base, amp)
    bottom = (band * stride + INTERNAL_HEIGHT - base + depth
              - _profile(x, band_seed + 911, 0, max(4, amp // 2)))
    return top, bottom


def _draw_layer(surface: pygame.Surface, shift: tuple[int, int], colour,
                seed: int, base: int, amp: int, stride: int, depth: int) -> None:
    """Kayanin alt kenari da var; dikey yolculukta yeni dilimler gorulur."""
    sx, sy = shift
    width, height = surface.get_size()
    for band in range((sy - INTERNAL_HEIGHT - depth) // stride,
                      (sy + height) // stride + 1):
        anchor = band * stride + INTERNAL_HEIGHT - base
        # Gorunmeyen dilimde yuzlerce profil degerini hesaplamayiz.
        if anchor - amp * 1.5 - 8 > sy + height or anchor + depth + amp < sy:
            continue
        for world_x in range((sx // STEP) * STEP, sx + width, STEP):
            top, bottom = _slab_edges(world_x, band, seed, base, amp,
                                      stride, depth)
            top = max(0, top - sy)
            bottom = min(height, bottom - sy)
            if bottom > top:
                surface.fill(colour, (world_x - sx, top, STEP, bottom - top))


def draw(surface: pygame.Surface, offset: tuple[int, int],
         frame: int = 0, depth: float = 0.0) -> None:
    """Magara arka plani. Zeminden **once** cizilir.

    `depth` (0..1) lav ve morarmayi acar - bkz. `depth_for`.
    """
    ox, oy = offset
    far = (round(ox * FAR_PARALLAX), round(oy * FAR_PARALLAX))
    mid = (round(ox * MID_PARALLAX), round(oy * MID_PARALLAX))
    near = (round(ox * NEAR_PARALLAX), round(oy * NEAR_PARALLAX))
    # Taban dolgu: ekranda bos karanlik kalmiyor - magarada gokyuzu yok.
    surface.fill(palette.color("abyss_dark"))

    _draw_strata(surface, far, depth)
    _draw_niches(surface, far)
    if depth >= LAVA_START:
        # Orta kayadan ONCE: sirt selalenin alt ucunu ve halenin yarisini
        # ortuyor, isik kenarin ardindan tasiyor.
        _draw_lava_falls(surface, far, mid, frame, depth)
    _draw_layer(surface, mid, palette.color("ink"), 311,
                MID_BASE, MID_AMP, MID_STRIDE, MID_DEPTH)
    _draw_cracks(surface, mid)
    if depth >= VEIN_START:
        _draw_magma_veins(surface, mid, frame, depth)
    _draw_layer(surface, near, palette.color("void"), 977,
                NEAR_BASE, NEAR_AMP, NEAR_STRIDE, NEAR_DEPTH)
    _draw_stalactites(surface, near)
    _draw_fog(surface, (ox, oy), frame, depth)
    _draw_haze(surface, frame, depth)


def _draw_strata(surface: pygame.Surface, shift: tuple[int, int],
                 depth: float = 0.0) -> None:
    """Yatay kaya katmanlari - derin kayanin uzerinde sonuk cizgiler.

    Tek basina dolgu duz bir duvar gibi okunuyor. Katmanlar hem doku
    veriyor hem de yeralti oldugunu anlatiyor: bu cizgiler tortul kaya.
    """
    sx, sy = shift
    width, height = surface.get_size()
    # Derinde tortul kaya morariyor - palet degisimi, karistirma degil.
    colour = palette.color("violet_dark" if depth >= 0.55 else "abyss")
    span = STEP * 3
    for index in range((sy - 4) // STRATA_SPACING,
                       (sy + height + 4) // STRATA_SPACING + 1):
        # Katmanlar **kesik**. Ilk hali ekrani bastan basa kesen duz
        # cizgiler ciziyordu ve cizgili kagit gibi okunuyordu: kaya
        # katmani sureklidir ama duz degildir, ustelik cogu yeri baska
        # kayanin altinda kalir.
        for world_x in range((sx // span) * span, sx + width, span):
            seed = (world_x + index * 137) * 2654435761
            if (seed >> 12) & 3:         # Dortte biri ciziliyor
                continue
            wobble = int(round(math.sin((world_x + index * 17) * 0.027) * 3))
            y = index * STRATA_SPACING + wobble - sy
            surface.fill(colour, (world_x - sx, y, span, 1))


def _draw_niches(surface: pygame.Surface, shift: tuple[int, int]) -> None:
    """Kayaya oyulmus seyrek kor kemerler: uzakta kalmis eski duvar izi.

    Tam bir kapi veya gecilebilir platform degil; alt cizgisi yok.
    Iki kirik kenar ve tas ekleri, genel kaya kutlesini insan yapimina
    baglar. Isik eklenmez, mevcut uzak katmanin tonlari kullanilir.
    """
    sx, sy = shift
    width, height = surface.get_size()
    spacing_x, spacing_y = 246, 294
    dark, edge = palette.color("ink"), palette.color("abyss")
    for row in range((sy - 130) // spacing_y, (sy + height) // spacing_y + 1):
        for column in range((sx - 90) // spacing_x, (sx + width) // spacing_x + 1):
            seed = (column * 971 + row * 131) & 0xFFFF
            x = column * spacing_x + 41 + seed % 27 - sx
            y = row * spacing_y + 53 + (seed >> 5) % 31 - sy
            w = 48 + seed % 17
            points = [(x, y + 80), (x, y + 22), (x + 5, y + 22),
                      (x + 5, y + 12), (x + 12, y + 12), (x + 12, y + 5),
                      (x + 20, y), (x + w - 20, y),
                      (x + w - 12, y + 5), (x + w - 12, y + 12),
                      (x + w - 5, y + 12), (x + w - 5, y + 22),
                      (x + w, y + 22), (x + w, y + 80)]
            pygame.draw.lines(surface, dark, False, points, 3)
            for side in (x, x + w):
                for step in (32, 49, 66):
                    surface.fill(edge, (side - 1, y + step, 3, 1))
            surface.fill(edge, (x + 20, y, 6, 1))


def _draw_cracks(surface: pygame.Surface, shift: tuple[int, int]) -> None:
    """Duvarda dusey yariklar. Dikey vurgu yoksa magara yatay bir seride
    donusuyor."""
    sx, sy = shift
    width, height = surface.get_size()
    colour = palette.color("void")
    band_height = 173
    for band in range((sy - 130) // band_height, (sy + height) // band_height + 1):
        for wx in range((sx // CRACK_SPACING) * CRACK_SPACING,
                        sx + width + CRACK_SPACING, CRACK_SPACING):
            seed = (wx * 2246822519 + band * 131) & 0xFFFF
            top = band * band_height + 30 + seed % 50 - sy
            length = 40 + (seed >> 5) % 65
            points = [(wx - sx + ((seed >> (i % 11)) & 3), top + i)
                      for i in range(0, length, 5)]
            pygame.draw.lines(surface, colour, False, points)


def _draw_stalactites(surface: pygame.Surface, shift: tuple[int, int]) -> None:
    """Tavandan sarkan disler. En yakin katman - siluet gibi koyu."""
    sx, sy = shift
    width, height = surface.get_size()
    colour = palette.color("void")
    spacing = 23
    for band in range((sy - INTERNAL_HEIGHT - NEAR_DEPTH - 40) // NEAR_STRIDE,
                      (sy + height) // NEAR_STRIDE + 1):
        for wx in range((sx // spacing) * spacing - spacing,
                        sx + width + spacing, spacing):
            seed = (wx * 40503 + band * 131 + 12345) & 0xFFFF
            length = 12 + seed % 26
            # Kok, en yakin kaya diliminin alt kenarina gomulur.
            _, root = _slab_edges(wx, band, 977, NEAR_BASE, NEAR_AMP,
                                  NEAR_STRIDE, NEAR_DEPTH)
            y = root - sy - 5
            if y >= height or y + length < 0:
                continue
            x = wx - sx
            pygame.draw.polygon(surface, colour,
                                ((x - 4, y), (x + 4, y), (x, y + length)))


def _draw_haze(surface: pygame.Surface, frame: int, depth: float = 0.0) -> None:
    """Alt kenarda yavasca kabaran sis. Derinligi tabandan da anlatir.

    Derinde sis morariyor; en dipte altindan lav isigi vuruyor: sisin en
    alt iki cizgisi kor rengine donup nabiz atiyor.
    """
    colour = palette.color("violet_dark" if depth >= 0.5 else "abyss")
    for i in range(4):
        wave = math.sin(frame * 0.011 + i * 1.7)
        y = INTERNAL_HEIGHT - 6 - i * 3 + int(round(wave * 1.5))
        surface.fill(colour, (0, y, INTERNAL_WIDTH, 1))
    if depth >= 0.75:
        pulse = (frame // 8) % 6
        ember = palette.color("ember_dark" if pulse else "ember")
        for i in range(2):
            wave = math.sin(frame * 0.017 + i * 2.3)
            y = INTERNAL_HEIGHT - 2 - i * 2 + int(round(wave))
            surface.fill(ember, (0, y, INTERNAL_WIDTH, 1))


# --- Lav ---------------------------------------------------------------------
_lava_texture: dict[str, pygame.Surface] = {}


def clear_cache() -> None:
    _lava_texture.clear()
    _fog_texture.clear()


# --- Sis ---------------------------------------------------------------------
_fog_texture: dict[str, pygame.Surface] = {}


def _fog_colour(depth: float) -> str:
    if depth >= 0.8:
        return "ember_dark"
    if depth >= 0.45:
        return "violet_dark"
    return "abyss"


def _fog(colour: str) -> pygame.Surface:
    """Yatayda dikissiz tekrar eden yumusak sis - **bir kez** uretilir.

    Deterministik (sabit tohum): kamera geri donunce ayni bulut ayni yerde.
    Yumusaklik iki kez kucultup buyutmekten geliyor - bu bir isik/hava
    katmani, piksel sanat degil (`smoothscale` yasagi sprite icin).
    """
    image = _fog_texture.get(colour)
    if image is not None:
        return image
    rng = random.Random(4417)
    rough = pygame.Surface((FOG_WIDTH // 8, FOG_HEIGHT // 8), pygame.SRCALPHA)
    tone = palette.color(colour)
    w, h = rough.get_size()
    for _ in range(26):
        x = rng.randrange(w)
        y = rng.randrange(2, h - 2)
        radius = rng.randint(2, 4)
        strength = rng.randint(90, 200)
        for dx in (-w, 0, w):            # yatay dikissiz sarma
            pygame.draw.circle(rough, (*tone, strength), (x + dx, y), radius)
    mid = pygame.transform.smoothscale(rough, (FOG_WIDTH // 2, FOG_HEIGHT // 2))
    image = pygame.transform.smoothscale(mid, (FOG_WIDTH, FOG_HEIGHT))
    # Ust ve alt kenar sifira insin - bant "serit" gibi kesilmesin.
    fade = pygame.Surface((FOG_WIDTH, FOG_HEIGHT), pygame.SRCALPHA)
    for y in range(FOG_HEIGHT):
        edge = min(y, FOG_HEIGHT - 1 - y) / (FOG_HEIGHT * 0.5)
        level = int(255 * min(1.0, edge * 1.6) * FOG_ALPHA / 255)
        fade.fill((255, 255, 255, level), (0, y, FOG_WIDTH, 1))
    image.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    if pygame.display.get_init() and pygame.display.get_surface() is not None:
        image = image.convert_alpha()
    _fog_texture[colour] = image
    return image


def _draw_fog(surface: pygame.Surface, offset: tuple[int, int], frame: int,
              depth: float) -> None:
    """Iki sis seridi: farkli parallax ve suruklenme - derinlik hissi."""
    texture = _fog(_fog_colour(depth))
    width = surface.get_width()
    ox, _ = offset
    for parallax, drift, y in FOG_LAYERS:
        # Ofset TAM SAYI (CLAUDE.md 9): ondalik ofset piksel dokusunu titretir.
        shift = int(ox * parallax + frame * drift) % FOG_WIDTH
        x = -shift
        while x < width:
            surface.blit(texture, (x, y))
            x += FOG_WIDTH


def _texture() -> pygame.Surface:
    """Selalenin tekrar eden dokusu - **bir kez** uretilir (`CLAUDE.md` 4).

    Dort sutun: iki kenar koyu kor, ortada acik akis cizgileri. Cizgiler
    farkli periyotlarda - ayni periyotta olsalar merdiven gibi okunuyor.
    """
    image = _lava_texture.get("fall")
    if image is not None:
        return image
    image = pygame.Surface((LAVA_WIDTH, LAVA_TEXTURE_HEIGHT))
    dark, mid = palette.color("ember_dark"), palette.color("ember")
    light, hot = palette.color("ember_light"), palette.color("gold")
    for y in range(LAVA_TEXTURE_HEIGHT):
        # Sol sutun isikta (sol-ust kurali), sag sutun golgede.
        image.set_at((0, y), light if (y // 3) % 4 == 0 else mid)
        image.set_at((1, y), hot if y % 8 == 2 else (light if (y // 2) % 3 == 0 else mid))
        image.set_at((2, y), mid if (y // 4) % 3 == 1 else dark)
    if pygame.display.get_init() and pygame.display.get_surface() is not None:
        image = image.convert()
    _lava_texture["fall"] = image
    return image


def _chance(seed: int, depth: float, start: float) -> bool:
    """Adayin bu derinlikte var olup olmadigi - deterministik.

    Esikte yaklasik %15, dipte %70. Rastgele degil: kamera geri donunce
    ayni selale ayni yerde.
    """
    share = 0.15 + 0.55 * max(0.0, (depth - start) / max(0.01, 1.0 - start))
    return (seed & 0xFF) < int(share * 256)


def _draw_lava_falls(surface: pygame.Surface, far: tuple[int, int],
                     mid: tuple[int, int], frame: int, depth: float) -> None:
    """Uzak duvardan dokulup orta kaya sirtinin ardina inen lav.

    Selale uzak katmanin bir yarigindan basliyor ve **orta kayanin ust
    kenarinda** bitiyor (o kaya zaten onune ciziliyor). Bittigi yerde
    bir hale: orta kaya ciziminde yarisi ortuluyor, kalan yarisi sirtin
    kenarini alttan aydinlatiyor. Doku asagi kayarak akiyor.
    """
    sx, sy = far
    width, height = surface.get_size()
    texture = _texture()
    scroll = (frame // LAVA_SCROLL_FRAMES) % LAVA_TEXTURE_HEIGHT
    for band in range((sy - LAVA_MAX_LENGTH) // LAVA_BAND,
                      (sy + height) // LAVA_BAND + 1):
        for column in range((sx - 8) // LAVA_FALL_SPACING,
                            (sx + width + 8) // LAVA_FALL_SPACING + 1):
            seed = ((column * 2654435761) ^ (band * 40503)) & 0xFFFFFF
            if not _chance(seed >> 4, depth, LAVA_START):
                continue
            x = column * LAVA_FALL_SPACING + (seed >> 12) % 89 - sx
            if x < -8 or x > width + 8:
                continue
            y0 = band * LAVA_BAND + 12 + (seed >> 7) % 40 - sy
            ridge = _mid_top_below(x + LAVA_WIDTH // 2, y0, mid, height)
            y1 = min(y0 + LAVA_MAX_LENGTH, ridge if ridge is not None
                     else y0 + LAVA_MAX_LENGTH)
            if min(y1, height) - max(y0, 0) < LAVA_MIN_VISIBLE:
                continue
            _blit_fall(surface, texture, x, y0, y1, scroll)
            # Yarik agzi - lavin ciktigi yer, koyu bir dudak.
            surface.fill(palette.color("ink"), (x - 1, y0 - 1, LAVA_WIDTH + 2, 2))
            if ridge is not None and y1 == ridge:
                _draw_ridge_glow(surface, x + LAVA_WIDTH // 2, ridge,
                                 frame + (seed & 63))


def _mid_top_below(screen_x: int, y: int, mid: tuple[int, int],
                   height: int) -> int | None:
    """Ekranin bu sutununda, `y`nin altindaki ilk orta kaya ust kenari."""
    mx, my = mid
    world_x = screen_x + mx
    best = None
    for band in range((my + y - INTERNAL_HEIGHT - MID_DEPTH) // MID_STRIDE,
                      (my + height) // MID_STRIDE + 2):
        top, bottom = _slab_edges(world_x, band, 311, MID_BASE, MID_AMP,
                                  MID_STRIDE, MID_DEPTH)
        top -= my
        bottom -= my
        if bottom <= y:
            continue
        candidate = max(top, y)
        if best is None or candidate < best:
            best = candidate
    return best


def _blit_fall(surface: pygame.Surface, texture: pygame.Surface, x: int,
               y0: int, y1: int, scroll: int) -> None:
    top = max(0, y0)
    bottom = min(surface.get_height(), y1)
    if bottom <= top:
        return
    # Doku selalenin basina bagli kayiyor: ilk parca `y0 - H + scroll`.
    start = y0 - LAVA_TEXTURE_HEIGHT + scroll
    while start + LAVA_TEXTURE_HEIGHT <= top:
        start += LAVA_TEXTURE_HEIGHT
    clip = surface.get_clip()
    surface.set_clip(pygame.Rect(x, top, LAVA_WIDTH, bottom - top).clip(clip))
    y = start
    while y < bottom:
        surface.blit(texture, (x, y))
        y += LAVA_TEXTURE_HEIGHT
    surface.set_clip(clip)
    # Hafif isik: selalenin iki yanina tek piksel kor yansimasi.
    edge = palette.color("ember_dark")
    surface.fill(edge, (x - 1, top, 1, bottom - top))
    surface.fill(edge, (x + LAVA_WIDTH, top, 1, bottom - top))


def _draw_ridge_glow(surface: pygame.Surface, x: int, y: int, frame: int) -> None:
    """Selalenin sirtin ardina indigi yer: hale ve 8 FPS sicrama.

    Hale orta kayadan once ciziliyor; kaya alt yarisini ortuyor ve isik
    kenarin ARDINDAN tasiyormus gibi okunuyor.
    """
    if y < -12 or y > surface.get_height() + 12:
        return
    pulse = 0.85 + 0.15 * math.sin(frame * 0.05)
    glow = radial_glow(22, palette.color("ember_dark"), peak=pulse)
    surface.blit(glow, (x - 22, y - 16), special_flags=pygame.BLEND_RGB_ADD)
    surface.fill(palette.color("ember"), (x - 4, y - 1, 9, 1))
    surface.fill(palette.color("ember_light"), (x - 2, y - 1, 5, 1))
    step = (frame // 8) % 4
    if step < 3:
        for dx, lift in ((-3, 2), (2, 3), (4, 1)):
            h = lift - abs(step - 1)
            if h > 0:
                surface.fill(palette.color("gold"), (x + dx, y - 2 - h, 1, 1))


def _draw_magma_veins(surface: pygame.Surface, shift: tuple[int, int],
                      frame: int, depth: float) -> None:
    """Duvardaki yariklarin bir kismi icten kor yaniyor.

    Mevcut yarik izgarasini kullaniyor (`_draw_cracks` ile ayni tohum),
    yani damar bir yarigin ICINDE - kayaya sonradan yapistirilmis bir
    cizgi degil. Isik yarik boyunca asagi dogru akiyor: 8 FPS'lik bir
    dalga, her parca kendi fazinda.
    """
    sx, sy = shift
    width, height = surface.get_size()
    dark, mid = palette.color("ember_dark"), palette.color("ember")
    band_height = 173
    for band in range((sy - 130) // band_height, (sy + height) // band_height + 1):
        for wx in range((sx // CRACK_SPACING) * CRACK_SPACING,
                        sx + width + CRACK_SPACING, CRACK_SPACING):
            seed = (wx * 2246822519 + band * 131) & 0xFFFF
            if not _chance((seed * 7919) >> 5, depth, VEIN_START):
                continue
            top = band * band_height + 30 + seed % 50 - sy
            length = 40 + (seed >> 5) % 65
            points = [(wx - sx + ((seed >> (i % 11)) & 3), top + i)
                      for i in range(0, length, 5)]
            if len(points) < 2:
                continue
            pygame.draw.lines(surface, dark, False, points)
            wave = frame // 8
            for index in range(len(points) - 1):
                if (index - wave) % 5 == 0:
                    pygame.draw.line(surface, mid, points[index], points[index + 1])
            cx, cy = points[len(points) // 2]
            glow = radial_glow(9, palette.color("ember_dark"), peak=0.55)
            surface.blit(glow, (cx - 9, cy - 9), special_flags=pygame.BLEND_RGB_ADD)


def draw_torches(surface: pygame.Surface, offset: tuple[int, int],
                 torches, frame: int = 0) -> None:
    """Mesaleler. `torches` (tile_x, tile_y, yaniyor_mu) uclusu.

    **Tavana asili** ciziliyor: sap yukari uzanip tavan tile'ina giriyor.
    Ilk hali sapi asagi uzatiyordu ve mesale havada asili duruyordu -
    hicbir seye baglanmayan bir isik kaynagi sahneyi bozuyor.

    Sonmus mesale de ciziliyor: gizli odadaki sonmus mesale bir **anlati**
    parcasi - buraya birisi gelmis ve donmemis.
    """
    ox, oy = offset
    for tile_x, tile_y, lit in torches:
        x = tile_x * TILE_SIZE + TILE_SIZE // 2 - ox
        y = tile_y * TILE_SIZE - oy
        if x < -40 or x > INTERNAL_WIDTH + 40:
            continue                     # Gorunmeyeni cizme

        # Sap: tavandan asagi sarkiyor. Tepesi tile sinirinin bir piksel
        # ustunde - tavana **girmis** gorunsun.
        surface.fill(palette.color("earth_dark"), (x, y - 1, 2, 8))
        surface.fill(palette.color("ink"), (x + 2, y - 1, 1, 8))

        if not lit:
            surface.fill(palette.color("ink"), (x - 1, y + 7, 4, 3))
            continue

        # Alev sapin **ucunda**, uc kareli bir dongude oynuyor.
        flicker = (frame // 6 + tile_x) % 3
        surface.fill(palette.color("ember"), (x - 1, y + 7, 4, 5 - flicker))
        surface.fill(palette.color("gold"), (x, y + 8, 2, 3 - flicker))
        glow = radial_glow(30, palette.color("ember"),
                           peak=0.46 + 0.05 * math.sin(frame * 0.09 + tile_x))
        surface.blit(glow, (x - 29, y - 21),
                     special_flags=pygame.BLEND_RGB_ADD)
