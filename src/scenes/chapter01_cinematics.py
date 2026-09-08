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

    "Bana koyumde arkadasim Berke ne derdi biliyor musun? Emre."

Prologun ikinci repligi (`line.prologue_rey_2`):

    "Bu yuzden mi koydekiler benden korktu? Bana tek bir ad verdiler...
     Lanetli."

Jet'in soyledigi sey tam olarak buna cevap: **takma ad baskalarinin
verdigi, ad seni tanianin kullandigidir.** Koy ona "Jet" diyor, Berke
"Emre" diyordu. Koy Rey'e "Lanetli" diyor.

Bu yuzden sahne bir hediye sahnesi degil bir **isim** sahnesi. Kilic
yalnizca bahane.

## Hem Rey'in hem Ardo'nun arkadasi

Arda'nin kisiti. Sahne iki karakter icin de oynuyor ama ayni degil:

    Rey oynarken    Jet ona kilici veriyor ve adindan soz ediyor
    Ardo oynarken   Jet eski bir tanidik; replik daha kisa, daha yakin

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
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.staging import ActorSpec, Cue, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

# Panel sureleri (kare). Toplam ~9 saniye ama replikler oyuncunun
# onayini bekliyor - sayilar yalnizca alt sinir.
APPROACH_FRAMES = 70
OFFER_FRAMES = 90
NAME_FRAMES = 110
LEAVE_FRAMES = 80


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
        self.ACTORS = (
            ActorSpec("player", character, self.PLAYER_X, self.GROUND_Y,
                      facing=1, state="idle", scale=2),
            ActorSpec("jet", "jet", self.JET_X, self.GROUND_Y,
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
                 Line("ardo", "line.ch01_ardo_jet"))
                if ardo else
                (Line("jet", "line.ch01_jet_offer"),
                 Line("rey", "line.ch01_rey_jet"))
            ),
            # **Sahnenin sebebi.** Ardo'da da soyleniyor ama cevap
            # farkli: Ardo bu hikayeyi zaten biliyor.
            "isim": (
                (Line("jet", "line.ch01_jet_name"),
                 Line("ardo", "line.ch01_ardo_name"))
                if ardo else
                (Line("jet", "line.ch01_jet_name"),
                 Line("rey", "line.ch01_rey_name"),
                 Line("jet", "line.ch01_jet_name2"))
            ),
            "ayrilik": (
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
        """Uzatilan kilic - **yalnizca uzatma panosunda.**

        Ikisinin arasinda, havada. Bir esyanin el degistirdigi an tek
        kareyle anlatiliyor: kimse onu tutmuyor, ikisi de uzaniyor.
        """
        if panel.name != "uzatma":
            return
        x = int((self.JET_X + self.PLAYER_X) * 0.5)
        y = int(self.GROUND_Y) - 26
        surface.fill(palette.color("stone_light"), (x, y, 1, 14))
        surface.fill(palette.color("bone"), (x, y, 1, 3))
        surface.fill(palette.color("gold"), (x - 3, y + 13, 7, 1))

    def on_finished(self) -> None:
        self.scenes.pop()
