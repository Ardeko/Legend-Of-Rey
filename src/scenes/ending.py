"""Oyunun sonu - "Safak" ve jenerik.

`docs/yapi.md` B18: *"Kazanir. Cemo kurtulur. **Gun isigi.** Rey
kolyeyi Cemo'ya geri takar, Ardo arkalarinda. Rey'in kafasi ilk kez
sessiz."*
`docs/gdd.md` 11: *"B18 | Kapanis | **Uclu son panel**."*

## Isik yon degistiriyor

On sekiz bolum boyunca isik hep yukaridan geliyordu ve oyuncu hep
asagi iniyordu. Burada kamera yukari bakiyor ve isik **karsidan**
geliyor - gun isigi bir aydinlatma degil bir **yon**. Bolum
sonlarindaki mor/kemik isiklarin yerini ilk kez `ember_light` aliyor.

## Uclu son panel

Uc figur, uc mesafe:

    Cemo    onde    - kurtarilan, ve artik kolyeyi tasiyan
    Rey     ortada  - kolyeyi TAKAN, ve ilk kez sessiz
    Ardo    arkada  - "arkalarinda" (belgenin kendi kelimesi)

Ardo'nun ne kadar arkada durdugu **B16'da secilen jeste** bagli. Ceza
degil: iki bolum once verilmis bir cevabin hala duruyor olmasi.
`docs/gdd.md` 11'in kurali geciyor - romantik an diyalogla degil
**duruma** anlatiliyor.

## Sessizlik bir SES olarak anlatiliyor

Butun oyun boyunca Yanki'nin bir vinyeti vardi (`EchoState.vignette`)
ve oyuncu onu gormeye alisti. Kapanista vinyet **yok** - ve yokluğu
fark ediliyor. "Rey'in kafasi ilk kez sessiz" cumlesi bir replikle
degil, on sekiz bolumdur ekranin kenarinda duran bir karartmanin
kalkmasiyla soyleniyor.

## Donup bakmak ★ (`docs/kalachev.md` 7)

Kalachev B18 faz 2'de oldu ve **geri gelmiyor.** Ama korku katmaninin
hayalet sistemi (`docs/korku.md` 5.3) yalnizca Yanki acikken goruyor -
ve Rey Yanki'yi susturdu.

    Rey arkasina bakar. Hicbir sey yoktur.
    Ardo arkasina bakar ve **bir an durur.**

Oyuncu Kalachev'i goremiyor. Ardo goruyor mu, o da belli degil - ve
belirsizlik bilincli: bir siluet cizseydik olum geri alinmis olurdu
(belgenin 8. bolumu: *"gorunmesi baska, dirilmesi baska"*). Ekranda
hicbir sey yok; olan tek sey bir duraklama.

Rey Yanki'yi susturarak Cemo'yu kurtardi ve ayni hareketle oluleri
gorme yetenegini de kaybetti. **Sessizligin bedeli bu.** Onu
goremiyor olmasi, gercekten gittiginin kaniti.

## Jenerik artik burada degil (24.09.2026)

Eskiden paneller bitince isim listesi ayni gun isigi uzerinde
akiyordu ve oyun ana menuye donuyordu. Arda: *"cok havada kalan bir
kisim var. koye hep beraber donduklari bir sinematik."* Bu sahne artik
bir **esik**: isik, Jet'in ipinin sarktigi kuyunun agzi. Zincir:

    DawnCinematic -> kuyunun dibi (oynanis) -> safakta yukari
    -> sabah koyu (oynanis) -> ates basi + jenerik -> ana menu

Jenerik cizimi `src/ui/credits.py`'de; ates basi onu kullaniyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.systems.homecoming import Homecoming
from src.ui import balloon
from src.ui.dialogue import Line

GROUND_Y = 200
CENTRE_X = INTERNAL_WIDTH // 2

# Uc figurun yerleri. Cemo onde ve **kucuk** - tek olcek 2 degil 1
# olan o, cunku cocuk.
CEMO_X = CENTRE_X - 34.0
REY_X = CENTRE_X + 6.0

# Ardo'nun mesafesi B16'daki jeste bagli.
#
#   reach     elini uzatmistin  -> yaninda
#   nod       basini sallamistin -> bir adim geride
#   withdraw  geri cekilmistin   -> uc adim geride
#
# Ceza degil: iki bolum once verilmis bir cevabin hala duruyor olmasi.
ALLY_DISTANCE = {"reach": 44.0, "nod": 62.0, "withdraw": 88.0}


class DawnCinematic(StagedScene):
    """Gun isigi. Uclu son panel. Ve sessizlik."""

    background = "void"
    wait_for_input = True

    PANELS = (
        Panel(64, "isik", wait_for_input=False, fade_in=40),
        Panel(52, "kolye", cues=(
            Cue("player", state="idle", face=-1),
            Cue("cemo", state="idle", face=1),
        )),
        Panel(56, "uclu", cues=(
            Cue("player", face=1),
            Cue("ally", face=-1),
        )),
        # **Donup bakma.** Ikisi de karanliga bakiyor; Ardo olan
        # duruyor. Panel uzun (78 kare) cunku olan sey bir hareket
        # degil bir DURAKLAMA - kisa olsaydi bir gecis sanilirdi.
        Panel(78, "bakis", cues=(
            Cue("player", state="idle", face=-1),
            Cue("ally", state="idle", face=-1),
            Cue("cemo", state="idle", face=1),
        )),
        # Son panel yuzden cikarken kararıyor: sonraki sahne (kuyunun
        # dibi) karanliktan aciliyor, kesme yok (`CLAUDE.md` 9).
        #
        # **Jenerik artik burada degil** (24.09.2026). Kapanis bir
        # sonsoz degil bir **esik** oldu: isik tunelin ucundaki kuyunun
        # agzi, ve oradan Jet'in ipiyle koye donuluyor. Jenerik koydeki
        # ates basinin sonunda (`epilogue_cinematics.py`).
        Panel(60, "sessiz", closeup="player", fade_in=14, fade_out=16),
    )

    def on_enter(self, character: str = "rey", ghost: bool = False,
                 lifted: bool = False, gesture_key: str = "nod",
                 tidy: bool = False, clean: bool = False,
                 kalachev: bool = False,
                 **kwargs: object) -> None:
        """Dort bayrak **cagirandan** geliyor.

        Sahnenin `save_data`ya elini uzatmasi kirilgan olurdu (ayni
        ders B10 ve B15'te yazildi); bolum okuyor, sahne yalnizca
        gosteriyor.
        """
        self.character = character
        self.ally = other_character(character)
        self.ghost = ghost              # B15: hic uyandirmadan gecti
        self.lifted = lifted            # B16: yoldasi kaldirdi
        self.gesture_key = gesture_key  # B16: hangi jest
        self.tidy = tidy                # B17: az gecisle cozdu
        self.clean = clean              # B18: az diriltmeyle bitirdi
        self.kalachev = kalachev        # B18: faz 2'de oldu

        ally_x = REY_X + ALLY_DISTANCE.get(gesture_key,
                                           ALLY_DISTANCE["nod"])
        self.ACTORS = (
            # Cemo tek olcek 1 olan - cocuk oldugu boyle soyleniyor.
            ActorSpec("cemo", "cemo", CEMO_X, GROUND_Y, facing=1, scale=2),
            ActorSpec("player", character, REY_X, GROUND_Y, facing=-1,
                      scale=2),
            ActorSpec("ally", self.ally, ally_x, GROUND_Y, facing=-1,
                      scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(26, drift=-0.05, sway=0.3, tone="ember_light")
        # **Vinyet YOK.** On sekiz bolumdur ekranin kenarinda duran
        # karartma kalkti; "Rey'in kafasi ilk kez sessiz" cumlesi
        # boyle soyleniyor.
        self.vignette = 0.0
        self.add_light(CENTRE_X + 150, GROUND_Y - 90, 190,
                       palette.color("ember_light"), peak=0.55)
        # "Raze" - `music.py`nin kendi notu: *"cok nadir
        # duygusal anlar."* On sekiz bolumde ilk kez calıyor.
        self.game.music.hold("emotional", 1400)
        self._write()

    def _write(self) -> None:
        """Anahtarlar **duz dize** - hesaplanmis ad testten kaciyor."""
        ardo = self.character == "ardo"
        light = ("line.ch18_ardo_dawn" if ardo else "line.ch18_rey_dawn")
        three = ("line.ch18_ardo_three" if ardo else "line.ch18_rey_three")
        quiet = ("line.ch18_ardo_quiet" if ardo else "line.ch18_rey_quiet")
        # Bakis repligi **karaktere gore bambaska bir sey.** Rey bir
        # yoklugu bildiriyor ("kimse yok"), Ardo bir duraklamayi
        # yasiyor ("bir saniye... yok bir sey"). Ayni panelde iki
        # farkli hikaye - `docs/kalachev.md` 3'un tam olarak istedigi.
        back = ("line.ch18_ardo_lookback" if ardo
                else "line.ch18_rey_lookback")
        # Kolyenin cevabi (24.09.2026). B1'de Cemo'nun umudu ("belki
        # karanlik iki kere dusunur"), B4'te Yanki'nin alayi, B18'de
        # yaratigin silahi olan cumle son kez **sahibinin** agzindan
        # soruluyor ve cevabini aliyor.
        answer = ("line.ch18_ardo_dawn_answer" if ardo
                  else "line.ch18_rey_dawn_answer")
        beats = {"kolye": (Line(self.character, light),
                           Line("cemo", "line.ch18_cemo_dawn"),
                           Line(self.character, answer)),
                 "uclu": (Line(self.character, three),),
                 "bakis": (Line(self.character, back),),
                 "sessiz": (Line(self.character, quiet),)}
        self.panels = tuple(
            Panel(p.frames, p.name, lines=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
                  wait_for_input=p.wait_for_input)
            if p.name in beats else p
            for p in self.panels
            # Bakis paneli yalnizca **Kalachev gercekten olduyse**
            # var. Bayraksiz bir oturumda (dogrudan sahne acilisi,
            # test) "arkamda kimse yok" cumlesi kimseden bahsetmezdi
            # ve sahne olmamis bir seye uzulmus olurdu.
            if p.name != "bakis" or self.kalachev)

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name == "kolye":
            self.game.play_sound("necklace_warm")
            self.burst(CEMO_X, GROUND_Y - 30, "echo", count=12)
        elif panel.name == "bakis":
            # **Parcacik yok, yeni ses yok.** Her panelde bir sey
            # oluyordu; burada olmuyor ve yoklugu fark ediliyor.
            # Muzik de kisiliyor: karanliga bakan iki kisi, ve hicbir
            # sey.
            self.game.music.duck(0.6)
        elif panel.name == "sessiz":
            # Kisilma **geri aliniyor** - kalici olsaydi kuyunun dibine
            # de tasinirdi ve "Raze" (on sekiz bolumde ilk kez calan
            # parca) sessizce bogulurdu.
            self.game.music.duck(0.0)

    # --- Cizim --------------------------------------------------------------
    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Magara agzi ve **karsidan** gelen gun isigi.

        On sekiz bolum boyunca isik yukaridan geliyordu. Burada
        karsidan geliyor - cikis o yonde ve oyuncu ilk kez asagi degil
        ileri bakiyor.
        """
        surface.fill(palette.color("ink"))
        # Magara agzi: sagda genis bir aciklik, icinden isik doluyor.
        mouth_x = CENTRE_X + 74
        for row in range(0, GROUND_Y):
            ratio = row / max(1, GROUND_Y)
            edge = mouth_x + int(math.sin(ratio * 3.0) * 10)
            surface.fill(palette.color("abyss_dark"), (0, row, edge, 1))
        # Isik katmanlari - disaridan iceri, gittikce soluyor.
        for step in range(6):
            width = INTERNAL_WIDTH - mouth_x + step * 14
            tone = ("ember_light", "ember", "gold", "bone",
                    "stone_light", "stone")[step]
            surface.fill(palette.color(tone),
                         (INTERNAL_WIDTH - width, 0, width, GROUND_Y))
        surface.fill(palette.color("earth_dark"),
                     (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
        surface.fill(palette.color("earth"),
                     (0, GROUND_Y, INTERNAL_WIDTH, 1))

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        ox, oy = offset
        if panel.name == "kolye":
            # Kolye Cemo'ya geri gidiyor - balonla, kelimesiz.
            balloon.draw(surface, "necklace", int(CEMO_X) - ox,
                         int(GROUND_Y) - 40 - oy, frame=self.frame,
                         colour=palette.color("gold"))
        elif panel.name == "uclu" and self.lifted:
            # B16'da onu kaldirdiysan burada bir kalp var. Kaldirmadiysan
            # yok - sahne yalan soylemiyor.
            balloon.draw(surface, "heart", int(REY_X + 22) - ox,
                         int(GROUND_Y) - 44 - oy, frame=self.frame,
                         colour=palette.color("blood_bright"))

    # --- Gecis --------------------------------------------------------------
    def homecoming(self) -> Homecoming:
        """Kapanisin bildigi her sey + kayittaki dusus sayisi.

        Bayraklar bu sahneye cagirandan geliyor (B18 ya da test); dusus
        sayisi yalnizca kayitta. Epilogun butun sahneleri bu nesneyi
        tasiyor - kayit bir kez okunuyor.
        """
        from src.systems.save import read_save
        data, _status = read_save()
        deaths = max(0, int(getattr(data, "deaths", 0) or 0)) if data else 0
        return Homecoming(character=self.character, ghost=self.ghost,
                          lifted=self.lifted, gesture=self.gesture_key,
                          tidy=self.tidy, clean=self.clean,
                          kalachev=self.kalachev, deaths=deaths)

    def on_finished(self) -> None:
        """Isik tunelin ucundaki kuyunun agzi: Jet'in ipi oradan sarkiyor."""
        from src.scenes.epilogue_shaft import EpilogueShaftScene
        self.scenes.set_root(EpilogueShaftScene, character=self.character,
                             homecoming=self.homecoming())
