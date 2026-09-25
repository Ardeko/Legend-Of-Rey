"""Oynanabilir sahne temeli - bolumler ve test odasi bundan turer.

Dovus odasi bir donem butun bu baglantiyi kendi icinde tutuyordu. Bolum 1
gelince ayni sey ikinci kez yazilacakti; **game feel'in tek gecis noktasi
olmasi** tam da bunu yasaklıyor (CLAUDE.md 7): hitstop, sarsinti ve parcacik
tek bir `on_hit()` cagrisindan tetiklenmeli. Iki kopya olsaydi biri
guncellenir digeri geride kalirdi ve fark "bir sahnede vurus daha iyi
hissettiriyor" diye ortaya cikardi - bulmasi cok zor bir hata.

Alt sinif yalnizca **sahneyi** kurar: tilemap, oyuncu, dusmanlar, kamera
sinirlari. Dongu, hasar cozumu, kalicilik ve kancalarin tamami burada.
"""
from __future__ import annotations

import math

import pygame

from src.art import bloom, palette, projectiles
from src.art.ambience import Ambience
from src.art.particles import ParticleField
from src.combat.attack_token import AttackTokenManager
from src.combat.hitbox import Hitbox, HitboxManager, Team
from src.config import (
    SENSE_BETRAYAL_DELAY, SENSE_BETRAYAL_RANGE,
    COMBO_THRESHOLD_HIGH, COMBO_THRESHOLD_MID, DEATH_SCREEN_DELAY,
    HARD_LAND_AIR_FRAMES, LAST_CHANCE_PER_LEVEL,
    INTERNAL_WIDTH, NECKLACE_BEAT_MIN_WARMTH, SKILL_BURST_COOLDOWN,
    SKILL_BURST_DAMAGE, SKILL_BURST_KNOCKBACK, SKILL_BURST_POISE,
    SKILL_BURST_SIZE, TILE_SIZE,
)
from src.systems.echo import COMBO_TO_RESTORE
from src.core.camera import Camera
from src.core.input import Action
from src.core.juice import ImpactEvent, ImpactWeight, Juice
from src.core.scene import Scene
from src.entities.character_stats import ARDO, REY
from src.entities.kalachev import WOUND_FLAG as KALACHEV_WOUND_FLAG
from src.entities.player import Player
from src.systems import abilities, consumables, horror, loyalty, skilltree
from src.systems.compass import Compass
from src.systems.echo import Answer, EchoState
from src.systems.tracking import BLOOD, SCORCH, TraceField, TrackingState
from src.systems.save import read_save, write_save
from src.ui import echo_view, tracking_view
from src.ui.chapter_card import ChapterCard
from src.systems.breath import Breath
from src.systems.lies import LieLedger
from src.systems.phantom import Phantom
from src.ui.dialogue import ECHO, Dialogue, Line
from src.ui import text
from src.ui.hud import HUD
from src.ui.interact_prompt import InteractPrompts
from src.ui.i18n import t
from src.world.decals import DecalField

HUD_MARGIN = 6
# Arena muhru oda basindan 1-4 tile icerde iniyor. Olum sonrasi spawn
# bu kadar icerde olunca duvar oyuncunun ARKASINDA kalir, icinde degil.
RESUME_INSET_TILES = 5
# Giris muhrunu oda basindan bu kadar tile icerde ara. Cikis kapisi
# (B2 sutun 180) bu pencerede olmasin.
SEAL_SCAN_TILES = 8
# Yoldas / muttefik olum sonrasi oyuncunun bu kadar yanina konur.
FOLLOWER_RESUME_GAP = 22.0


class _WallTarget:
    """Yanki'nin parlatacagi duvar. `echo_view` `.rect` bekliyor."""

    __slots__ = ("rect",)

    def __init__(self, rect) -> None:
        self.rect = rect


# Yanki Darbesi / Ayi Kukremesi halkasinin genisleme suresi (kare).
BURST_RING_FRAMES = 14


