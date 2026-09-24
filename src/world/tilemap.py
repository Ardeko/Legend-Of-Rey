"""Tile haritasi: veri, carpisma sorgulari, cizim.

16x16 tile. Harita ASCII satirlardan kurulur - bir bolumu duz metin olarak
gormek tasarim hatalarini daha yazarken yakalatir.

Carpisma dogrudan diziden okunur: tile'lar nesne degil, sayidir. Bir
dikdortgenin dokundugu tile araligi hesaplanip yalnizca o araliga bakilir.

Tek yonlu platformlar (`=`) yalnizca **asagi dogru hareket ederken** ve ayak
platformun ustundeyken katidir. Kural fizik katmaninda uygulanir.

Cizim `src/art/tileset.py`'den geliyor (Gorev 9): prosedurel tugla/kiris
dokusu, karakter sprite'lari gibi kod ile uretilip onbelleklenir. Duz renk
dolgu yok artik - kirilabilir duvarin normal duvardan **ayirt edilemez**
kalmasi (docs/gdd.md 4) ayni (tx, ty) icin ayni varyantin uretilmesiyle
korunuyor.
"""
from __future__ import annotations

import numpy as np
import pygame

from src.art import palette, tileset
from src.config import TILE_DRAW_MARGIN, TILE_SIZE

EMPTY = 0
SOLID = 1
PLATFORM = 2
SPIKE = 3
# Kirilabilir duvar: kati gibi davranir ama vurulunca yok olur. Yanki
# olmadan **normal duvardan ayirt edilemez** - gizli gecidin tamami bu
# ayirt edilemezlik uzerine kurulu (docs/gdd.md 4).
BREAKABLE = 4

SOLID_TILES = frozenset({SOLID, BREAKABLE})
HAZARD_TILES = frozenset({SPIKE})

LEGEND: dict[str, int] = {
    ".": EMPTY, " ": EMPTY,
    "#": SOLID,
    "=": PLATFORM,
    "^": SPIKE,
    "B": BREAKABLE,
}


