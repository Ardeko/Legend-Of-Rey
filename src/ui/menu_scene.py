"""Ana menu sahnesi - mor alev, zincirler, Rey ve Ardo.

`docs/menu-ui.md` 1 ve 2. On katman, arkadan one:

    1 derin karanlik    tonoz kemerleri
    2 arka duvar        tas dokusu, catlaklar
    3 sarkan zincirler  farkli fazlarda salinim
    4 toz zerrecikleri  yukari suzulur, alevin isiginda parlar
    5 mor alev + kaide  ana isik kaynagi
    6 aura              nefes gibi buyuyup kuculur
    7 karakterler       Rey ve Ardo, sirt sirta, ruzgarda
    8 zemin             islak tas, alevin yansimasi
    9 on toz            kameraya yakin, hizli - derinlik hissi
   10 vinyet            kenar karartma

Hicbiri pahali degil; 3, 4, 6, 9 tamamen kodla uretiliyor, sprite yok.

## Menu hikayeyle degisir (docs/menu-ui.md 2)

Bes asama. Oyuncu oyunu her actiginda ilerlemesini gorur:

    1 Yalniz      yeni oyun     sadece Rey, alev turuncu, kolye elinde
    2 Ilk Isik    B3 bitti      alev mora doner, arkada belirsiz bir golge
    3 Iki Kisi    B6 bitti      Ardo belirir, sirt sirta, 8 piksel mesafe
    4 Yaklasma    B16 bitti     mesafe 3 piksele iner, ruzgar azalir
    5 Ev          oyun bitti    Cemo da var, alev turuncu, ruzgar durmus

Ayni sprite'lar, farkli konum + palet. Neredeyse bedava, etkisi buyuk.
"""
from __future__ import annotations

import math
import random

import pygame

from src.art import palette
from src.art.animator import Animator
from src.art.glow import radial_glow, rim_light
from src.art.wind import shear, shear_offsets
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH

# --- Sahne yerlesimi --------------------------------------------------------
# Sol ucte bir logo ve butonlar, sag ucte iki sahne (docs/menu-ui.md 1).
# Kayit karti x 250..428 arasini kapliyor. Alev sahnenin kalbi; kartin
# arkasinda kalmamali - bu yuzden kaide kartin **saginda** duruyor.
SCENE_CENTER_X = 382           # Karakterlerin ortasi
FLOOR_Y = 240
PEDESTAL = pygame.Rect(436, 194, 28, 46)
FLAME_BASE = (450, 195)

CHAIN_COLUMNS = ((248, 70), (296, 46), (338, 86), (404, 58), (470, 36))
DUST_COUNT = 40
FRONT_DUST_COUNT = 15

AURA_PERIOD = 150          # 2.5 saniye - nefes
FLAME_FRAME_HOLD = 7       # ~8 FPS (CLAUDE.md 6)

# --- Asamalar ---------------------------------------------------------------
class Stage:
    """Bir menu asamasinin gorunumu."""

    def __init__(self, index: int, flame: str, ardo: bool, cemo: bool,
                 gap: int, wind: float, shadow: bool = False) -> None:
        self.index = index
        self.flame = flame          # "torch" (turuncu) | "violet"
        self.ardo = ardo
        self.cemo = cemo
        self.gap = gap              # Rey ile Ardo arasindaki piksel
        self.wind = wind            # Ruzgar carpani
        self.shadow = shadow        # Arkada belirsiz golge (asama 2)


STAGES = (
    Stage(1, "torch",  ardo=False, cemo=False, gap=0,  wind=1.0),
    Stage(2, "violet", ardo=False, cemo=False, gap=0,  wind=1.0, shadow=True),
    Stage(3, "violet", ardo=True,  cemo=False, gap=8,  wind=1.0),
    Stage(4, "violet", ardo=True,  cemo=False, gap=3,  wind=0.5),
    Stage(5, "torch",  ardo=True,  cemo=True,  gap=3,  wind=0.0),
)


def stage_for(save_data) -> Stage:
    """Kayittaki ilerlemeye gore asama.

    Kayit yoksa 1. asama - yeni baslayan Rey'i yalniz gorur.
    """
    if save_data is None:
        return STAGES[0]
    if (getattr(save_data, "finished", False)
            or getattr(save_data, "flags", {}).get("finished", False)):
        return STAGES[4]
    chapter = getattr(save_data, "chapter", 1)
    if chapter > 16:
        return STAGES[3]
    if chapter > 6:
        return STAGES[2]
    if chapter > 3:
        return STAGES[1]
    return STAGES[0]