class PlayScene(Scene):
    """Oynanabilir bir alan: tilemap, oyuncu, dusmanlar, game feel."""

    # Adim sesi zemine gore degil **sahneye** gore degisir (SES-LISTESI 2:
    # "Taş zeminde"/"Toprak/koy zemininde") - zindan varsayilan, Bolum 1
    # (koy) kendi degerini ezer.
    footstep_sound = "step_stone"

    # Bolum basi karti - alt sinif ikisini de verirse gosterilir.
    # `0` = kart yok (dovus test odasi, temel dogrulama ekrani gibi
    # bolum olmayan sahneler).
    chapter_number: int = 0
    chapter_name_key: str = ""

    # Odanin havasi (src/art/ambience.py). Bos = atmosfer katmani yok.
    # `particles` olaylar icin (vurus/olum), bu SUREKLI olan sey - oda
    # hicbir sey olmasa bile yasiyor gorunsun.
    ambience_preset: str = ""

    # Rey burada **karanlikta ve yalniz** mi? (docs/korku.md 5.1)
    #
    # Nefes sisteminin ucuncu tetikleyicisi: karanlikta hareketsiz
    # durmak. Bolum 3'un gercek isik sistemi (`self.light`) varken bu
    # bayrak kullanilmiyor - orada karanlik olculuyor, varsayilmiyor.
    #
    # Ardo'nun yaninda oldugu bolumlerde **kasitli olarak False**:
    # `docs/korku.md` 7'nin yerlesim tablosu B6/B7/B16'yi bos birakiyor
    # cunku korkunun ise yaramasi icin nefes alinan yerler gerekiyor.
    # Yaninda biri varken korkmuyorsun.
    dark_ambient: bool = False

    # Yoldasa "burada bekle" denebilir mi? Epilogda hayir: yoldas bir
    # dovus ortagi degil, eve donen biri. Kapaliyken ogretici kart da
    # cikmiyor - kapanista "YOLDASA KOMUT" karti anin ustune biniyordu.
    companion_orders: bool = True

    def setup(self) -> None:
        """Alt sinif sahneyi burada kurar.

        `self.tilemap` ve `self.player` **zorunlu**; `self.enemies` istege
        bagli (varsayilan bos).
        """
        raise NotImplementedError

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        # Yalnizca DEVAM ET bunu True verir. `main.py bolumN` ve bolum
        # gecisleri kayittaki odaya isinlamasin - o bir debug/akis yolu,
        # kayitli ilerleme degil.
        self._resume_save = bool(kwargs.get("resume_save", False))
        self.enemies: list = []
        self.toast = ""
        self.toast_frames = 0
        self.total_hits = 0

        self.particles = ParticleField()
        self.juice = Juice(self.game, spawn_particles=self._emit_particles)
        # Ekran sarsintisi ayarlardan gelir - erisilebilirlik icin kapatilabilir.
        shake = float(self.game.settings.get("screen_shake", 1.0))
        self.juice.configure(shake_enabled=shake > 0.0, shake_scale=shake)
        self.hitboxes = HitboxManager(on_hit=self.on_hit)
        # Ayni anda en fazla 2 dusman saldirabilir.
        self.tokens = AttackTokenManager()
        self.camera = Camera()
        self.save_data, _ = read_save()
        # Sirali toast'lar - ayni karede iki bildirim birbirini ezmesin
        # (kayit gocu + yetenek puani gibi).
        self._toast_queue: list[tuple[str, int]] = []
        self._migrate_save()
        # Son sans (CLAUDE.md 8) - bolum basina. `restart()` tasiyor.
        self.last_chance_left = LAST_CHANCE_PER_LEVEL

        # **Yanki'nin tersine donmesi** (`docs/yapi.md` B14). Bayrak
        # kayittan geliyor, yani B15-B18 hicbir sey yazmadan
        # devraliyor. Gerekce `config.py`de: "her bolum bir satir
        # eklemek zorunda" bu projede uc kez hatanin sekli oldu.
        self.sense_betrayed = bool(
            self.save_data is not None
            and self.save_data.flags.get("sense_betrayed"))
        self._sense_open_frames = 0
        self.hud = HUD(self.game)

        # Yanki yalnizca Rey'de. Ardo'da `None` kalir ve kod her yerde
        # "Yanki var mi?" diye dallanmaz - `has_echo` tek yerde sorulur.
        self.echo = (EchoState(tier=self.echo_tier)
                     if self.character != "ardo" else None)
        self._echo_was_active = False   # echo_open/close kenar tespiti icin
        # Yanki Darbesi / Ayi Kukremesi (yetenek agaci): duyunun ACILDIGI
        # kare ve bekleme suresi. Halka cizimi icin kalan kare.
        self._burst_was_open = False
        self._burst_cooldown = 0
        self._burst_ring = 0
        self._burst_origin = (0.0, 0.0)
        self._burst_key = ""

        # IZ SURME - Ardo'nun karsi mekanigi (`src/systems/tracking.py`,
        # `docs/derinlestirme.md` 2.4). Yanki'nin tam simetrigi: Rey'de
        # `None`, Ardo'da dolu. Ayni tus (`Action.ECHO`) ikisini de aciyor;
        # ayrilan sey duyu.
        #
        # Ardo artik bir EKSIKLIKLE tanimli degil - belgenin en net
        # tespitiydi: *"Su an Ardo'nun oynanisi 'Yanki yok'. Bu zayif
        # tasarim."*
        self.tracking = (TrackingState() if self.character == "ardo"
                         else None)
        # Izler her karakterde toplaniyor - Rey oynarken de dunya iz
        # birakiyor. Ayni kayitla Ardo bolumu bastan oynadiginda tutarli
        # bir gecmis buluyor; ayrica ileride "zindan hatirliyor"
        # (derinlestirme 3.4) ayni alandan beslenebilir.
        self.traces = TraceField()
        self.compass = Compass()
        self._beat_index = -1            # necklace_beat kenar tespiti icin
        self.breakables: list = []
        # Diyalog oynanisi **durdurmuyor**: oyuncu konusma surerken
        # yuruyebilir. Durdursaydik her replik bir kesinti olurdu ve oyuncu
        # okumak yerine gecmeye calisirdi.
        self.dialogue = Dialogue()
        # Dunya icindeki tus gostergeleri (`src/ui/interact_prompt.py`).
        # Sahneler "yakin mi" hesabinin yaninda her kare teklif ediyor.
        self.prompts = InteractPrompts()
        # Odaya girildigi andaki ok/bomba cantasi - olumde geri
        # yukleniyor (`_restore_bag`). Yeniden denemede tasiniyor.
        self.checkpoint_bag: dict[str, int] = {}

        # Bolum basi karti - alt sinif `chapter_number`/`chapter_name_key`
        # verirse gosterilir. Ara sahne DEGIL, bindirme: oynanisi
        # durdurmuyor, oyuncu ilk kareden itibaren yuruyebilir.
        # Mekanik tanitim karti (src/ui/mechanic_card.py). Ayni anda
        # tek kart: iki mekanik ust uste tanitilirsa ikisi de kaybolur.
        self.mechanic_card = None
        self.card = (ChapterCard(self.chapter_number, self.chapter_name_key)
                     if self.chapter_number else None)
        self.ambience = (Ambience(self.ambience_preset)
                         if self.ambience_preset else None)
        # Su seviyesi - yalnizca suyu olan bolumlerde (`setup()` kuruyor).
        # `self.echo` ile ayni desen: yoksa `None` ve kod her yerde
        # "su var mi?" diye dallanmiyor.
        self.water = None

        # Nefes (docs/korku.md 5.1). Katman 2; ayardan kapatilabiliyor.
        # Sahne kurulumundan ONCE: `setup()` icinde bir sey nefesi
        # sifirlamak isteyebilir.
        self.breath = Breath()

        # Yalan defteri (docs/korku.md 4.1). **Katman 1** - kapatilamaz,
        # cunku Yanki'nin yalani bir korku efekti degil ana mekanik.
        # Bolume ozel degil: `ask()` her bolumde yalan soyleyebiliyor.
        self.lies = LieLedger()

        # Hayalet parilti (docs/korku.md 4.4) - Yanki Gorusu'nun yalani.
        # Ayni zamanda yalan defterinin **kaniti**: bolume ozel kod
        # istemeyen tek curutme yolu.
        self.phantom = Phantom()

        # Izleyenler (docs/korku.md 5.2). **`enemies` listesine girmiyor**:
        # oraya girseydi Yanki Gorusu onlari dusman gibi isaretler,
        # saldiri hakki sistemi hak ayirir, "oda temizlendi" sayimlari
        # onlari beklerdi. Izleyen dovusun parcasi degil.
        self.watchers: list = []

        # Hayaletler (docs/korku.md 5.3). Oldugun yerde kalir, YALNIZCA
        # Yanki acikken gorunur. `restart()` bunlari sahne yeniden
        # kurulurken tasiyor - yoksa her olum hafizayi silerdi ve
        # "zindan hatirliyor" fikri hic yasanmazdi.
        self.ghosts: list = []

        # Kalachev (docs/kalachev.md). **`Companion` DEGIL** ve
        # `enemies` listesinde de degil: kendi listesinde duruyor
        # cunku ne yoldas ne dusman - belirip giden bir olay.
        self.allies: list = []

        # Temizlenmis odaya donunce bir sey degismis olmali - bolum
        # basina BIR kez (docs/korku.md 5.5).
        self._room_changed_done = False
        # Bu bolumde hangi sok anlari oynadi (`docs/korku.md` §6).
        # **Kural 2: ayni numara iki kez yok.**
        self._shocks_fired: set[str] = set()
        self._rooms_seen: set[str] = set()

        self.setup()
        # Gezgin Mum Bekcisi (`src/systems/merchant.py`). `setup()`'tan
        # hemen sonra: oyuncu dogdugu yerde, yeniden dogma oncesi.
        self.merchant = None
        if self.merchant_tile is not None:
            from src.systems import merchant
            self.merchant = merchant.place_at_tile(self, *self.merchant_tile)
        elif self.merchant_offset is not None:
            from src.systems import merchant
            self.merchant = merchant.place(self, self.merchant_offset)
        self.shrine = self._make_shrine()

        # Mermiler duvarda olsun: `setup()` tilemap'i kurdu.
        self.hitboxes.tilemap = self.tilemap
        # Tas dili derinlige gore (`tileset.theme_for`): B2'den B18'e ayni
        # gri tugla vardi, asagi inmek gorsel olarak hissedilmiyordu.
        from src.art.tileset import theme_for
        self.tilemap.theme = theme_for(self.chapter_number or 0)

        # Yetenek agacindan acilanlar oyuncuya biniyor. `setup()`'tan
        # SONRA: oyuncu orada yaratiliyor. Duz bonuslar (can, pencere,
        # sarj) burada bir kez uygulaniyor.
        if self.save_data is not None:
            self._restore_abilities()
            self.player.apply_skills(getattr(self.save_data, "skills", ()))
            self._equip_saved_weapon()
        self.refresh_skills()

        self.camera.set_bounds(self.tilemap.bounds)
        self.decals = DecalField(*self.tilemap.bounds.size)
        self.camera.snap_to(self.player.body.center_x, self.player.body.center_y)
        self._stamp_progress()
        self._resume_if_needed()

    def _restore_abilities(self) -> None:
        """Kazanilmis yetenekleri kayittan geri yukler.

        **Bu yoktu ve oyunun yarisini sessizce bozuyordu.** Arda
        (30.08.2026): *"Ardo karakterinin geldigi bolumde yine silahimiz
        yok."* Sebep sanildigi gibi silah degil, yetenekti:

        `SaveData.abilities` alani vardi ama **hicbir yer ona yazmiyor,
        hicbir yer geri yuklemiyordu.** Rey `REY_STARTING = frozenset()`
        ile basliyor, kilici Bolum 1'de `grant()` ile aliyor - ve o
        yalnizca bellekte. Bolum 2'den sonraki her bolumde Rey:

            kilic YOK  -  yumrukla dovusuyor
            kacinma YOK - `Action.DODGE` hicbir sey yapmiyor
            Yanki YOK   - bolumun anlati araci calismiyor

        Ucu de sessiz: hata vermiyor, sadece eksik. `_persist_abilities`
        yazma tarafi.
        """
        for ability in getattr(self.save_data, "abilities", ()) or ():
            # Yanki yetenekleri Rey'e ait; Ardo'nun karsiligi Iz Surme.
            # Kayit tek dosya ve ayni kayitla iki karakter de
            # oynanabiliyor, yani Rey'in `echo_sight`i orada duruyor.
            if self.character == "ardo" and ability in abilities.ECHO_SET:
                continue
            # **Tanitildigi bolumden once geri yuklenmiyor.** Gerekce
            # `abilities.INTRODUCED_IN` tablosunda.
            if not abilities.restorable(ability, self.chapter_number):
                continue
            self.player.grant(ability)
        self._grant_baseline()

    def _grant_baseline(self) -> None:
        """Bu bolume gelmis bir oyuncunun **mutlaka** sahip oldugu seyler.

        Iki isi birden yapiyor:

        1. **Eski kayitlari onariyor.** `abilities` alani bir donem hic
           yazilmiyordu (bkz. `_restore_abilities`), yani 30.08 oncesi
           her kayit bos. Yalnizca kayittan okusaydik o kayitlar
           duzelmezdi - Arda'nin *"Bolum 6'da hala kilicim yoktu"*
           bildirimi tam olarak buydu.

        2. **Yeni bolumlerin unutmasini onluyor.** Bolum 3 ve 4 bunu
           `setup()` icinde elle yapiyordu; 5, 6 ve 7 yapmayi unutmustu
           ve kimse fark etmedi. Her bolume bir satir eklemek, birini
           unutmanin yoluydu - nitekim ucu unutulmus.

        Taban **bolum numarasindan** turuyor: oraya gelebilmis olmak o
        yetenege sahip olmayi gerektiriyor.
        """
        if self.chapter_number <= 1:
            return                      # B1 hikayenin kendisi - eli bos baslar
        self.player.grant(abilities.SWORD)
        if self.chapter_number >= 3:
            self.player.grant(abilities.DODGE)
            # Yanki gormesi Rey'e ait; Ardo'nun karsiligi Iz Surme.
            if self.character != "ardo":
                self.player.grant(abilities.ECHO_SIGHT)

    def _persist_abilities(self) -> None:
        """Oyuncunun yeteneklerini kayda yazar.

        Sirali degil **kumeleyerek**: bir bolumde kazanilan sonrakinde
        kaybolmasin.
        """
        if self.save_data is None:
            return
        known = set(getattr(self.save_data, "abilities", ()) or ())
        self.save_data.abilities = sorted(known | set(self.player.abilities))

    def _update_inventory_hint(self) -> None:
        """Gercek bir **secimi** olan oyuncuya envanteri ogret.

        Kosul "birden fazla silah" degil, "Bolum 2'nin odulu var mi":
        yumruk + kilic de iki silah ama bir secim degil - kilic her
        acidan daha iyi ve kimse yumruga donmez. Ipucu Bolum 1'de
        cikiyordu ve orada tamamen anlamsizdi (test yakaladi).

        Hancer/Balta ise gercek bir tercih (`src/ui/weapon_choice.py`):
        hizli ve zayif mi, yavas ve agir mi.
        """
        if self.save_data is None:
            return
        from src.combat import weapons
        from src.ui.equipment import owned
        choices = owned(self.save_data)
        if weapons.DAGGER not in choices and weapons.AXE not in choices:
            return
        self.hint_once("hint_inventory", "hint.inventory", Action.NEXT_TAB,
                       icon="inventory")

    def _sync_abilities(self) -> None:
        """Yetenek sayisi degistiyse kayda yaz.

        Her bolume "burada da kaydet" satiri eklemek yerine tek yerde:
        bir bolum unutursa sessizce kaybolurdu ve bu tam olarak bir kez
        yasandi - `SaveData.abilities` alani vardi, kimse yazmiyordu.

        Maliyeti kare basina bir tamsayi karsilastirmasi. Kayit diske
        burada yazilmiyor; `pause`/`death`/bolum sonu zaten yaziyor.
        """
        count = len(self.player.abilities)
        if count != getattr(self, "_ability_count", -1):
            self._ability_count = count
            self._persist_abilities()

    def _equip_saved_weapon(self) -> None:
        """Kayittaki silahi kusandirir - Bolum 2'deki secim burada tasiniyor.

        Yalnizca oyuncunun **gercekten sahip oldugu** bir silah kusaniliyor.
        Kilic/yumruk yolu `Player.grant()` ile ilerliyor; burasi onu
        ezmiyor, sadece Bolum 2 odulunu (Hancer/Balta) geri yukluyor.
        Kosul olmasaydi kayitsiz/varsayilan "sword" degeri Bolum 1'de
        yumrukla baslayan Rey'e kilic verirdi ve o bolumun butun anlati
        ani ("kilici buluyor") bozulurdu.

        Kilic artik `_restore_abilities` uzerinden geliyor: yetenek
        kazanildiysa `grant(SWORD)` zaten kusandiriyor. Burasi hala
        yalnizca Hancer/Balta ile ilgileniyor - o ikisi bir yetenek
        degil bir **secim**.
        """
        from src.combat import weapons
        key = getattr(self.save_data, "weapon", "")
        # Kilic/yumruk yetenekten geliyor; geri kalan her silah (Hancer,
        # Balta, 23.09.2026'dan beri Fisilti/Iz Mizragi/Zincir Orak) kayittan.
        if (key in weapons.WEAPONS and key not in (weapons.FISTS, weapons.SWORD)
                and weapons.usable_by(key, self.character)):
            self.player.equip_weapon(key)

    @property
    def enemy_fade(self) -> float:
        """Yasayan dusmanlarin solma orani - `enemy_render` okuyor.

        Iz Surme'nin bedeli. Rey'de `tracking is None`, yani hep 0.0.
        """
        return self.tracking.enemy_fade if self.tracking is not None else 0.0

    # --- Yardimcilar --------------------------------------------------------
    def make_player(self, x: float, y: float) -> Player:
        stats = ARDO if self.character == "ardo" else REY
        return Player(self, x, y, stats)

    @property
    def gold(self) -> int:
        return self.save_data.gold if self.save_data else 0

    @property
    def echo_tier(self) -> int:
        return self.save_data.echo_tier if self.save_data else 2

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        # **Bolume ait bir bindirme aciksa ESC once ONU kapatir.**
        #
        # Arda (30.08.2026): *"Mum Bekcisi ile bir seyler almaya
        # girdigimizde hicbir sey almadan cikamiyoruz."* Sebep buydu:
        # ticaret ekrani ESC'yi dinliyordu ama ESC buraya once ugrayip
        # duraklatma menusunu aciyordu. Menuyu kapatinca ticaret hala
        # acik, ESC yine menuyu aciyor - sonsuz dongu. Yalnizca
        # Backspace (`Action.CANCEL`'in oteki tusu) ise yariyordu ve onu
        # kimse tahmin edemez.
        #
        # Cozum tek yerde: sahne "su an modal bir sey aciyim" diyebiliyor
        # ve duraklatma o tusu calmiyor.
        if self.modal_active:
            return
        if self.game.input.pressed(Action.PAUSE):
            from src.ui.pause import PauseScene
            self.scenes.push(PauseScene, save_data=self.save_data)
            return
        # Envanter **dogrudan** Tab ile. Arda (30.08.2026): *"r veya tab
        # tusuyla envanterimiz falan acilsa da gorsek."*
        #
        # Ekran zaten vardi (`src/ui/equipment.py`) ama yalnizca
        # duraklatma menusunun icinden aciliyordu - yani oyuncunun once
        # onu orada bulmasi gerekiyordu. Silahini merak eden biri ESC'ye
        # basip menu okumak istemiyor.
        #
        # R kullanilmadi: o, olum ekraninda "yeniden dene" ve iki islevli
        # bir tus kazayla yeniden baslatma riski demek.
        if self.game.input.pressed(Action.NEXT_TAB) and not self.player.dead:
            from src.ui.equipment import EquipmentScene
            self.game.play_sound("ui_tick")
            self.scenes.push(EquipmentScene, save_data=self.save_data,
                             player=self.player)
            return
        if event.key == pygame.K_r and self.player.dead:
            self.restart()

    def restart(self) -> None:
        """Olumden sonra sahneyi bastan kurar.

        **Bu bir yumusak kilit duzeltmesi.** Olum ekrani "OLDUN - R ile
        sifirla" yaziyordu ama R'yi YALNIZCA dovus test odasi dinliyordu;
        bolumlerde tusun hicbir karsiligi yoktu, yazi bos bir soz
        veriyordu (24.08.2026'da bulundu).

        Boss arenasinin cikisi anahtarla acilir hale gelince bu gercek bir
        kilitlenmeye donustu: boss'a yenilen oyuncu ne sifirlayabiliyor ne
        de cikabiliyordu. Cikis kapisini "olunce de ac" yapmak daha kolay
        olurdu ama o zaman olmek boss'u atlamanin YOLU olurdu - dogru
        cozum sifirlamanin gercekten calismasi.

        `on_enter` sahneyi bastan kuruyor (dovus odasinin `K_r`'siyle ayni
        yol). Kayit dosyasina dokunulmuyor: altin ve Yanki kademesi
        olumden once neyse o kaliyor.

        ## Kontrol noktasi (29.08.2026)

        Bastan kurmak **dogru** ama tek basina acimasiz: on dakikalik bir
        bolumun sonunda olen oyuncu her seye yeniden basliyordu ve bu,
        Arda'nin yapacagi ara degerlendirmeyi zehirlerdi.

        Cozum bir "kismi geri alma" DEGIL - o yol her zaman bayat durum
        birakir (kapilar, anahtarlar, arena muhru, su seviyesi... her
        bolumun kendi degismezleri var ve biri mutlaka unutulur). Sahne
        yine **tamamen** bastan kuruluyor; sonra oyuncu oldugu ODANIN
        basina isinlaniyor ve o odanin dusmanlari yeniden doguyor.

        Yani: butun degismezler taze, ilerleme korunuyor. Bedeli odayi
        bastan oynamak - retry'in olmasi gereken bedeli tam olarak bu.
        Boss arenasi da dogal calisiyor: arena bir oda, yani boss'a
        yenilen oyuncu arenanin basindan devam ediyor, bolumun basindan
        degil.
        """
        # `entered_rooms` yalnizca oda tabanli bolumlerde var (Bolum 1 ve
        # dovus odasi oda kullanmiyor) - `getattr` ile soruluyor, ozniteligi
        # olmayan sahnelerde sistem sessizce devre disi kaliyor.
        self.death_frames = 0        # bekleyen olum ekrani iptal
        room = self.checkpoint_room
        entered = set(getattr(self, "entered_rooms", ())) if room else set()
        x, y = self.checkpoint_x, self.checkpoint_y
        # Hayaletler olumu **atlatmali** - `on_enter` sahneyi bastan
        # kuruyor ve listeyi bosaltiyor. "Zindan hatirliyor" fikrinin
        # tamami buna bagli: her olum hafizayi silseydi hicbir hayalet
        # ikinci kez gorulmezdi (docs/korku.md 5.3).
        ghosts = list(getattr(self, "ghosts", ()))
        bag = dict(getattr(self, "checkpoint_bag", {}))
        # Son sans BOLUM basina (CLAUDE.md 8) - olup yeniden dogmak onu
        # tazelememeli, yoksa "bolum basina bir" kurali "deneme basina"
        # olurdu.
        last_chance = getattr(self, "last_chance_left", LAST_CHANCE_PER_LEVEL)
        self._pending_resume = (room, x, y, entered)
        self.on_enter(character=self.character)
        self.last_chance_left = last_chance
        self.ghosts = ghosts
        self.checkpoint_bag = bag
        self._restore_bag(bag)

    def _restore_bag(self, bag: dict[str, int]) -> None:
        """Basarisiz denemede atilan ok/bomba geri geliyor.

        Arda, 23.09.2026: *"Firlatilabilir itemler olunce sifirlanacak
        mi? ... Adaletsiz olur."* Olum zaten odayi bastan oynatiyor;
        ustune malzemeyi de almak **cift ceza** - ve oyuncu bombayi
        saklamayi ogrenir, kullanmayi degil.

        ## Neden `max(disk, oda girisi)`

        `on_enter` kaydi **diskten** yeniden okuyor: son yazimdan beri
        atilan her sey zaten geri geliyor. Ilk surum atilanlari bir de
        ustune ekliyordu - cift iade, olup dirilerek ok cogaltmak. Eksik
        kalan tek durum su: oyuncu atti, sonra duraklatti (disk yazildi),
        sonra oldu. Oda girisindeki sayi o durumu kapatiyor. Sonuc hicbir
        zaman oda girisindekinden ya da diskteki gercek bir durumdan
        fazla olamiyor - cogaltma yok.
        """
        data = self.save_data
        if data is None:
            return
        for key, amount in bag.items():
            if consumables.count(data, key) < amount:
                consumables.add(data, key, amount - consumables.count(data, key))

    # --- Kontrol noktasi ----------------------------------------------------
    # Oda tabanli. Alt siniflar bunun icin **hicbir sey yapmiyor**: hepsi
    # zaten `self.room` tutuyor ve odaya girerken degistiriyor, biz de
    # o degisimi izliyoruz. Her bolume ayri bir kanca eklemek besinde
    # birini unutmanin yoluydu.
    #
    # Sadece **ayaktayken** kaydediliyor: havadayken kaydedilseydi oyuncu
    # bosluga dusup oldugunde tekrar bosluga dogar ve sonsuz olum
    # dongusune girerdi.
    checkpoint_room: str = ""
    checkpoint_x: float = 0.0
    checkpoint_y: float = 0.0

    # Gezgin bekcinin oyuncunun dogdugu yere uzakligi (piksel). `None`:
    # bu bolumde dukkan yok. Bkz. `src/systems/merchant.py`.
    merchant_offset: float | None = None
    # Ya da acik bir karo (sutun, satir) - `merchant_offset`in onunde.
    merchant_tile: tuple[int, int] | None = None

    # Silah kaidesi (`src/world/weapon_shrine.py`). "personal": karakterin
    # kendi silahi (Rey Fisilti, Ardo Iz Mizragi); ya da bir silah anahtari.
    # Bos: bu bolumde kaide yok. Konum oyuncunun dogdugu yerden piksel.
    weapon_shrine: str = ""
    weapon_shrine_offset: float = 56.0

    # Dovus muzigi son uyanik dusmandan sonra bu kadar kare daha calar.
    _combat_frames: int = 0
    # Dovus yokken calacak parca. Alt sinif ezerek kendi havasini
    # seciyor.
    #
    # ## Varsayilan neden "combat"
    #
    # Arda, canli oynanis (31.08.2026): *"combat ve kesif icin
    # kullandigimiz sarkilar farkli oldugundan muzik hizli degisiyor.
    # Arka planda sadece combat icin olan muzik kalsin."*
    #
    # Sebep yapisaldi: varsayilan "explore" idi ve bir dusman
    # uyandiginda "combat"a geciliyordu. Zindanda dusmanlar surekli
    # uyanip uyudugu icin parca dakikada birkac kez takas ediyordu -
    # ve iki parca birbirinden cok farkli oldugu icin her takas
    # duyuluyordu.
    #
    # Artik ikisi de "combat": `_update_music` dovuste de dovus
    # disinda da ayni baglami hesapliyor, `MusicDirector.play` ayni
    # baglamda **hicbir sey yapmiyor**, yani takas yok.
    #
    # Kesif parcasi (Fade) atilmadi - **saklandi**. Bulmaca agirlikli
    # bolumlerde (`docs/ekonomi-uretim.md` boyle etiketliyor: B5, B11
    # ve sirasi gelince B17) `music_context = "explore"` veriliyor.
    # Orada dovus seyrek oldugu icin gecis nadir ve **anlamli**:
    # muzigin degismesi bir sey oldugunu soyluyor.
    music_context: str = "combat"

    def _update_music(self) -> None:
        """Sahnenin durumundan muzik baglamini turetir.

        Sahne "hangi dosya" demiyor, "ne oluyor" diyor
        (`src/audio/music.py`). Dosya adlari tek yerde.

        Gecikme (`COMBAT_LINGER_FRAMES`) sart: tek bir dusmanin gozden
        kaybolmasi muzigi kesip acsaydi ses **titrerdi**. Dovus bittikten
        sonra gerilim de hemen dusmuyor - bu hem dogru his hem dogru
        muhendislik.
        """
        from src.audio.music import COMBAT_LINGER_FRAMES, combat_context

        context = combat_context(self)
        if not context:
            if any(getattr(e, "aware", False) and not e.dead
                   for e in self.enemies):
                self._combat_frames = COMBAT_LINGER_FRAMES
            elif self._combat_frames > 0:
                self._combat_frames -= 1
            if self._combat_frames > 0:
                context = "combat"
            else:
                # Sahne kendi sakin baglamini bildiriyor. Varsayilan
                # "combat" (gerekce `music_context`te); Bolum 4 "sad",
                # bulmaca bolumleri "explore".
                context = self.music_context or "combat"

        from src.audio.music import COMBAT_FADE_IN_MS
        fade = COMBAT_FADE_IN_MS if context != "explore" else None
        self.game.music.play(context, fade_ms=fade)

    def sense_open(self) -> bool:
        """Oyuncunun duyusu (Yanki ya da Iz Surme) su an acik mi.

        Iki sistem de ayni `active` sozlesmesini tasiyor, o yuzden
        cagiran taraf "hangi karakter?" diye sormuyor - `EchoState` ve
        `TrackingState` ayni desenle yazildiginin karsiligi burada
        toplaniyor.
        """
        if self.echo is not None:
            return self.echo.active
        if self.tracking is not None:
            return self.tracking.active
        return False

    def _update_dialogue_hint(self) -> None:
        """Ilk bekleyen replikte devam tusunu **bir kez** ogret.

        Arda, canli oynanis (31.08.2026): prolog artik oyuncuyu
        bekliyor (*"kullanici basana kadar yazilar gecmesin"*) ve
        bunun bir yan etkisi var - ilk kez oynayan biri icin ekranda
        duran bir yazi "donmus" gibi de okunabiliyor.

        Kutudaki yanip sonen ucgen bunu soyluyor ama bir simge, bir
        cumle degil. Tus **adiyla** bir kez soylenince belirsizlik
        bitiyor; ikinci kez soylenirse ogut olur.

        `hint_once` tus adini **tablodan** okuyor: tuslar yeniden
        atanabiliyor (`src/systems/bindings.py`), "Enter'a bas"
        yazmak tusu degistiren oyuncuya yalan soylerdi.

        Burada, `PlayScene`de - yani her bolum bedavaya aliyor.
        Bolum 1'e yazsaydik ikinci bolumde konusan ilk karakterde
        oyuncu yine ayni soruyu sorardi.
        """
        if not self.dialogue.active or not self.dialogue.complete:
            return
        self.hint_once("hint_dialogue", "hint.dialogue", Action.CONFIRM)

    def _update_betrayal(self) -> None:
        """Duyuyu acmak seni **ele veriyor** - B14'ten sonra kalici.

        `docs/yapi.md` B14: *"Yanki tersine doner - actiginda dusmanlar
        da seni gorur."*

        On uc bolumdur refleks suydu: emin degilsen Yanki'yi ac. Bu
        bayraktan sonra ayni tus odanin tamamini uyandiriyor. Arac
        degismedi, **sozlesme degisti**.

        Kisa bir gecikme var (`SENSE_BETRAYAL_DELAY`): bir an bakmak
        ile acik tutmak ayni sey olmamali, yoksa yanlislikla dokunan
        oyuncu cezalandirilir ve mekanik bir tuzaga doner.

        Ardo'da ayni kural, baska kurgu: onun twist'i "sesler benim
        degil" degil, **"izler benim icin birakilmis"**.
        """
        if not self.sense_betrayed:
            self._sense_open_frames = 0
            return
        if not self.sense_open():
            self._sense_open_frames = 0
            return
        self._sense_open_frames += 1
        if self._sense_open_frames < SENSE_BETRAYAL_DELAY:
            return
        body = self.player.body
        for enemy in self.enemies:
            if enemy.dead or enemy.aware:
                continue
            dx = enemy.body.center_x - body.center_x
            dy = enemy.body.center_y - body.center_y
            if dx * dx + dy * dy > SENSE_BETRAYAL_RANGE ** 2:
                continue
            enemy.aware = True
            self.on_betrayal_wake(enemy)

    def on_betrayal_wake(self, enemy) -> None:
        """Bir dusman **duyu yuzunden** uyandi. Bolum kendi dilinde
        gosterebilsin diye kanca; varsayilan sessiz."""

    def _update_traces(self) -> None:
        """Dunya iz birakiyor - oyuncu ve dusmanlarin ayak izleri.

        **Her karakterde** calisiyor, yalnizca Ardo'da degil: Rey oynarken
        de gecmis birikiyor. Kayit sahne omruyle sinirli (bolum bitince
        gidiyor), yani "gecmis" burada tek bir oturumun gecmisi.

        Kare butcesi: dusman basina karede bir `dict` bakisi. Izler
        yalnizca Iz Surme acikken ve yalnizca menzildekiler CIZILIYOR
        (`tracking_view.draw_traces`), yani asil maliyet orada ve o da
        Ardo'ya ozel.
        """
        self.traces.update()
        self.traces.record_step(self.player)
        for enemy in self.enemies:
            if not enemy.dead:
                self.traces.record_step(enemy)

    # Olum ekrani bu kadar kare sonra aciliyor: olum vurusunun hitstop'u,
    # sarsintisi ve parcaciklari once bitsin. Aninda acilirsa oyuncu neyle
    # oldugunu goremiyor.
    death_frames: int = 0

    def _update_death(self) -> None:
        if self.death_frames <= 0:
            return
        self.death_frames -= 1
        if self.death_frames == 0:
            self._open_death_screen()

    def _update_checkpoint(self) -> None:
        room = getattr(self, "room", "")
        if not room or self.player.dead:
            return
        if room != self.checkpoint_room:
            if not self.player.body.grounded:
                return          # havada kaydetme - bkz. yukaridaki not
            self.checkpoint_room = room
            self.checkpoint_x = self.player.body.center_x
            self.checkpoint_y = self.player.body.bottom
            # Yeni oda, yeni deneme: canta bu haliyle hatirlaniyor.
            if self.save_data is not None:
                self.checkpoint_bag = dict(getattr(self.save_data,
                                                   "consumables", {}) or {})
            self._persist_checkpoint()

    def _persist_checkpoint(self) -> None:
        """Kontrol noktasini kayit nesnesine yazar - disk duraklat/olumde."""
        data = self.save_data
        if data is None:
            return
        data.checkpoint = self.checkpoint_room
        data.checkpoint_x = self.checkpoint_x
        data.checkpoint_y = self.checkpoint_y

    def _update_room_drift(self) -> None:
        """Temizlenmis bir odaya donunce **bir sey degismis** oluyor.

        `docs/korku.md` 5.5: *"Bolum basina en fazla bir degisiklik ve
        hicbiri oynanisi etkilemez. Fark eden oyuncu urperir, fark
        etmeyen hicbir sey kaybetmez."*

        ## Degisiklik bir TIRMIK IZI

        Belge uc secenek sayiyor (sonmus mesale, yer degistirmis ceset,
        yeni tirmik izi). Tirmik secildi cunku **her bolumde** calisiyor:
        oteki ikisi o odada bir mesale ya da ceset bulunmasini
        gerektiriyor, yani on sekiz bolume ayri ayri icerik yazmak
        demek. Iz ise duvara ait ve duvar her yerde var.

        ## Bir kez, ve **geri donuste**

        Sayac odaya ilk giriste degil **ikinci** giriste isliyor:
        degisiklik ancak "onceden boyle degildi" diyebilen bir oyuncuya
        bir sey ifade eder. Ilk kez giren fark edemez cunku
        karsilastiracagi bir hafizasi yoktur.

        Korku katmani kapaliysa hic olmuyor (`horror.atmosphere`).
        """
        if self._room_changed_done:
            return
        room = getattr(self, "room", "")
        if not room or self.player.dead:
            return
        if room not in self._rooms_seen:
            self._rooms_seen.add(room)
            return
        # Ikinci giris. Ama **odaya yeni girmis** olmali - zaten
        # icindeyken tetiklenirse oyuncu izin belirdigini gorur ve
        # "degismis" degil "olusuyor" okur.
        if not self.player.body.grounded:
            return
        if not horror.atmosphere(self.game.settings):
            return
        self._room_changed_done = True
        body = self.player.body
        self.decals.claw(body.center_x + 24, body.feet[1] - 6)
        self.game.play_sound("room_changed")

    def update(self) -> None:
        self.prompts.begin_frame()
        self._update_music()
        self._update_player()
        self._sync_abilities()
        self._update_inventory_hint()
        self._update_companion_order()
        self._update_death()
        self._update_checkpoint()
        self._update_room_drift()
        self.tokens.update()
        for enemy in self.enemies:
            enemy.update()
        self.enemies = [e for e in self.enemies if not e.remove]

        self.hitboxes.update({
            # Muttefikler oyuncu takiminda: dusman saldirilari onlara
            # da degiyor. Degmeseydi Kalachev dokunulmaz olurdu ve
            # "bu adam boyle giderse olecek" hissi hic kurulmazdi.
            Team.ENEMY: self.enemies,
            Team.PLAYER: [self.player],
        })

        self.particles.update()
        self.juice.update()
        self.camera.shake_offset = self.juice.shake.offset
        self.camera.update(self.player.body.center_x,
                           self.player.body.center_y - 6,
                           facing=self.player.facing,
                           grounded=self.player.body.grounded)

        self._update_traces()
        self._update_betrayal()
        self._update_dialogue_hint()
        self._update_throw()
        if self.merchant is not None:
            self.merchant.update(self)
        if self.shrine is not None:
            self.shrine.update(self)
        if self.echo is not None:
            self.echo.update(self.echo_held())
            self._update_echo_audio()
            if self.game.input.pressed(Action.ECHO_ASK):
                self.on_echo_ask()
        if self.tracking is not None:
            # **Ayni tus.** Rey'de Yanki, Ardo'da Iz Surme. Girdi
            # sozlesmesi ortak, duyu farkli (derinlestirme 2.4).
            self.tracking.update(self.echo_held())
        self._update_sense_burst()
        self.compass.update(self.player)
        self._update_necklace_audio()
        self.dialogue.update(self.game)
        self.breath.update(self.game, self)
        self.lies.update()
        self.phantom.update(self.game, self)
        self._watch_intimacy()
        for watcher in self.watchers:
            watcher.update(self.game, self)
        self.watchers = [w for w in self.watchers if not w.gone]
        for ghost in self.ghosts:
            ghost.update(self.game, self)
        for ally in self.allies:
            ally.update()
        self.allies = [a for a in self.allies if not a.gone]
        if self.card is not None:
            self.card.update()
        if self.mechanic_card is not None:
            self.mechanic_card.update()
            if self.mechanic_card.done:
                self.mechanic_card = None
        if self.ambience is not None:
            self.ambience.update(self.camera.offset)
        if self.water is not None:
            self._update_water()
        # Kirilabilir duvarlar Yanki ile parliyor. Liste kucuk (oda basina
        # birkac tane), her karede uretmek sorun degil.
        self.breakables = [_WallTarget(r)
                           for r in self.tilemap.breakable_rects()]

        self.hud.update(self.player, self.gold, self.echo_tier)
        # Cephane gostergesi HUD'da saklanmiyor, her karede veriliyor:
        # tek kaynak kayit, HUD yalnizca ciziyor.
        chosen = consumables.selected(self.save_data)
        self.hud.set_ammo(chosen, consumables.count(self.save_data, chosen))
        if self.toast_frames > 0:
            self.toast_frames -= 1
        elif self._toast_queue and (self.card is None or self.card.done):
            # Bolum basi karti bitince: iki bilgi ayni anda okunmuyor.
            self.show_toast(*self._toast_queue.pop(0))
        self.update_scene()
        self.prompts.update(self.game.input)
        # Sahne bu karede duvar cikarmis olabilir (arena muhuru).
        # `Body.move` mevcut gomulmeyi cozmez, yalnizca yeni girisi
        # keser - oyuncu bir tile'lik sutunda kalici sikisir.
        self._eject_from_solids()

    def _update_water(self) -> None:
        """Suyun seviyesini surer ve butun aktorlere etkisini uygular.

        Dusmanlar da suyun icinde: yalnizca oyuncuya uygulasaydik su
        "oyuncuya ozel bir kural" olurdu, mekan degil. Yuzme YALNIZCA
        oyuncuda - dusmanlarin yuzme davranisi ayri bir tasarim isi ve
        Bolum 5'te sudaki dusman yok (tasarim geregi: su bir bulmaca,
        dovus alani degil).
        """
        self.water.update()
        swimming = (self.game.input.held(Action.JUMP)
                    and not self.player.dead)
        self.player.water_ratio = self.water.apply(self.player.body,
                                                   swimming)
        for enemy in self.enemies:
            self.water.apply(enemy.body)

    def echo_held(self) -> bool:
        """Yanki bu karede acik mi?

        Normalde tusun kendisi. Bolum, anlatimin gerektirdigi anlarda
        (Bolum 2'nin Yanki odasi: ses **kendiliginden** yukselir) bunu
        ezebilsin diye ayri bir kanca. Ezme `EchoState`'in icine
        yazilsaydi bedel muhasebesi iki yere dagilirdi.
        """
        return self.game.input.held(Action.ECHO)

    def update_scene(self) -> None:
        """Alt sinifa ait kare islemleri (tetikleyiciler, anlatim)."""

    @property
    def depth(self) -> float:
        """Zindanin ne kadar derininde (0..1) - lav ve morarma buna bagli.

        Bolum numarasindan turuyor (`cave_backdrop.depth_for`); her bolume
        elle bir sayi yazmak birinin unutulmasi demekti.
        """
        from src.world.cave_backdrop import depth_for
        return depth_for(self.chapter_number or 0)

    @property
    def rim_light(self) -> tuple[str, float] | None:
        """Derinde karakterlerin golge kenarina ortam isigi (`rimlight`)."""
        from src.art import rimlight
        return rimlight.for_depth(self.depth)

    @property
    def modal_active(self) -> bool:
        """Bolume ait bir bindirme acik mi (ticaret, secim, bulmaca)?

        Aciksa duraklatma ve envanter tuslari **calismiyor** - o an
        ekrandaki sey kendi tuslarini kullaniyor. Alt sinif ezip kendi
        durumunu doner (`Chapter03Scene`: `self.trading`).
        """
        return self.merchant is not None and self.merchant.open

    def _make_shrine(self):
        """Bolumun silah kaidesi - silah zaten alindiysa BOS kaide."""
        if not self.weapon_shrine:
            return None
        from src.combat import weapons
        from src.ui.equipment import owned
        from src.world.weapon_shrine import WeaponShrine
        key = (weapons.PERSONAL.get(self.character, "")
               if self.weapon_shrine == "personal" else self.weapon_shrine)
        if not weapons.usable_by(key, self.character):
            return None
        x = self.player.body.center_x + self.weapon_shrine_offset
        feet = self.tilemap.floor_below(x, self.player.body.feet[1], 18, 30)
        if feet is None:
            return None
        taken = self.save_data is not None and key in owned(self.save_data)
        return WeaponShrine(x, feet, key, taken)

    def take_weapon(self, key: str, x: float, y: float) -> None:
        """Kaideden silah alindi: sahiplik, kusanma, kayit, kart.

        Hemen kusaniliyor: yeni silahi eline alan oyuncu onu **denemek**
        ister; envantere gidip kusanmak zorunda kalmamali. Eski silah
        envanterde duruyor (`equipment.grant`).
        """
        from src.combat import weapons
        from src.systems.save import write_save
        from src.ui import equipment
        from src.world.weapon_shrine import HINT_KEYS
        if self.save_data is not None:
            equipment.grant(self.save_data, key)
            self.save_data.weapon = key
            write_save(self.save_data)
        self.player.equip_weapon(key)
        self.game.play_sound("chest_open")
        self.game.hitstop(4)
        self.particles.burst(x, y, 18,
                             path="echo" if key == weapons.WHISPER else "spark",
                             speed=(0.5, 1.8))
        self.hint_once(f"weapon_taken_{key}", HINT_KEYS[key], Action.ATTACK,
                       icon="weapon")

    def _update_player(self) -> None:
        """Oyuncu. Modal bir pencere aciksa (dukkan) **komut almiyor**.

        B3'te tezgah acikken yukari tusu hem secimi degistiriyor hem de
        oyuncuyu zipliyordu. `controlled` bayragi B17'nin ikili
        kontrolu icin zaten vardi: girdi NOTR ama yer cekimi, animasyon
        ve sayaclar isliyor.
        """
        if not self.modal_active:
            self.player.update()
            return
        was = self.player.controlled
        self.player.controlled = False
        try:
            self.player.update()
        finally:
            self.player.controlled = was

    def after_restart(self, room: str) -> None:
        """Olumden sonra sahne kuruldu ve oyuncu odasina kondu.

        `setup()` her seyi sifirdan kuruyor - dogru ve kasitli - ama
        sahne icinde **kazanilmis** durumlar var: Bolum 6'da yoldas
        `setup()`'ta `None`, ancak "kose"de kurtarilinca dogar. Olum
        arenada gerceklestiginde o an bir daha hic gelmiyordu ve boss
        yalniz doguluyordu (Arda, 30.08.2026: *"oldukten sonra o boss
        fight ta hic dogmuyor"*).

        Alt sinif burada o durumlari geri kuruyor.
        """

    def _stamp_progress(self) -> None:
        """Bu bolume girmek kayittaki 'nerede kaldin'i gunceller.

        Bolum numarasi bir donem yalnizca bolum BITINCE yaziliyordu.
        Ortadaki boss'ta kaydedip menuye donen oyuncu kartta onceki
        bolumu goruyor, DEVAM ET de oraya (veya unutulan Bolum 1'e)
        iniyordu.
        """
        data = self.save_data
        if data is None or not self.chapter_number:
            return
        if data.chapter == self.chapter_number:
            return
        data.chapter = self.chapter_number
        if self.chapter_name_key:
            data.chapter_name = self.chapter_name_key
        data.checkpoint = ""
        data.checkpoint_x = 0.0
        data.checkpoint_y = 0.0
        write_save(data)

    def _resume_if_needed(self) -> None:
        """Olum retry'si ya da DEVAM ET. Dogrudan bolum acmak dokunmaz."""
        pending = getattr(self, "_pending_resume", None)
        self._pending_resume = None
        if pending is not None:
            room, x, y, entered = pending
            self._apply_resume(room, x, y, entered)
            return
        if not getattr(self, "_resume_save", False):
            return
        data = self.save_data
        if data is None or not data.checkpoint:
            return
        if data.chapter != self.chapter_number:
            return
        self._apply_resume(
            data.checkpoint, data.checkpoint_x, data.checkpoint_y,
            {data.checkpoint})

    def _apply_resume(self, room: str, x: float, y: float,
                      entered: set[str]) -> None:
        """Oyuncuyu odaya koy, dusmanlari dogur, muhurun icinde tut."""
        if not room:
            return
        rooms = getattr(self, "entered_rooms", None)
        if isinstance(rooms, set):
            rooms.clear()
            rooms.update(entered)
        else:
            self.entered_rooms = set(entered)
        self.room = room
        self.player.body.set_feet(x, y)
        spawn_room = getattr(self, "_spawn_room", None)
        if spawn_room is not None:
            spawn_room(room)
        self._resuming = True
        try:
            self.after_restart(room)
        finally:
            self._resuming = False
        self._eject_from_solids()
        self._pull_inside_if_sealed()
        self._place_followers_for_resume()
        self.checkpoint_room = room
        self.checkpoint_x = self.player.body.center_x
        self.checkpoint_y = self.player.body.bottom
        self._persist_checkpoint()
        self.camera.snap_to(self.player.body.center_x,
                            self.player.body.center_y)

    def _sealed_entry_center(self, room: str, width: float) -> float | None:
        """Giris muhrunun saginda, govdenin TAMAMEN durabilecegi merkez.

        Oda basina +5 tile varsaymak B13/B14 icin yetiyor (muhur
        start+3). B2 kapi 157 / oda 156, B18 muhur start+4 - yine
        icerde. Asil risk: merkeze bakmak govdenin sol yarısını
        kapi sutununa bindirir; `_eject_from_solids` es mesafede
        saga oncelik verse de `free_spot_near` once sola bakar ve
        yoldasi boslukta, duvarin ARKASINDA birakir.
        """
        span = getattr(self, "_room_span", None)
        if span is None or not room:
            return None
        start, end = span(room)
        body = self.player.body
        top = max(0, int(body.top) // TILE_SIZE)
        bottom = max(top, int(body.bottom - 1) // TILE_SIZE)
        last_block: int | None = None
        limit = min(end, start + SEAL_SCAN_TILES)
        for col in range(start, limit):
            blocked = any(self.tilemap.is_solid(col, row)
                          for row in range(top, bottom + 1))
            if blocked:
                last_block = col
            elif last_block is not None:
                break
        if last_block is None:
            col = start + RESUME_INSET_TILES
        else:
            col = last_block + 1
        return float(col * TILE_SIZE + width * 0.5)

    def _interior_feet(self, x: float, y: float,
                       room: str, width: float = 0.0) -> tuple[float, float]:
        """Oda kenarindaki spawn'u muhurun icine kaydirir."""
        span = getattr(self, "_room_span", None)
        if span is None or not room:
            return x, y
        start, end = span(room)
        body_w = width or float(self.player.body.width)
        left = self._sealed_entry_center(room, body_w)
        if left is None:
            left = float((start + RESUME_INSET_TILES) * TILE_SIZE + body_w * 0.5)
        right = (end - 2) * TILE_SIZE
        if left >= right:
            return x, y
        if x < left:
            x = float(left)
        elif x > right:
            x = float(right)
        return x, y

    def _pull_inside_if_sealed(self) -> None:
        """Muhur indiyse oyuncu duvarin arkasinda kalmasin.

        Kontrol noktasi odaya ILK giriste aliniyor; kapi birkac tile
        icerde kapaninca o nokta muhurun disinda kaliyor. Oyuncu
        bosluktadir (gomulu degil) bu yuzden `_eject_from_solids`
        yardim etmez.
        """
        if not getattr(self, "arena_sealed", False):
            return
        room = getattr(self, "room", "")
        x, y = self._interior_feet(self.player.body.center_x,
                                   self.player.body.bottom, room,
                                   float(self.player.body.width))
        self.player.body.set_feet(x, y)
        self._eject_from_solids()
        # Eject en kisa yolu secti ve o yol disariysa (nadir) tekrar it.
        x, y = self._interior_feet(self.player.body.center_x,
                                   self.player.body.bottom, room,
                                   float(self.player.body.width))
        if abs(x - self.player.body.center_x) > 0.5:
            self.player.body.set_feet(x, y)
            self._eject_from_solids()

    def _resume_followers(self) -> list:
        """Olum sonrasi yaninda olmasi gerekenler - yoldas ve Kalachev."""
        found: list = []
        companion = getattr(self, "companion", None)
        if companion is not None:
            found.append(companion)
        for ally in getattr(self, "allies", ()):
            if ally in found:
                continue
            if getattr(ally, "gone", False) or getattr(ally, "dead", False):
                continue
            found.append(ally)
        return found

    def _place_followers_for_resume(self) -> None:
        """Yoldas ve muttefikler oyuncunun yaninda, muhurun icinde.

        Boss kapisi oyuncunun arkasinda kapaninca yoldas oda girisinde
        (duvarin ARKASINDA) kalabiliyordu. Oyuncu iceri cekildikten
        sonra onlar da ayni tarafa alinir.
        """
        room = getattr(self, "room", "")
        px = self.player.body.center_x
        py = self.player.body.feet[1]
        sealed = bool(getattr(self, "arena_sealed", False))
        for index, follower in enumerate(self._resume_followers()):
            body = getattr(follower, "body", None)
            if body is None:
                continue
            # Saga once: sola bakmak muhurun arkasindaki boslugu "serbest
            # yer" sanar ve yoldasi duvarin DISINA koyar.
            side = 1 if index % 2 == 0 else -1
            desired = px + side * FOLLOWER_RESUME_GAP * ((index // 2) + 1)
            x_want, y_want = desired, py
            if sealed:
                x_want, y_want = self._interior_feet(
                    desired, py, room, float(body.width))
            x, y = self.free_spot_near(x_want, y_want, body)
            if sealed:
                x, y = self._interior_feet(x, y, room, float(body.width))
            body.set_feet(x, y)
            releaser = getattr(follower, "release", None)
            if callable(releaser):
                releaser()

    def present_kalachev(self, beat: str) -> None:
        """Yuzu ve adi - 32 piksellik figuru taninir kilar.

        Olum retry'sinde tekrar oynamaz: tanisma bir kez.
        """
        if getattr(self, "_resuming", False):
            return
        from src.scenes.kalachev_cinematics import KalachevCinematic
        self.scenes.push(KalachevCinematic, character=self.character,
                         beat=beat)

    # --- Ipuclari -----------------------------------------------------------
    def hint_once(self, flag: str, message_key: str, action: Action,
                  frames: int = 210, icon: str = "") -> None:
        """Bir tusu **bir kez** ogretir ve kayda isaretler.

        Arda (30.08.2026): *"Tab ile envanter acacagimi ve U ile komut
        verecegimin hint'i yok."* Iki yeni tus eklendi ve ikisi de
        oyuncuya hic soylenmedi - bir tus varsa ama kimse bilmiyorsa
        yok demektir.

        **Tus adi tablodan okunuyor, sabit yazilmiyor.** Tuslar artik
        yeniden atanabilir (`src/systems/bindings.py`); "Tab" diye
        yazsaydik tusu degistiren oyuncuya yalan soylerdik.

        Bir kez: `SaveData.flags`'e yaziliyor. Her odada tekrarlanan bir
        ipucu ogut olur.
        """
        data = self.save_data
        if data is None or data.flags.get(flag):
            return
        data.flags[flag] = True
        from src.systems import bindings as binds
        table = binds.read(self.game.settings)
        label = binds.labels_for(table, action)

        if icon:
            # **Yeni bir MEKANIK ise kart aciliyor** (docs: Arda,
            # 08.09.2026 - "yeni mekanik acilan her bolum icin guzel
            # grafiklerle ve belirgin UX UI ile ipuclari").
            #
            # Bildirim, "14 COMBO" ile ayni yerde ve ayni bicimde
            # cikiyordu: oyunun "bu senin yeni yetenegin" demesiyle bir
            # combo sayaci gorsel olarak ayni seydi. Kart farki BICIMLE
            # kuruyor - ortada, cerceveli, ikonlu, tus kapakli.
            #
            # Ikonu olmayan ipuclari (bir kolu cek, freni tut) bildirim
            # olarak kaliyor: onlar yeni bir mekanik degil, o odaya ait
            # bir talimat.
            from src.ui.mechanic_card import MechanicCard, title_for
            self.mechanic_card = MechanicCard(
                title_key=title_for(message_key), body_key=message_key,
                icon=icon, key_label=label)
            self.game.play_sound("ui_confirm", bus="volume_sfx")
            return

        self.show_toast(t(message_key, key=label), frames=frames)

    def offer_resonate(self, targets) -> None:
        """En yakin calinabilir rezonans hedefinin ustunde `RESONATE` tusu.

        B8 kristali, B9 canlari, B15 ciniklari ayni sozlesmeyi tasiyor
        (`rect`). Arda'nin B8 geri bildirimi (19.09.2026) "ates basindaki
        ipucu belirsiz" idi: kart bir kez cikiyordu, kristalin kendisi
        hicbir sey soylemiyordu.
        """
        from src.systems.resonance import PULSE_RANGE
        px, py = self.player.body.center_x, self.player.body.center_y
        best, best_distance = None, PULSE_RANGE * 0.9
        for target in targets:
            if getattr(target, "triggered", False):
                continue
            if not getattr(target, "ready", True):
                continue
            rect = target.rect
            distance = math.hypot(rect.centerx - px, rect.centery - py)
            if distance < best_distance:
                best, best_distance = target, distance
        if best is not None:
            self.prompts.offer("resonate", best.rect.centerx, best.rect.top,
                               action=Action.RESONATE,
                               verb_key="prompt.resonate")

    # --- Yoldas komutu ------------------------------------------------------
    def _update_companion_order(self) -> None:
        """"Burada bekle / pesimden gel" - tek tus, iki durum.

        Yoldasi olan her bolumde calisiyor: `self.companion` varsa
        yeter, bolume ozel kod gerekmiyor.
        """
        companion = getattr(self, "companion", None)
        if companion is None or self.player.dead or not self.companion_orders:
            return
        # Yoldas ilk kez yanindayken komutu ogret.
        self.hint_once("hint_companion", "hint.companion_wait",
                       Action.COMPANION_WAIT, icon="companion")
        if not self.game.input.pressed(Action.COMPANION_WAIT):
            return
        if companion.hold_x is None:
            companion.hold(companion.body.center_x)
            self.show_toast(t("companion.waiting"), frames=110)
        else:
            companion.release()
            self.show_toast(t("companion.following"), frames=110)
        self.game.play_sound("ui_tick")

    @property
    def has_echo(self) -> bool:
        """Yanki bu oynanista var mi? (Rey'de var, Ardo'da yok.)

        `docs/gdd.md` 4: Yanki **Rey'in laneti**. Bir donem replikler
        karakterden bagimsiz oynuyordu ve Ardo da mor sesi duyuyordu -
        sahip olmadigi bir gucun sesini. Her Yanki repligi bunun ardina
        alinmali.
        """
        return self.echo is not None

    def say_player(self, key: str, ardo_key: str = "", **kwargs) -> None:
        """Oynanan karakterin agzindan replik.

        Sabit `Line("rey", ...)` yaziliydi ve Ardo oynarken ekranda REY
        etiketi cikiyordu. `ardo_key` verilmezse ayni metin kullanilir -
        cogu tepki iki karakter icin de gecerli.
        """
        chosen = ardo_key if (self.character == "ardo" and ardo_key) else key
        self.say(Line(self.character, chosen), **kwargs)

    def _watch_intimacy(self) -> None:
        """Yanki ilk kez **tekil** konusuyor (docs/korku.md 4.3).

        Sadakat esigi gecildiginde bir kez. Ardo'da hic - onun Yanki'si
        yok. Kayit bayragi tekrari engelliyor: bu bir uslup degil, bir
        **kayma**; iki kez olursa kayma olmaktan cikar.

        Suren bir konusmanin ustune binmiyor - ani kendi basina kalmali.
        """
        if self.echo is None or self.save_data is None:
            return
        if loyalty.spoke_alone(self.save_data):
            return
        if not loyalty.intimate(self.save_data):
            return
        if not self.dialogue.done:
            return
        loyalty.mark_spoke_alone(self.save_data)
        self.say(Line(ECHO, "line.echo_alone_voice"))

    def summon_kalachev(self, x: float, feet_y: float,
                        stay: int = 0, silent: bool = False) -> object | None:
        """Kalachev'i sahneye sokar (`docs/kalachev.md`).

        **Bolum basina bir kez.** Iki kez belirse bir olay olmaktan
        cikip bir doku olurdu - belgenin 5. bolumu yedi bolumu kasitli
        olarak bos birakiyor, ayni gerekce.
        """
        if self.allies:
            return None
        from src.entities.kalachev import DEFAULT_STAY, Kalachev
        # **Yara kayittan geliyor** (`docs/kalachev.md` 5, B13). Tek
        # yerde okunuyor: B15 ve B18 hicbir sey yazmadan yarali bir
        # Kalachev aliyor. Bayrak kaydi olmayan bir oturumda (test,
        # dogrudan sahne acilisi) yalnizca yarasiz beliriyor.
        hurt = bool(self.save_data
                    and self.save_data.flags.get(KALACHEV_WOUND_FLAG))
        ally = Kalachev(self, x, feet_y, stay=stay or DEFAULT_STAY,
                        wounded=hurt, silent=silent)
        # Ilk giris retry yoluna ugramaz. Oyuncunun arkasindaki
        # istenen nokta kapanmis muhrun disinda kalabilir (B13).
        # Yalniz merkezin degil, govdenin tamaminin icerde olmasi gerek.
        if getattr(self, "arena_sealed", False):
            x, feet_y = self._interior_feet(
                x, feet_y, self.room, float(ally.body.width))
            x, feet_y = self.free_spot_near(x, feet_y, ally.body)
            x, feet_y = self._interior_feet(
                x, feet_y, self.room, float(ally.body.width))
            ally.body.set_feet(x, feet_y)
        self.allies.append(ally)
        self.on_kalachev_arrived(ally)
        return ally

    def on_kalachev_arrived(self, ally) -> None:
        """Alt sinif tepki verebilir - replik, kamera, ses."""

    def wound_kalachev(self, ally) -> bool:
        """Senaryolu yarayi isle **ve kayda yaz** (B13).

        Kayit yazmasi burada, sahnede degil: yaranin gorunur kalmasi
        (`docs/kalachev.md` 5) bolumun degil karakterin ozelligi.
        """
        if ally is None or ally.wounded:
            return False
        ally.wound()
        if self.save_data is not None:
            self.save_data.flags[KALACHEV_WOUND_FLAG] = True
        return True

    def try_shock(self, name: str) -> bool:
        """Bir sok anini **bir kez** acar (`docs/korku.md` §6).

        Kapi tek yerde: dagitilsaydi dort bolume yayilirdi ve biri
        mutlaka unuturdu - "korku kapali" diyen oyuncu uc bolumde
        rahat, birinde irkilirdi (`systems/horror.py` basligindaki
        ayni gerekce).

        Iki sey birden soruluyor:

          * **Bir kez mi** - §6'nin 2. kurali: *"Bir kez ise yarayan
            sey ikinci seferde komik olur."*
          * **Katman 3 acik mi** - erisilebilirlik ayari (§8).

        `True` donerse cagiran soku oynatir. Donmezse **hicbir sey
        olmaz** - sok atlanir, oynanis degismez (§3 kural 1).
        """
        if name in self._shocks_fired:
            return False
        if not horror.shock(self.game.settings):
            return False
        self._shocks_fired.add(name)
        return True

    def spawn_watcher(self, tile_x: int, tile_y: int,
                      retreats: bool = True) -> None:
        """Bir Izleyen koy (docs/korku.md 5.2).

        **Bolum basina en fazla bir kez.** Ikinci bir Izleyen ilkini
        ucuzlatir: "bu sey ara sira cikiyor" bir olay degil bir doku
        olur. Ayrica korku katmani kapaliysa hic olusturulmuyor.
        """
        from src.config import TILE_SIZE
        from src.entities.watcher import Watcher
        if self.watchers or not horror.atmosphere(self.game.settings):
            return
        self.watchers.append(Watcher(
            tile_x * TILE_SIZE + TILE_SIZE * 0.5,
            (tile_y + 1) * TILE_SIZE,
            retreats=retreats))

    # --- Uzaktan dovus ------------------------------------------------------
    def _update_throw(self) -> None:
        """Secili sarf malzemesini firlat (`src/systems/consumables.py`).

        Oyuncu **mesgulken atamiyor**: zincirin ortasinda ok firlatmak
        combo penceresini kirar ve iki sistem birbirini yer. Kacinma
        sirasinda da yok - kacinma bir kacis, bir saldiri firsati degil.
        """
        if self.save_data is None or self.modal_active:
            return
        if not self.game.input.pressed(Action.THROW):
            return
        if self.player.dead or self.player.busy or self.player.control_locked:
            return
        key = consumables.selected(self.save_data)
        if not key:
            # Elde bir sey yoksa **sessizce gecmiyoruz**: reddedilen bir
            # giris oyuncuya "tus mu calismadi" dedirtir.
            self.game.play_sound("ui_deny")
            return
        if not consumables.spend(self.save_data, key):
            return
        self.throw(key)

    def throw(self, key: str) -> None:
        """Bir mermi uretir. Sayac zaten dusuruldu."""
        item = consumables.get(key)
        if item is None:
            return
        body = self.player.body
        facing = self.player.facing or 1
        rect = pygame.Rect(int(body.center_x + facing * 6),
                           int(body.center_y - 4), 6, 6)
        box = Hitbox(
            rect=rect, owner=self.player, targets=Team.ENEMY | Team.BREAKABLE,
            damage=item.damage, active_frames=item.life,
            knockback=1.8, poise_damage=1,
            velocity=(facing * item.speed, item.lift),
            gravity=item.gravity,
            stop_on_solid=True,
            # Bomba **carpinca yok olmuyor**: hasari sifir, isi patlamak.
            pierce=item.blast > 0,
            visual="bomb" if item.blast > 0 else "arrow",
        )
        if item.blast > 0:
            box.on_expire = self._explode
        self.hitboxes.spawn(box)
        self.game.play_sound("swing_light")
        self.on_thrown(key, item)

    def _explode(self, box) -> None:
        """Bomba tukendi - **radyal** patlama (docs/derinlestirme.md 1.2).

        Yeni bir hitbox aciliyor: genis, delici, tek kare. Delici olmasi
        sart - `pierce=False` olsaydi ilk dusmanda tukenir ve alan
        hasari diye bir sey kalmazdi (ayni tuzaga Sismek'te dusulmustu).
        """
        item = consumables.get(consumables.BOMB)
        if item is None:
            return
        centre = box.rect.center
        blast = pygame.Rect(0, 0, item.blast * 2, item.blast * 2)
        blast.center = centre
        self.hitboxes.spawn(Hitbox(
            rect=blast, owner=self.player, targets=Team.ENEMY | Team.BREAKABLE,
            damage=item.blast_damage, active_frames=4,
            knockback=3.4, knockback_up=1.6, poise_damage=3, pierce=True,
        ))
        from src.core.juice import ImpactWeight
        self.juice.explosion(centre[0], centre[1], ImpactWeight.FINISHER)
        self.particles.burst(centre[0], centre[1], 20, path="spark",
                             speed=(1.2, 3.4))
        self.decals.scorch(centre[0], centre[1])

    def on_thrown(self, key: str, item) -> None:
        """Alt sinif tepki verebilir. Taban: ipucu bir kez gosteriliyor."""

    def catch_lie(self) -> bool:
        """Oyuncu bir yalani curuttu (docs/korku.md 4.1).

        Bolumler bunu, Yanki'nin gosterdigi seyin **yanlis oldugunun
        kanitlandigi** anlarda cagiriyor: kolye tersini gosteriyor,
        gosterilen gizli gecit duz duvar cikiyor, isaretlenen dusman
        zaten olu.

        Yakalandiysa Yanki susuyor - ne aciklama ne ozur. Ozur dileyen
        bir ses karakter olur; konuyu degistiren bir ses tehdit kalir.
        """
        if self.echo is None or not self.lies.catch():
            return False
        self.game.play_sound("lie_caught", bus="volume_echo")
        # Suren repligi de kes: yakalanan ses cumlesini bitirmiyor.
        if not self.dialogue.done and self.dialogue.current is not None:
            if self.dialogue.current.speaker == ECHO:
                self.dialogue.stop()
        return True

    def say(self, *lines, auto_advance: bool = False) -> None:
        """Replik dizisi baslatir. `lines` `Line` nesneleri.

        **Yanki susturulmussa Yanki repligi yutuluyor** (docs/korku.md
        4.1): yalani yakalanan ses uc saniye konusmuyor. Diger
        konusmacilar etkilenmiyor - susan Yanki, sahne degil.

        `auto_advance=True` yalnizca bir sahne-zamanlayicisiyla yarisan
        (orn. Bolum 1'in prolog beat'leri) dizilerde kullanilir - normal
        kesif/dovus repligi oyuncu onaylayana kadar ekranda kalir.
        """
        if self.lies.silenced:
            lines = tuple(line for line in lines if line.speaker != ECHO)
            if not lines:
                return
        self.dialogue.start(tuple(lines), auto_advance=auto_advance)

    # --- Yanki --------------------------------------------------------------
    def on_echo_ask(self) -> None:
        """Oyuncu Yanki'ya soru sordu. Alt sinif cevabin **anlamini** verir.

        Taban yalnizca cevabin turunu uretiyor (dogru/eksik/yalan); o
        cevabin neyi gosterdigine bolum karar veriyor - cikis mi, gizli oda
        mi, Cemo mu.
        """
        if self.echo is None:
            return
        answer = self.echo.ask()
        self.game.play_sound("echo_ask", bus="volume_echo")
        # `echo_answer_lie` **bilerek** `echo_answer_truth` ile ayni dalga
        # formu (sfx_world.py) - kulaktan ayirt edilebilir olsaydi mekanik
        # olurdu (docs/dovus-sistemi.md 5).
        answer_sound = {
            Answer.TRUTH: "echo_answer_truth",
            Answer.PARTIAL: "echo_answer_partial",
            Answer.LIE: "echo_answer_lie",
        }.get(answer)
        if answer_sound:
            self.game.play_sound(answer_sound, bus="volume_echo")

        # Yalan **deftere geciyor** (docs/korku.md 4.1). Bir donem
        # yalan soyleniyor ama hicbir yerde tutulmuyordu; oyuncu yanlis
        # yere gidip "ben yanlis anladim" diyordu, yani Yanki'nin yalani
        # oyuncunun kendi hatasi gibi okunuyordu. Artik curutulebilir.
        if answer is Answer.LIE:
            self.lies.record(self.player.body.feet,
                             direction=self.compass.direction_from(self.player))
            if self.player.knows(skilltree.ECHO_LIE):
                self._sense_lie()

    def _update_echo_audio(self) -> None:
        """Yanki acilirken/kapanirken kenar tespiti - `EchoState` kendisi
        sesle ilgilenmiyor (systems/ katmani salt mantik), kenar burada.

        Surekli `echo_loop` dongusu **kaldirildi** (Arda'nin canli oynanis
        geri bildirimi, 22.08.2026: "cizirti gibi, rahatsiz edici").
        Sentezlenmis surekli/donguluk sesler bu oturumda genel olarak
        guvenilir bulunmadi; kisa, nedeni belli tek seferlik sesler
        (echo_open/close gibi) kaliyor.
        """
        active = self.echo.active
        if active and not self._echo_was_active:
            self.game.play_sound("echo_open", bus="volume_echo")
        elif not active and self._echo_was_active:
            self.game.play_sound("echo_close", bus="volume_echo")
        self._echo_was_active = active

    def _update_necklace_audio(self) -> None:
        """Kalp atisi periyodu her devri tamamladiginda tek `tak` sesi.

        `Compass.pulse` surekli bir 0..1 egri veriyor (cizim icin); ses
        icin **kenar** gerekiyor - donguyu kendisi saymiyor, burada sayilir.
        """
        if self.compass.warmth <= NECKLACE_BEAT_MIN_WARMTH:
            self._beat_index = -1
            return
        index = self.compass.frame // max(1, self.compass.beat_period)
        if index != self._beat_index:
            self._beat_index = index
            self.game.play_sound("necklace_beat", volume=self.compass.warmth)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        offset = self.camera.offset

        self.draw_background(surface, offset)
        self.tilemap.draw(surface, offset)
        self.decals.draw(surface, offset)
        if self.merchant is not None:
            self.merchant.draw_world(surface, offset)
        if self.shrine is not None:
            self.shrine.draw(surface, offset)
        for enemy in self.enemies:
            enemy.draw(surface, offset)
        self.player.draw(surface, offset)
        # Ucan mermiler (`src/art/projectiles.py`) - aktorlerin ustunde,
        # parcaciklarin altinda: carpma kivilcimi okun onune dussun.
        projectiles.draw(surface, offset, self.hitboxes.boxes, self.game.frame)
        self.particles.draw(surface, offset)
        self._draw_burst(surface, offset)
        # Su aktorlerin USTUNE ama yari saydam ciziliyor: suya giren
        # oyuncu kaybolmamali, "suyun icinde" gorunmeli.
        if self.water is not None:
            from src.world import water as water_draw
            water_draw.draw(surface, offset, self.water)
        # Izleyen oyuncudan ONCE ciziliyor: hep uzakta, hep arkada.
        # One cizilseydi oyuncunun onune gecerdi ve "yaklasti" gibi
        # okunurdu - oysa hicbir zaman yaklasmiyor.
        for watcher in self.watchers:
            watcher.draw(surface, offset)
        for ghost in self.ghosts:
            ghost.draw(surface, offset)
        for ally in self.allies:
            ally.draw(surface, offset)
        self.draw_foreground(surface, offset)
        # Atmosfer aktorlerin ONUNDE: toz "odanin icinde" degil "kamerayla
        # oyuncu arasinda" olmali, yoksa zemin dokusu sanilir. Yanki
        # karartmasinin ALTINDA kaliyor - Yanki acikken hava da bulaniyor.
        if self.ambience is not None:
            self.ambience.draw(surface)

        # Sira: once dunya kararir (bedel), sonra gizli seyler o karanligi
        # delerek cikar (kazanc). Ters sirada Yanki acilinca ekran
        # aydinlaniyordu - bedel tam tersine donmustu.
        if self.echo is not None:
            echo_view.draw_dim(surface, self.echo)
            echo_view.draw_reveal(surface, offset, self.echo, self.player,
                                  self.enemies, self.breakables)
            echo_view.draw_phantom(surface, offset, self.echo, self.phantom)
            echo_view.draw_answer(surface, offset, self.echo, self.player)

        # Iz Surme ayni yerde ama **karartma yok**: Yanki'nin bedeli
        # dunyanin kararmasi, Iz Surme'ninki dusmanlarin solmasi (o
        # `_draw_enemies`'de). Ayni gorseli kullansalardi "Ardo'nun
        # Yankisi" gibi okunurdu - oysa mesele farkli bir duyu olmasi.
        if self.tracking is not None:
            # Sira: once dunya agarir (isaret), sonra gecmis o soluklugun
            # icinden cikar. Yanki'nin sirasinin aynadaki hali - orada
            # once kararir sonra gizli seyler karanligi deler.
            tracking_view.draw_wash(surface, self.tracking)
            tracking_view.draw_traces(surface, offset, self.tracking,
                                      self.player, self.traces)
            tracking_view.draw_cracks(surface, offset, self.tracking,
                                      self.player, self.breakables)

        if self.game.debug_overlay:
            self._draw_hitboxes(surface, offset)
        # Isima (`src/art/bloom.py`): dunya, isik ve Yanki katmanlarindan
        # SONRA, arayuzden ONCE - lav ve mesale havayi aydinlatiyor, yazilar
        # keskin kaliyor. Guc "Efekt gucu" ayarindan; 0 ise kapali.
        bloom.apply(surface, float(self.game.settings.get("postfx", 1.0)))
        # Tus gostergeleri isik ve Yanki katmanlarinin USTUNDE: karanlikta
        # kalan bir vana da hangi tusla acildigini soylemeli.
        self.prompts.draw(surface, offset, self.game.input, self.game.frame)
        self._draw_hud(surface)
        self.dialogue.draw(surface, self.game.frame)
        # Kart diyalogun USTUNDE ama Yanki saciliminin ALTINDA: bolum
        # adi her zeminde okunmali, ama Yanki acikken o da bulanir.
        if self.card is not None:
            self.card.draw(surface)
        if self.mechanic_card is not None:
            self.mechanic_card.draw(surface)
        self._draw_boss_bar(surface)
        self.draw_overlay(surface)
        if self.merchant is not None:
            self.merchant.draw_panel(surface, self)

        # Kromatik kayma en son: arayuz dahil her seyin uzerine. Yanki
        # acikken oyuncu her seyi biraz daha zor goruyor.
        if self.echo is not None:
            echo_view.draw_fringe(surface, self.echo)

    def draw_background(self, surface, offset) -> None: ...

    def draw_foreground(self, surface, offset) -> None: ...

    def draw_overlay(self, surface) -> None: ...

    def _draw_boss_bar(self, surface) -> None:
        """Boss can bari - **her bolumde, otomatik.**

        `CLAUDE.md` 7: *"Dusman can bari yok. Sadece boss'larda bar
        var."* Bar `Boss.draw_health_bar` icinde ama cagirmak her
        bolumun kendi isiydi ve Bolum 6 unutmustu: BOSS 1'in cani hic
        gorunmuyordu (Arda, 30.08.2026). `DEVIR.md` 21 bu tuzagi bir
        kez zaten yakalamisti - "unutulmasin" demek yetmemis.

        Artik burada: `self.boss` varsa ve yasiyorsa cizilir. Bolum
        hicbir sey yapmiyor, dolayisiyla unutamiyor.
        """
        boss = getattr(self, "boss", None)
        if boss is None or getattr(boss, "dead", True):
            return
        boss.draw_health_bar(surface)

    def free_spot_near(self, x: float, y: float, body) -> tuple[float, float]:
        """Verilen govde icin yakinda **bos** bir yer bulur.

        Arda (30.08.2026): *"Oldukten sonra yeniden dene dedigimizde
        Ardo duvarin icinde kaliyor."* `after_restart` yoldasi
        oyuncunun 24 piksel soluna koyuyordu ve orasi bir duvar
        sutunuysa icinde sikisiyordu - `Companion` kendi kendini
        kurtarmiyor.

        Once istenen yer, sonra iki yana artan mesafeler deneniyor.
        Hicbiri olmazsa en kisa kaydirma (`_nudge_clear_feet`);
        oyuncunun kendi konumu yedek DEGIL - o da duvardaysa
        sikisma kalici olur.
        """
        probe = body.rect.copy()
        for dx in (0, -14, 14, -28, 28, -44, 44, -60, 60):
            probe.x = int(x + dx - probe.width * 0.5)
            probe.y = int(y - probe.height)
            if not self.tilemap.solid_overlap(probe):
                return (x + dx, y)
        return self._nudge_clear_feet(body)

    def _eject_from_solids(self) -> None:
        """Duvarin icinde kalan oyuncuyu en kisa yoldan cikarir.

        Arena muhuru (`set_tile(..., SOLID)`) govdenin ustune binebilir:
        esik merkeze bakinca 10 piksellik kutu sutunun 5 pikselinde
        kaliyor. `Body.move` bunu cozmez. `docs/derinlestirme.md`:
        *"Hicbir odada oyuncu kalici olarak sikismasin."*
        """
        if self.player.dead or self.player.body.ignore_solids:
            return
        if not self.tilemap.solid_overlap(self.player.body.rect):
            return
        x, y = self._nudge_clear_feet(self.player.body)
        self.player.body.set_feet(x, y)
        self.player.body.vx = 0.0

    def _nudge_clear_feet(self, body) -> tuple[float, float]:
        """En kisa yatay kaydirma. Es mesafede saga (arena ici) oncelik."""
        y = body.feet[1]
        probe = body.rect.copy()
        probe.y = int(y - probe.height)
        half = probe.width * 0.5
        for dist in range(1, TILE_SIZE * 4):
            for sign in (1, -1):
                nx = body.center_x + sign * dist
                probe.x = int(nx - half)
                if not self.tilemap.solid_overlap(probe):
                    return (nx, y)
        return (body.center_x, y)

    # --- Game feel kancalari ------------------------------------------------
    def on_hit(self, box, target, result, direction) -> None:
        """Bir vurus degdi. **Ucu birden tek cagridan** - kare kaymasi olmasin."""
        weight = ImpactWeight.NORMAL
        if result.killed:
            weight = ImpactWeight.KILL
        elif box.is_finisher:
            weight = ImpactWeight.FINISHER

        self.juice.on_hit(
            ImpactEvent(
                x=target.body.center_x,
                y=target.body.center_y,
                direction=direction,
                weight=weight,
                particle_path="violet" if box.is_counter else "blood",
                particle_count=10 if box.is_finisher else 6,
            ),
            target_flash=target.flash,
            target_squash=target.squash,
        )

        # **Muttefikin kesim sayaci.** `Kalachev.kills` tanimlaniyordu
        # ama hicbir yerde ARTMIYORDU - olu bir sayac. B5'in ilk
        # gorusu onu okuyunca ortaya cikti (08.09.2026): "hepsini
        # kesiyor" iddiasi olculemiyordu.
        #
        # Burada duruyor cunku "kim oldurdu" sorusunun cevabi yalnizca
        # burada var: `box.owner` vuranı, `result.killed` sonucu
        # soyluyor. Muttefige ozel degil - `allies` listesindeki her
        # sey icin isliyor.
        if result.killed and box.owner in self.allies:
            box.owner.kills += 1

        if box.owner is self.player:
            self.total_hits += 1
            self.player.register_hit()
            self.game.play_sound(self._hit_sound(box, result),
                                 muffled=self._echo_active())
            if box.is_counter:
                self.show_toast(t("combat.counter"))
            self._on_skill_hit(target, result)
            if result.killed:
                # Kill cancel: recovery aninda kesilir, akis surer.
                self.player.notify_kill()

    def _hit_sound(self, box, result) -> str:
        if result.killed:
            return "hit_kill"
        if box.is_counter:
            return "hit_counter"
        if box.is_finisher:
            return "hit_heavy"
        return "hit_light"

    def _echo_active(self) -> bool:
        return self.echo is not None and self.echo.active

    def on_enemy_died(self, enemy) -> None:
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.FINISHER)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 16,
                             path="blood", speed=(1.0, 3.0))
        # Parcaciklar soner, leke kalir: koridora donunce dovusun izi durur.
        self.decals.splatter(enemy.body.center_x, enemy.body.feet[1], amount=10)
        # Ayni an `TraceField`'e de yaziliyor: leke CIZILMIS PIKSEL,
        # iz SORGULANABILIR VERI. Iz Surme "yakindakileri yasina gore
        # goster" diyor, pisirilmis bir yuzey bunu cevaplayamaz.
        self.traces.add(enemy.body.center_x, enemy.body.feet[1], BLOOD)
        # Bos dize = sessiz kal (orn. Sismek zaten patlama sesiyle oldu,
        # ustune binmesin - src/entities/enemies/bloated.py).
        if enemy.death_sound:
            self.game.play_sound(enemy.death_sound)

    def on_enemy_tell(self, enemy) -> None:
        """Tell basladi - hangi ses calinacagini dusmanin kendi tipi
        soyluyor (`Enemy.tell_sound`, varsayilan genel "enemy_tell")."""
        self.game.play_sound(enemy.tell_sound, muffled=self._echo_active())

    def on_climber_drop(self, enemy) -> None:
        """Tirmanan tavandan koptu - toz doksun, telegraf tamamlansin."""
        self.particles.burst(enemy.body.center_x, enemy.body.bottom, 5,
                             direction=(0.0, 1.0), path="dust",
                             speed=(0.2, 0.7), life=(10, 20), gravity=0.03)
        self.game.play_sound("climber_drop")

    def on_bloated_explode(self, enemy) -> None:
        """Patlama radyal - yonlu degil (docs/derinlestirme.md 1.2)."""
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.KILL)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 22,
                             path="spark", speed=(1.2, 3.6))
        self.decals.scorch(enemy.body.center_x, enemy.body.feet[1])
        self.traces.add(enemy.body.center_x, enemy.body.feet[1], SCORCH)
        self.game.play_sound("bloated_explode")

    def on_shield_block(self, enemy) -> None:
        """Vurus Kalkanli'nin kalkanina carpti (Katman 2, `shieldbearer.py`).

        Blok **hasar vermiyor** - ceza ritmi kaybetmek. Ama geri bildirim
        vurustan daha GURULTULU olmali: oyuncu "vurdum ama olmadi"
        belirsizligini bir kare bile yasamamali. Kivilcim + sert sarsinti
        + kalkan sesi, ucu birden `juice.on_hit`'ten degil ama ayni ruhla.
        """
        x = enemy.body.center_x + enemy.facing * 8
        self.juice.explosion(x, enemy.body.center_y, ImpactWeight.NORMAL)
        self.particles.burst(x, enemy.body.center_y, 8, path="spark",
                             speed=(0.8, 2.2))
        self.game.play_sound("enemy_blocked", muffled=self._echo_active())

    def on_shield_turn(self, enemy) -> None:
        """Kalkanli donmeye karar verdi - okunur olmali.

        Sessizce donmek "arkasindayim" sozlesmesini bozar; oyuncu bunu
        haksizlik olarak okur (docs/derinlestirme.md 4.2).
        """
        self.game.play_sound("enemy_tell", muffled=self._echo_active())

    def on_combo_threshold(self, player, threshold: int) -> None:
        # Saldirgan oynayan kademesini geri kazanir (DEVIR gorev 3.1).
        # Korkak oynayan iyilesemez - can siseleri nadir tutuluyor.
        # ONARIM yetenegi esigi dusuruyor (20 -> 14). Tabani degistirmiyor,
        # ustune indirim biniyor - `docs/dovus-sistemi.md`'nin sayilari
        # yerinde kaliyor.
        needed = COMBO_TO_RESTORE
        if self.player.skills:
            from src.systems import skilltree
            needed = max(1, needed
                         - skilltree.restore_combo_reduction(self.player.skills))
        if (threshold >= needed and self.echo is not None
                and self.echo.restore()):
            self.on_echo_tier_changed(self.echo.tier, gained=True)
        if threshold >= COMBO_THRESHOLD_HIGH:
            self.show_toast(t("combat.combo_echo", count=threshold))
        elif threshold >= COMBO_THRESHOLD_MID:
            self.show_toast(t("combat.combo_health", count=threshold))
        else:
            self.show_toast(t("combat.combo", count=threshold))

    def on_combo_reset(self) -> None: ...

    def on_player_attack(self, player, index: int) -> None:
        """Zincir bir sonraki vurusa gecti - degip degmemesinden bagimsiz,
        kilic her savrulduğunda calar (SES-LISTESI 1: "vurus degmese de
        calar")."""
        self.game.play_sound(
            "swing_heavy" if player.chain.is_finisher else "swing_light")

    def on_attack_swing(self, player, box) -> None:
        """Vurus kirilabilir duvara degdi mi?

        Hitbox sistemi yalnizca **varliklara** bakiyor; duvar bir tile.
        Burada ayrica sorulmasi gerekiyor - yoksa oyuncu duvara vurur ve
        hicbir sey olmaz.
        """
        broken: list[pygame.Rect] = []
        for rect in self.tilemap.breakable_rects():
            if not box.rect.colliderect(rect):
                continue
            tx = rect.x // TILE_SIZE
            ty = rect.y // TILE_SIZE
            if self.tilemap.break_at(tx, ty):
                broken.append(rect)
                self.particles.burst(rect.centerx, rect.centery, 8,
                                     path="dust", speed=(0.5, 1.8))
                self.decals.splatter(rect.centerx, rect.bottom, amount=4,
                                     path="soot", spread=7.0)
        if broken:
            self.juice.explosion(player.body.center_x, player.body.center_y,
                                 ImpactWeight.NORMAL)
            self.on_wall_broken(broken)

    def on_wall_broken(self, rects: list[pygame.Rect]) -> None:
        """Gizli gecit acildi. `rects` yikilan tile'lar.

        Hangi duvarin yikildigi bolume soyleniyor: bir bolumde birden fazla
        kirilabilir duvar olabiliyor ve hepsi ayni sey anlamina gelmiyor
        (Bolum 2: biri yolu aciyor, digeri gizli odayi).
        """
        self.show_toast(t("echo.wall_broken"), frames=120)

    def on_player_jump(self, player) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 4,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.3, 0.9), life=(8, 16), gravity=0.04)
        self.game.play_sound("jump")

    def on_player_land(self, player, air_frames: int) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 6,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.4, 1.2), life=(10, 20), gravity=0.05)
        hard = air_frames >= HARD_LAND_AIR_FRAMES
        self.game.play_sound("land_hard" if hard else "land_soft")

    def on_player_brake(self, player) -> None:
        """Tam hizdan durus: on ayagin onunde kisa bir toz yelpazesi."""
        self.particles.burst(player.body.center_x + player.facing * 5,
                             player.body.feet[1], 5,
                             direction=(player.facing, -0.4), path="dust",
                             speed=(0.4, 1.3), life=(8, 16), gravity=0.05)

    def on_player_dodge(self, player) -> None:
        self.particles.burst(player.body.center_x, player.body.feet[1], 8,
                             direction=(-player.facing, 0.0), path="dust",
                             speed=(0.5, 1.6), life=(10, 22), gravity=0.03)
        self.game.play_sound("dodge")

    def on_dodge_trail(self, player) -> None:
        if player.dodge.frames_left % 3 == 0:
            self.particles.burst(player.body.center_x, player.body.center_y, 1,
                                 direction=(-player.facing, 0.0), path="echo",
                                 speed=(0.1, 0.4), life=(8, 14), gravity=0.0)

    # --- Yetenek agaci: hareketlerin sahne tarafi -------------------------
    def refresh_skills(self) -> None:
        """Yetenekler degisti (kurulus ya da duraklat menusundeki agac).

        Oyuncunun kendi bonuslarini `Player.apply_skills` kuruyor; burasi
        SAHNEYE ait olanlari: Iz menzili `TrackingState`te duruyor.
        """
        if self.tracking is not None:
            self.tracking.range_scale = skilltree.trace_range_scale(
                self.player.skills)

    def learn_skill(self, node_key: str) -> None:
        """Agac ekrani bir dugum acti - canli oyuncu ve sahne yetissin."""
        self.player.learn_skill(node_key)
        self.refresh_skills()

    def _migrate_save(self) -> None:
        """ESKI KAYIT icin tek seferlik iki duzeltme, ikisi de bayrakli.

          * Tezgahtan kalkan Sonmez Fitil / Koruyucu Mum'un parasi iade
          * Yeni agacin GECILMIS kaynaklarinin puani (`skilltree.backfill`)

        Degisiklik olursa kayit hemen yaziliyor: yazilmasaydi olup yeniden
        dogan oyuncu ayni bildirimi her denemede yeniden gorurdu.
        """
        data = self.save_data
        if data is None:
            return
        from src.systems import merchant
        refund = merchant.refund_legacy(data)
        points = skilltree.backfill(data, self.chapter_number or 0)
        if not (refund or points):
            return
        write_save(data)
        if refund:
            self._toast_queue.append((t("shop.refund_toast", gold=refund), 220))
        if points:
            self._toast_queue.append((t("skilltree.backfill_toast",
                                        count=points), 220))

    def _update_sense_burst(self) -> None:
        """Yanki Darbesi (Rey) / Ayi Kukremesi (Ardo): duyu ACILDIGI anda.

        Tus ayni (`Action.ECHO`), yeni bir tus yok - hareketin kendisi
        duyuyu acmak. Bedeli de ayni: Rey icin Yanki'nin karartmasi ve
        savunma cezasi, Ardo icin dusmanlarin solmasi. Bekleme 5 saniye.
        """
        if self._burst_cooldown > 0:
            self._burst_cooldown -= 1
        if self._burst_ring > 0:
            self._burst_ring -= 1
        opened = self.sense_open()
        rising = opened and not self._burst_was_open
        self._burst_was_open = opened
        if not rising or self._burst_cooldown > 0 or self.player.dead:
            return
        key = (skilltree.ECHO_BURST if self.echo is not None
               else skilltree.TRACE_ROAR)
        if not self.player.knows(key):
            return
        self._burst_cooldown = SKILL_BURST_COOLDOWN
        self._sense_burst(key)

    def _sense_burst(self, key: str) -> None:
        """Cevreyi iten, sendeleten halka. Hasari kucuk - isi alan acmak."""
        body = self.player.body
        width, height = SKILL_BURST_SIZE
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(body.center_x), int(body.center_y))
        self.hitboxes.spawn(Hitbox(
            rect=rect, damage=SKILL_BURST_DAMAGE, owner=self.player,
            targets=Team.ENEMY, knockback=SKILL_BURST_KNOCKBACK,
            knockback_up=1.6, active_frames=3,
            poise_damage=SKILL_BURST_POISE, pierce=True,
        ))
        rey = key == skilltree.ECHO_BURST
        self._burst_ring = BURST_RING_FRAMES
        self._burst_origin = (body.center_x, body.center_y)
        self._burst_key = key
        self.particles.burst(body.center_x, body.center_y, 18,
                             path="echo" if rey else "dust",
                             speed=(1.2, 2.8), life=(12, 26), gravity=0.0)
        self.juice.explosion(body.center_x, body.center_y,
                             ImpactWeight.FINISHER)
        self.game.play_sound("sense_burst" if rey else "bear_roar",
                             bus="volume_echo" if rey else "volume_sfx")

    def _draw_burst(self, surface: pygame.Surface, offset) -> None:
        """Genisleyen halka - itmenin ALANI gorunsun (renk + sekil)."""
        if self._burst_ring <= 0:
            return
        progress = 1.0 - self._burst_ring / BURST_RING_FRAMES
        width, height = SKILL_BURST_SIZE
        ox, oy = offset
        cx = int(self._burst_origin[0]) - ox
        cy = int(self._burst_origin[1]) - oy
        rx = max(2, int(width * 0.5 * (0.35 + 0.65 * progress)))
        ry = max(2, int(height * 0.5 * (0.35 + 0.65 * progress)))
        rey = self._burst_key == skilltree.ECHO_BURST
        outer = palette.color("echo_bright" if rey else "bone")
        inner = palette.color("echo" if rey else "stone_light")
        thickness = 2 if progress < 0.6 else 1
        pygame.draw.ellipse(surface, outer,
                            (cx - rx, cy - ry, rx * 2, ry * 2), thickness)
        if rx > 6 and ry > 4:
            pygame.draw.ellipse(surface, inner,
                                (cx - rx + 3, cy - ry + 2,
                                 (rx - 3) * 2, (ry - 2) * 2), 1)

    def _sense_lie(self) -> None:
        """Yalan Sezgisi (YANKI 3b): Yanki yalan soyleyince kolye urperiyor.

        Yalan yine SOYLENIYOR ve deftere yaziliyor - yetenek onu silmiyor,
        kulak veren oyuncuya bir supheli an veriyor. Iki kanal: ses
        (kolyenin celiskili atisi) ve goz (boyundan dokulen is).
        Yazi yok: "bu yalan" demek Yanki'nin yerine konusmak olurdu
        (docs/korku.md 4.1).
        """
        body = self.player.body
        self.particles.burst(body.center_x, body.y + 6, 7, path="soot",
                             direction=(0.0, 1.0), speed=(0.2, 0.7),
                             life=(18, 34), gravity=0.02)
        self.game.play_sound("necklace_conflict", bus="volume_echo")

    def _on_skill_hit(self, target, result) -> None:
        """Oyuncunun vurusu degdi - yetenek agacinin vurus tarafi."""
        healed = self.player.on_dealt_damage(result.amount)
        if healed:
            body = self.player.body
            self.particles.burst(body.center_x, body.center_y, 3,
                                 path="spark", direction=(0.0, -1.0),
                                 speed=(0.3, 0.9), life=(10, 18))
        if getattr(result, "ambush", False):
            # Pusu: vurusun nereden geldigi okunsun - hedefin ustunde
            # kisa bir kivilcim ve sesin agir hali.
            self.particles.burst(target.body.center_x, target.body.y, 8,
                                 path="spark", direction=(0.0, -1.0),
                                 speed=(0.6, 1.8), life=(10, 20))
            self.game.play_sound("hit_counter")

    def on_player_dash(self, player) -> None:
        """Hamle basladi: arkada toz, havayi yaran ses."""
        self.particles.burst(player.body.center_x - player.facing * 4,
                             player.body.feet[1], 10,
                             direction=(-player.facing, -0.3), path="dust",
                             speed=(0.8, 2.2), life=(10, 22), gravity=0.04)
        self.game.play_sound("dodge")

    def on_dash_trail(self, player) -> None:
        if self.game.frame % 2 == 0:
            self.particles.burst(player.body.center_x, player.body.center_y,
                                 1, direction=(-player.facing, 0.0),
                                 path="spark", speed=(0.1, 0.5),
                                 life=(6, 12), gravity=0.0)

    def on_player_poised(self, player) -> None:
        """Sarsilmaz: darbe yendi ama durus bozulmadi - metalik bir tik."""
        self.particles.burst(player.body.center_x, player.body.center_y, 5,
                             path="spark", speed=(0.4, 1.4), life=(6, 12))
        self.game.play_sound("enemy_blocked")

    def on_shield_broken(self, player, box, direction) -> None:
        """Eski Kalkan ilk darbeyi karsiladi ve kirildi.

        Tek `on_hit` gecidi (CLAUDE.md 7 "uclu senkron"): hitstop, sarsinti
        ve parcacik ayni cagridan. Agirlik NORMAL - baglayici 3 kare.
        """
        x = player.body.center_x - player.facing * 4
        y = player.body.center_y - 2
        self.juice.on_hit(
            ImpactEvent(x=x, y=y, direction=direction,
                        weight=ImpactWeight.NORMAL,
                        particle_path="splinter", particle_count=12),
            target_flash=player.flash, target_squash=player.squash,
        )
        self.decals.splatter(x, player.body.bottom, amount=3,
                             path="splinter", spread=9.0)
        self.game.play_sound("shield_break")
        self.show_toast(t("combat.shield_broken"), frames=110)

    def on_player_step(self, player) -> None:
        """Adim - hangi ses calinacagi sahnenin `footstep_sound`'undan gelir
        (zemine gore degil **sahneye** gore, bkz. sinif tanimi)."""
        self.game.play_sound(self.footstep_sound, muffled=self._echo_active())

    def on_player_hurt(self, player, result) -> None:
        self.show_toast(t("combat.hurt"))
        self.game.play_sound("player_hurt", muffled=self._echo_active())

    def on_echo_tier_changed(self, tier: int, gained: bool) -> None:
        """Kademe degisti. Asamali aciga cikarma: yalnizca **degisince**
        gosteriliyor (CLAUDE.md 9)."""
        # Anahtarlar **acikca** yazili: f-string ile kurulan anahtari
        # tests/test_lang.py kaynak taramasinda goremiyor ve "olu anahtar"
        # sayiyor. Bu tuzaga ikinci kez dusuldu.
        self.show_toast(t("echo.tier_up" if gained else "echo.tier_down"),
                        frames=120)
        self.game.play_sound("echo_tier_up" if gained else "echo_tier_down",
                             bus="volume_echo")

    def on_player_died(self, player) -> None:
        # Olunce Yanki bir kademe zayiflar. Dip SESSIZ - daha asagi inmez,
        # olum sarmali boyle engelleniyor (docs/gdd.md 4).
        if self.echo is not None and self.echo.weaken():
            self.on_echo_tier_changed(self.echo.tier, gained=False)
        self.game.play_sound("player_death")
        self.death_frames = DEATH_SCREEN_DELAY
        self._leave_ghost(player)

    def _leave_ghost(self, player) -> None:
        """Oldugun yerde bir hayalet kalir (docs/korku.md 5.3).

        Ust uste ayni yerde olen oyuncu hayalet YIGMASIN: yakindaki bir
        hayalet varsa yenisi konmuyor. On tane ust uste duran mor leke
        bir anlam degil bir hata gibi okunur.
        """
        if not horror.atmosphere(self.game.settings):
            return
        from src.entities.ghost import Ghost
        fx, fy = player.body.feet
        for existing in self.ghosts:
            if abs(existing.x - fx) < 20.0 and abs(existing.feet_y - fy) < 24.0:
                return
        self.ghosts.append(Ghost(fx, fy))

    def _open_death_screen(self) -> None:
        """Olum ekranini acar.

        **Toast yeterli degildi** (Arda, 29.08.2026 canli oynanis: *"boss
        fight'ta olunce kaldik oyle, hicbir sey yapilmiyor"*). `restart()`
        calisiyordu ama onu soyleyen yazi 72 karede sonuyor ve oyuncu
        hareketsiz bir ekranla bas basa kaliyordu. Gecici bir bildirim
        kalici bir durumu anlatamaz.

        Gecikme bilincli: olum vurusunun hitstop'u, sarsintisi ve
        parcaciklari once bitsin. Menu aninda acilirsa oyuncu neyle
        oldugunu goremiyor.
        """
        from src.ui.death import DeathScene
        self.scenes.push(DeathScene, save_data=self.save_data,
                         room_label=self.room_label(),
                         on_retry=self.restart)

    def room_label(self) -> str:
        """Olum ekraninda gosterilecek yer.

        **Bolum adi KULLANILMIYOR.** Ilk surum onu gosteriyordu ve Bolum
        6'da ekranda "ARDO - odanin basindan" yaziyordu: bolumun adi ama
        oyuncu bir KARAKTER adi okuyor ve "Ardo'nun odasi mi?" diye
        soruyor. Belirsiz bir etiket, etiketsizlikten kotudur.

        Oda adlari ic anahtar (`vana_odasi`, `arena`) ve cevrilmiyor;
        cevirmek her bolume dokuz anahtar eklerdi. Onun yerine ekran
        **numarayi** soyluyor - hangi bolumde oldugu zaten belli, eksik
        olan bilgi "bastan mi basliyorum" sorusuydu ve ona `death.resume_at`
        cevap veriyor.
        """
        return str(self.chapter_number) if self.chapter_number else ""

    def on_ability_gained(self, ability: str) -> None:
        """Yetenek kazanildi. Bir sey **kazanmis** olmali - sessiz gecmesin.

        Paylasilan (chapter01.py'den tasindi): her bolum kendi yetenek
        anini yasiyor, ama "kazanmak" hep ayni goruntu/ses/yaziya sahip
        olmali - dagitilsaydi biri farkli hissettirirdi.
        """
        action = abilities.action_for(ability)
        label = self.game.input.binding_label(action) if action else ""
        self.show_toast(t(abilities.label_key(ability), key=label), frames=180)
        self.pickup_juice()

    def pickup_juice(self, gold: bool = False) -> None:
        """Bir sey kazanmanin GORUNTUSU - yaziyi cagiran belirler.

        `gold=True` altin sesini caliyor. Ses paketinde `gold_pickup`
        vardi ama **hicbir yerden cagrilmiyordu**: sandiklar da altin
        da genel `item_pickup` sesini kullaniyordu ve para sesi hic
        duyulmuyordu. `tests/test_audio.py` bunu ilk calistirmasinda
        buldu.

        `on_ability_gained`'dan ayrildi: anahtar, tilsim, silah gibi
        yetenek OLMAYAN kazanimlar da ayni parlama/parcacik/sesi
        kullanmali ama kendi yazisini yazmali. Once anahtar icin
        `on_ability_gained("")` cagirmistim - `abilities.label_key("")`
        "?" donuyor ve ekranda soru isareti cikiyordu.
        """
        self.juice.explosion(self.player.body.center_x,
                             self.player.body.center_y, ImpactWeight.NORMAL)
        self.particles.burst(self.player.body.center_x,
                             self.player.body.center_y, 14,
                             path="spark", speed=(0.6, 2.2))
        self.game.play_sound("gold_pickup" if gold else "item_pickup")

    def _emit_particles(self, event: ImpactEvent) -> None:
        self.particles.burst(event.x, event.y, event.particle_count,
                             direction=event.direction, path=event.particle_path)

    def show_toast(self, message: str, frames: int = 72) -> None:
        self.toast = message
        self.toast_frames = frames

    def _draw_hitboxes(self, surface: pygame.Surface,
                       offset: tuple[int, int]) -> None:
        ox, oy = offset
        for box in self.hitboxes.boxes:
            pygame.draw.rect(surface, palette.color("danger_bright"),
                             box.rect.move(-ox, -oy), 1)
        for actor in [self.player, *self.enemies]:
            pygame.draw.rect(surface, palette.color("echo"),
                             actor.hurtbox.move(-ox, -oy), 1)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        # Asamali aciga cikarma: bilgi yalnizca ilgili oldugunda gorunur.
        self.hud.draw(surface, self.player, self.gold, self.echo_tier)
        if self.toast_frames > 0:
            text.draw(surface, self.toast, INTERNAL_WIDTH // 2, 42,
                      color=palette.color("violet_bright"), align="center",
                      outline=True)

    def debug_lines(self) -> list[str]:
        return [
            *self.player.debug_lines(),
            f"hitbox {self.hitboxes.active_count}  "
            f"parcacik {self.particles.alive_count}  "
            f"sarsinti {self.juice.shake.frames_left}",
            f"dusman {len(self.enemies)}  hak {self.tokens.active_count}  "
            f"leke {self.decals.count}",
        ]