class TileMap:
    def __init__(self, rows: list[str]) -> None:
        self.height = len(rows)
        self.width = max((len(r) for r in rows), default=0)
        self.tiles: list[list[int]] = [
            [LEGEND.get(char, EMPTY) for char in row.ljust(self.width, ".")]
            for row in rows
        ]
        # Tas dili (`tileset.THEMES`). Sahne bolum numarasina gore
        # degistiriyor (`PlayScene.on_enter`); varsayilan ust katlarin
        # tuglasi.
        self.theme = tileset.DEFAULT_THEME
        # Her degisiklikte artar; kutle derinligi haritasi buna bakip
        # yeniden hesaplaniyor (`_depth_rows`).
        self._version = 0
        self._depth_cache: tuple[int, list[list[int]]] | None = None

    # --- Sorgular -----------------------------------------------------------
    @property
    def pixel_width(self) -> int:
        return self.width * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return self.height * TILE_SIZE

    @property
    def bounds(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.pixel_width, self.pixel_height)

    def at(self, tx: int, ty: int) -> int:
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.tiles[ty][tx]
        # Harita disi: yanlar kati (oyuncu bolumden cikamaz), tepe ve taban
        # bos (bosluga dusen gercekten duser, gorunmez zeminde durmaz).
        if ty < 0 or ty >= self.height:
            return EMPTY
        return SOLID

    def is_solid(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) in SOLID_TILES

    def is_breakable(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) == BREAKABLE

    def break_at(self, tx: int, ty: int) -> bool:
        """Kirilabilir duvari yikar. Yikildiysa True."""
        if not self.is_breakable(tx, ty):
            return False
        row = self.tiles[ty]
        row[tx] = EMPTY
        self._version += 1
        return True

    def set_tile(self, tx: int, ty: int, value: int) -> bool:
        """Tek bir tile'i degistirir. Harita disindaysa `False`.

        Arena kapisi gibi **oynanis sirasinda** degisen zeminler icin.
        Ayri bir "kapi varligi" yazmak yerine tile'i degistirmek, fizigin
        zaten dogru calisiyor olmasi demek: yeni bir carpisma yolu yok.
        """
        if not (0 <= ty < self.height and 0 <= tx < self.width):
            return False
        self.tiles[ty][tx] = value
        self._version += 1
        return True

    def breakable_rects(self) -> list[pygame.Rect]:
        """Kalan kirilabilir duvarlarin dikdortgenleri.

        Yanki bunlari parlatiyor. Liste kucuk - bir odada en fazla birkac
        tane - o yuzden her karede yeniden uretmek sorun degil.
        """
        found: list[pygame.Rect] = []
        for ty, row in enumerate(self.tiles):
            for tx, value in enumerate(row):
                if value == BREAKABLE:
                    found.append(pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE,
                                             TILE_SIZE, TILE_SIZE))
        return found

    def is_platform(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) == PLATFORM

    def is_hazard(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) in HAZARD_TILES

    def tile_range(self, rect: pygame.Rect) -> tuple[int, int, int, int]:
        return (rect.left // TILE_SIZE, rect.top // TILE_SIZE,
                (rect.right - 1) // TILE_SIZE, (rect.bottom - 1) // TILE_SIZE)

    def solid_overlap(self, rect: pygame.Rect) -> bool:
        x0, y0, x1, y1 = self.tile_range(rect)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.is_solid(tx, ty):
                    return True
        return False

    def platform_top_overlap(self, rect: pygame.Rect,
                             previous_bottom: float) -> bool:
        """Tek yonlu platforma **ustunden** iniliyor mu?

        Ayak onceki karede platformun ustundeyse kati sayilir; asagidan
        ziplayan oyuncu icin gecirgen kalir.
        """
        x0, _, x1, y1 = self.tile_range(rect)
        for tx in range(x0, x1 + 1):
            if not self.is_platform(tx, y1):
                continue
            top = y1 * TILE_SIZE
            if previous_bottom <= top + 1 <= rect.bottom:
                return True
        return False

    def floor_below(self, x: float, feet_hint: float, width: int,
                    height: int, search: int = TILE_SIZE * 5) -> float | None:
        """`x` sutununda, `feet_hint`in bir karo ustunden asagi ilk zemin.

        Sahne parcalari (satici, silah kaidesi) icin: govde bos olmali, bir
        piksel alti kati. Bulunamazsa `None` - havada asili bir sey hic
        olmamasindan kotu.
        """
        start = int(feet_hint) - TILE_SIZE
        for feet in range(start, start + search):
            body = pygame.Rect(int(x) - width // 2, feet - height, width, height)
            below = pygame.Rect(int(x) - width // 2, feet, width, 1)
            if self.solid_overlap(body):
                continue
            if self.solid_overlap(below):
                return float(feet)
        return None

    def hazard_rects(self, rect: pygame.Rect) -> list[pygame.Rect]:
        found: list[pygame.Rect] = []
        x0, y0, x1, y1 = self.tile_range(rect)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.is_hazard(tx, ty):
                    # Diken hitbox'i tile'dan kucuk - tepesine degmeden olmek
                    # oyuncuyu haksiz yere cezalandirir.
                    found.append(pygame.Rect(tx * TILE_SIZE + 2,
                                             ty * TILE_SIZE + 6,
                                             TILE_SIZE - 4, TILE_SIZE - 6))
        return found

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        """Yalnizca gorunur tile'lari cizer (kamera alani + marj)."""
        ox, oy = offset
        view = pygame.Rect(ox, oy, surface.get_width(), surface.get_height())
        margin = TILE_DRAW_MARGIN
        x0 = max(0, view.left // TILE_SIZE - margin)
        y0 = max(0, view.top // TILE_SIZE - margin)
        x1 = min(self.width - 1, view.right // TILE_SIZE + margin)
        y1 = min(self.height - 1, view.bottom // TILE_SIZE + margin)

        ts = tileset.shared()
        theme = self.theme
        depth_rows = self._depth_rows()
        batch: list[tuple[pygame.Surface, tuple[int, int]]] = []
        props: list[tuple[pygame.Surface, tuple[int, int]]] = []
        for ty in range(y0, y1 + 1):
            row = self.tiles[ty]
            depth_row = depth_rows[ty]
            above = self.tiles[ty - 1] if ty > 0 else None
            below = self.tiles[ty + 1] if ty + 1 < self.height else None
            y = ty * TILE_SIZE - oy
            for tx in range(x0, x1 + 1):
                value = row[tx]
                if value == EMPTY:
                    continue
                x = tx * TILE_SIZE - ox
                if value == SPIKE:
                    tile = ts.spike()
                elif value == PLATFORM:
                    tile = ts.platform(tx, ty)
                else:
                    # SOLID/BREAKABLE ayni komsuluk ve yuzeyi kullanir.
                    # Harita disi yanlar kati, ust/alt bos: at() ile ayni
                    # kural. Canli kapi/duvar degisimi sonraki karede gorunur.
                    depth = depth_row[tx]
                    if depth > 0:
                        tile = ts.wall(tx, ty, False, 0, depth, theme)
                    else:
                        lit_top = above is None or above[tx] not in SOLID_TILES
                        edges = self._exposed_sides(row, below, tx)
                        tile = ts.wall(tx, ty, lit_top, edges, 0, theme)
                        self._collect_props(ts, props, tx, ty, x, y, above, below)
                batch.append((tile, (x, y)))
        surface.blits(batch, doreturn=False)
        if props:
            surface.blits(props, doreturn=False)

    def _collect_props(self, ts, props: list, tx: int, ty: int, x: int, y: int,
                       above: list[int] | None, below: list[int] | None) -> None:
        """Yuzey karosunun ustune/altina tasan sus (`tileset.prop`).

        Yalnizca BOS komsu hucreye: platform, diken ya da kapi sutununun
        uzerine sus binmesin.
        """
        if above is not None and above[tx] == EMPTY:
            prop = ts.prop(tx, ty, False, self.theme)
            if prop is not None:
                props.append((prop, (x, y - tileset.PROP_HEIGHT)))
        if below is not None and below[tx] == EMPTY:
            prop = ts.prop(tx, ty, True, self.theme)
            if prop is not None:
                props.append((prop, (x, y + TILE_SIZE)))

    def _depth_rows(self) -> list[list[int]]:
        """Her kati karonun havaya uzakligi (0..MAX_DEPTH), satir listesi.

        numpy ile 8-komsu genisleme: MAX_DEPTH (3) adim, harita boyutundan
        bagimsiz birkac dizi islemi. Harita disi **kati** sayiliyor:
        tavanin ust kenari ekranin tepesinde aydinlanmasin, kutle oraya
        dogru kararsin. (Carpisma kurali `at()` farkli - orada tepe bos;
        bu yalnizca gorunum.)

        Liste olarak saklaniyor: cizim dongusu hucre hucre okuyor ve
        numpy'nin tekil erisimi Python listesinden yavas.
        """
        cached = self._depth_cache
        if cached is not None and cached[0] == self._version:
            return cached[1]
        solid = np.array([[value in SOLID_TILES for value in row]
                          for row in self.tiles], dtype=bool)
        if solid.size == 0:
            rows: list[list[int]] = [[] for _ in range(self.height)]
            self._depth_cache = (self._version, rows)
            return rows
        padded = np.pad(solid, 1, constant_values=True)
        depth = np.full(padded.shape, tileset.MAX_DEPTH, dtype=np.int8)
        frontier = ~padded
        remaining = padded.copy()
        for level in range(tileset.MAX_DEPTH):
            hit = remaining & _dilate8(frontier)
            depth[hit] = level
            remaining &= ~hit
            frontier = hit
        rows = depth[1:-1, 1:-1].tolist()
        self._depth_cache = (self._version, rows)
        return rows

    def _exposed_sides(self, row: list[int], below: list[int] | None,
                       tx: int) -> int:
        """Yalnizca gorunen karonun gercek dis kenarlarini hesapla."""
        edges = 0
        if tx > 0 and row[tx - 1] not in SOLID_TILES:
            edges |= tileset.EDGE_LEFT
        if tx + 1 < self.width and row[tx + 1] not in SOLID_TILES:
            edges |= tileset.EDGE_RIGHT
        if below is None or below[tx] not in SOLID_TILES:
            edges |= tileset.EDGE_BOTTOM
        return edges

    def draw_debug(self, surface: pygame.Surface,
                   offset: tuple[int, int]) -> None:
        ox, oy = offset
        colors = {SOLID: "echo_bright", PLATFORM: "gold", SPIKE: "danger_bright"}
        for ty in range(self.height):
            for tx in range(self.width):
                value = self.tiles[ty][tx]
                if value == EMPTY:
                    continue
                pygame.draw.rect(
                    surface, palette.color(colors.get(value, "bone")),
                    (tx * TILE_SIZE - ox, ty * TILE_SIZE - oy,
                     TILE_SIZE, TILE_SIZE), 1)


def _dilate8(mask: np.ndarray) -> np.ndarray:
    """Bir maskeyi sekiz yone birer hucre genisletir (kenarlar tasmaz)."""
    out = mask.copy()
    out[1:, :] |= mask[:-1, :]
    out[:-1, :] |= mask[1:, :]
    out[:, 1:] |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    out[1:, 1:] |= mask[:-1, :-1]
    out[1:, :-1] |= mask[:-1, 1:]
    out[:-1, 1:] |= mask[1:, :-1]
    out[:-1, :-1] |= mask[1:, 1:]
    return out
