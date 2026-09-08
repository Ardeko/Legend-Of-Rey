"""Bolum 18 - "Son". Oyunun son bolumu.

Boss `src/entities/bosses/caller.py`, susturma
`src/systems/silence.py`, ara sahneler
`src/scenes/chapter18_cinematics.py`, kapanis `src/scenes/ending.py`.

`docs/yapi.md` B18: *"Yaratik, Yanki'yi kullanarak Cemo'nun sesiyle
konusur. Rey sesi susturmayi secer - sessizlikte, yardimsiz savasir."*
`docs/ekonomi-uretim.md`: zorluk **9/10**.

## Finalin tek kurali

    Yanki acikken Cagiran olmuyor.

On sekiz bolumdur Yanki oyuncunun araciydi. Burada onun **dusmani
ayakta tuttugu** ortaya cikiyor: can bitiyor, yaratik diz cokuyor,
sonra kalkiyor. Oyuncu bunu bir kez gorunce sorunun ne oldugunu
anliyor; iki kez gorunce ne yapmasi gerektigini.

Susturmak (`[K]` basili tut) gorusu, hasari ve soru sormayi
goturuyor. Belgenin "yardimsiz" kelimesi bir anlatim degil bir
**oynanis**.

## Uc faz ★ (`docs/kalachev.md` 6)

    faz 1   Rey - yoldas - Kalachev      Cagiran dirilir. Dordunuz birlikte
    faz 2   (dovus yok)                  Yaratik Cemo'nun sesiyle konusur.
                                         Kalachev o sese kosar ve OLUR.
                                         Yoldas onu cekmeye giderken kapi
                                         iner - disarida kalir
    faz 3   Rey - yalniz                 Sesi susturur, sessizlikte bitirir

Belgenin en onemli cumlesi: **"Olumu, Rey'i yalniz birakan seyin ta
kendisi oluyor."** Ilk surumde bolum `companion = None` ile basliyordu
ve "yardimsiz" bir varsayimdi - dogru cumleyi soyluyor ama kimseden
bir sey almiyordu. Simdi oyuncunun uc kisisi var ve ucu de aliniyor.
Doruk keyfi olmaktan cikip **kazanilmis** oluyor.

Faz 2 bir ara sahne DEGIL, arenada gecen senaryolu bir an: oyuncunun
kamerasi, oyuncunun arenasi, oyuncunun elinden alinan kontrol. Kesip
baska bir yuzeye gitseydik olay oyuncunun basina degil ekranin
basina gelirdi.

## Bolum sonu, bolum sonu EKRANI degil

Oteki on yedi bolum `ChapterEndScene` acip sayilari gosteriyordu.
Burada acmiyoruz: oyunun son dovusunden cikip bir istatistik paneli
gormek anin butun agirligini alirdi. Sayilar jenerige tasindi
(`ending.py` `credits.path_*`) - orada bir puan degil bir
**hatirlatma** oluyorlar.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.entities.bosses.caller import Caller, Lure
from src.entities.companion import Companion, other_character
from src.entities.kalachev import DEATH_FLAG as KALACHEV_DEATH_FLAG
from src.scenes.play import PlayScene
from src.systems.echo import EchoState
from src.systems.silence import SilenceState
from src.ui.dialogue import Line
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.rooms.chapter18 import (
    ARENA_SEAL_COLUMN, ARENA_SEAL_ROWS, CALLER_TILE, CEMO_TILE, CLEAN_RISES,
    FALSE_CEMO_TILE, LEVEL, ZONE_STARTS,
)
from src.world.tilemap import SOLID, TileMap

# Susturma halkasinin yaricapi (piksel) - oyuncunun ustunde.
RING_RADIUS = 13

# --- Uc faz ------------------------------------------------------------------
PHASE_TOGETHER = 1      # dorduniz birlikte
PHASE_TAKEN = 2         # aliniyor - dovus yok
PHASE_ALONE = 3         # yalniz

# Faz 1'de kim nerede duruyor. Kalachev **onde**: on dort bolumdur
# hep once o giriyor ve faz 2 tam olarak bunun bedeli.
ALLY_OFFSET = 30.0
KALACHEV_OFFSET = 56.0
# Sahne bitirene kadar duruyor. `DEFAULT_STAY` (22 sn) burada sessizce
# kaybolmasi demekti - finalde bir karakterin suresi dolmaz.
KALACHEV_STAY = 60 * 60 * 9

# Yem muhrun **disinda** beliriyor: yaratik onlari arenadan disari
# cagiriyor, yani ayirmayi kendisi seciyor.
#
# 47. tile **olculdu**, secilmedi. Once 51 yazilmisti: yem oyuncudan
# yalnizca 60 piksel otedeydi ve Kalachev "kosuyor" degil "iki adim
# atiyor" gibi gorunuyordu - govdesi oyuncunun dibine dusuyordu.
# 47'de mesafe 125 piksel: gercek bir kosu, ve kamera (yarim genislik
# 240) hala hepsini goruyor.
LURE_TILE = 47

# --- Faz 2'nin kare cetveli --------------------------------------------------
# Her adim bir oncekinin okunmasina yetecek kadar bekliyor. Sikistirmak
# ucuza gelirdi: uc sey (ses, olum, kapi) ust uste binseydi oyuncu
# hicbirini ayri ayri gormezdi.
TAKEN_CALL = 0          # yaratik Cemo'nun sesiyle konusuyor, herkes DURUYOR
TAKEN_GATE = 46         # muhur aciliyor
TAKEN_RUN = 62          # Kalachev kosuyor - oyuncu bagiriyor
TAKEN_DEATH = 200       # yeme varinca oluyor (bu kare yalnizca UST SINIR)
TAKEN_ALLY = 226        # yoldas arkasindan kosuyor
TAKEN_SLAM = 320        # kapi iniyor, yoldas disarida
TAKEN_END = 392         # kontrol geri geliyor, susturma aciliyor


class Chapter18Scene(PlayScene):
    """Son: uc bolge, bir yaratik, bir karar."""

    chapter_number = 18
    chapter_name_key = "chapter.end"
    postfx_grade = "descent"
    ambience_preset = "dust"
    dark_ambient = True    # docs/korku.md 5.1 - yalniz ve karanlikta
    music_context = "boss"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        # **Yoldas yaninda.** B17'yi ikisi birlikte bitirdi; buraya
        # yalniz gelmesi bir sureklilik hatasiydi. Belgenin
        # "yardimsiz"i artik basta verilen degil faz 2'de ALINAN bir
        # sey (`docs/kalachev.md` 6).
        self.companion_key = other_character(self.character)
        self.companion = Companion(self, spawn.x - 26, spawn.feet_y,
                                   self.companion_key)

        # Yanki bolum basinda **acik** - ve bu bilincli. Oyuncunun
        # birakacagi seyi once elinde tutmasi lazim.
        self.echo = EchoState()
        self.silence = SilenceState(unlocked=False)

        self.boss: Caller | None = None
        self.arena_sealed = False
        self.boss_defeated = False

        self.zone = ""
        self.frames = 0
        self.entered_zones: set[str] = set()
        self.fired_triggers: set[str] = set()
        self.finished = False
        self.silence_hinted = False
        self.calls = 0

        # --- Uc faz -----------------------------------------------------
        self.phase = PHASE_TOGETHER
        self.taken_frames = 0       # faz 2'nin kendi sayaci
        self.taken_step = 0         # cetvelde kacinci adim islendi
        self.kalachev = None
        self.gate_open = False

        self._enter_zone(self._zone_at(self.player.body.center_x))

    # --- Bolgeler -----------------------------------------------------------
    def _zone_at(self, x: float) -> str:
        tile = int(x) // TILE_SIZE
        name = ZONE_STARTS[0][0]
        for zone_name, start in ZONE_STARTS:
            if tile >= start:
                name = zone_name
        return name

    def _enter_zone(self, name: str) -> None:
        self.zone = name
        if name in self.entered_zones:
            return
        self.entered_zones.add(name)
        self._narrate_zone(name)

    def _narrate_zone(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "dip":
            self.say_player("line.ch18_rey_bottom", "line.ch18_ardo_bottom")
        elif name == "ses":
            # **Tohumun patladigi yer** (docs/korku.md 11.1).
            #
            # Uc bolumdur parca parca duyulan replik burada butun olarak
            # geliyor - ve Cemo'nun agzindan. Oyuncu B1'de bu cumleyi
            # kolyeyi alirken duymustu:
            #
            #     "Bunu senin icin yaptim... Belki karanlik sana
            #      yaklasirken iki kez dusunur."
            #
            # Karanlik iki kez dusunmedi. Iceri girdi ve simdi o
            # cocugun sesiyle konusuyor.
            #
            # Once yaratik konusuyor, sonra Rey tepki veriyor: sira
            # onemli, cunku oyuncunun once TANIMASI gerekiyor.
            # `say()` kuyrugu DEGISTIRIYOR, eklemiyor: iki ayri cagri
            # birincisini dusururdu. Tek cagrida veriliyor.
            if self.character == "ardo":
                self.say(Line("ardo", "line.ch18_ardo_voice"))
            else:
                # **B1'in anahtarinin ta kendisi.** Ayri bir anahtar
                # acsaydik ikisi zamanla ayrisirdi (Ingilizce cevirisi
                # bir kez ayristi bile) ve tohum taninmaz olurdu.
                # Taninmayan tohum, tohum degildir.
                self.say(Line("cemo", "line.ch01_cemo_gift"),
                         Line("rey", "line.ch18_rey_voice"))

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        zone = self._zone_at(self.player.body.center_x)
        if zone != self.zone:
            self._enter_zone(zone)

        if self.companion is not None:
            # `PlayScene` yoldasi guncellemiyor - her bolum kendi
            # cagiriyor. B16'da bu satir unutulmustu ve yoldas donmus
            # halde havada asili kalmisti.
            self.companion.update()

        if self.phase is PHASE_TAKEN:
            # Faz 2 boyunca susturma, ipucu ve cikis kapali: bir sey
            # aliniyor, oyuncu bir tusa basmiyor.
            self._update_taken()
            return

        self._update_silence()
        self._update_triggers()
        self._update_hints()
        self._check_exit()

    def _update_silence(self) -> None:
        """Basili tut, ses gitsin.

        Tus `ECHO`: on sekiz bolumdur Yanki'yi **acan** tus. Onu
        kapatmak icin de ayni tusun kullanilmasi bilincli - oyuncu
        yeni bir sey ogrenmiyor, hep yaptigi seyi son kez yapiyor.
        """
        holding = self.game.input.held(Action.ECHO)
        hurt = self.player.hurt_frames > 0
        if not self.silence.update(self.echo, holding, hurt):
            return
        self.game.play_sound("echo_tier_down")
        self.game.hitstop(10)
        self.particles.burst(self.player.body.center_x,
                             self.player.body.center_y, 24, path="echo")
        self.show_toast(t("chapter18.silenced"), frames=200)

    def _update_hints(self) -> None:
        if self.silence_hinted or not self.silence.unlocked:
            return
        self.silence_hinted = True
        self.hint_once("hint_silence", "hint.silence", Action.ECHO)

    def _update_triggers(self) -> None:
        for spot in LEVEL.of("trigger"):
            key = f"trigger{spot.tile_x}"
            if key in self.fired_triggers:
                continue
            if abs(self.player.body.center_x - spot.x) > TILE_SIZE:
                continue
            self.fired_triggers.add(key)
            self._fire_trigger(spot.tile_x)

    def _fire_trigger(self, tile_x: int) -> None:
        from src.scenes import chapter18_cinematics as cine
        zone = self._zone_at(tile_x * TILE_SIZE)
        if zone == "dip":
            self.scenes.push(cine.DescentCinematic, character=self.character)
        elif zone == "ses":
            self.scenes.push(cine.VoiceCinematic, character=self.character)
        elif zone == "arena":
            self._spawn_boss()
            self._seal_arena()
            self._summon_kalachev()
            self.scenes.push(cine.NameCinematic, character=self.character)

    # --- Boss ---------------------------------------------------------------
    def _spawn_boss(self) -> None:
        if self.boss is not None:
            return
        x = CALLER_TILE[0] * TILE_SIZE + TILE_SIZE * 0.5
        y = (CALLER_TILE[1] + 1) * TILE_SIZE
        self.boss = Caller(self, x, y)
        self.enemies.append(self.boss)

    def _summon_kalachev(self) -> None:
        """Faz 1: dorduncusu de geliyor (`docs/kalachev.md` 6).

        **Onde duruyor** - oyuncunun ilerisinde, yaratiga daha yakin.
        Konum bir karakter tarifi: on dort bolumdur hep once o giriyor.
        Faz 2 bunun bedelini aliyor.
        """
        body = self.player.body
        self.kalachev = self.summon_kalachev(
            body.center_x + KALACHEV_OFFSET, body.feet[1],
            stay=KALACHEV_STAY)

    def on_kalachev_arrived(self, ally) -> None:
        """Son kez geliyor - ve iki karakter icin farkli bir sey.

        Rey icin bir takviye, Ardo icin eski bir dostun yine
        cagrilmadan gelmesi (`docs/kalachev.md` 3).
        """
        self.juice.shake.add(ImpactWeight.FINISHER, (0.0, 1.0))
        self.say_player("line.ch18_rey_kalachev", "line.ch18_ardo_kalachev")

    def _seal_arena(self) -> None:
        """Arena muhurleniyor - oyuncu ICERI alindiktan sonra.

        Tetikleyici yerel sutun 2, muhur 4. Tetik aninda oyuncu
        henuz sutunu gecmemis oluyor; duvar Cagiran'la araya
        iniyordu. Testler `set_feet` ile duvarin icinden gectigi
        icin bunu yakalamiyordu.
        """
        if self.arena_sealed:
            return
        edge = (ARENA_SEAL_COLUMN + 1) * TILE_SIZE
        body = self.player.body
        if body.x < edge:
            body.set_feet(edge + body.width * 0.5, body.feet[1])
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(ARENA_SEAL_COLUMN, row, SOLID)
        self.arena_sealed = True
        self._pull_companion_in()

    def _pull_companion_in(self) -> None:
        """Yoldas da iceri aliniyor - **olculdu, tahmin edilmedi.**

        Oyuncu arenaya girdiginde yoldas 37 tile geride kaliyordu
        (tasma onu yavas yavas cekiyor, muhur ise aninda iniyor). Yani
        faz 1'de "dorduniz birlikte" ekranda uc kisiydi ve faz 2'nin
        "yoldas geride kaldi" ani, oyuncunun butun arena boyunca
        gormedigi biri icin oynuyordu.

        Oyuncunun kendisi de ayni sekilde iceri itiliyor
        (`_seal_arena`); ayni gerekce, ayni cozum.
        """
        if self.companion is None:
            return
        edge = (ARENA_SEAL_COLUMN + 1) * TILE_SIZE
        if self.companion.body.center_x >= edge:
            return
        # **Muhrun ICINE degil, IC TARAFINA.** Ilk deneme
        # `center_x - ALLY_OFFSET` yaziyordu ve bu 855'e denk
        # geliyordu - muhur sutunu 864..880, yani yoldas hala
        # disarida (ve `free_spot_near` onu duvarin icine, 867'ye
        # itiyordu). Olcum: oyuncu 885, kenar 880.
        body = self.player.body
        inside = max(edge + ALLY_OFFSET, body.center_x - ALLY_OFFSET)
        x, y = self.free_spot_near(inside, body.feet[1],
                                   self.companion.body)
        self.companion.body.set_feet(x, y)
        self.companion.release()

    def on_caller_kneel(self, boss) -> None:
        """Diz cokup **kalkacak**. Bu bir hata degil, bolumun tezi.

        **Ilk diz artik faz 2'yi baslatiyor.** Sira onemli: oyuncu
        once kazaniyor (dordu birlikte yaratigi dize getirdi), sonra
        her sey aliniyor. Ters sirada - once kayip, sonra zafer -
        kayip bir engel olurdu; bu sirada bir BEDEL oluyor.

        Susturma faz 2'nin sonunda aciliyor (`_finish_taken`), cunku
        "yardimsiz savas" teklifi ancak yardim gercekten gittikten
        sonra bir anlam tasiyor.
        """
        self.game.hitstop(12)
        self.game.play_sound("echo_tier_up")
        if self.phase == PHASE_TOGETHER:
            self._begin_taken(boss)
            return
        if not self.silence.unlocked:
            self._unlock_silence()

    def _unlock_silence(self) -> None:
        self.silence.unlocked = True
        from src.scenes import chapter18_cinematics as cine
        self.scenes.push(cine.SilenceCinematic, character=self.character)

    # --- Faz 2: aliniyor - dovus yok ★ ---------------------------------------
    def _begin_taken(self, boss) -> None:
        """Yaratik diz cokmus haldeyken konusuyor.

        Diz coktugu sure **uzatiliyor**: cetvel 340 kare, oysa
        `CALLER_RISE_FRAMES` 96. Uzatilmasaydi yaratik sahnenin
        ortasinda kalkip kontrolu kilitli bir oyuncuyu dovmeye
        baslardi - ve o oyuncu bunu hakli olarak bir hata sayardi.
        """
        self.phase = PHASE_TAKEN
        self.taken_frames = 0
        self.taken_step = 0
        boss.rise_frames = max(boss.rise_frames, TAKEN_END + 30)

    def _update_taken(self) -> None:
        """Faz 2'nin kare cetveli. Oyuncu izliyor, oynamiyor.

        Kontrol her karede yeniden kilitleniyor: tek seferlik uzun
        bir sayac verseydik cetvelin uzunlugunu iki yerde tutmus
        olurduk ve biri degisince oteki sessizce yanlis kalirdi.
        """
        self.player.control_locked = 4
        self.taken_frames += 1
        frame = self.taken_frames

        for step, (at, action) in enumerate(self._taken_script()):
            if step >= self.taken_step and frame >= at:
                self.taken_step = step + 1
                action()

        if self.kalachev is not None and self.kalachev.chase_x is not None:
            self._check_kalachev_reached()

    def _taken_script(self):
        return (
            (TAKEN_CALL, self._taken_voice),
            (TAKEN_GATE, self._taken_open_gate),
            (TAKEN_RUN, self._taken_run),
            (TAKEN_DEATH, self._taken_death),
            (TAKEN_ALLY, self._taken_ally_follows),
            (TAKEN_SLAM, self._taken_slam),
            (TAKEN_END, self._finish_taken),
        )

    def _lure_x(self) -> float:
        return LURE_TILE * TILE_SIZE + TILE_SIZE * 0.5

    def _taken_voice(self) -> None:
        """**Cemo'nun sesi.** Sahnenin en sessiz ani.

        Yem yaratigin kendi `lures` listesine giriyor - ayri bir liste
        tutsaydik susturma aninda temizlenmezdi ve sustuktan sonra
        ekranda bir cocuk kalirdi.
        """
        self.game.hitstop(16)
        self.camera.linger(40)
        self.game.play_sound("echo_answer_partial")
        if self.boss is not None:
            lure = Lure(self._lure_x(), self.player.body.feet[1])
            # **Omru uzatiliyor.** `CALLER_LURE_FRAMES` 150 ve kosu
            # 190 kare suruyor - ekranda kimse yokken kosan bir adam
            # goruluyordu (olculdu, 150. karede yem sonmustu). Bu yem
            # bir hamle degil bir SAHNE; sahnenin sonuna kadar duruyor.
            lure.frames = TAKEN_DEATH + 40
            self.boss.lures.append(lure)
        # **Duruyor ve dinliyor.** B15'in sessiz kipinin ta kendisi -
        # ayni durus, bambaska bir sebep. Iki isi birden goruyor:
        # bir beat veriyor (herkes duruyor, ses geliyor) ve kosunun
        # nereden basladigini sabitliyor. Olculmemis olsaydi Cagiran'a
        # dogru ilerlemeye devam eder, kosuya 60 piksel daha uzaktan
        # baslar ve yeme yetisemezdi.
        if self.kalachev is not None:
            self.kalachev.silent = True
        self.say(Line("cemo", "line.ch18_cemo_call"))

    def _taken_open_gate(self) -> None:
        """Muhur aciliyor. **Yaratik onlari ayirmayi seciyor.**"""
        from src.world.tilemap import EMPTY
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(ARENA_SEAL_COLUMN, row, EMPTY)
        self.gate_open = True
        self.arena_sealed = False
        # `rift_open` - muhrun kapanisi zaten `rift_close`.
        # Yeni bir ad uydurmak "yazilmamis bir ozellik" olurdu.
        self.game.play_sound("rift_open")
        self.juice.shake.add(ImpactWeight.BOSS, (0.0, -1.0))

    def _taken_run(self) -> None:
        """Kosuyor. Oyuncu bagiriyor ve **duyulmuyor.**"""
        if self.kalachev is not None:
            self.kalachev.chase(self._lure_x())
        self.say_player("line.ch18_rey_stop", "line.ch18_ardo_stop")

    def _check_kalachev_reached(self) -> None:
        """Yere varinca oluyor - cetveldeki kareyi beklemeden.

        `TAKEN_DEATH` bir **ust sinir**: bir yere takilirsa sahne yine
        de ilerlesin, yoksa faz 2 hic bitmez ve bolum kilitlenir.
        """
        if abs(self.kalachev.body.center_x - self._lure_x()) > 10.0:
            return
        self._taken_death()
        self.taken_step = max(self.taken_step, 4)

    def _taken_death(self) -> None:
        """**Oluyor.** Ve son sozu bir cevap.

        "Buradayim" - beklemeyi hic ogrenmemis adam
        (`docs/kalachev.md` 4) ilk ve son kez bir cagriya cevap
        veriyor. Yaratik herkese kaybettigini gosteriyor; Rey
        direniyor, o direnmiyor.
        """
        ally = self.kalachev
        if ally is None or ally.dead:
            return
        self.say(Line("kalachev", "line.ch18_kalachev_last"))
        ally.perish()
        self.game.hitstop(20)
        self.camera.linger(50)
        self.juice.explosion(ally.body.center_x, ally.body.center_y,
                             ImpactWeight.BOSS)
        self.decals.splatter(ally.body.center_x, ally.body.bottom, amount=14)
        if self.boss is not None:
            self.boss.lures.clear()

    def _taken_ally_follows(self) -> None:
        """Yoldas onu cekmeye gidiyor - **kimse durduramiyor.**"""
        if self.companion is None:
            return
        self.companion.hold(self._lure_x())
        self.say(Line(self.companion_key, "line.ch18_ally_after"))

    def _taken_slam(self) -> None:
        """Kapi iniyor. Yoldas disarida kaliyor.

        Yoldas sahneden **cikariliyor**, duvarin arkasinda
        birakilmiyor: arenanin disinda duran ama hala guncellenen bir
        Companion kamera oraya donerse gorunurdu ve "geride kaldi"
        yerine "orada bekliyor" gibi okunurdu.
        """
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(ARENA_SEAL_COLUMN, row, SOLID)
        self.gate_open = False
        self.arena_sealed = True
        # Kayboluşu bir **olayla** ortuluyor: toz, sarsinti, inen
        # duvar. Ciplak bir silinme ekranda bir hata gibi okunurdu.
        # Bu kareye kadar 94 kare kosmus oluyor, yani zaten kenarda.
        if self.companion is not None:
            self.particles.burst(self.companion.body.center_x,
                                 self.companion.body.center_y, 14,
                                 path="dust")
        self.companion = None
        self.game.play_sound("rift_close")
        self.juice.shake.add(ImpactWeight.BOSS, (0.0, 1.0))
        self.camera.linger(30)

    def _finish_taken(self) -> None:
        """Kontrol geri geliyor - ve elinde hicbir sey yok.

        Susturma tam **burada** aciliyor. "Yardimsiz savas" teklifi
        ancak yardim gittikten sonra bir teklif; oncesinde bir
        secenekti.
        """
        self.phase = PHASE_ALONE
        self.player.control_locked = 0
        if self.save_data is not None:
            self.save_data.flags[KALACHEV_DEATH_FLAG] = True
        self.say_player("line.ch18_rey_alone", "line.ch18_ardo_alone")
        if not self.silence.unlocked:
            self._unlock_silence()

    def on_caller_rise(self, boss) -> None:
        self.game.play_sound("echo_open")
        self.particles.burst(boss.body.center_x, boss.body.center_y, 18,
                             path="echo")

    def on_caller_call(self, boss) -> None:
        self.calls += 1
        self.camera.linger(20)

    def on_caller_empty_call(self, boss) -> None:
        """Cagiriyor ama kimse duymuyor.

        Sustuktan sonra `call` bos donuyor ve bu **goruluyor**: hamle
        oynuyor, yem cikmiyor. Oyuncunun kazandigi seyin resmi.
        """
        self.particles.burst(boss.body.center_x, boss.body.center_y, 6,
                             path="dust")

    def on_enemy_died(self, enemy) -> None:
        super().on_enemy_died(enemy)
        if enemy is self.boss and not self.boss_defeated:
            self.boss_defeated = True
            self._open_arena()

    def _open_arena(self) -> None:
        from src.world.tilemap import EMPTY
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(ARENA_SEAL_COLUMN, row, EMPTY)
        self.arena_sealed = False

    # --- Cikis --------------------------------------------------------------
    def _check_exit(self) -> None:
        exit_at = LEVEL.first("exit")
        if self.finished or exit_at is None or not self.boss_defeated:
            return
        if self.player.body.center_x < exit_at.x - 8:
            return
        self.finished = True
        self._end_game()

    def _end_game(self) -> None:
        """Bolum sonu ekrani YOK - dogrudan kapanis.

        Oyunun son dovusunden cikip bir istatistik paneli gormek anin
        agirligini alirdi. Dort bayrak jenerige gidiyor ve orada bir
        puan degil bir hatirlatma oluyor.
        """
        data = self.save_data
        flags = data.flags if data is not None else {}
        if data is not None:
            data.chapter = 18
            data.chapter_name = "chapter.end"
            data.playtime_frames += self.frames
            data.flags["finished"] = True
            if self.silence.done:
                data.flags["ch18_silenced"] = True

        from src.scenes.ending import DawnCinematic
        self.scenes.set_root(
            DawnCinematic,
            character=self.character,
            ghost=bool(flags.get("ch15_ghost")),
            lifted=bool(flags.get("ch16_lifted")),
            gesture_key=str(flags.get("ch16_gesture") or "nod"),
            tidy=bool(flags.get("ch17_tidy")),
            clean=self.boss is not None and self.boss.rises <= CLEAN_RISES,
            # `docs/kalachev.md` 7: kapanistaki bakis yalnizca o
            # gercekten olduyse bir anlam tasiyor.
            kalachev=bool(flags.get(KALACHEV_DEATH_FLAG)),
        )

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.frames)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        # Yoldasi **sahne ciziyor** - `PlayScene` yalnizca `allies`
        # listesini ciziyor, `companion`i degil. Kalachev o listede,
        # yoldas degil.
        if self.companion is not None:
            self.companion.draw(surface, offset)
        self._draw_false_cemo(surface, offset)
        self._draw_cemo(surface, offset)
        self._draw_silence_ring(surface, offset)

    def _draw_false_cemo(self, surface: pygame.Surface, offset) -> None:
        """Bolge 2'deki yalan - **Yanki sustuktan sonra yok.**

        Oyuncu geri donerse orada bir sey olmadigini goruyor. Sahne
        yalan soylemiyor: gosterdigi sey aracin gosterdigi seydi.
        """
        if "ses" not in self.entered_zones or self.silence.done:
            return
        if "trigger44" in self.fired_triggers:
            return
        ox, oy = offset
        x = FALSE_CEMO_TILE[0] * TILE_SIZE - ox
        y = (FALSE_CEMO_TILE[1] + 1) * TILE_SIZE - 30 - oy
        wobble = int(math.sin(self.frames * 0.17) * 1.5)
        body = pygame.Surface((14, 30), pygame.SRCALPHA)
        body.fill((*palette.color("echo"), 150))
        body.fill((*palette.color("echo_bright"), 200), (4, 0, 6, 7))
        surface.blit(body, (x + wobble, y))

    def _draw_cemo(self, surface: pygame.Surface, offset) -> None:
        """**Gercek** Cemo - arenaya girildigi andan beri sahnede.

        `docs/kalachev.md` 6: *"Cemo sahnede - kafeste, savasmiyor."*
        ve 8: *"Cemo final dovusunde savasmayacak. Kacirilmis bir
        cocugun kurtarilma hikayesini onu dovusturerek zayiflatmayiz."*

        Ilk surumde yalnizca boss olunce ciziliyordu ve dovus boyunca
        ekranda **yoktu** - yani oyuncu ne icin dovustugunu
        gormuyordu. Simdi orada, parmaklarin arkasinda, hicbir sey
        yapmadan; parmakliklar boss olunce kalkiyor.

        Yem gibi titremiyor, yari saydam degil. Fark ilk bakista
        okunuyor ve bu bilincli: oyuncu on sekiz bolumdur bu ani
        bekliyor, "acaba bu da mi yalan" diye sormamali.
        """
        if "arena" not in self.entered_zones:
            return
        ox, oy = offset
        x = CEMO_TILE[0] * TILE_SIZE - ox
        y = (CEMO_TILE[1] + 1) * TILE_SIZE - 26 - oy
        surface.fill(palette.color("flesh"), (x + 3, y, 8, 8))
        surface.fill(palette.color("violet_dark"), (x + 2, y + 8, 10, 18))
        if not self.boss_defeated:
            self._draw_cage(surface, x, y)

    def _draw_cage(self, surface: pygame.Surface, x: int, y: int) -> None:
        """Parmakliklar. **Sallanmiyor, parlamiyor** - bir bulmaca degil.

        Oyuncunun onunla yapabilecegi hicbir sey yok; bir etkilesim
        gibi gorunmemeli. Duz dikey cizgiler, tek renk.
        """
        tone = palette.color("stone_darkest")
        for step in range(5):
            surface.fill(tone, (x - 2 + step * 4, y - 8, 1, 36))
        surface.fill(tone, (x - 2, y - 8, 17, 1))
        surface.fill(tone, (x - 2, y + 27, 17, 1))

    def _draw_silence_ring(self, surface: pygame.Surface, offset) -> None:
        """Susturma ilerlemesi - oyuncunun ustunde bir halka.

        `CLAUDE.md` 9: durum HUD cubuguyla degil dunyanin icinde
        anlatilir. B16'nin kaldirma halkasiyla ayni dil - ve bilerek:
        oyuncu bu sekli tanıyor, "basili tut" demek icin ikinci bir
        gorsel dil gerekmiyor.
        """
        if self.silence.done or not self.silence.unlocked:
            return
        progress = self.silence.progress
        if progress <= 0.0:
            return
        ox, oy = offset
        cx = int(self.player.body.center_x) - ox
        cy = int(self.player.body.top) - oy - 12
        filled = max(1, int(round(progress * 20)))
        for step in range(20):
            angle = step / 20 * math.tau - math.tau / 4
            x = cx + int(round(math.cos(angle) * RING_RADIUS))
            y = cy + int(round(math.sin(angle) * RING_RADIUS))
            if step < filled:
                surface.fill(palette.color("violet_bright"),
                             (x - 1, y - 1, 2, 2))
            else:
                surface.fill(palette.role("ui_text_dim"), (x, y, 1, 1))
