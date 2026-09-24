"""Dikey yolculuk - menuden oyuna kesintisiz gecis.

`docs/menu-ui.md` 0.3 ve 0.4. God of War 2'deki koltuktan oynanisa gecen
kamera mantigi.

**Sorun:** Menu sahnesi mahzende (derinde), Bolum 1 koyde (yuzeyde). Duz
kayma bu iki mekani baglamaz.

**Cozum:** Kamera mor alevden **yukari** cikar.

    KOY / GECE          <- Bolum 1 baslar
    toprak, kokler
    ust kaya katmani
    tas tonoz
    MOR ALEV            <- menu sahnesi

**Anlami:** Menu **gideceginiz** yer, oyun **geldiginiz** yer. Mor alev sen
daha baslamadan orada seni bekliyor. Oyuncu bunu ilk oynayista anlamaz -
B3'te alevi bulunca fark eder.

DEVAM ET ayni gecisin tersi: kamera alevden **asagi** iner, kaldigin bolume
kadar. Ne kadar ilerlediysen o kadar uzun dusersin - ilerlemeyi bedavaya
hissettiren bir gecis. Varis `catalog.chapter_scene_class` ile kayittaki
bolum; Bolum 1'e duserse yolculuk yalan soylemis olur.

## Teknik

Tek bir uzun dikey doku yuzeyi, dort parallax katmani. Her karede yalnizca
y-ofset degisir.

**Ofset tam sayiya yuvarlanir.** Ondalik ofset piksel art dokusunu titretir -
projenin en yaygin ve en fark edilir hatasi (CLAUDE.md 9).

Hizli gecerken hafif dikey hareket bulanikligi: ayni yuzey uc kez, birer
piksel kaydirilarak, dusuk alfa ile ust uste. Ucuz ve etkili.
"""
from __future__ import annotations

import random

import pygame

from src.art import palette
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.cinematic import CinematicScene

TOTAL_UP = int(4.5 * FPS)       # Menuden koye
BAND_HEIGHT = 300               # Bir katmanin dikey yuksekligi
MOTION_BLUR_AT = 1.6            # Bu hizin ustunde bulaniklik

# Katmanlar asagidan yukari: mahzenden yuzeye.
# (ad, taban rengi, doku rengi, yogunluk)
BANDS = (
    ("alev",   "abyss_dark",    "violet_dark",  0.05),
    ("tonoz",  "ink_soft",      "stone_darkest", 0.30),
    ("kaya",   "stone_darkest", "stone_dark",   0.45),
    ("toprak", "earth_dark",    "earth",        0.55),
    ("koy",    "abyss",         "abyss_light",  0.12),
)


# --- Safak varyanti (24.09.2026, epilog "Eve Donus") --------------------------
# Oyunun sonunda ayni yolculuk bir daha yapiliyor: bu kez mor alevden
# degil **Jet'in kuyusundan**, ve varilan koy gece degil sabah. Oyunun
# basindaki yolculugun aynasi - bu kez gidilen yer degil donulen yer.
DAWN_BOTTOM = ("kuyu", "ink_soft", "stone_darkest", 0.30)
# Ip, seridin ortasindan biraz sagda, dipten ufka kadar.
ROPE_X = INTERNAL_WIDTH // 2 + 22
ROPE_KNOT_STEP = 14
# Safak gogu: ustten ufka (satir, renk). `village_backdrop.DAWN_BANDS`
# ile ayni sira, seride olceklenmis.
DAWN_SKY = ((0, "abyss"), (60, "abyss_light"), (120, "stone_light"),
            (170, "flesh_light"), (210, "ember_light"), (238, "gold"))


