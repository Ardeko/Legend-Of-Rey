"""Bolum 3'un iki ara sahnesi - "Inis" ve "Mor".

`docs/bolum-03.md` panel panel yazili.

## Yeniden yazildi (30.08.2026)

Iki sahne de birer **daireden** ibaretti: "Inis" kuculen bir hale,
"Mor" buyuyen bir hale. Ekranda karakter yoktu, mekan yoktu, olay
yoktu - yalnizca `radial_glow` cagrilari.

Arda: *"Ara sahnelerin gorsel yazim bicimini yeni sahneleme katmani
ile, hatta daha iyisi ile guncelle."*

Ikisi de artik `StagedScene`: gercek sprite, animasyon durumlari,
parcacik, ortam zerreleri, kenar isigi. Cizim degil **sahne**.

## Ama iki sey aynen korundu

1. **"Inis"te kelime yok.** `docs/bolum-03.md`: *"Kelime yok. Sadece
   isigin kucuklugu ve karanligin buyuklugu."* Sahne sessiz kaldi;
   eklenen sey karakterin kendisi, konusma degil.

2. **"Mor"un karanligi hizlandirilamiyor.** Iki saniyelik tam karanlik
   zamanlamaya bagli: hizlanirsa etkisi olmuyor. Oyuncu o iki saniyede
   *"oyun mu dondu?"* diye dusunmeli - sahnenin butun isi bu. Alev
   belirdikten sonrasi basili tutunca hizlaniyor (25.09.2026).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

GROUND_Y = 184

# --- Ara Sahne 1: "Inis" (bolum acilisi, ~8 saniye) --------------------------
WALK_FRAMES = int(2.2 * FPS)
STAIR_FRAMES = int(2.4 * FPS)
SWALLOW_FRAMES = int(3.4 * FPS)


class DescentCinematic(StagedScene):
    """Mesaleyle inis - isik kuculur, karanlik buyur.

    *"Kelime yok. Sadece isigin kucuklugu ve karanligin buyuklugu."*
    """

    background = "void"
    wait_for_input = False

    PANELS = (
        # A: soldan yururken girer. Mesale elinde, isik genis.
        Panel(WALK_FRAMES, "giris", cues=(
            Cue("player", state="run", face=1,
                move_to=(210.0, GROUND_Y), move_frames=WALK_FRAMES - 12,
                move_ease="out"),
        )),
        # B: basamaklardan **asagi**. Sahne kayiyor, o iniyor.
        Panel(STAIR_FRAMES, "basamak", cues=(
            Cue("player", state="fall", face=1,
                move_to=(268.0, GROUND_Y + 26), move_frames=STAIR_FRAMES,
                move_ease="in"),
        )),
        # C: yutulma. Isik sonuyor, karanlik kapaniyor.
        Panel(SWALLOW_FRAMES, "yutulma", cues=(
            Cue("player", state="idle", face=1),
        )),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.ACTORS = (
            ActorSpec("player", character, 44.0, GROUND_Y, facing=1,
                      state="run", scale=2),
        )
        self.motes = MoteField(26, drift=-0.22, sway=0.9, tone="stone_dark")
        super().on_enter(**kwargs)
        self.vignette = 0.28
        self.game.music.play("explore")
        self.torch_radius = 62.0

    def update_cinematic(self) -> None:
        super().update_cinematic()
        # Mesale isigi **oyuncuyu takip ediyor** ve son panelde soner.
        # Sabit bir isik olsaydi karakter kendi isiginin disina cikardi
        # ve sahne "isigi tasiyor" demezdi.
        actor = self.actor("player")
        if actor is None:
            return
        panel = self.panel
        if panel is not None and panel.name == "yutulma":
            self.torch_radius = max(0.0, self.torch_radius - 0.42)
            self.vignette = min(0.86, self.vignette + 0.004)
        self.clear_lights()
        if self.torch_radius > 2.0:
            self.add_light(int(actor.x), int(actor.y) - 28,
                           int(self.torch_radius),
                           palette.color("ember_light"), peak=0.52)
            self.add_light(int(actor.x), int(actor.y) - 34,
                           int(self.torch_radius * 2.6),
                           palette.color("ember"), peak=0.15)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_crypt(surface, self.frame, stairs=panel.name != "giris")

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Elde tasinan mesale - tek piksellik bir alev kumesi.

        Sprite'ta mesale yok (`animation.CHARACTERS` genel bir
        insansi); tasidigi sey burada, elinin hizasinda ciziliyor.
        Isik zaten oradan geliyor, yani kaynak gorunur oluyor.
        """
        if self.torch_radius <= 2.0:
            return
        actor = self.actor("player")
        if actor is None:
            return
        x = int(actor.x) + 10
        y = int(actor.y) - 26
        flicker = 0.6 + 0.4 * math.sin(self.frame * 0.27)
        surface.fill(palette.color("earth_dark"), (x, y + 3, 2, 7))
        height = max(1, int(5 * flicker))
        surface.fill(palette.color("ember_light"), (x, y - height, 2, height))
        surface.fill(palette.color("gold"), (x, y - height, 2, 1))

    def on_finished(self) -> None:
        from src.scenes.chapter03 import Chapter03Scene
        self.scenes.replace(Chapter03Scene, transition=False,
                            character=self.character)