# --- Sahne ------------------------------------------------------------------
class MenuBackdrop:
    """Menunun arkasindaki canli sahne.

    Menu sahnesinden ayri tutuldu: `menu.py` butonlarin ve kayit kartinin
    mantigini tasiyor, burasi yalnizca gorunum. Ikisi bir dosyada olsaydi
    600 satiri asardi (CLAUDE.md 11).
    """

    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.frame = 0

        self.rey = Animator("rey")
        self.rey.play("idle")
        self.ardo = Animator("ardo")
        self.ardo.play("idle")
        self.cemo = Animator("cemo")
        self.cemo.play("idle")

        # Toz: konum ve hiz bir kez secilir, sonra sabit dolasir. Her karede
        # yeniden rastgele olsaydi titrerdi.
        rng = random.Random(7)
        self.dust = [self._new_mote(rng, front=False) for _ in range(DUST_COUNT)]
        self.front_dust = [self._new_mote(rng, front=True)
                           for _ in range(FRONT_DUST_COUNT)]
        self._rng = rng

        self._aura_cache: dict[tuple, pygame.Surface] = {}
        self._pool_cache: dict[tuple, pygame.Surface] = {}
        self._vault = None       # Katman 1-2 bir kez cizilir, sonra blit
        self._floor = None
        self._vignette = None
        self._palette_mode = palette.active_mode()

    # --- Toz ---------------------------------------------------------------
    def _new_mote(self, rng: random.Random, front: bool) -> list[float]:
        return [
            rng.uniform(170, INTERNAL_WIDTH),
            rng.uniform(0, INTERNAL_HEIGHT),
            rng.uniform(0.10, 0.34) * (3.0 if front else 1.0),   # yukselme
            rng.uniform(0.0, math.tau),                          # salinim fazi
        ]

    def _update_dust(self, motes: list[list[float]], front: bool) -> None:
        for mote in motes:
            mote[1] -= mote[2]
            if mote[1] < -2:
                mote[0] = self._rng.uniform(170, INTERNAL_WIDTH)
                mote[1] = INTERNAL_HEIGHT + 2

    # --- Dongu -------------------------------------------------------------
    def update(self) -> None:
        self.frame += 1
        self.rey.update()
        self.ardo.update()
        self.cemo.update()
        self._update_dust(self.dust, front=False)
        self._update_dust(self.front_dust, front=True)

    # --- Cizim -------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        # Ayarlardan donulunce eski renk koru paletinin dokusu kalmasin.
        if self._palette_mode != palette.active_mode():
            self._palette_mode = palette.active_mode()
            self._vault = self._floor = self._vignette = None
            self._aura_cache.clear()
            self._pool_cache.clear()
        self._draw_vault(surface)
        self._draw_chains(surface)
        self._draw_dust(surface, self.dust, front=False)
        self._draw_pedestal(surface)
        aura_radius = self._draw_aura(surface)
        self._draw_flame(surface)
        self._draw_characters(surface)
        self._draw_floor(surface, aura_radius)
        self._draw_dust(surface, self.front_dust, front=True)
        self._draw_vignette(surface)

    # 1-2: derin karanlik + arka duvar --------------------------------------
    def _draw_vault(self, surface: pygame.Surface) -> None:
        if self._vault is None:
            self._vault = self._build_vault()
        surface.blit(self._vault, (0, 0))

    def _build_vault(self) -> pygame.Surface:
        """Karanlik koridor, kemer taslari ve on sutunlar: uc derinlik."""
        layer = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT)).convert()
        layer.fill(palette.color("ink"))
        rng = random.Random(11)
        # Soldaki negatif alan, baslik ve butonlarin sakin zemini.
        layer.fill(palette.color("abyss_dark"), (222, 0, 258, FLOOR_Y))
        for row, y in enumerate(range(10, FLOOR_Y, 19)):
            for x in range(222 - (row % 2) * 23, INTERNAL_WIDTH, 46):
                block = pygame.Rect(max(222, x), y, 43, 17)
                pygame.draw.rect(layer, palette.color("ink"), block, 1)
                if rng.randrange(3) == 0:
                    layer.fill(palette.color("stone_darkest"),
                               (max(224, x + 3), y + 2, rng.randrange(4, 12), 1))
        self._draw_arch(layer, 355, 99, 32, "stone_darkest")
        self._draw_arch(layer, 355, 69, 66, "ink")
        # En gerideki kapinin icindeki dar isik: koridorun derinligini kurar.
        layer.fill(palette.color("abyss_dark"), (346, 124, 18, 102))
        layer.fill(palette.color("ink_soft"), (347, 125, 2, 91))
        for x in (232, 470):
            layer.fill(palette.color("ink_soft"), (x, 0, 10, FLOOR_Y))
            layer.fill(palette.color("stone_darkest"), (x, 0, 2, FLOOR_Y))
            for y in range(24, FLOOR_Y, 32):
                layer.fill(palette.color("ink"), (x, y, 10, 2))
                layer.fill(palette.color("stone_darkest"), (x - 2, y - 3, 14, 3))
        # Rastgele ama sabit catlaklar: animasyonda yuzey titremiyor.
        for _ in range(22):
            x, y = rng.randrange(236, 478), rng.randrange(8, 214)
            pygame.draw.lines(layer, palette.color("ink"), False,
                              [(x, y), (x - 2, y + 4), (x, y + 9)])
        return layer

    def _draw_arch(self, surface: pygame.Surface, cx: int, radius: int,
                   top: int, stone: str) -> None:
        """Yuvarlak ust, dik ayaklar, tek tek okunabilen kilit taslari."""
        spring = top + radius
        opening = pygame.Rect(cx - radius + 10, spring, radius * 2 - 20,
                              FLOOR_Y - spring)
        pygame.draw.circle(surface, palette.color("ink"), (cx, spring), radius)
        surface.fill(palette.color("ink"), opening)
        arc = pygame.Rect(cx - radius, top, radius * 2, radius * 2)
        pygame.draw.arc(surface, palette.color(stone), arc, 0, math.pi, 9)
        pygame.draw.arc(surface, palette.color("ink_soft"), arc.inflate(-18, -18),
                        0, math.pi, 2)
        for side in (-1, 1):
            x = cx + side * radius - (9 if side > 0 else 0)
            surface.fill(palette.color(stone), (x, spring, 9, FLOOR_Y - spring))
            for y in range(spring, FLOOR_Y, 17):
                surface.fill(palette.color("ink"), (x, y, 9, 1))
        for step in range(1, 12):
            angle = step * math.pi / 12
            points = [(round(cx + math.cos(angle) * r),
                       round(spring - math.sin(angle) * r))
                      for r in (radius - 9, radius)]
            pygame.draw.line(surface, palette.color("ink"), *points)

    # 3: sarkan zincirler ---------------------------------------------------
    def _draw_chains(self, surface: pygame.Surface) -> None:
        """Her zincir farkli fazda salinir - hepsi ayni anda sallanmasin."""
        dark = palette.color("ink_soft")
        light = palette.color("stone_dark")
        for index, (x, length) in enumerate(CHAIN_COLUMNS):
            phase = self.frame * 0.015 + index * 1.7
            offsets = shear_offsets(length, phase, amplitude=2.4 + index * 0.3,
                                    wave_length=0.06, anchor="top")
            for y in range(0, length - 4, 5):
                px = x + offsets[y]
                pygame.draw.rect(surface, dark, (px, y, 3, 5), 1)
                surface.fill(light, (px, y + 1, 1, 2))

    # 4 ve 9: toz -----------------------------------------------------------
    def _draw_dust(self, surface: pygame.Surface, motes: list[list[float]],
                   front: bool) -> None:
        # On toz daha parlak ve daha buyuk: kameraya yakin.
        for x, y, _speed, wobble in motes:
            drift = math.sin(self.frame * 0.02 + wobble) * 3.0
            px = int(x + drift)
            py = int(y)
            if 0 <= px < INTERNAL_WIDTH and 0 <= py < INTERNAL_HEIGHT:
                distance = math.hypot(px - FLAME_BASE[0], py - FLAME_BASE[1])
                colour = (self._flame_colour(bright=True) if distance < 44
                          else palette.color("stone_dark" if front else "stone_darkest"))
                size = 2 if front and distance < 70 else 1
                surface.fill(colour, (px, py, size, size))

    # 5: kaide --------------------------------------------------------------
    def _draw_pedestal(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("stone_dark"), PEDESTAL)
        surface.fill(palette.color("stone_darkest"),
                     (PEDESTAL.right - 6, PEDESTAL.y, 6, PEDESTAL.height))
        # Basamakli sutun basi, oluklar ve oyulmus alev amblemi.
        for x in (PEDESTAL.x + 4, PEDESTAL.right - 10):
            surface.fill(palette.color("ink_soft"), (x, PEDESTAL.y + 10, 2, 28))
            surface.fill(palette.color("stone"), (x - 1, PEDESTAL.y + 10, 1, 28))
        surface.fill(palette.color("stone"),
                     (PEDESTAL.x - 3, PEDESTAL.y, PEDESTAL.width + 6, 3))
        surface.fill(palette.color("stone_darkest"),
                     (PEDESTAL.x - 1, PEDESTAL.y + 5, PEDESTAL.width + 2, 3))
        surface.fill(palette.color("stone"),
                     (PEDESTAL.x - 3, PEDESTAL.bottom - 4, PEDESTAL.width + 6, 2))
        cx, cy = PEDESTAL.centerx - 2, PEDESTAL.centery
        pygame.draw.polygon(surface, palette.color("ink_soft"),
                            [(cx, cy - 6), (cx + 4, cy), (cx, cy + 6), (cx - 4, cy)])
        surface.fill(self._flame_colour(bright=False), (cx, cy - 2, 1, 4))

    # 6: aura ---------------------------------------------------------------
    def _draw_aura(self, surface: pygame.Surface) -> int:
        """Radyal isik halesi. Yaricap nefes gibi +-%12 degisir."""
        breath = math.sin(self.frame * math.tau / AURA_PERIOD)
        radius = int(46 * (1.0 + 0.12 * breath))
        colour = self._flame_colour(bright=False)

        cached = self._aura_cache.get((radius, colour))
        if cached is None:
            cached = radial_glow(radius, colour, peak=0.42)
            if len(self._aura_cache) > 32:
                self._aura_cache.clear()
            self._aura_cache[(radius, colour)] = cached
        surface.blit(cached, (FLAME_BASE[0] - radius, FLAME_BASE[1] - radius),
                     special_flags=pygame.BLEND_RGB_ADD)
        return radius

    # 5: alev ---------------------------------------------------------------
    def _flame_colour(self, bright: bool) -> palette.RGB:
        if self.stage.flame == "torch":
            return palette.color("ember_light" if bright else "ember")
        return palette.color("violet_bright" if bright else "violet")

    def _draw_flame(self, surface: pygame.Surface) -> None:
        """Alti karelik dongu, 8 FPS. Kod uretimi - sprite yok."""
        step = (self.frame // FLAME_FRAME_HOLD) % 6
        base_x, base_y = FLAME_BASE
        body = self._flame_colour(bright=False)
        core = self._flame_colour(bright=True)

        height = 24
        for i in range(height):
            t = i / height
            # Yukari dogru daralir; her kare dalga biraz kayar.
            width = max(1, int((1.0 - t) * 9 * (1.0 + 0.12 * math.sin(
                step * 1.05 + t * 5.5))))
            sway = int(round(2.2 * t * math.sin(step * 0.9 + t * 3.1)))
            y = base_y - i
            surface.fill(body, (base_x - width // 2 + sway, y, width, 1))
            if t < 0.62 and width > 2:
                inner = max(1, width // 2)
                surface.fill(core,
                             (base_x - inner // 2 + sway, y, inner, 1))

        # Kivilcimlar: alevden yukari suzulur, yukseldikce soner.
        for i in range(9):
            phase = (self.frame * 0.9 + i * 31) % 90
            if phase > 70:
                continue
            rise = phase * 0.8
            drift = math.sin(self.frame * 0.05 + i) * 4.0
            y = int(base_y - height - rise)
            x = int(base_x + drift)
            if 0 <= y < INTERNAL_HEIGHT and 0 <= x < INTERNAL_WIDTH:
                surface.fill(core if phase < 30 else body, (x, y, 1, 1))

    # 7: karakterler --------------------------------------------------------
    def _draw_characters(self, surface: pygame.Surface) -> None:
        stage = self.stage
        gap = stage.gap
        # Rey solda, one donuk; Ardo saginda, sirt sirta.
        rey_x = SCENE_CENTER_X - (gap // 2) - 10
        ardo_x = SCENE_CENTER_X + (gap // 2) + 10

        if stage.shadow:
            # Asama 2: arkada belirsiz bir golge - Ardo'nun habercisi.
            # Alfa 52 denendi: karanlik duvarda tamamen kayboluyordu.
            # Golge belirsiz olmali ama **gorunur** - habercisi oldugu sey
            # ancak gorulurse anlam tasiyor.
            self._blit_character(surface, self.ardo, ardo_x + 6, facing=1,
                                 wind=stage.wind, alpha=110, flat=True)

        if stage.ardo:
            self._blit_character(surface, self.ardo, ardo_x, facing=1,
                                 wind=stage.wind)
        # Rey daima var. Sola bakiyor: sirt sirta duruslari boyle olusuyor.
        self._blit_character(surface, self.rey, rey_x, facing=-1,
                             wind=stage.wind)

        if stage.cemo:
            # Asama 5: Cemo ikisinin arasinda. Kendi spec'i var - kucultulmus
            # Rey degil. Cocuk oranlari (buyuk kafa, kisa uzuv) ve kivircik
            # sac onu bir bakista ayiriyor.
            self._blit_character(surface, self.cemo, SCENE_CENTER_X, facing=1,
                                 wind=0.0)

    def _blit_character(self, surface: pygame.Surface, animator: Animator,
                        x: int, facing: int, wind: float,
                        alpha: int = 255, flat: bool = False,
                        scale: float = 1.0) -> None:
        image = animator.render(facing, alpha=alpha)
        if image is None:
            return
        if flat:
            from src.art.forge import silhouette
            image = silhouette(image, palette.color("ink"))
            image = image.copy()
            image.set_alpha(alpha)
        if scale != 1.0:
            size = (max(1, int(image.get_width() * scale)),
                    max(1, int(image.get_height() * scale)))
            image = pygame.transform.scale(image, size)

        if wind > 0.0:
            # Ruzgar sagdan sola: Rey'in saci ve Ardo'nun pelerini **ayni**
            # yonde dalgalanir. Kucuk detay, "birlikteler" mesaji.
            phase = self.frame * 0.055
            image = shear(image, phase, amplitude=1.7 * wind,
                          wave_length=0.30, anchor="bottom")

        pos = (x - image.get_width() // 2, FLOOR_Y - image.get_height())
        if not flat:
            pygame.draw.ellipse(surface, palette.color("void"),
                                (x - 10, FLOOR_Y - 3, 20, 4))
        surface.blit(image, pos)

        if not flat:
            # Isik alevden geliyor: alev karakterin saginda oldugu icin
            # aydinlanan kenar da sag kenar.
            lit_side = 1 if FLAME_BASE[0] > x else -1
            rim = rim_light(image, self._flame_colour(bright=True), lit_side)
            if rim is not None:
                surface.blit(rim, pos, special_flags=pygame.BLEND_RGB_ADD)

    # 8: zemin --------------------------------------------------------------
    def _draw_floor(self, surface: pygame.Surface, aura_radius: int) -> None:
        if self._floor is None:
            self._floor = self._build_floor()
        surface.blit(self._floor, (0, FLOOR_Y))

        # Islak yansima: alevin isigi zeminde titresir.
        colour = self._flame_colour(bright=False)
        flicker = 1.0 + 0.10 * math.sin(self.frame * 0.11)
        width = max(8, int(aura_radius * 0.8 * flicker))
        # Yuvarlak haleyi yassilastirip zemine yatiriyoruz: islak tasta
        # yansima boyle okunur.
        key = (width, colour)
        pool = self._pool_cache.get(key)
        if pool is None:
            glow = radial_glow(width, colour, peak=0.22)
            pool = pygame.transform.scale(glow, (width * 2, 14)).convert()
            self._pool_cache[key] = pool
        surface.blit(pool, (FLAME_BASE[0] - width, FLOOR_Y - 2),
                     special_flags=pygame.BLEND_RGB_ADD)
        # Dar kirik yansimalar islak tas hissi verir; UI bolgesine tasmaz.
        for row in range(4):
            spread = 11 - row * 2
            shift = round(math.sin(self.frame * 0.035 + row * 1.4) * 2)
            surface.fill(colour, (FLAME_BASE[0] - spread + shift,
                                 FLOOR_Y + 3 + row * 3, spread * 2, 1))

    def _build_floor(self) -> pygame.Surface:
        floor = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT - FLOOR_Y)).convert()
        floor.fill(palette.color("ink_soft"))
        floor.fill(palette.color("stone_darkest"), (0, 0, INTERNAL_WIDTH, 2))
        for y in (4, 12, 25):
            floor.fill(palette.color("ink"), (220, y, INTERNAL_WIDTH - 220, 1))
        for x in range(210, INTERNAL_WIDTH, 50):
            pygame.draw.line(floor, palette.color("ink"),
                             (x, 1), (x + (x - 355) // 3, 29))
        return floor

    # 10: vinyet ------------------------------------------------------------
    def _draw_vignette(self, surface: pygame.Surface) -> None:
        if self._vignette is None:
            veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                                  pygame.SRCALPHA)
            for i in range(26):
                alpha = int(7 * (1.0 - i / 26))
                pygame.draw.rect(veil, (*palette.color("void"), alpha),
                                 pygame.Rect(i, i, INTERNAL_WIDTH - i * 2,
                                             INTERNAL_HEIGHT - i * 2), 1)
            self._vignette = veil.convert_alpha()
        surface.blit(self._vignette, (0, 0))
