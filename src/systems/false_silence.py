"""Yanlis sessizlik - `docs/korku.md` 5.4.

## Bir sinyali ogretip sonra bozmak

Oyun sessizligi bir **alarm** olarak ogretiyor: gizli odada muzik
kesiliyor, boss olurken kesiliyor, onemli anlarda kesiliyor. Oyuncu
uc bolum sonra sunu biliyor - *muzik kesildi, bir sey olacak.*

Bu sistem o bilgiyi **bozuyor**. Uc kez, hicbir sey olmayacak bir
koridorda muzik kesiliyor. Oyuncu hazirlaniyor. Hicbir sey olmuyor.
Muzik geri geliyor.

Dorduncusunde (B15'in girisi) muzik **kesilmiyor** - ve olay tam o
zaman oluyor.

Sonuc: oyuncu bir daha hicbir sinyale guvenemiyor. Korkunun kaynagi
artik oyunun kendisi degil, oyuncunun **kendi tahmini**.

## Neden bu kadar ucuz

Sifir yeni sistem. `game.music_hush` zaten var ve `MusicDirector`
zaten okuyor. Burasi yalnizca "nerede ve ne kadar" diyor.

## Neden hicbir sey OLMAMASI sart

Bir kez bile "aslinda bir sey oluyordu" dersek numara olur ve
oyuncu bir daha yutmaz. Bu araliklarda dusman dogmuyor, tetikleyici
yok, replik yok. Bos olmasi **isin kendisi**.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import TILE_SIZE
from src.systems import horror

# Sessizlige girme ve cikma hizi (kare basina oran). Girme daha hizli:
# ani kesilme fark ediliyor, yavas geri gelme fark edilmiyor - oyuncu
# muzigin ne zaman dondugunu bilmesin.
FADE_IN = 0.055
FADE_OUT = 0.022


@dataclass(frozen=True)
class Stretch:
    """Sessiz kalinacak tile araligi. `[start, end)`"""

    start: int
    end: int


class FalseSilence:
    """Bir bolumdeki yanlis sessizlik araliklari.

    Sahne `setup()` icinde kuruyor, `update()` her karede cagriliyor.
    Katman 2 kapaliysa hicbir sey yapmiyor.
    """

    __slots__ = ("stretches", "hush", "inside", "visited")

    def __init__(self, *stretches: Stretch) -> None:
        self.stretches = stretches
        self.hush = 0.0
        self.inside = False
        # Hangi aralik yasandi - hata ayiklama ve test icin.
        self.visited: set[int] = set()

    def update(self, game, scene) -> None:
        if not horror.atmosphere(game.settings):
            # Ayar kapaliyken sessizligi **birakip cikmak** gerekiyor:
            # oyun ortasinda kapatilirsa muzik kisik kalmasin.
            if self.hush > 0.0:
                self.hush = max(0.0, self.hush - FADE_OUT)
                game.music_hush = max(game.music_hush, self.hush)
            self.inside = False
            return

        player = getattr(scene, "player", None)
        if player is None:
            return
        tile = int(player.body.center_x) // TILE_SIZE

        index = self._index_at(tile)
        self.inside = index is not None
        if index is not None:
            self.visited.add(index)
            self.hush = min(1.0, self.hush + FADE_IN)
        else:
            self.hush = max(0.0, self.hush - FADE_OUT)

        # **`max` ile biniyor, atamiyor.** Bolumun kendi sessizligi
        # (gizli oda, boss) varsa onu ezmemeli - ikisi ayni anda
        # oldugunda daha sessiz olan kazanmali.
        if self.hush > 0.0:
            game.music_hush = max(game.music_hush, self.hush)

    def _index_at(self, tile: int) -> int | None:
        for index, stretch in enumerate(self.stretches):
            if stretch.start <= tile < stretch.end:
                return index
        return None

    def debug_line(self) -> str:
        return (f"yanlis sessizlik {self.hush:.2f} "
                f"{'ICERIDE' if self.inside else 'disarida'}")