# --- Ara Sahne 2: "Mor" (~14 saniye) - bolumun kalbi -------------------------
# `docs/bolum-03.md` Ara Sahne 3, alti panel:
#   A mesale soner              B iki saniye hicbir sey
#   C uzakta mor bir isik       D yaklasma: alev bir TAS KAIDEDE duruyor,
#                                 etrafinda donmus mumlar
#   E el uzanir, alev SOGUK,    F Yanki bagirir - ilk kez fisilti degil -
#     nefes bugulanir             ve sonra SUSAR. Ilk kez tamamen.
#
# ## Yeniden yazildi (25.09.2026)
#
# Arda: *"Ardo ile oynasam da Rey ile oynasam da ekranda Rey cikiyor ve
# mor alev geliyor. Ne oldugu hic anlasilmiyor."* Iki ayri hata:
#
#   1. Bolum sahneyi karakter VERMEDEN aciyordu -> sahne hep Rey'di.
#   2. Alev sagdan UCARAK oyuncunun ustune geliyor, ardindan ekran
#      sarsiliyordu: bir saldiri gibi okunuyordu. Belgede alev bir
#      kaidede DURUYOR ve yaklasan oyuncu. Kaide, donmus mumlar, uzanan
#      el ve "soguk" ani hic cizilmemisti; Yanki'nin bagirisi ve
#      ardindaki sessizlik sozsuzdu - oyuncu neyin sustugunu bilemiyordu.
#
# **Ardo Yanki'yi duymuyor** (`docs/gdd.md` 4). Onun sahnesinde bagiris
# yok: alev soguk bir nefes veriyor, Ardo geri cekiliyor ve kendi
# gozlemini soyluyor - zindanin dogal olmadigini fark ettigi an
# (`docs/bolum-03.md`: "Rey ilk kez zindanin dogal olmadigini anlar").
FLICKER_FRAMES = int(1.4 * FPS)
BLACKOUT_FRAMES = int(2.0 * FPS)       # tam karanlik + tam sessizlik
APPEAR_FRAMES = int(1.8 * FPS)
APPROACH_FRAMES = int(3.0 * FPS)
REACH_FRAMES = int(2.0 * FPS)
ROAR_FRAMES = int(1.6 * FPS)
SILENCE_FRAMES = int(1.6 * FPS)

START_X = 150.0
# Kaide gogus hizasinda (aktor 2x): el uzaninca parmaklar alevin dibinde.
PEDESTAL_X = 330
PEDESTAL_TOP = GROUND_Y - 36
FLAME_BASE = PEDESTAL_TOP - 1
STAND_X = 305.0                       # uzanirken durdugu yer
BACK_X = 282.0                        # irkilince geri adim
# Yaklasirken adimlar temkinli: kosu dongusu yavas akiyor (B15'in sessiz
# yuruyusuyle ayni yol - yeni kare yok).
APPROACH_HOLD_SCALE = 1.9
# Donmus mumlar: (x, taban y, boy). Kaidenin dibinde ve ustunde. Fitilleri
# yanmiyor, uclari buz tutmus.
FROZEN_CANDLES = ((319, GROUND_Y, 7), (344, GROUND_Y, 6), (351, GROUND_Y, 4),
                  (324, PEDESTAL_TOP, 4), (337, PEDESTAL_TOP, 5))