def continue_kwargs(data) -> dict:
    """DEVAM ET: kayittaki bolume **asagi** - bitmis oyunda koye **yukari**.

    Menu ve yuva ekrani ayni karari veriyor; iki yerde yazilsaydi bir
    gun ayrisirdi. Oyunu bitirmis kayit eskiden son boss'a iniyordu
    (24.09.2026'da duzeltildi): artik sabah koyune cikiyor - oyun
    sonrasi, donulebilecek bir yer.
    """
    from src.systems.homecoming import finished
    if finished(data):
        from src.scenes.epilogue_village import EpilogueVillageScene
        return {"direction": "up", "variant": "dawn",
                "character": data.character,
                "next_scene": EpilogueVillageScene,
                "next_kwargs": {"character": data.character,
                                "postgame": True}}
    return {"direction": "down", "chapter": data.chapter,
            "character": data.character}


class VerticalJourneyScene(CinematicScene):
    """Menu ile bolum arasindaki dikey kamera yolculugu."""

    duration_frames = TOTAL_UP

    def on_enter(self, direction: str = "up", chapter: int = 1,
                 character: str = "rey", variant: str = "night",
                 next_scene: type | None = None,
                 next_kwargs: dict | None = None,
                 **kwargs: object) -> None:
        """`variant="dawn"` epilogun yolculugu; `next_scene` varisi ezer.

        Varis normalde yone gore (yukari = Bolum 1, asagi = kayittaki
        bolum). Epilog kendi varisini veriyor: sabah koyu.
        """
        super().on_enter(**kwargs)
        self.direction = direction
        self.chapter = chapter
        self.character = character
        self.variant = variant
        self.next_scene = next_scene
        self.next_kwargs = dict(next_kwargs or {})

        # Ne kadar ilerlediysen o kadar uzun dusersin (docs/menu-ui.md 0.4).
        if direction == "down":
            extra = min(3.0, 0.12 * max(0, chapter - 1))
            self.duration_frames = int(TOTAL_UP * (1.0 + extra))

        self._strip = self._build_strip()
        self._last_offset = 0

    # --- Doku --------------------------------------------------------------
    def _build_strip(self) -> pygame.Surface:
        """Tek uzun dikey yuzey. Bir kez uretilir, sonra yalnizca kaydirilir."""
        height = BAND_HEIGHT * len(BANDS)
        strip = pygame.Surface((INTERNAL_WIDTH, height))
        rng = random.Random(23)
        dawn = self.variant == "dawn"
        bands = ((DAWN_BOTTOM,) + BANDS[1:]) if dawn else BANDS

        for index, (_name, base, detail, density) in enumerate(bands):
            top = height - (index + 1) * BAND_HEIGHT     # 0 = en ust (koy)
            strip.fill(palette.color(base),
                       (0, top, INTERNAL_WIDTH, BAND_HEIGHT))

            # Katmanlar birbirine **gecerek** karisir - keskin sinir olmasin.
            blend = 40
            for i in range(blend):
                if top + i >= height:
                    break
                alpha_row = pygame.Surface((INTERNAL_WIDTH, 1), pygame.SRCALPHA)
                alpha_row.fill((*palette.color(base),
                                int(255 * (1.0 - i / blend))))
                strip.blit(alpha_row, (0, top + i))

            count = int(INTERNAL_WIDTH * BAND_HEIGHT * density / 220)
            for _ in range(count):
                x = rng.randrange(INTERNAL_WIDTH)
                y = top + rng.randrange(BAND_HEIGHT)
                if index == 3:        # toprak: kokler - dikey cizgiler
                    for k in range(rng.randrange(3, 9)):
                        strip.set_at((x, min(height - 1, y + k)),
                                     palette.color(detail))
                elif index == 4:      # koy: gece gokyuzu
                    strip.set_at((x, y), palette.color(
                        "bone" if rng.random() < 0.3 else "stone_light"))
                else:                 # tas: catlak ve derz
                    length = rng.randrange(2, 7)
                    for k in range(length):
                        strip.set_at((min(INTERNAL_WIDTH - 1, x + k // 3),
                                      min(height - 1, y + k)),
                                     palette.color(detail))
        if dawn:
            self._decorate_dawn(strip)
            self._draw_rope(strip, height)
        else:
            self._decorate_village(strip, height)
        return strip.convert()

    def _decorate_dawn(self, strip: pygame.Surface) -> None:
        """Varis: sabah koyu. Gradyan gok, dogan gunes, sonuk pencereler.

        Gece surumunun (`_decorate_village`) aynasi: ayni ufuk, ayni
        tepe siluetleri; renkler ve isik kaynagi degisiyor.
        """
        horizon = BAND_HEIGHT - 46
        from src.world.village_backdrop import paint_bands
        paint_bands(strip, DAWN_SKY, horizon)
        from src.art.glow import radial_glow
        sun_x, sun_y = INTERNAL_WIDTH - 110, horizon - 8
        halo = radial_glow(40, palette.color("gold"), peak=0.40)
        strip.blit(halo, (sun_x - 40, sun_y - 40),
                   special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(strip, palette.color("gold"), (sun_x, sun_y), 12)
        pygame.draw.circle(strip, palette.color("white_flash"), (sun_x, sun_y), 8)

        rng = random.Random(31)
        x = 0
        while x < INTERNAL_WIDTH:
            width = rng.randrange(26, 62)
            top = horizon - rng.randrange(6, 26)
            pygame.draw.polygon(strip, palette.color("stone_dark"), [
                (x, horizon), (x + width // 2, top), (x + width, horizon)])
            x += width - 8
        strip.fill(palette.color("stone_darkest"),
                   (0, horizon, INTERNAL_WIDTH, BAND_HEIGHT - horizon))
        for _ in range(7):
            hx = rng.randrange(10, INTERNAL_WIDTH - 20)
            hw, hh = rng.randrange(9, 16), rng.randrange(7, 13)
            hy = horizon - hh
            strip.fill(palette.color("earth_dark"), (hx, hy, hw, hh))
            strip.fill(palette.color("ember_dark"), (hx + hw // 2, hy + hh // 2, 2, 2))

    def _draw_rope(self, strip: pygame.Surface, height: int) -> None:
        """Jet'in ipi - dipten ufka kadar, araliklarla dugum.

        Kamera ipin yaninda yukari cikiyor: oyuncu tirmanmiyor gibi
        gorunebilir ama **yol** o ip. B4'teki "dönüş için ip bıraktım"
        cumlesinin gorsel karsiligi bu cizgi.
        """
        horizon = BAND_HEIGHT - 46
        rope = palette.color("earth")
        knot = palette.color("earth_dark")
        strip.fill(rope, (ROPE_X, horizon, 1, height - horizon))
        for y in range(horizon + ROPE_KNOT_STEP, height, ROPE_KNOT_STEP):
            strip.fill(knot, (ROPE_X - 1, y, 3, 2))
        # Kazik - ipin ufukta bagli oldugu yer.
        strip.fill(knot, (ROPE_X - 1, horizon - 12, 3, 12))

    def _decorate_village(self, strip: pygame.Surface, height: int) -> None:
        """Varis noktasi okunur olmali.

        Yolculuk boyunca gecilen katmanlar dokudan ibaret; **varilan yer**
        bir yer gibi gorunmeli, yoksa yolculuk "karanlikta kaydik" olur.
        Ay ve ufuk cizgisi bunu tek basina yapiyor.
        """
        band_top = height - len(BANDS) * BAND_HEIGHT
        band_top = 0                       # koy en ustteki band
        horizon = BAND_HEIGHT - 46

        # Ay - sag ust, yumusak hale.
        from src.art.glow import radial_glow
        moon_x, moon_y = INTERNAL_WIDTH - 96, band_top + 62
        halo = radial_glow(34, palette.color("stone_light"), peak=0.30)
        strip.blit(halo, (moon_x - 34, moon_y - 34),
                   special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(strip, palette.color("bone"), (moon_x, moon_y), 11)
        pygame.draw.circle(strip, palette.color("stone_light"),
                           (moon_x - 3, moon_y - 2), 3)

        # Ufuk: tepeler ve koy silueti.
        rng = random.Random(31)
        x = 0
        while x < INTERNAL_WIDTH:
            width = rng.randrange(26, 62)
            top = horizon - rng.randrange(6, 26)
            pygame.draw.polygon(strip, palette.color("ink_soft"), [
                (x, horizon), (x + width // 2, top), (x + width, horizon)])
            x += width - 8
        strip.fill(palette.color("ink"),
                   (0, horizon, INTERNAL_WIDTH, BAND_HEIGHT - horizon))
        # Birkac ev - kucuk dikdortgen ve isikli pencere.
        for _ in range(7):
            hx = rng.randrange(10, INTERNAL_WIDTH - 20)
            hw, hh = rng.randrange(9, 16), rng.randrange(7, 13)
            hy = horizon - hh
            strip.fill(palette.color("earth_dark"), (hx, hy, hw, hh))
            strip.fill(palette.color("ember"), (hx + hw // 2, hy + hh // 2, 2, 2))

    # Ses: ruzgar/mahzen/gece-bocegi caprazlamasi kaldirildi (Arda'nin
    # canli oynanis geri bildirimi, 22.08.2026 - sentezlenmis surekli
    # sesler "cizirti gibi, rahatsiz edici" bulundu). Bkz. chapter01.py
    # ayni tarihli not.

    # --- Cizim -------------------------------------------------------------
    def draw_cinematic(self, surface: pygame.Surface, progress: float) -> None:
        height = self._strip.get_height()
        travel = height - INTERNAL_HEIGHT

        if self.direction == "up":
            # Basta en altta (alev), sonda en ustte (koy).
            offset = travel * (1.0 - progress)
        else:
            offset = travel * progress

        # **Tam sayiya yuvarla** - ondalik ofset dokuyu titretir.
        offset_i = int(round(offset))
        speed = abs(offset_i - self._last_offset)
        self._last_offset = offset_i

        surface.blit(self._strip, (0, -offset_i))

        if speed >= MOTION_BLUR_AT:
            self._motion_blur(surface, offset_i, speed)

        self._draw_vignette(surface, progress)

    def _motion_blur(self, surface: pygame.Surface, offset: int,
                     speed: float) -> None:
        """Ayni yuzey birkac kez, birer piksel kaydirilarak, dusuk alfa ile."""
        ghost = self._strip.copy()
        ghost.set_alpha(70)
        step = max(1, int(speed) // 3)
        for i in (1, 2, 3):
            surface.blit(ghost, (0, -offset + i * step))

    def _draw_vignette(self, surface: pygame.Surface, progress: float) -> None:
        """Uclarda karartma: yolculuk karanliktan cikip karanliga girer."""
        # Yalnizca ilk ve son %12'de kararma. Ilk denemede daha genisti ve
        # yolun yarisi karanlikta geciyordu - gecilen katmanlar hic
        # gorunmuyordu.
        edge = min(progress, 1.0 - progress)
        darkness = int(255 * max(0.0, 1.0 - edge / 0.12))
        if darkness <= 0:
            return
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        veil.set_alpha(darkness)
        surface.blit(veil, (0, 0))

    # --- Gecis -------------------------------------------------------------
    def on_finished(self) -> None:
        # Epilog kendi varisini veriyor (sabah koyu).
        if self.next_scene is not None:
            self.scenes.replace(self.next_scene, transition=False,
                                **self.next_kwargs)
            return
        # Yukari cikis koye varir (yeni oyun). Asagi inis kayittaki
        # bolume - numara yolculugun suresini zaten belirliyor, varis
        # da ayni numarayi kullanmali. Aksi halde kart "Bolum 13"
        # derken koy acilir.
        if self.direction == "up":
            from src.scenes.chapter01 import Chapter01Scene
            self.scenes.replace(Chapter01Scene, transition=False,
                                character=self.character)
            return
        from src.scenes.catalog import chapter_scene_class
        scene_cls = chapter_scene_class(self.chapter)
        self.scenes.replace(scene_cls, transition=False,
                            character=self.character, resume_save=True)

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"yolculuk {self.direction}  bolum {self.chapter}"]
