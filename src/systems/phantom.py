"""Hayalet parilti - `docs/korku.md` 4.4.

## Yanki Gorusu bugune kadar HIC yalan soylemedi

Yanki'nin **sozu** yalan soyluyor (`LIE_CHANCE`), ama **gorusu**
soylemiyordu: duvar ardinda parlayan her sey gercekten oradaydi.
Oyuncu bu yuzden sesine guvenmiyor ama gozune guveniyordu, ve o guven
hicbir zaman sinanmadi.

Bulanik kademede artik sinaniyor: %10 ihtimalle **olmayan bir sey**
parliyor. Oyuncu yaklasiyor, parilti soner ve orada hicbir sey yoktur.

## Oran neden dusuk

%10 "acaba mi?" uretir, %30 "oyun bozuk" uretir. Ikisi arasindaki fark
korkunun tamami. Oyuncu bir hata sandigi seyi ikinci kez yasayana kadar
suphelenmemeli.

## Hayalet ayni zamanda bir KANIT

`systems/lies.py` bir yalanin curutulmesini bekliyor. Hayalet tam olarak
bunu veriyor: "burada bir sey var" denildi, gidildi, yoktu. Bu yuzden
hayalet dogarken deftere yazilyor ve sonerken yakalaniyor - butun
bolumlerde calisan, bolume ozel kod istemeyen tek kanit.

## BERRAK kademede yok

Yalnizca BULANIK'ta. Berrak Yanki dogru soyluyor - `LIE_CHANCE` de
oyle diyor (%0). Sessiz kademede zaten gorus yok. Kademe sisteminin
anlami korunuyor: **kademen dustukce gozune de guvenemezsin.**
"""
from __future__ import annotations

import random

from src.config import ECHO_TIER_MURKY, TILE_SIZE
from src.systems import horror

CHANCE = 0.10               # Dogma ihtimali (deneme basina)
TRY_EVERY = 150             # Bu kadar karede bir zar atiliyor
COOLDOWN = 60 * 12          # Sondukten sonra bu kadar kare yeni hayalet yok

LIFETIME = 60 * 8           # Yaklasilmazsa kendiliginden soner
FADE_FRAMES = 26            # Sonme suresi
NOTICE_RANGE = 30.0         # Bu kadar yaklasinca sonmeye baslar

# Hayalet oyuncunun onunde, bu araliktaki bir mesafede beliriyor.
# Cok yakin olursa "yanimda belirdi" gibi durur; cok uzak olursa
# oyuncu hic yaklasmaz ve numara hic yasanmaz.
SPAWN_MIN = TILE_SIZE * 4
SPAWN_MAX = TILE_SIZE * 7


class Phantom:
    """Yanki Gorusu'nun gosterdigi, orada olmayan sey."""

    __slots__ = ("x", "y", "life", "fading", "timer", "cooldown", "_rng",
                 "caught")

    def __init__(self, seed: int | None = None) -> None:
        self.x = 0.0
        self.y = 0.0
        self.life = 0
        self.fading = False
        self.timer = 0
        self.cooldown = 0
        self.caught = False
        # Kendi rastgeleligi: `random` modulunun genel durumuna
        # dokunmuyoruz, boylece test yeniden uretilebilir kaliyor.
        self._rng = random.Random(seed)

    @property
    def active(self) -> bool:
        return self.life > 0

    @property
    def alpha(self) -> float:
        """0..1 gorunurluk. Sonerken duzgun azaliyor."""
        if not self.active:
            return 0.0
        if self.fading:
            return max(0.0, self.life / FADE_FRAMES)
        return 1.0

    # --- Dongu --------------------------------------------------------------
    def update(self, game, scene) -> None:
        if self.cooldown > 0:
            self.cooldown -= 1

        if self.active:
            self._update_active(game, scene)
            return

        if not self._may_spawn(game, scene):
            return
        self.timer += 1
        if self.timer < TRY_EVERY:
            return
        self.timer = 0
        if self._rng.random() < CHANCE:
            self._spawn(scene)

    def _may_spawn(self, game, scene) -> bool:
        if self.cooldown > 0:
            return False
        # Katman 2: ayardan kapatilabiliyor. Yanki'nin SOZLU yalani
        # Katman 1 ve kapanmiyor; gorsel yalan atmosferin parcasi.
        if not horror.atmosphere(game.settings):
            return False
        echo = getattr(scene, "echo", None)
        if echo is None or not echo.active:
            return False
        # **Yalnizca BULANIK.** Berrak dogru soyluyor, sessizde gorus yok.
        return echo.tier == ECHO_TIER_MURKY

    def _spawn(self, scene) -> None:
        player = scene.player
        facing = player.facing or 1
        distance = self._rng.uniform(SPAWN_MIN, SPAWN_MAX)
        self.x = player.body.center_x + facing * distance
        # Oyuncunun goz hizasindan biraz yukarida - zemine oturmuyor,
        # duvar ardinda bir sey gibi asili duruyor.
        self.y = player.body.center_y - self._rng.uniform(2.0, 10.0)
        self.life = LIFETIME
        self.fading = False
        self.caught = False

        # Deftere yaz: bu bir yalan ve curutulebilir olmali.
        ledger = getattr(scene, "lies", None)
        if ledger is not None:
            ledger.record((self.x, self.y), direction=facing)

    def _update_active(self, game, scene) -> None:
        self.life -= 1
        if self.fading:
            if self.life <= 0:
                self._end()
            return

        echo = getattr(scene, "echo", None)
        if echo is None or not echo.active:
            # Yanki kapaninca hayalet de gider - ama **yakalanmadan**.
            # Oyuncu ona ulasmadi, yani hicbir sey kanitlanmadi.
            self._end()
            return

        player = scene.player
        near = (abs(player.body.center_x - self.x) < NOTICE_RANGE
                and abs(player.body.center_y - self.y) < NOTICE_RANGE * 1.5)
        if near or self.life <= FADE_FRAMES:
            self._begin_fade(game, scene, proven=near)

    def _begin_fade(self, game, scene, proven: bool) -> None:
        self.fading = True
        self.life = FADE_FRAMES
        game.play_sound("phantom_fade", bus="volume_echo",
                        volume=horror.loudness(game.settings))
        # **Yalnizca yaklasilirsa kanit sayiliyor.** Uzaktan sonen bir
        # parilti "gitti" demek; yanina gidip hicbir sey bulmamak
        # "yoktu" demek. Ikisi ayni sey degil.
        if proven and not self.caught:
            self.caught = True
            catch = getattr(scene, "catch_lie", None)
            if catch is not None:
                catch()

    def _end(self) -> None:
        self.life = 0
        self.fading = False
        self.cooldown = COOLDOWN

    def debug_line(self) -> str:
        if not self.active:
            return f"hayalet yok (bekleme {self.cooldown})"
        return (f"hayalet ({self.x:.0f},{self.y:.0f}) "
                f"{'soniyor' if self.fading else 'duruyor'} {self.life}")