FLAME_LIGHT = 48                      # alevin sabit isik yaricapi
# Mahzen duvarinin karartilmasi (RGB cikarma). Sahnenin vinyeti ortayi
# bos birakiyor ve ilk surumde duvarin ortasi bos bir spot isigi gibi
# parliyordu; bu sahnede tek isik mesale, sonra alev olmali.
CRYPT_DARKEN = 30
# Karanlikta, alevin uzaginda duran oyuncu: gorunur ama silik.
DIM_ALPHA = 150


def _purple_panels(character: str) -> tuple[Panel, ...]:
    """Karaktere gore alti panel. Ilk bes ortak, son ikisi ayri.

    Anahtarlar **acikca** yazili (`tests/test_lang.py` f-string ile
    kurulan anahtari goremiyor).
    """
    shared = (
        # A: mesale titrer ve soner - elde, gorunur. Sonerken bir tutam is.
        Panel(FLICKER_FRAMES, "titreme", cues=(
            Cue("player", state="idle", face=1),
        )),
        # B: **hicbir sey.** Iki saniye. Yalniz nefes.
        Panel(BLACKOUT_FRAMES, "karanlik", cues=(
            Cue("player", visible=False),
            Cue("player", delay=BLACKOUT_FRAMES // 2, sound="breath_in"),
        )),
        # C: uzakta mor bir isik. Titremiyor, citirdamiyor - duruyor.
        # Oyuncu karanlikta, silik (siluet kipi duz acik gri bir leke
        # ciziyordu - hayalet gibi okunuyordu).
        Panel(APPEAR_FRAMES, "beliris", cues=(
            Cue("player", visible=True, alpha=DIM_ALPHA, state="idle"),
        )),
        # D: oyuncu ona yurur. Alev YERINDEN KIPIRDAMIYOR; isiga girdikce
        # oyuncu belirginlesiyor.
        Panel(APPROACH_FRAMES, "yaklasma", cues=(
            Cue("player", state="run", move_to=(STAND_X, GROUND_Y),
                move_frames=APPROACH_FRAMES - 24, move_ease="inout"),
            Cue("player", delay=APPROACH_FRAMES // 3, alpha=180),
            Cue("player", delay=APPROACH_FRAMES * 2 // 3, alpha=255),
            Cue("player", delay=APPROACH_FRAMES - 22, state="idle"),
        )),
        # E: el uzanir. Alev soguk - nefes bugulanir.
        Panel(REACH_FRAMES, "el", cues=(
            Cue("player", state="reach"),
            Cue("player", delay=REACH_FRAMES // 2, sound="breath_out"),
        )),
    )
    if character == "ardo":
        return shared + (
            # F: alev soguk bir nefes verir; Ardo geri cekilir.
            Panel(ROAR_FRAMES, "irkilme", shake=1.2, cues=(
                Cue("player", state="brake", sound="breath_sharp"),
                Cue("player", delay=4, move_to=(BACK_X, GROUND_Y),
                    move_frames=22, move_ease="out"),
            )),
            Panel(SILENCE_FRAMES, "sessizlik",
                  line=Line("ardo", "line.ch03_ardo_cold"), cues=(
                      Cue("player", state="idle"),
                  )),
        )
    return shared + (
        # F: Yanki BAGIRIR - ilk kez fisilti degil. Rey geri savrulur.
        Panel(ROAR_FRAMES, "kukreme", shake=3.4,
              line=Line("echo", "line.ch03_echo_shout"), cues=(
                  Cue("player", state="hurt", shake=3.4, flash=0.3,
                      freeze=8, sound="echo_open"),
                  Cue("player", delay=10, move_to=(BACK_X, GROUND_Y),
                      move_frames=24, move_ease="out"),
              )),
        # ...ve susar. Ilk kez tamamen.
        Panel(SILENCE_FRAMES, "sessizlik",
              line=Line("rey", "line.ch03_rey_silence"), cues=(
                  Cue("player", state="idle"),
              )),
    )


class PurpleCinematic(StagedScene):
    """Mesale soner, iki saniye hicbir sey, sonra kaidedeki Mor Alev.

    **Karanlik hizlandirilamaz.** Iki saniyelik karanlik zamanlamaya
    bagli - hizlanirsa etkisi olmuyor; oyuncu o iki saniyede *"oyun mu
    dondu?"* diye dusunmeli. Alev belirdikten sonrasi `CLAUDE.md` 9'un
    genel kuralina donuyor: basili tutunca hizlanir, okunmamis replik
    atlanmaz.
    """

    background = "void"
    wait_for_input = False
    # Hizlandirmanin YASAK oldugu paneller.
    UNSKIPPABLE = ("titreme", "karanlik", "beliris")

    @property
    def skippable(self) -> bool:                 # type: ignore[override]
        panel = self.panel
        if panel is not None and panel.name in self.UNSKIPPABLE:
            return False
        return super().skippable

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = "ardo" if character == "ardo" else "rey"
        self.PANELS = _purple_panels(self.character)
        self.ACTORS = (
            # Golge acik: bu sahnede yerde duruyor. (`shadow=False`
            # yalnizca havadaki aktorler icin - Bolum 2'nin dususu.)
            ActorSpec("player", self.character, START_X, GROUND_Y,
                      facing=1, scale=2),
        )
        self.motes = MoteField(20, drift=-0.15, sway=1.2, tone="violet_dark")
        self.flame_strength = 0.0        # 0 = yok, 1 = tam
        self.flare = 0.0                 # bagiris / soguk nefes parlamasi
        self.torch_out = False
        self.fogged = False
        super().on_enter(**kwargs)
        # Karartma zaten duvarda (`CRYPT_DARKEN`); vinyet hafif. 0.5 iken
        # alevin halesini de siliyordu - kenara yakin tek isik oydu.
        self.vignette = 0.22
        # Sessizlik bir enstruman (`docs/derinlestirme.md` 6.3): iki
        # saniyelik karanlikta muzik de kesiliyor.
        self.game.music.stop(fade_ms=600)

    def on_stage_panel(self, panel: Panel) -> None:
        actor = self.actor("player")
        if actor is not None:
            actor.animator.hold_scale = (APPROACH_HOLD_SCALE
                                         if panel.name == "yaklasma" else 1.0)
        if panel.name == "kukreme":
            self.flare = 1.0
            self.burst(PEDESTAL_X, FLAME_BASE - 8, "violet", 18,
                       speed=(0.8, 2.4), gravity=0.0)
        elif panel.name == "irkilme":
            # Soguk nefes: alevden disari, buz renginde.
            self.flare = 0.7
            self.burst(PEDESTAL_X, FLAME_BASE - 8, "echo", 16,
                       direction=(-1.0, -0.2), speed=(0.6, 2.0),
                       gravity=0.0)

    def update_cinematic(self) -> None:
        super().update_cinematic()
        panel = self.panel
        name = panel.name if panel is not None else ""
        self.clear_lights()
        self.flare = max(0.0, self.flare - 0.03)
        if name == "titreme":
            self._update_torch()
            return
        if name == "karanlik":
            return                      # hicbir isik. Bilerek.
        if name == "beliris":
            self.flame_strength = min(1.0, 0.1 + self.panel_progress)
        else:
            self.flame_strength = 1.0
        if name == "el":
            self._update_breath()
        # Alev sabit: yaricap degismiyor, yalnizca cok yavas "nefes".
        breathe = 1.0 + 0.04 * math.sin(self.frame * 0.035)
        radius = int(FLAME_LIGHT * self.flame_strength * breathe
                     * (1.0 + 0.5 * self.flare))
        colour = palette.color("echo" if name == "irkilme" and self.flare > 0.2
                               else "violet")
        if radius > 2:
            self.add_light(PEDESTAL_X, FLAME_BASE - 8, radius, colour,
                           peak=0.7)
            self.add_light(PEDESTAL_X, FLAME_BASE - 8, int(radius * 2.6),
                           palette.color("violet"), peak=0.28)

    def _update_torch(self) -> None:
        """Elde sonen mesale; sonerken bir tutam is."""
        actor = self.actor("player")
        if actor is None:
            return
        fade = 1.0 - self.panel_progress
        radius = int(46 * fade)
        if radius > 2:
            self.add_light(int(actor.x) + 10, int(actor.y) - 28, radius,
                           palette.color("ember"), peak=0.6 * fade)
            self.add_light(int(actor.x) + 10, int(actor.y) - 28, radius * 2,
                           palette.color("ember_dark"), peak=0.3 * fade)
        elif not self.torch_out:
            self.torch_out = True
            self.burst(actor.x + 11, actor.y - 32, "soot", 8,
                       direction=(0.0, -1.0), speed=(0.2, 0.7),
                       life=(20, 36), gravity=-0.01)

    def _update_breath(self) -> None:
        """Alev SOGUK: el uzanmisken agizdan bir bulut buhar."""
        actor = self.actor("player")
        if actor is None or self.fogged or self.panel_progress < 0.5:
            return
        self.fogged = True
        self.burst(actor.x + actor.facing * 7, actor.y - 54, "dust", 7,
                   direction=(float(actor.facing), -0.4), speed=(0.2, 0.6),
                   life=(24, 40), gravity=-0.01)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        if panel.name == "karanlik":
            surface.fill(palette.color("void"))
            return
        _draw_crypt(surface, self.frame, stairs=False)
        # Duvar karanlikta: yalnizca mesalenin, sonra alevin isigi aciyor.
        dark = pygame.Surface(surface.get_size())
        dark.fill((CRYPT_DARKEN, CRYPT_DARKEN, CRYPT_DARKEN))
        surface.blit(dark, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
        if panel.name != "titreme":
            _draw_pedestal(surface, self.flame_strength,
                           frost=panel.name not in ("beliris",),
                           frame=self.frame)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        if panel.name == "titreme":
            self._draw_torch(surface, 1.0 - progress)
            return
        if panel.name == "karanlik" or self.flame_strength <= 0.05:
            return
        _draw_still_flame(surface, self.flame_strength, self.flare,
                          self.frame)

    def _draw_torch(self, surface: pygame.Surface, fade: float) -> None:
        """Elde tasinan mesale (`DescentCinematic` ile ayni yer)."""
        actor = self.actor("player")
        if actor is None:
            return
        x = int(actor.x) + 10
        y = int(actor.y) - 26
        surface.fill(palette.color("earth_dark"), (x, y + 3, 2, 7))
        flicker = 0.6 + 0.4 * math.sin(self.frame * 0.9)
        height = int(5 * fade * flicker)
        if height > 0:
            surface.fill(palette.color("ember_light"), (x, y - height, 2, height))
            surface.fill(palette.color("gold"), (x, y - height, 2, 1))

    def on_finished(self) -> None:
        # `push` ile acildi (Chapter03Scene altta dondurulmus bekliyor) -
        # `pop` onu kaldigi yerden aynen surduruyor.
        self.scenes.pop()


def _draw_pedestal(surface: pygame.Surface, strength: float, frost: bool,
                   frame: int) -> None:
    """Tas kaide ve etrafindaki donmus mumlar - alevin DURDUGU yer.

    Yalnizca alevin isiginda gorunmeli: parlaklik `strength` ile geliyor.
    Isik sol-ustten degil ALEVDEN - bu sahnede tek kaynak o.
    """
    if strength <= 0.05:
        return
    body = palette.color("stone_dark")
    edge = palette.color("stone" if strength > 0.6 else "stone_dark")
    outline = palette.outline()
    lit = palette.color("violet_bright" if strength > 0.6 else "violet")
    x = PEDESTAL_X
    column_h = GROUND_Y - PEDESTAL_TOP - 4
    # Govde: sutun, ust tabla, taban. Kontur paletin koyusu (CLAUDE.md 6);
    # alevin isigi ust tablaya ve sutunun alev tarafina dusuyor.
    surface.fill(outline, (x - 6, PEDESTAL_TOP + 4, 12, column_h))
    surface.fill(body, (x - 5, PEDESTAL_TOP + 4, 10, column_h))
    surface.fill(edge, (x - 5, PEDESTAL_TOP + 4, 2, column_h))
    surface.fill(outline, (x - 11, PEDESTAL_TOP, 22, 5))
    surface.fill(body, (x - 10, PEDESTAL_TOP + 1, 20, 3))
    surface.fill(lit, (x - 10, PEDESTAL_TOP, 20, 1))           # alevin dustugu yuz
    surface.fill(outline, (x - 12, GROUND_Y - 4, 24, 4))
    surface.fill(body, (x - 11, GROUND_Y - 3, 22, 3))
    surface.fill(edge, (x - 11, GROUND_Y - 3, 22, 1))
    wax = palette.color("bone" if strength > 0.6 else "stone_light")
    for cx, base, height in FROZEN_CANDLES:
        top = base - height
        surface.fill(outline, (cx - 1, top, 5, height))
        surface.fill(wax, (cx, top, 3, height))
        surface.fill(palette.color("stone_light"), (cx + 2, top, 1, height))  # golge yani
        surface.fill(palette.color("ink_soft"), (cx + 1, top - 2, 1, 2))       # sonuk fitil
        if frost:
            # Buz: fitilin ucunda soguk bir pirilti, yavas yanip soner;
            # mumun yaninda donmus bir damla.
            if (frame // 12 + cx) % 5 != 0:
                surface.fill(palette.color("echo_bright"), (cx + 1, top - 3, 1, 1))
            surface.fill(palette.color("echo"), (cx, top + 2, 1, 3))


def _draw_still_flame(surface: pygame.Surface, strength: float, flare: float,
                      frame: int) -> None:
    """Mor Alev'in govdesi - isik degil, **sey**.

    *"Titremiyor, citirdamiyor - sadece duruyor."* Mesale 0.9 hizla
    titrerken bu alev cok yavas nefes aliyor: fark tekinsizligin kendisi.
    """
    x = PEDESTAL_X
    base = FLAME_BASE
    breathe = 1 if math.sin(frame * 0.035) > 0.6 else 0
    height = max(1, int((18 + breathe + 8 * flare) * strength))
    for column in range(-3, 4):
        h = max(1, height - abs(column) * 4)
        tone = ("white_flash" if column == 0 and h > 6
                else "violet_bright" if abs(column) <= 1 else "violet")
        surface.fill(palette.color(tone), (x + column * 2 - 1, base - h, 2, h))
    surface.fill(palette.color("violet_dark"), (x - 7, base - 1, 14, 1))


# --- Ortak arka plan ---------------------------------------------------------
def _draw_crypt(surface: pygame.Surface, frame: int,
                stairs: bool = False) -> None:
    """Mesale Mahzeni - tonozlu tavan, tas duvar, istege bagli basamak.

    Bolum 3'un mekani: insan yapimi ve eski. Bolum 7/8'in dogal kaya
    oyugundan farkli olmali, yoksa butun zindan tek bir odaya benziyor.
    """
    surface.fill(palette.color("ink"))

    # Tonoz: tekrarlanan kemerler. Bir magara degil bir **yapi**.
    arch_colour = palette.color("stone_darkest")
    for start in range(-20, INTERNAL_WIDTH + 40, 60):
        for x in range(start, start + 60, 3):
            t = (x - start) / 60.0
            top = int(26 + math.sin(t * math.pi) * -18) + 18
            surface.fill(arch_colour, (x, 0, 3, max(0, top)))

    # Duvar: yatay tas siralari, kaydirmalı.
    wall = palette.color("stone_darkest")
    edge = palette.color("stone_dark")
    for index, row in enumerate(range(48, GROUND_Y, 11)):
        surface.fill(wall, (0, row, INTERNAL_WIDTH, 9))
        surface.fill(edge, (0, row, INTERNAL_WIDTH, 1))
        offset = 14 if index % 2 else 0
        for x in range(offset, INTERNAL_WIDTH, 28):
            surface.fill(edge, (x, row, 1, 9))

    if stairs:
        # Sagda asagi inen basamaklar - "iniyoruz" bilgisinin sekli.
        for step in range(6):
            x = 250 + step * 18
            y = GROUND_Y + step * 5
            surface.fill(palette.color("stone_dark"),
                         (x, y, 20, INTERNAL_HEIGHT - y))
            surface.fill(palette.color("stone"), (x, y, 20, 1))

    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))


CINEMATIC_DURATION_HINT = int(6.0 * FPS)
