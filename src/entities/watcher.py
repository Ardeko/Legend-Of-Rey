"""Izleyen - `docs/korku.md` 5.2. **Dusman degil.**

Odanin uzak ucunda durur, sana doner, bakar. Yaklasirsan geri cekilir.
Vurulmaz - vurmaya kalkarsan zaten orada degildir.

## Neden `Enemy` degil

`Enemy` cani, hitbox'i, saldiri hakki, poise ve olum animasyonu olan
bir sey. Izleyen'in hicbiri yok ve **olmamasi** onun tanimi. `Enemy`den
tureseydi bu ozellikler "kullanilmiyor" diye orada dururdu ve bir gun
biri onlari kullanirdi.

Ayrica `scene.enemies` listesine girmemesi sart: oraya girseydi Yanki
Gorusu onu bir dusman gibi isaretler, saldiri hakki sistemi ona hak
ayirir, "oda temizlendi" sayimlari onu beklerdi. Izleyen sahnenin
dekoru degil ama dovusunun de parcasi degil.

## Kural: yaklasirsan CEKILIR

Uc bolum boyunca (B5, B11, B13) tek bir sey ogretiliyor: **bu sey sana
yaklasmaz.** Oyuncu bunu ogrenmeden B14'un jumpscare'i ucuz olur -
orada kirilan sey ani hareket degil, uc bolumluk bir kural.

`retreats=False` verildiginde artik cekilmiyor. B14 icin.

## Gozler govdeden bagimsiz

Govde nereye donuk olursa olsun gozler oyuncuya bakiyor. Prosedurel
sprite sisteminde bu `facing`i cizim aninda oyuncuya gore secmek
demek - tek satir, ve ekranda "yanlis bir sey var" diyen en ucuz
sinyal.
"""
from __future__ import annotations

import math

import pygame

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.systems import horror

# Bu mesafeye yaklasilinca cekilmeye basliyor.
RETREAT_RANGE = 96.0
# Cekilme hizi - oyuncunun kosu hizindan **yavas**. Kacmiyor, geri
# cekiliyor; ikisi cok farkli seyler.
RETREAT_SPEED = 0.55
# Bu kadar yaklasilirsa (cekilemiyorsa) siliniyor.
VANISH_RANGE = 42.0

FADE_FRAMES = 34            # Belirme ve silinme suresi
# Fark edilme sesi bu mesafede caliniyor - goruldugu an degil, oyuncunun
# ona BAKTIGI an. Ekranin kenarinda beliren bir sey fark edilmiyor.
NOTICE_RANGE = 190.0


class Watcher:
    """Bakan sey. Sahne tutar, `enemies` listesine **girmez**."""

    __slots__ = ("x", "feet_y", "retreats", "animator", "sprite_foot_y",
                 "facing", "state", "fade", "noticed", "_home_x", "_bob")

    def __init__(self, x: float, feet_y: float, retreats: bool = True) -> None:
        self.x = float(x)
        self.feet_y = float(feet_y)
        self._home_x = float(x)
        self.retreats = retreats
        self.animator = Animator("watcher")
        self.animator.play("idle")
        self.sprite_foot_y = CHARACTERS["watcher"].foot_y
        self.facing = -1
        self.state = "appearing"        # appearing | watching | leaving | gone
        self.fade = 0
        self.noticed = False
        self._bob = 0.0

    @property
    def gone(self) -> bool:
        return self.state == "gone"

    @property
    def alpha(self) -> float:
        if self.state == "appearing":
            return min(1.0, self.fade / FADE_FRAMES)
        if self.state == "leaving":
            return max(0.0, self.fade / FADE_FRAMES)
        return 1.0 if self.state == "watching" else 0.0

    # --- Dongu --------------------------------------------------------------
    def update(self, game, scene) -> None:
        if self.state == "gone":
            return
        # Katman 2 oyun ortasinda kapatilirsa Izleyen **silinir**, aniden
        # yok olmaz: ayar degisimi bir korku ani uretmemeli.
        if not horror.atmosphere(game.settings):
            self._leave()

        self.animator.update()
        self._bob += 0.03

        player = getattr(scene, "player", None)
        if player is None:
            return
        distance = player.body.center_x - self.x
        # **Gozler daima oyuncuda** - govde nereye donuk olursa olsun.
        self.facing = 1 if distance > 0 else -1

        if self.state == "appearing":
            self.fade += 1
            if self.fade >= FADE_FRAMES:
                self.state = "watching"
            self._notice(game, abs(distance))
            return

        if self.state == "leaving":
            self.fade -= 1
            if self.fade <= 0:
                self.state = "gone"
            return

        self._watch(game, scene, distance)

    def _notice(self, game, distance: float) -> None:
        """Oyuncu ona baktiginda bir kez calan alcak ses."""
        if self.noticed or distance > NOTICE_RANGE:
            return
        self.noticed = True
        game.play_sound("watcher_notice", bus="volume_sfx",
                        volume=horror.loudness(game.settings) * 0.8)

    def _watch(self, game, scene, distance: float) -> None:
        self._notice(game, abs(distance))
        if not self.retreats:
            # B14: artik cekilmiyor. Oyuncu istedigi kadar yaklassin -
            # durup bakmaya devam ediyor. Kural burada kiriliyor.
            return

        if abs(distance) > RETREAT_RANGE:
            return

        # Oyuncudan **uzaga** dogru, yavasca.
        step = -RETREAT_SPEED if distance > 0 else RETREAT_SPEED
        target = self.x + step
        if self._blocked(scene, target):
            # Sikisti: cekilemiyorsa siliniyor. "Kosede yakaladim" ani
            # olmamali - Izleyen'e hicbir zaman ulasilamaz.
            self._leave()
            return
        self.x = target

        if abs(distance) < VANISH_RANGE:
            self._leave()

    def _blocked(self, scene, x: float) -> bool:
        tilemap = getattr(scene, "tilemap", None)
        if tilemap is None:
            return False
        from src.config import TILE_SIZE
        tx = int(x) // TILE_SIZE
        ty = int(self.feet_y - 1) // TILE_SIZE
        return tilemap.is_solid(tx, ty)

    def _leave(self) -> None:
        if self.state in ("leaving", "gone"):
            return
        self.state = "leaving"
        self.fade = FADE_FRAMES

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        alpha = self.alpha
        if alpha <= 0.0:
            return
        image = self.animator.render(self.facing)
        if image is None:
            return
        ox, oy = offset
        # Cok hafif suzulme - nefes almiyor ama hareketsiz de degil.
        # Tamamen sabit bir sey dekor gibi okunuyordu.
        drift = int(round(math.sin(self._bob) * 1.0))
        x = int(self.x - image.get_width() * 0.5) - ox
        y = int(self.feet_y - self.sprite_foot_y) - oy + drift

        if alpha < 1.0:
            image = image.copy()
            image.set_alpha(int(255 * alpha))
        surface.blit(image, (x, y))

    def debug_line(self) -> str:
        return (f"izleyen {self.state} x={self.x:.0f} "
                f"{'cekilir' if self.retreats else 'CEKILMEZ'}")
