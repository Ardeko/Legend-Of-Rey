"""Onbelleklenen tas, ahsap ve diken karolari - dort derinlik temasiyla.

Tasin sol/ust yuzu isik, sag/alt yuzu golge alir. Kenar yalnizca o
yonde bosluk varsa cizilir; dolu duvarin her 16 pikselinde yapay bir
karo cercevesi olusmaz. Dort tas varyanti dunya koordinatindan secilir:
kamera donunce doku degismez, kirilabilir duvar kendini ele vermez.

Uretim yalnizca onbellek iskalamasinda yapilir. Renkler uretim aninda
aktif paletten okunur; mevcut clear_cache yolu erisilebilirlik ve ekran
bicimi degisikliklerinde butun karolari birlikte yeniler.

## Kutle ici karartma (23.09.2026)

Arda: *"grafikleri gelistir."* Olculen sorun: tavan ve zemin bantlari
ekranin ~%35'i ve **ici de yuzeyi kadar aydinlikti** - duz gri bir
duvar kagidi. Artik her kati karonun havaya uzakligi var (`depth`):

    0   havaya komsu      tam aydinlik tas, kenar isigi, suslemeler
    1   bir karo iceride  koyu tas
    2   iki karo          neredeyse siyah tas
    3+  kutlenin kalbi    siyah, seyrek iz

Goz yalnizca **oynanan yuzeyi** goruyor; kaya kutlesi karanliga
gomuluyor. Kirilabilir duvar ayni hesaba giriyor (kati sayiliyor), yani
hala ayirt edilemez.

## Derinlik temalari

B2'den B18'e ayni gri tugla vardi; asagi inmek gorsel olarak
hissedilmiyordu. Tema bolum numarasindan (`theme_for`):

    zindan   B1-B6    yontulmus tugla - insan yapisi ust katlar
    magara   B7-B11   yuvarlak dogal tas, yosun, sarkan kok
    bazalt   B12-B15  sutunlu koyu kaya, mor derz, mor kristal
    cekirdek B16-B18  obsidyen levha, kor catlaklari, kor sarkitlari

Oynanan yuzeyin (ust kenar isigi) parlakligi dort temada da AYNI -
okunurluk temayla degismiyor, yalnizca doku ve sus degisiyor.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.art import palette
from src.config import TILE_SIZE

WALL_VARIANTS = 4
PLATFORM_VARIANTS = 2
MAX_DEPTH = 3

EDGE_LEFT = 1
EDGE_RIGHT = 2
EDGE_BOTTOM = 4
_SIDE_MASK = EDGE_LEFT | EDGE_RIGHT | EDGE_BOTTOM
_ROW_HEIGHT = 8

# Suslerin yuksekligi (karo disina tasan kisim, piksel).
PROP_HEIGHT = 8


@dataclass(frozen=True)
class Theme:
    """Bir derinlik kademesinin tas dili. Butun renkler palet adi."""

    name: str
    pattern: str                    # brick | cobble | basalt | slab
    mortar: str
    face: str
    chisel: str                     # sol-ust keski isigi
    pit: str
    # Derinlik 1, 2, 3 icin (derz, yuz).
    deep: tuple[tuple[str, str], ...]
    # Ust yuzey susu, alt yuzey (tavan alti) susu. Bos: yok.
    top_prop: str = ""
    hang_prop: str = ""
    # Kac karede bir sus (dunya hash'i ile secilir).
    top_every: int = 5
    hang_every: int = 6


THEMES: dict[str, Theme] = {
    "dungeon": Theme(
        "dungeon", "brick", "stone_darkest", "stone_dark", "stone",
        "stone_darkest",
        deep=(("ink_soft", "stone_darkest"), ("ink", "ink_soft"), ("ink", "ink")),
        top_prop="rubble", hang_prop="drip", top_every=6, hang_every=7),
    "cavern": Theme(
        "cavern", "cobble", "ink_soft", "stone_dark", "stone",
        "ink_soft",
        deep=(("ink", "stone_darkest"), ("ink", "ink_soft"), ("void", "ink")),
        top_prop="moss", hang_prop="roots", top_every=3, hang_every=3),
    "basalt": Theme(
        "basalt", "basalt", "violet_dark", "stone_dark", "stone",
        "ink_soft",
        deep=(("violet_dark", "stone_darkest"), ("ink", "ink_soft"),
              ("void", "ink")),
        top_prop="crystal", hang_prop="shard", top_every=5, hang_every=5),
    "core": Theme(
        "core", "slab", "ink", "stone_darkest", "stone_dark",
        "ink",
        deep=(("ink", "ink_soft"), ("void", "ink"), ("void", "ink")),
        top_prop="cinder", hang_prop="ember_drip", top_every=4, hang_every=4),
}
DEFAULT_THEME = "dungeon"


def theme_for(chapter: int) -> str:
    """Bolum numarasindan tema - bkz. modul basligi."""
    if chapter >= 16:
        return "core"
    if chapter >= 12:
        return "basalt"
    if chapter >= 7:
        return "cavern"
    return "dungeon"


def _theme(name: str) -> Theme:
    return THEMES.get(name, THEMES[DEFAULT_THEME])


# --- Desenler ----------------------------------------------------------------
def _brick_course(surface: pygame.Surface, variant: int, row: int,
                  face: str, chisel: str, pit: str) -> None:
    """Daha genis tas yuzleri; az sayida oyuk, sol ustte kisa keski izi."""
    y = row * _ROW_HEIGHT
    step = 10 + (variant % 3) * 2
    shift = (variant * 3 + row * 6) % step
    x = shift - step
    while x < TILE_SIZE:
        pygame.draw.rect(surface, palette.color(face),
                         (x + 1, y + 1, step - 1, _ROW_HEIGHT - 2))
        # Keski izi tum tas boyunca parlak serit olusturmaz. Harc ve
        # tasin alt yuzu ayni koyu ailede; duvar karakterlerden rol calmaz.
        if chisel:
            pygame.draw.line(surface, palette.color(chisel),
                             (x + 2, y + 1), (x + step // 2 + 1, y + 1))
        pit_x = x + 3 + (variant + row) % max(1, step - 5)
        pygame.draw.line(surface, palette.color(pit),
                         (pit_x, y + 4), (pit_x + 1, y + 4))
        if chisel and (variant + row) % 3 == 0:
            pygame.draw.line(surface, palette.color(chisel),
                             (x + step - 4, y + 3), (x + step - 3, y + 3))
        x += step


def _cobble(surface: pygame.Surface, variant: int, face: str, chisel: str,
            pit: str, mortar: str) -> None:
    """Dogal tas: yuvarlatilmis, farkli boylarda iri cakil.

    Koseler derz rengine kirpiliyor - tugla gibi keskin degil, suyun
    asindirdigi tas gibi.
    """
    widths = ((7, 9), (5, 6, 5), (9, 7), (6, 5, 5))[variant % 4]
    heights = ((7, 9), (9, 7), (6, 10), (8, 8))[variant % 4]
    y = 0
    for row, height in enumerate(heights):
        x = -((variant + row * 3) % 4)
        for index in range(8):
            width = widths[(index + row) % len(widths)]
            rect = pygame.Rect(x + 1, y + 1, width - 1, height - 1)
            surface.fill(palette.color(face), rect)
            for cx, cy in ((rect.left, rect.top), (rect.right - 1, rect.top),
                           (rect.left, rect.bottom - 1),
                           (rect.right - 1, rect.bottom - 1)):
                surface.set_at((cx, cy), palette.color(mortar))
            if chisel:
                surface.fill(palette.color(chisel), (rect.left + 1, rect.top, max(1, width // 2 - 1), 1))
                surface.fill(palette.color(chisel), (rect.left, rect.top + 1, 1, max(1, height // 3)))
            surface.set_at((rect.centerx, rect.centery + 1), palette.color(pit))
            x += width
            if x >= TILE_SIZE:
                break
        y += height


def _basalt(surface: pygame.Surface, variant: int, face: str, chisel: str,
            pit: str, mortar: str) -> None:
    """Sutunlu bazalt: dikey prizmalar, her birinde kaymis bir eklem.

    Komsu prizmalar iki tonda: tek tonlu hali ahsap panel gibi okundu
    (olculdu, B13). Isikli yuz `face`, golgedeki yuz bir kademe koyu.
    """
    shade = palette.color("stone_darkest" if face == "stone_dark" else "ink")
    x = -((variant * 2) % 6)
    column = 0
    while x < TILE_SIZE:
        width = 6 + (variant + column) % 2
        lit = (column + variant) % 2 == 0
        surface.fill(palette.color(face) if lit else shade,
                     (x + 1, 0, width - 1, TILE_SIZE))
        joint = (variant * 5 + column * 7) % TILE_SIZE
        surface.fill(palette.color(mortar), (x + 1, joint, width - 1, 1))
        if chisel and lit:
            # Prizmanin sol yuzu isikta - sol-ust kurali.
            surface.fill(palette.color(chisel), (x + 1, 0, 1, TILE_SIZE))
            surface.fill(palette.color(chisel), (x + 2, (joint + 1) % TILE_SIZE, 2, 1))
        surface.set_at((x + 3, (joint + 8) % TILE_SIZE), palette.color(pit))
        x += width
        column += 1


def _slab(surface: pygame.Surface, variant: int, face: str, chisel: str,
          pit: str, mortar: str) -> None:
    """Obsidyen levhalar: capraz kirilmis iri, parlak yuzler."""
    surface.fill(palette.color(face))
    cut = 4 + variant * 3
    pygame.draw.line(surface, palette.color(mortar), (0, cut),
                     (TILE_SIZE - 1, (cut + 7) % TILE_SIZE))
    pygame.draw.line(surface, palette.color(mortar), (cut, 0),
                     ((cut + 5) % TILE_SIZE, TILE_SIZE - 1))
    if chisel:
        # Cam gibi parlama - obsidyen. Kisa, keskin.
        surface.fill(palette.color(chisel), (1, 1, 3, 1))
        surface.fill(palette.color(chisel), (cut + 2, cut + 2, 2, 1))
    surface.set_at((11 - variant, 12), palette.color(pit))


def _pattern(surface: pygame.Surface, theme: Theme, variant: int,
             depth: int) -> None:
    """Temanin desenini `depth`e gore koyulasmis renklerle basar."""
    if depth <= 0:
        mortar, face = theme.mortar, theme.face
        chisel, pit = theme.chisel, theme.pit
    else:
        mortar, face = theme.deep[min(depth, MAX_DEPTH) - 1]
        # Iceride keski isigi yok: isik yalnizca yuzeye vuruyor.
        chisel, pit = "", mortar
    surface.fill(palette.color(mortar))
    if depth >= MAX_DEPTH:
        # Kutlenin kalbi: duz karanlik + seyrek iz (doku tamamen
        # kaybolunca ekranda "delik" gibi okunuyordu).
        surface.set_at((3 + variant * 3, 5 + variant), palette.color(face))
        surface.set_at((11 - variant * 2, 12 - variant), palette.color(face))
        return
    if theme.pattern == "cobble":
        _cobble(surface, variant, face, chisel, pit, mortar)
    elif theme.pattern == "basalt":
        _basalt(surface, variant, face, chisel, pit, mortar)
    elif theme.pattern == "slab":
        _slab(surface, variant, face, chisel, pit, mortar)
    else:
        for row in range(TILE_SIZE // _ROW_HEIGHT):
            _brick_course(surface, variant, row, face, chisel, pit)


def _wall_edges(surface: pygame.Surface, variant: int, lit_top: bool,
                exposed_sides: int) -> None:
    """Gercek dis kenarlara iki piksellik pah; isik yonu hep sol ust."""
    if exposed_sides & EDGE_RIGHT:
        surface.fill(palette.color("stone_darkest"), (TILE_SIZE - 2, 0, 1, TILE_SIZE))
        surface.fill(palette.color("ink_soft"), (TILE_SIZE - 1, 0, 1, TILE_SIZE))
    if exposed_sides & EDGE_BOTTOM:
        surface.fill(palette.color("stone_darkest"), (0, TILE_SIZE - 2, TILE_SIZE, 1))
        surface.fill(palette.color("ink_soft"), (0, TILE_SIZE - 1, TILE_SIZE, 1))
    if exposed_sides & EDGE_LEFT:
        surface.fill(palette.color("stone"), (0, 0, 1, TILE_SIZE))
        # Taslarin arasindaki derz, dis silueti delmeden devam eder.
        surface.set_at((0, _ROW_HEIGHT - 1), palette.color("stone_dark"))
        surface.set_at((0, TILE_SIZE - 1), palette.color("stone_dark"))
    if lit_top:
        surface.fill(palette.color("stone_light"), (0, 0, TILE_SIZE, 1))
        surface.fill(palette.color("stone"), (0, 1, TILE_SIZE, 1))
        # Basilabilir yuzey surekli kalir; asinma yalnizca ikinci sirada.
        surface.set_at((3 + variant * 3, 1), palette.color("stone_dark"))


def _wall(theme: Theme, variant: int, lit_top: bool, exposed_sides: int,
          depth: int) -> pygame.Surface:
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE)).convert()
    _pattern(surface, theme, variant, depth)
    if depth <= 0:
        _wall_edges(surface, variant, lit_top, exposed_sides)
    return surface


# --- Susler ------------------------------------------------------------------
# Yuzeyin disina tasan kucuk parcalar: ustte yosun/kristal/moloz, altta
# kok/sarkit. Karo yuzeyine cizilemezler (karonun disinda duruyorlar),
# o yuzden `TileMap.draw` ikinci bir gecisle bunlari basiyor.
#
# Oynanisa karismasinlar diye kucuk (en fazla PROP_HEIGHT) ve yalnizca
# BOS hucreye tasiyorlar - platform, diken ya da kapi olan yere degil.
def _prop_top(kind: str, variant: int) -> pygame.Surface:
    """Ustte duran sus; yuzeyin alt kenari zemine oturur."""
    image = pygame.Surface((TILE_SIZE, PROP_HEIGHT), pygame.SRCALPHA)
    base = PROP_HEIGHT
    if kind == "moss":
        # Yosun tutamlari: farkli boyda uc yaprak, sol yaprak isikta.
        for i, (x, h) in enumerate(((2 + variant, 3), (6 + variant, 5),
                                    (11 - variant, 2), (13, 3))):
            colour = "moss_light" if i % 2 == 0 else "moss"
            image.fill(palette.color("moss_dark"), (x, base - h, 1, h))
            image.fill(palette.color(colour), (x, base - h, 1, 1))
        image.fill(palette.color("moss_dark"), (1, base - 1, 14, 1))
    elif kind == "crystal":
        # Mor kristal kumesi: sol yuz isik, sag yuz golge, parlak uc.
        for x, h in ((5 + variant, 6), (8 + variant, 4), (3 + variant, 3)):
            image.fill(palette.color("violet_dark"), (x - 1, base - h + 1, 3, h - 1))
            image.fill(palette.color("violet"), (x, base - h, 1, h))
            image.fill(palette.color("violet_bright"), (x - 1, base - h + 1, 1, max(1, h - 2)))
    elif kind == "cinder":
        # Obsidyen kiymiklari ve arasinda sonmemis kor.
        image.fill(palette.color("ink_soft"), (3 + variant, base - 3, 2, 3))
        image.fill(palette.color("stone"), (3 + variant, base - 3, 1, 1))
        image.fill(palette.color("ember"), (9 - variant, base - 1, 2, 1))
        image.set_at((9 - variant, base - 2), palette.color("ember_light"))
    else:  # rubble
        image.fill(palette.color("stone_dark"), (4 + variant * 2, base - 2, 3, 2))
        image.set_at((4 + variant * 2, base - 2), palette.color("stone"))
        image.fill(palette.color("stone_darkest"), (11 - variant, base - 1, 2, 1))
    return image


def _prop_hang(kind: str, variant: int) -> pygame.Surface:
    """Tavanin altinda sarkan sus; yuzeyin ust kenari tavana yapisir."""
    image = pygame.Surface((TILE_SIZE, PROP_HEIGHT), pygame.SRCALPHA)
    if kind == "roots":
        for x, h in ((3 + variant, 6), (7 + variant, 3), (12 - variant, 5)):
            image.fill(palette.color("earth_dark"), (x, 0, 1, h))
            image.set_at((x + (1 if h > 4 else -1), h - 2), palette.color("earth_dark"))
            image.set_at((x, h - 1), palette.color("moss_dark"))
    elif kind == "shard":
        for x, h in ((5 + variant, 6), (10 - variant, 4)):
            for row in range(h):
                width = max(1, 3 - row * 3 // h)
                image.fill(palette.color("violet_dark"), (x - width // 2, row, width, 1))
            image.fill(palette.color("violet"), (x, 0, 1, h - 1))
    elif kind == "ember_drip":
        for x, h in ((4 + variant, 5), (11 - variant, 3)):
            image.fill(palette.color("ink_soft"), (x - 1, 0, 3, 2))
            image.fill(palette.color("ember_dark"), (x, 0, 1, h))
            image.set_at((x, h - 1), palette.color("ember"))
    else:  # drip - kuru tas sarkit
        x = 6 + variant * 2
        image.fill(palette.color("stone_darkest"), (x - 1, 0, 3, 2))
        image.fill(palette.color("stone_darkest"), (x, 2, 1, 2))
    return image


def _platform(variant: int) -> pygame.Surface:
    """Ahsap kiris: kesintisiz basma cizgisi, koyu alt yuz ve kisa damar."""
    surface = pygame.Surface((TILE_SIZE, 6)).convert()
    surface.fill(palette.color("earth"))
    surface.fill(palette.color("flesh"), (0, 0, TILE_SIZE, 1))
    surface.fill(palette.color("earth_dark"), (0, 4, TILE_SIZE, 1))
    surface.fill(palette.color("ink"), (0, 5, TILE_SIZE, 1))
    grain_x = 2 + variant * 6
    surface.fill(palette.color("earth_dark"), (grain_x, 2, 5, 1))
    surface.set_at((12 - variant * 8, 2), palette.color("stone_darkest"))
    return surface


def _spike() -> pygame.Surface:
    """Dikenin sivri silueti ve tehlike rengi birlikte korunur."""
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA).convert_alpha()
    surface.fill((0, 0, 0, 0))
    for x in range(0, TILE_SIZE, 4):
        pygame.draw.polygon(surface, palette.color("blood_bright"),
                            [(x, TILE_SIZE - 4), (x + 2, 3), (x + 4, TILE_SIZE - 4)])
        pygame.draw.line(surface, palette.color("danger_bright"),
                         (x + 2, 3), (x + 1, TILE_SIZE - 5))
        pygame.draw.line(surface, palette.color("blood_dark"),
                         (x + 3, 7), (x + 4, TILE_SIZE - 4))
    surface.fill(palette.color("stone_darkest"), (0, TILE_SIZE - 4, TILE_SIZE, 4))
    surface.fill(palette.color("stone_dark"), (0, TILE_SIZE - 4, TILE_SIZE, 1))
    return surface


class TileSet:
    """Uretilen karo yuzeylerinin onbellegi.

    Anahtar tema + varyant + (derinlik 0 ise) kenar bilgisi. Bir
    bolumde tek tema var; en fazla 4 varyant x 16 kenar + 12 derin
    yuzey + 8 sus = ~84 yuzey.
    """

    def __init__(self) -> None:
        self._cache: dict[tuple, pygame.Surface] = {}

    def wall(self, tx: int, ty: int, lit_top: bool,
             exposed_sides: int = 0, depth: int = 0,
             theme: str = DEFAULT_THEME) -> pygame.Surface:
        variant = (tx * 7 + ty * 13) % WALL_VARIANTS
        depth = max(0, min(MAX_DEPTH, depth))
        if depth > 0:
            key = ("wall", theme, variant, depth)
        else:
            exposed_sides &= _SIDE_MASK
            key = ("wall", theme, variant, lit_top, exposed_sides)
        surface = self._cache.get(key)
        if surface is None:
            surface = _wall(_theme(theme), variant, lit_top, exposed_sides, depth)
            self._cache[key] = surface
        return surface

    def prop(self, tx: int, ty: int, hanging: bool,
             theme: str = DEFAULT_THEME) -> pygame.Surface | None:
        """Bu yuzey karosunun ustunde/altinda sus var mi - varsa yuzeyi.

        Secim dunya koordinatindan (hash): kamera donunce ayni yerde,
        kirilabilir duvar da komsulari gibi suslu ya da suslu degil.
        """
        spec = _theme(theme)
        kind = spec.hang_prop if hanging else spec.top_prop
        every = spec.hang_every if hanging else spec.top_every
        if not kind or every <= 0:
            return None
        seed = (tx * 73856093) ^ (ty * 19349663) ^ (0x5bd1 if hanging else 0x1f3)
        if (seed >> 3) % every:
            return None
        variant = (seed >> 7) % 3
        key = ("prop", kind, variant)
        surface = self._cache.get(key)
        if surface is None:
            maker = _prop_hang if hanging else _prop_top
            surface = maker(kind, variant)
            if pygame.display.get_init() and pygame.display.get_surface() is not None:
                surface = surface.convert_alpha()
            self._cache[key] = surface
        return surface

    def platform(self, tx: int, ty: int) -> pygame.Surface:
        variant = (tx * 11 + ty * 5) % PLATFORM_VARIANTS
        key = ("platform", variant)
        surface = self._cache.get(key)
        if surface is None:
            surface = _platform(variant)
            self._cache[key] = surface
        return surface

    def spike(self) -> pygame.Surface:
        key = ("spike",)
        surface = self._cache.get(key)
        if surface is None:
            surface = _spike()
            self._cache[key] = surface
        return surface


_SHARED = TileSet()


def shared() -> TileSet:
    return _SHARED


def clear_cache() -> None:
    """Renk korlugu/ekran bicimi degisince butun taslari yeniden uret."""
    _SHARED._cache.clear()
