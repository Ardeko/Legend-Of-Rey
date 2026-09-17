"""Bolum 1'in ara sahnesi: **Jet kilici veriyor.**

Arda, 08.09.2026: *"oyunun basinda kilici veren kisi Jet isimli bir
karakter olsun. Hem Ardo'nun hem Rey'in arkadasi olsun. Kilici verirken
bir sinematik ara sahne girsin."*

## Kilic yerde YATMIYORDU degil - yatiyordu, ve bu bir kayipti

Bolum 1'de kilic yerde duran bir esyaydi. Tasarim notu su sirayi
savunuyordu ve hakliydi: *"Rey silahsiz basliyor, ilk yaratigi gorunce
kacacak yeri yok - kilici alma ani bir rahatlama oluyor. Once ihtiyaci
hissettiriyoruz, sonra veriyoruz."*

O sira **korunuyor**. Degisen tek sey kilici kimin verdigi: yer degil,
bir insan. Yerden alinan bir kilic bir kaynak; uzatilan bir kilic bir
**karar** - birisi Rey'e, koyun "Lanetli" dedigi kiza, silah vermeyi
secti.

## Jet'in repligi bu oyunun tam merkezinde

    "Jet… baskalarinin verdigi isim. Adimiysa, beni gercekten
     taniyanlar soyler."

Prologun ikinci repligi (`line.prologue_rey_2`):

    "Bu yuzden mi koydekiler benden korktu? Bana tek bir ad verdiler...
     Lanetli."

Jet'in soyledigi sey tam olarak buna cevap: **takma ad baskalarinin
verdigi, ad seni tanianin kullandigidir.** Koy ona "Jet" diyor, Berke
"Emre" diyordu. Koy Rey'e "Lanetli" diyor. Rey "hangi birisin" diye
sorunca Jet "belki ikisi de" diyor - cevabi kapatmiyor.

Bu yuzden sahne bir hediye sahnesi degil bir **isim** sahnesi. Kilic
yalnizca bahane.

## Hem Rey'in hem Ardo'nun arkadasi

Arda'nin kisiti. Sahne iki karakter icin de oynuyor ama ayni degil:

    Rey oynarken    Jet ona kilici veriyor; adini ogreniyor
    Ardo oynarken   Jet eski bir tanidik; Berke'yi ikisi de biliyor

`Kalachev` ile ayni desen (`docs/kalachev.md` 3): ayni adam, iki
iliski. Fark su ki Jet **ikisinin de** arkadasi - Kalachev yalnizca
Ardo'nun.

## Oynanisi durduruyor - ve bu istisna

`CLAUDE.md` 9 ara sahnelerin ani kesilmemesini soyluyor; `StoryScene`
zaten oyle calisiyor (basili tutunca 3x hizlaniyor, atlanmiyor).
Prolog disinda oyunun ilk gercek konusmasi bu ve durmasi dogru:
oyuncu bir insanla ilk kez karsi karsiya geliyor.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.art.glow import radial_glow
from src.config import HITSTOP_FINISHER, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.chapter01_render import blit_sword
from src.scenes.staging import ActorSpec, Cue, StagedScene
from src.scenes.story import Panel
from src.systems import horror
from src.ui.dialogue import Line

# Panel sureleri (kare). Toplam ~9 saniye ama replikler oyuncunun
# onayini bekliyor - sayilar yalnizca alt sinir.
APPROACH_FRAMES = 70
OFFER_FRAMES = 90
NAME_FRAMES = 110
LEAVE_FRAMES = 80

# Kilic, 2x aktorlerle ayni olcekte. 1px namlu iki govde arasinda
# bir cizgi okunuyordu; el degisiminin agırligi gorunmuyordu.
SWORD_SCALE = 2
# Ayaktan namlu ucuna. 2x 32px karakterde eller bel-gogus hizasinda;
# kabza orada, namlu yukari. 40 px tabanda kilic bilekte kaliyordu.
SWORD_LIFT = 52
# Jet sola uzatiyor. 18 px kilici govdenin ICINE gomuyordu; 34 px
# sol kenarin onunde, iki elin arasindaki bosluga tasiyor.
SWORD_REACH = 34
HANDOFF_FLASH = 0.22
HANDOFF_SPARKS = 18
HANDOFF_GLOW_IDLE = 10
HANDOFF_GLOW_PASS = 16
HANDOFF_GLOW_IDLE_PEAK = 0.22
HANDOFF_GLOW_PASS_PEAK = 0.50


class SwordCinematic(StagedScene):
    """Jet kilici uzatiyor. Bolum 1, yaratiklar cikmadan **once**."""

    background = "abyss_dark"
    # Konusma sahnesi: oyuncu okuyana kadar bekliyor (`story.py` Panel
    # aciklamasi - prolog da boyle).
    wait_for_input = True

    JET_X = INTERNAL_WIDTH * 0.62
    PLAYER_X = INTERNAL_WIDTH * 0.38
    GROUND_Y = INTERNAL_HEIGHT * 0.70

    PANELS = (
        # 1. Jet yaklasiyor. Kelimesiz - yuz once taniniyor.
        Panel(APPROACH_FRAMES, "yaklasma", cues=(
            Cue("jet", state="run", face=-1),
            Cue("player", state="idle", face=1),
        )),
        # 2. Kilici uzatiyor.
        Panel(OFFER_FRAMES, "uzatma", cues=(
            Cue("jet", state="idle", face=-1, sound="ui_confirm"),
        )),
        # 3. **Isim.** Sahnenin sebebi bu panel - ve tek YAKIN PLAN
        # burada. `closeup` portreyi tam ekran veriyor (3x), sahne
        # kayboluyor: bu replik bir olay degil bir yuz.
        #
        # Yakin plani "uzatma"ya koymak yanlis olurdu - orada onemli
        # olan el degistiren kilic, yani iki govde. Burada onemli olan
        # kimin konustugu.
        Panel(NAME_FRAMES, "isim", closeup="jet"),
        # 4. Gidiyor. Aciklama yok - Jet'in kendi isi var.
        Panel(LEAVE_FRAMES, "ayrilik", cues=(
            Cue("jet", state="run", face=1),
        )),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self._passing = False
        self._handed = False
        self.ACTORS = (
            ActorSpec("player", character, self.PLAYER_X, self.GROUND_Y,
                      facing=1, state="idle", scale=2),
            # Actor adi `jet` (cue/yakin plan); sprite `jet_unarmed`.
            # Bel kilici sahnenin uzattigi prop ile cift namlu olurdu.
            ActorSpec("jet", "jet_unarmed", self.JET_X, self.GROUND_Y,
                      facing=-1, state="run", scale=2),
        )
        # **`_write` super()'den SONRA.** `self.panels` orada
        # kuruluyor; once cagirinca ortada yazilacak bir pano yok
        # (chapter13_cinematics ayni sirayi izliyor).
        super().on_enter(**kwargs)
        self._write()

    def _write(self) -> None:
        """Repliki panolara yaziyor.

        Anahtarlar **duz dize** - f-string ile kurulani
        `tests/test_lang.py` goremiyor ve "olu anahtar" sayiyor. Bu
        tuzaga projede bes kez dusuldu.
        """
        ardo = self.character == "ardo"
        beats: dict[str, tuple[Line, ...]] = {
            "uzatma": (
                (Line("jet", "line.ch01_jet_offer_ardo"),
                 Line("ardo", "line.ch01_ardo_jet"),
                 Line("jet", "line.ch01_jet_changed"),
                 Line("jet", "line.ch01_jet_offer_ardo2"),
                 Line("ardo", "line.ch01_ardo_jet2"),
                 Line("jet", "line.ch01_jet_must"))
                if ardo else
                (Line("jet", "line.ch01_jet_offer"),
                 Line("rey", "line.ch01_rey_jet"))
            ),
            # **Sahnenin sebebi.** Takma ad / ad. Rey ogreniyor;
            # Ardo Berke'yi zaten biliyor.
            "isim": (
                (Line("jet", "line.ch01_jet_name_ardo"),
                 Line("ardo", "line.ch01_ardo_emre"),
                 Line("jet", "line.ch01_jet_remember"),
                 Line("ardo", "line.ch01_ardo_names"),
                 Line("jet", "line.ch01_jet_name2_ardo"),
                 Line("ardo", "line.ch01_ardo_name"),
                 Line("jet", "line.ch01_jet_stay"))
                if ardo else
                (Line("jet", "line.ch01_jet_name"),
                 Line("rey", "line.ch01_rey_name"),
                 Line("jet", "line.ch01_jet_name2"),
                 Line("rey", "line.ch01_rey_which"),
                 Line("jet", "line.ch01_jet_both"))
            ),
            "ayrilik": (
                (Line("jet", "line.ch01_jet_leave_ardo"),
                 Line("ardo", "line.ch01_ardo_leave"),
                 Line("jet", "line.ch01_jet_east"))
                if ardo else
                (Line("jet", "line.ch01_jet_leave"),)
            ),
        }
        # Yon her panoda **acikca** veriliyor: cue'su olmayan bir pano
        # onceki yonu miras aliyor ve yakin plandan cikinca Jet ters
        # donmus kaliyordu.
        faces: dict[str, tuple[Cue, ...]] = {
            "isim": (Cue("jet", state="idle", face=-1),
                     Cue("player", state="idle", face=1)),
        }
        self.panels = tuple(
            Panel(p.frames, p.name, lines=beats[p.name],
                  cues=p.cues or faces.get(p.name, ()),
                  closeup=p.closeup, shake=p.shake, wait_for_input=True)
            if p.name in beats else p
            for p in self.panels
        )

    def draw_stage_background(self, surface: pygame.Surface, panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Koyun gece silueti - Bolum 1'in kendi arka planiyla ayni aile.

        Sahne koyde geciyor ve oraya ait gorunmeli; ayri bir "sinematik
        arka plani" cizmek ani oyundan koparirdi.
        """
        surface.fill(palette.color("abyss_dark"))
        # Yildizlar - `chapter01.draw_background` ile ayni desen.
        for index in range(48):
            x = (index * 97) % INTERNAL_WIDTH
            y = (index * 53) % 96
            tone = "bone" if index % 5 == 0 else "stone_dark"
            surface.fill(palette.color(tone), (x, y, 1, 1))
        # Zemin cizgisi.
        ground = int(self.GROUND_Y)
        surface.fill(palette.color("earth_dark"),
                     (0, ground, INTERNAL_WIDTH, INTERNAL_HEIGHT - ground))
        surface.fill(palette.color("earth"), (0, ground, INTERNAL_WIDTH, 1))

    def draw_stage_foreground(self, surface: pygame.Surface, panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Uzatilan kilic - **yalnizca uzatma panosunda, teslimden once.**

        Jet'in elinde baslar; ilk onayda iki elin arasina gecer (freeze);
        sonra oyuncu armed sprite'a doner ve sahte kilic kaybolur.
        Iki kez cizmek kusanmis karede cift namlu demek.
        """
        pos = self.sword_screen_pos()
        if pos is None:
            return
        x, y = pos
        passing = self._passing and not self._handed
        radius = HANDOFF_GLOW_PASS if passing else HANDOFF_GLOW_IDLE
        peak = HANDOFF_GLOW_PASS_PEAK if passing else HANDOFF_GLOW_IDLE_PEAK
        glow = radial_glow(radius, palette.color("gold"), peak=peak)
        # Hale namlunun ortasinda - uca konursa yere dusmus gibi okunur.
        cy = y + 7 * SWORD_SCALE
        surface.blit(glow, (x - radius, cy - radius),
                     special_flags=pygame.BLEND_RGB_ADD)
        blit_sword(surface, x, y, scale=SWORD_SCALE)

    def sword_screen_pos(self) -> tuple[int, int] | None:
        """Sahte kilicin namlu ucu. Teslimden sonra `None` - sprite tasiyor."""
        panel = self.panel
        if panel is None or panel.name != "uzatma" or self._handed:
            return None
        y = int(self.GROUND_Y) - SWORD_LIFT
        if self._passing:
            jx, _jy = self._jet_hand()
            px, _py = self._player_hand()
            return int(round((jx + px) * 0.5)), y
        jx, _jy = self._jet_hand()
        return jx, y

    def _jet_hand(self) -> tuple[int, int]:
        return (int(round(self.JET_X)) - SWORD_REACH,
                int(self.GROUND_Y) - SWORD_LIFT)

    def _player_hand(self) -> tuple[int, int]:
        return (int(round(self.PLAYER_X)) + SWORD_REACH,
                int(self.GROUND_Y) - SWORD_LIFT)

    def update_cinematic(self) -> None:
        # Freeze biter bitmez kusan: ayni karede diyalog da ailsin,
        # oyuncu donmus karede onay basip sahneyi kacirmasin.
        if self._passing and not self._handed and self.freeze_frames == 0:
            self._finish_handoff()
        super().update_cinematic()
        self._watch_handoff()

    def _watch_handoff(self) -> None:
        """Ilk onay = Jet uzatti, oyuncu aldi.

        `panel_progress` 1.0'a OFFER_FRAMES'te varir; replik hâlâ
        bekliyor. Teslimi oraya baglamak kilici konusmadan once
        savururdu. `dialogue.index` ilk satiri gecince tetiklenir.
        """
        if self._passing or self._handed or self.freeze_frames > 0:
            return
        panel = self.panel
        if panel is None or panel.name != "uzatma":
            return
        if self.dialogue.index < 1:
            return
        self._begin_handoff()

    def _begin_handoff(self) -> None:
        self._passing = True
        self.freeze_frames = max(self.freeze_frames, HITSTOP_FINISHER)
        mx, my = self._midpoint()
        self.burst(mx, my + 8, "spark", HANDOFF_SPARKS,
                   direction=(-1.0, -0.2), speed=(0.8, 2.4))
        self.game.play_sound("intro_spark")
        if horror.flash_allowed(self.game.settings):
            self.flash(HANDOFF_FLASH)

    def _midpoint(self) -> tuple[float, float]:
        jx, jy = self._jet_hand()
        px, py = self._player_hand()
        return (jx + px) * 0.5, (jy + py) * 0.5

    def _finish_handoff(self) -> None:
        if self._handed:
            return
        self._handed = True
        self._passing = False
        player = self.actor("player")
        if player is None:
            return
        armed = f"{self.character}_armed"
        if armed not in CHARACTERS:
            return
        state = player.animator.state or "idle"
        player.animator = Animator(armed)
        player.animator.play(state)

    def on_finished(self) -> None:
        self.scenes.pop()
