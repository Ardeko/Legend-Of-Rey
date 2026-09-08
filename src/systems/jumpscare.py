"""Jumpscare - oyunun tek sok ani (`docs/korku.md` 6.1).

Arda, 08.09.2026: *"mutlaka bir yerde jumpscare olsun."*

## Ucuz olmamasinin tek yolu: on bolumluk bir kurulumun karsiligi

Izleyen'in kurali uc bolum boyunca ogretiliyor:

    B5   ilk gorulur   yaklasirsan geri cekilir
    B11  ikinci kez    yine geri cekilir
    B13  ucuncu kez    Cemo ona bakar, yine geri cekilir
    B14  ...

Oyuncu tek bir sey ogrendi: **bu sey sana yaklasmaz.** Sonra B14'te,
Rey'in Yanki'nin ne oldugunu anladigi karede, Izleyen tam onunde
beliriyor.

Korkutucu olan ani hareket degil, **kuralin bozuldugunun anlasilmasi.**

## Sok SESIN GELMESIYLE degil, GELMEMESIYLE kuruluyor

Kare tablosu (`docs/korku.md` 6.1'den birebir):

    0       muzik ve butun ortam sesi kesilir
    1-44    hicbir sey. ~0,75 saniye tam sessizlik. Oyuncu OYNAYABILIR
    45      Izleyen ekranin ortasinda, oyuncunun iki tile onunde,
            ekranin %70'ini kaplayacak olcekte. Tek kare parlama,
            tek sert ses
    46-51   alti kare durur. Gozler oyuncuda
    52      yok olur. **Ses geri gelmez** - B14'un kalani sessiz oynanir

`player.control_locked = 20` yalnizca 45-65 arasi: Rey donuyor
(irkilme), oyun donmuyor. Yirmi kare bir kacinmadan kisa.

## Kurallara uyum

  * **Oynanisi durdurmuyor**: kamera alinmiyor, ara sahne acilmiyor,
    oyuncu ekranda kaliyor.
  * **Ayni numara iki kez yok**: oyunda bir tane var, ve `done`
    bayragi ikinciyi imkansiz kiliyor.
  * **Fotosensitivite**: `flash_allowed` kapaliysa parlama atlaniyor,
    olay atlanmiyor - erisilebilirlik icerigi kaldirmaz, sunumu
    degistirir.
"""
from __future__ import annotations

from src.config import INTERNAL_HEIGHT, TILE_SIZE
from src.systems import horror

# Kare tablosu - `docs/korku.md` 6.1 ile birebir.
HUSH_AT = 0
APPEAR_AT = 45
VANISH_AT = 52
UNLOCK_AT = 65

# Ekranin bu kadarini kapliyor. Belge %70 diyor.
SCREEN_SHARE = 0.70
# Oyuncunun kac tile onunde.
AHEAD_TILES = 2
# Rey'in donma suresi. Bir kacinma 18 kare; bu ondan biraz uzun ama
# oyunu durdurmuyor.
CONTROL_LOCK = 20


class Jumpscare:
    """Tek seferlik sok. `arm()` ile kuruluyor, `update()` sayiyor."""

    __slots__ = ("frames", "armed", "done", "x", "feet_y", "facing")

    def __init__(self) -> None:
        self.frames = -1
        self.armed = False
        self.done = False
        self.x = 0.0
        self.feet_y = 0.0
        self.facing = 1

    # --- Durum --------------------------------------------------------------
    @property
    def running(self) -> bool:
        return self.armed and not self.done

    @property
    def visible(self) -> bool:
        """Izleyen su an ekranda mi (45-51 arasi)."""
        return self.armed and APPEAR_AT <= self.frames < VANISH_AT

    @property
    def height(self) -> int:
        """Cizim yuksekligi - ekranin %70'i."""
        return int(INTERNAL_HEIGHT * SCREEN_SHARE)

    # --- Akis ---------------------------------------------------------------
    def arm(self, player) -> bool:
        """Sayaci baslatir. Bir kez - ikincisi reddediliyor."""
        if self.armed or self.done:
            return False
        self.armed = True
        self.frames = -1
        body = player.body
        self.facing = getattr(player, "facing", 1)
        self.x = body.center_x + self.facing * AHEAD_TILES * TILE_SIZE
        self.feet_y = body.feet[1]
        return True

    def update(self, game, player) -> None:
        """Bir kare ilerlet ve tablodaki isleri yap."""
        if not self.running:
            return
        self.frames += 1
        frame = self.frames

        if frame == HUSH_AT:
            # **Ses kesiliyor ve geri gelmiyor.** Sokun kurulumu bu.
            game.music_hush = 1.0

        elif frame == APPEAR_AT:
            game.play_sound("watcher_strike")
            game.play_sound("breath_sharp")
            # Rey irkiliyor - OYUN donmuyor.
            player.control_locked = max(getattr(player, "control_locked", 0),
                                        CONTROL_LOCK)

        elif frame >= UNLOCK_AT:
            # Bitti. `music_hush` **bilerek** geri alinmiyor: belge
            # "ses geri gelmez, B14'un kalani sessiz oynanir" diyor.
            self.armed = False
            self.done = True

    def flash(self, settings) -> float:
        """Beliris karesinde tek kare parlama - 0 ise cizilmiyor.

        `flash_limit` acikken sifir donuyor ama olay yine oluyor.
        """
        if self.frames != APPEAR_AT:
            return 0.0
        if not horror.flash_allowed(settings):
            return 0.0
        return 1.0


def allowed(settings) -> bool:
    """Katman 3 acik mi (`docs/korku.md` 8)."""
    return horror.shock(settings)
