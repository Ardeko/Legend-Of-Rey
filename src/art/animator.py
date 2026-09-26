"""Animasyon oynatici ve sprite onbellegi.

Iki oynatma kipi var, ikisi de gerekli:

  * **Zamanla surulen** (bosta, kosu, dusme): her sanat karesi sabit sayida
    oyun karesi durur - 8 FPS hissi.
  * **Ilerlemeyle surulen** (saldirilar): kare, saldirinin kendi kare
    butcesindeki (`4/3/8`) ilerleme oranindan secilir. Animasyon dovus
    zamanlamasini asla kaydiramaz - kare hassasiyeti dovusun kalbidir.

Sprite'lar **bir kez** uretilir ve onbellege alinir; her karede yeniden
uretmek kare butcesini yer (CLAUDE.md 4).
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animation import (
    ANIMATIONS, CHARACTERS, SWAY_BIASES, SWAY_NEUTRAL, build_sprite_set,
    has_cloth,
)
from src.art.forge import flip_h, silhouette, squash_surface, tint
from src.art.spritegen import CharSpec

# Bosta/kosu gibi donguselerde her sanat karesi kac oyun karesi durur.
DEFAULT_HOLD_FRAMES = 7
HOLD_OVERRIDES: dict[str, int] = {
    "fall": 6,
    "death": 8,
    # Gecis kareleri kisa: uc kare x uc oyun karesi = 9 kare (~0.15 sn).
    # Varsayilan 7'de tutulsalardi inis ve donus agir cekim gorunurdu.
    "land": 3,
    "turn": 3,
    "brake": 3,
}
# **Zamanla surulen durumlarin TOPLAM suresi** (oyun karesi). Poz sayisi
# 25.09.2026'da artti (akici animasyon); bekleme bu sureden turetiliyor ki
# dongunun temposu ve dusmanlarin savurusu eskisiyle AYNI kalsin:
#   bosta 6x9=54, kosu 8x5=40, saldiri 5x7=35, hasar/kacinma 2x7=14.
# Poz sayisi degisse de sure degismiyor - kare kare ayni zaman, daha cok poz.
DURATIONS: dict[str, int] = {
    "idle": 54,
    "run": 40,
    "attack1": 35,
    "attack2": 35,
    "attack3": 35,
    "hurt": 14,
    "dodge": 14,
    "jump": 16,
}


def hold_for(state: str, count: int) -> float:
    """Bu durumda bir pozun kac oyun karesi durdugu (kesirli olabilir)."""
    total = DURATIONS.get(state)
    if total is not None and count > 0:
        return total / count
    return float(HOLD_OVERRIDES.get(state, DEFAULT_HOLD_FRAMES))

# Onbellek anahtari (ad, sallanma_indeksi, sprite_golgesi). Kumasi olmayan karakterler
# yalnizca notr varyanti alir - varyant uretmek bos maliyet olurdu.
_sprite_cache: dict[tuple[str, int, bool], dict[str, list[pygame.Surface]]] = {}

# Sallanma varyanti YALNIZCA bu karakterlere uretiliyor. Oyuncu her karede
# ekranda ve kontrol edilen sey o; dusman/NPC icin ek 2x sprite bellegi
# gorunmeyecek bir kazanc icin odenirdi.
SWAY_CHARACTERS: frozenset[str] = frozenset({
    "rey", "rey_armed", "ardo", "ardo_armed",
})
_flipped_cache: dict[int, pygame.Surface] = {}
_silhouette_cache: dict[int, pygame.Surface] = {}
_tint_cache: dict[tuple, pygame.Surface] = {}


def sway_levels(name: str) -> int:
    """Bu karakterin kac sallanma varyanti var? Kumasi yoksa 1."""
    spec = CHARACTERS.get(name)
    if spec is None or name not in SWAY_CHARACTERS or not has_cloth(spec):
        return 1
    return len(SWAY_BIASES)


def sprite_set(name: str, sway: int = SWAY_NEUTRAL, *, shadow: bool = True
               ) -> dict[str, list[pygame.Surface]]:
    """Karakterin tum animasyonlari - ilk cagirmada uretilir, sonra onbellek."""
    if sway_levels(name) == 1:
        sway = SWAY_NEUTRAL
    key = (name, sway, shadow)
    cached = _sprite_cache.get(key)
    if cached is None:
        spec: CharSpec = CHARACTERS[name]
        cached = build_sprite_set(spec, SWAY_BIASES[sway], shadow=shadow)
        _sprite_cache[key] = cached
    return cached


def clear_cache() -> None:
    """Palet ya da rig degistiginde cagrilir."""
    _sprite_cache.clear()
    _flipped_cache.clear()
    _silhouette_cache.clear()
    _tint_cache.clear()


def _flipped(surface: pygame.Surface) -> pygame.Surface:
    key = id(surface)
    cached = _flipped_cache.get(key)
    if cached is None:
        cached = flip_h(surface)
        _flipped_cache[key] = cached
    return cached


def _silhouetted(surface: pygame.Surface,
                 colour: palette.RGB) -> pygame.Surface:
    key = (id(surface), colour)
    cached = _silhouette_cache.get(key)
    if cached is None:
        cached = silhouette(surface, colour)
        if len(_silhouette_cache) > 512:
            _silhouette_cache.clear()
        _silhouette_cache[key] = cached
    return cached


def _tinted(surface: pygame.Surface, colour: palette.RGB,
            strength: float) -> pygame.Surface:
    """Renge dogru **karistirir** - siluet korunur.

    `_silhouetted` sprite'i tek renge duzlestirir; iki karelik vurus flasi
    icin dogru, kalici bir durum icin degil. Az canli dusman o yolla
    ciziliyordu ve omrunun geri kalaninda sekilsiz bir bloga donuyordu -
    "durumu renkle anlat" kurali siluet okunurlugunu yemeyecek.
    """
    key = (id(surface), colour, round(strength, 2))
    cached = _tint_cache.get(key)
    if cached is None:
        cached = tint(surface, colour, strength)
        if len(_tint_cache) > 512:
            _tint_cache.clear()
        _tint_cache[key] = cached
    return cached


class Animator:
    """Bir karakterin animasyon durumunu surer."""

    def __init__(self, character: str) -> None:
        self.character = character
        self.levels = sway_levels(character)
        # Sallanma yayı: hedefi GECIKMELI takip eder. Ikincil hareketin
        # tamami bu gecikmede - anlik takip etseydi pelerin govdeye
        # yapisik olurdu ve hicbir sey kazanmazdik. Duran karakterde
        # hedef 0'a duser ama yay asar (overshoot) ve pelerin one
        # savrulur: durusun "agirligi" buradan okunuyor.
        self.sway_value = 0.0        # -1..+1 surekli
        self.sway_velocity = 0.0
        self.sway_index = SWAY_NEUTRAL
        self.frames = sprite_set(character, self.sway_index)
        self.state = "idle"
        self.index = 0
        self.hold = 0
        self.finished = False
        # Kare bekleme carpani: 1.0 normal. Sessiz yuruyuste kosu dongusu
        # yavasliyor - yavas kayan govde tam hizda kosuyor gibi gorunmesin.
        self.hold_scale = 1.0

    def play(self, state: str, restart: bool = False) -> None:
        if state not in self.frames:
            return
        if state == self.state and not restart:
            return
        self.state = state
        self.index = 0
        self.hold = 0
        self.finished = False

    def update(self) -> None:
        """Zamanla surulen kip - bir oyun karesi ilerlet."""
        sequence = self.frames.get(self.state)
        if not sequence:
            return
        _, _, looping = ANIMATIONS.get(self.state, (None, 1, True))
        if self.finished and not looping:
            return

        self.hold += 1
        limit = hold_for(self.state, len(sequence)) * self.hold_scale
        if self.hold < limit:
            return
        # Kesirli bekleme: kalan birikiyor - 35 karelik saldiri 8 pozla
        # yine 35 karede biter, 40'ta degil.
        self.hold -= limit
        self.index += 1
        if self.index >= len(sequence):
            if looping:
                self.index = 0
            else:
                self.index = len(sequence) - 1
                self.finished = True

    def update_sway(self, target: float) -> None:
        """Sallanmayi bir yay gibi hedefe yaklastirir.

        `target` -1..+1: **arkaya dogru** ne kadar savruluyor. Genelde
        yatay hizdan turetiliyor (bkz. `player_anim.update_animation`).

        Kritik sayilar: sertlik dusuk (0.14) ki gecikme hissedilsin,
        sonumleme 0.80 ki durusta bir kez asip geri gelsin. Sonumlemeyi
        1.0'a yaklastirmak sonsuz salinim, 0.5'e cekmek gecikmesiz
        takip demek - ikisi de ikincil hareketi oldururdu.
        """
        if self.levels <= 1:
            return
        target = max(-1.0, min(1.0, target))
        self.sway_velocity += (target - self.sway_value) * 0.14
        self.sway_velocity *= 0.80
        self.sway_value += self.sway_velocity

        # Surekli degeri ayrik varyanta cevir. Histerezis (0.34/0.26)
        # sinirdaki bir degerin iki varyant arasinda titremesini onler -
        # tek esik olsaydi karakter kosarken pelerin carpardi.
        index = self.sway_index
        if self.sway_value > 0.34:
            index = 2
        elif self.sway_value < -0.34:
            index = 0
        elif abs(self.sway_value) < 0.26:
            index = SWAY_NEUTRAL
        if index != self.sway_index:
            self.sway_index = index
            self.frames = sprite_set(self.character, index)

    def set_progress(self, ratio: float) -> None:
        """Ilerlemeyle surulen kip - saldirilar icin.

        `ratio` saldirinin kendi kare butcesindeki konumu (0..1).
        """
        sequence = self.frames.get(self.state)
        if not sequence:
            return
        ratio = max(0.0, min(1.0, ratio))
        self.index = min(len(sequence) - 1, int(ratio * len(sequence)))
        self.hold = 0

    @property
    def image(self) -> pygame.Surface | None:
        sequence = self.frames.get(self.state)
        if not sequence:
            return None
        return sequence[min(self.index, len(sequence) - 1)]

    def render(self, facing: int, *, flash: bool = False,
               squash: tuple[float, float] = (1.0, 1.0),
               silhouette_mode: bool = False,
               tint_colour: palette.RGB | None = None,
               tint_strength: float = 1.0,
               alpha: int = 255, shadow: bool = True) -> pygame.Surface | None:
        """Cizime hazir yuzey: yon, flas, deformasyon ve siluet uygulanmis."""
        if shadow:
            image = self.image
        else:
            # Oynanista golge haritanin zeminine cizilir. Ayak veya silah
            # piksellerini kirpmak yerine golgesiz atlas bir kez uretilir.
            sequence = sprite_set(self.character, self.sway_index,
                                  shadow=False).get(self.state)
            image = sequence[min(self.index, len(sequence) - 1)] if sequence else None
        if image is None:
            return None
        if facing < 0:
            image = _flipped(image)

        if silhouette_mode:
            image = _silhouetted(image, palette.color("stone_light"))
        elif flash:
            image = _silhouetted(image, palette.role("hit_flash"))
        elif tint_colour is not None:
            # strength 1.0 = tam duzlestirme (eski davranis), altinda
            # karistirma: renk okunur ama siluet kaybolmaz.
            if tint_strength >= 1.0:
                image = _silhouetted(image, tint_colour)
            else:
                image = _tinted(image, tint_colour, tint_strength)

        image = squash_surface(image, squash)

        if alpha < 255:
            image = image.copy()
            image.set_alpha(alpha)
        return image
