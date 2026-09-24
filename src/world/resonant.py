"""Rezonansa tepki veren dunya nesneleri.

`docs/yapi.md` mekanik havuzu 5: *"Sesle kristal kir, can cal, uzaktaki
kapiyi ac."* Ucu de burada tek bir tabandan turuyor - `ResonantObject`
yalnizca "vuruldum" diyor, ne oldugu alt sinifin isi.

Uc nesne, uc farkli is:

    Crystal  kiriliyor ve **yok oluyor** - yolu aciyor
    Latch    ulasilamaz bir yerde, kapiyi aciyor
    Bell     caliyor ve **yerinde kaliyor** - sirasi hatirlaniyor

`Bell` Bolum 8'de bilerek yazilmamisti: `CLAUDE.md` 3 sirasi gelmemis
bolum icerigini yasakliyor ve B9'un sira bulmacasi tasarlanmadan bir
can sinifi yazmak tahmin uzerine kurmak olurdu. Sirasi geldi
(30.08.2026) ve taban sinif oldugu gibi ise yaradi - dogru sinir
oradaymis.

## Neden `pickups.py`'ye eklenmedi

`Chest` gibi seyler **dokunmayla** calisiyor: oyuncunun govdesi
carpiyor. Bunlar **uzaktan** calisiyor ve tetikleyicileri bir govde
degil bir halka. Ayni dosyaya koymak iki farkli etkilesim modelini
karistirirdi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE

# Kristalin kirilma animasyonu (kare).
SHATTER_FRAMES = 24
# Mandalin acilma animasyonu.
LATCH_FRAMES = 30
# Canin calma suresi - sallanma ve ses bu kadar surer.
RING_FRAMES = 46


class ResonantObject:
    """Rezonans halkasinin vurabilecegi her sey."""

    def __init__(self, tile_x: int, tile_y: int,
                 width: int = 1, height: int = 1) -> None:
        self.rect = pygame.Rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE,
                                width * TILE_SIZE, height * TILE_SIZE)
        self.triggered = False
        self.frames = 0

    @property
    def done(self) -> bool:
        return self.triggered and self.frames <= 0

    def strike(self) -> bool:
        """Halka vurdu. Ilk kez vuruluyorsa True."""
        if self.triggered:
            return False
        self.triggered = True
        self.frames = self.duration
        return True

    duration = SHATTER_FRAMES

    def update(self) -> None:
        if self.frames > 0:
            self.frames -= 1

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        raise NotImplementedError


class Crystal(ResonantObject):
    """Ses kristali - kirilinca yolu aciyor.

    Tilemap'te kati bir sutun olarak duruyor; kirilinca sahne o
    sutunu bosaltiyor (`chapter08.py`). Kristalin kendisi tilemap'i
    bilmiyor - dunya nesnesi kendi kendini kaldirmiyor, sahne
    kaldiriyor. Ayni ayrim `plate.PlateGate`'te de var.
    """

    duration = SHATTER_FRAMES

    def __init__(self, tile_x: int, tile_y: int, height: int = 2) -> None:
        super().__init__(tile_x, tile_y, 1, height)
        self.shards: list[tuple[float, float, float, float]] = []

    def strike(self) -> bool:
        if not super().strike():
            return False
        # Parcalar disari savruluyor - `ParticleField` degil, cunku
        # bunlar sahnenin parcacik butcesini yemeden yalnizca 24 kare
        # yasayan bir avuc kare.
        for index in range(10):
            angle = index * math.tau / 10
            self.shards.append((float(self.rect.centerx),
                                float(self.rect.centery),
                                math.cos(angle) * 1.6,
                                math.sin(angle) * 1.6 - 0.6))
        return True

    def update(self) -> None:
        super().update()
        moved = []
        for x, y, vx, vy in self.shards:
            moved.append((x + vx, y + vy, vx * 0.94, vy * 0.94 + 0.16))
        self.shards = moved

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        if self.done:
            return
        if not self.triggered:
            self._draw_body(surface, ox, oy)
            return
        fade = self.frames / max(1, self.duration)
        colour = tuple(int(c * fade) for c in palette.color("echo_bright"))
        for x, y, _vx, _vy in self.shards:
            surface.fill(colour, (int(x) - ox, int(y) - oy, 2, 2))

    def _draw_body(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        """Kristal govdesi - **sivri**, kutu degil.

        Siluet testi (`CLAUDE.md` 6): tek renge indiginde ne oldugu
        anlasilmali. Bir dikdortgen "kutu" okunur; asagi dogru daralan
        bir bicim "kristal" okunur.
        """
        left = self.rect.x - ox
        top = self.rect.y - oy
        height = self.rect.height
        tip = (left + 7, top + 1)
        bottom = (left + 8, top + height - 2)
        ridge = (left + 6, top + height // 3)
        a, b = (left + 1, top + height // 3), (left + 14, top + height // 4)
        c = (left + 13, top + height * 3 // 4)
        pygame.draw.polygon(surface, palette.color("ink"),
                            (tip, b, c, bottom, (left + 2, top + height - 8), a))
        pygame.draw.polygon(surface, palette.color("echo"), (tip, a, ridge, bottom))
        pygame.draw.polygon(surface, palette.color("abyss_light"),
                            (tip, b, c, bottom, ridge))
        pygame.draw.polygon(surface, palette.color("echo_bright"),
                            (tip, (left + 4, top + height // 3), ridge))
        pygame.draw.line(surface, palette.color("echo_bright"), ridge, bottom)
        pygame.draw.line(surface, palette.color("abyss"),
                         (left + 9, top + height // 2), c)
        # Tas yuva, kristali duvarin parcasi gibi oturtur.
        surface.fill(palette.color("stone_darkest"),
                     (left + 2, top + height - 3, 12, 3))
        surface.fill(palette.color("stone"), (left + 3, top + height - 3, 4, 1))


class Latch(ResonantObject):
    """Uzaktaki kapinin mandali - ses varinca aciliyor.

    Kristalden farki: mandal **ulasilamaz** bir yerde duruyor. Oyuncu
    oraya yuruyemez, yalnizca sesi gonderebilir. Mekanigin butun
    noktasi bu - elle yapilabilen bir sey icin sese gerek olmazdi.
    """

    duration = LATCH_FRAMES

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        left = self.rect.x - ox
        top = self.rect.y - oy
        # Halka + dil. Acilinca dil dusuyor.
        drop = 0 if not self.triggered else int(
            (1.0 - self.frames / max(1, self.duration)) * 5)
        surface.fill(palette.color("ink"), (left + 1, top + 1, 14, 14))
        surface.fill(palette.color("stone_dark"), (left + 2, top + 2, 12, 12))
        surface.fill(palette.color("stone"), (left + 2, top + 2, 12, 1))
        for dx, dy in ((3, 4), (12, 4), (3, 11), (12, 11)):
            surface.set_at((left + dx, top + dy), palette.color("gold"))
        surface.fill(palette.color("ember" if self.triggered else "stone"),
                     (left + 6, top + 6 + drop, 4, 6))
        if not self.triggered:
            # Titresim isareti: mandalin **ses** bekledigi okunsun.
            surface.fill(palette.color("echo"), (left + 2, top, 2, 2))
            surface.fill(palette.color("echo"),
                         (left + TILE_SIZE - 4, top, 2, 2))


class Bell(ResonantObject):
    """Can - **calindigi SIRA hatirlaniyor.**

    `docs/yapi.md` B9: *"Rezonans ile uc cani dogru sirada calmak. Sira
    ipucu duvardaki freskte."*

    Kristalden farki bir sey **yikmamasi**: kristal kirilip yok oluyor,
    can caliyor ve yerinde duruyor. Yanlis sira geldiginde hepsi
    sifirlaniyor ve yeniden calinabiliyor - bir bulmaca geri
    alinabilir olmali, yoksa oyuncu bolumu bastan oynamak zorunda
    kalir.

    Taban sinif Bolum 8'de (`Crystal`, `Latch`) yazilmisti; can o zaman
    **bilerek** yazilmadi: `CLAUDE.md` 3 sirasi gelmemis bolum
    icerigini yasakliyor ve bir sira bulmacasi tasarlanmadan `Bell`
    yazmak tahmin uzerine kurmak olurdu. Sirasi geldi.
    """

    duration = RING_FRAMES

    def __init__(self, tile_x: int, tile_y: int, index: int,
                 height: int = 2) -> None:
        super().__init__(tile_x, tile_y, 1, height)
        # Freskteki numarasi - dogru sirayi bu belirliyor.
        self.index = index

    def reset(self) -> None:
        """Yanlis sira - can yeniden calinabilir hale geliyor."""
        self.triggered = False
        self.frames = 0

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        x = self.rect.x - ox
        y = self.rect.y - oy
        # Askı
        surface.fill(palette.color("earth_dark"), (x + 6, y, 4, 3))
        surface.fill(palette.color("stone_dark"), (x - 3, y - 3, 22, 3))
        surface.fill(palette.color("stone"), (x - 3, y - 3, 22, 1))
        # Govde: asagi dogru genisleyen bir cerceve - siluet testi
        # (`CLAUDE.md` 6) tek renkte "can" demeli, "kutu" degil.
        swing = 0
        if self.triggered and self.frames > 0:
            # Calarken sallaniyor. Genlik sonuyor - bir can vurulup
            # birakilir, surekli sallanmaz.
            fade = self.frames / max(1, self.duration)
            swing = int(math.sin(self.frames * 0.55) * 2 * fade)
        # "gold"/"ember" birer RENK. `brass` bir golge ZINCIRI ve
        # `palette.color()` onu tanimaz - projede bu tuzaga uc kez
        # dusuldu (`steel`, `brass`).
        tone = "gold" if self.triggered else "earth"
        for row in range(3, self.rect.height - 2):
            # Omuz dar, etek asagi dogru acilir: kapsul yerine can silueti.
            spread = 1 + int(4 * (row / max(1, self.rect.height - 3)) ** 1.7)
            surface.fill(palette.color(tone),
                         (x + 5 - spread + swing, y + row,
                          6 + spread * 2, 1))
            surface.fill(palette.color("gold"),
                         (x + 6 - spread + swing, y + row, 2, 1))
            surface.fill(palette.color("earth_dark"),
                         (x + 8 + spread + swing, y + row, 3, 1))
            if row in (self.rect.height // 2, self.rect.height - 6):
                surface.fill(palette.color("earth"),
                             (x + 6 - spread + swing, y + row, 3 + spread * 2, 1))
        surface.fill(palette.color("gold"),
                     (x + swing, y + self.rect.height - 4, 16, 1))
        surface.fill(palette.color("ink"),
                    (x + 3 + swing, y + self.rect.height - 2, 10, 1))
        # Tokmak
        surface.fill(palette.color("earth_dark"),
                     (x + 7 + swing, y + self.rect.height - 2, 2, 2))
        pygame.draw.circle(surface, palette.color("stone"),
                           (x + 8 - swing, y + self.rect.height - 1), 2)
