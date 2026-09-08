"""Bolum 10 - "Ayrilik". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter10.py`, ara sahneler
`src/scenes/chapter10_cinematics.py`.

`docs/yapi.md` B10: *"Yol ikiye ayrilir. Yalniz devam. Yanki yukselir,
yorum yapmaya baslar, **ilk kez yanlis bilgi verip seni tuzaga
sokar.** Mekanik: Zorluk sicramasi. Yanki'ya guvenmeme dersi."*

## Yalan bir sahne degil bir SECIM

Yanki ust yolu **isaretliyor** - Bolum 1'den beri kirilabilir duvarlari
isaretledigi ayni gorsel dille (`echo_view`). Oyuncu o isarete sekiz
bolumdur guveniyor ve isaret hep dogruydu. Burada degil.

Yalanin ise yaramasi icin isaretin **tanidik** olmasi sart: yeni bir
gosterge uydursaydik oyuncu supheye duserdi ve ders olusmazdi.

## Ardo oynanirken - ayni beat, oteki duyu

Ardo'nun Yanki'si yok; Iz Surme'si var. Iz yalan soylemez ama
**yanlis okunabilir**: birileri sahte bir iz birakmis. Ayni tuzak,
ayni ders, farkli gerekce - `EchoState`/`TrackingState` ciftinin her
yerdeki ilkesi.

## Sadakat sayaci

`docs/derinlestirme.md` 2.2: gorunmez bir int, B14'te okunacak.
Yanki'nin yolundan gitmek artiriyor, kendi yolunu bulmak azaltiyor.
Oyuncuya **hicbir sey** gosterilmiyor - gorunur olsaydi optimize
edilirdi ve olculen sey guven degil puan olurdu.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.juice import ImpactWeight
from src.scenes.play import PlayScene
from src.systems.false_silence import FalseSilence, Stretch
from src.systems import loyalty
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter10 import (
    CHEST_GOLD, HONEST_TILE, LEVEL, LOWER_ROW, LURE_TILE, ROOM_STARTS,
    SECRETS_TOTAL, SPLIT_TILE, TRAP_ROW, TRAP_TILES, UPPER_ROW,
)
from src.world.tilemap import EMPTY, TileMap

ENEMY_CLASSES = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "shieldbearer": "src.entities.enemies.shieldbearer:Shieldbearer",
    "spearman": "src.entities.enemies.spearman:Spearman",
}

# Tuzak bu kadar kare once **gicirdiyor**: zemin cokmeden once bir
# uyari. Uyarisiz bir tuzak haksizlik olur; uyarili bir tuzak ders
# olur - oyuncu geri donebilirdi ve donmedi.
TRAP_CREAK_FRAMES = 26

# --- Kalachev (`docs/kalachev.md` 5) -----------------------------------------
# Tuzagin ortasi: `TRAP_TILES` 70-75, ortasi 72.
ALLY_TRAP_COLUMN = 72
# Oyuncu tuzaga bu kadar kala beliriyor (tile). 11 secildi: ekranin
# yarisi 15 tile, yani olay kenarda degil kadrajin icinde basliyor -
# B5'te 13 ile olculen ayni gerekce.
ALLY_TRIGGER_TILES = 11
# Belge "~40 sn" diyor; 60 FPS'te 2400 kare. Kalachev bu sure boyunca
# oradaki mizraklilari da kesiyor, sonra cekiliyor.
ALLY_STAY = 2400


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter10Scene(PlayScene):
    """Ayrilik: dort oda, bir yalan, bir sayac."""

    chapter_number = 10
    chapter_name_key = "chapter.parting"
    postfx_grade = "descent"
    ambience_preset = "dust"
    dark_ambient = True    # docs/korku.md 5.1 - yalniz ve karanlikta

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)

        # **Yoldas yok.** Bolumun adi bu. `PlayScene`'in yoldas
        # kancalari `getattr` ile soruyor, yani hicbir sey kirilmiyor.
        self.companion = None

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHEST_GOLD, secret=True)
                       for spot in LEVEL.of("chest")]

        self.room = ""
        self.room_frames = 0
        self.frames = 0
        self.entered_rooms: set[str] = set()
        self.earned_gold = 0
        self.secret_found = False
        self.finished = False

        # --- Yalan ------------------------------------------------------
        self.parting_played = False
        self.lure_shown = False          # Yanki ust yolu isaretledi mi
        self.choice = ""                 # "" | "followed" | "ignored"
        self.trap_creak = 0
        self.trap_sprung = False
        # Kalachev tuzagi KIRDI mi (`docs/kalachev.md` 5).
        # `trap_sprung`dan **ayri**: o "oyuncu dustu" demek ve bolum
        # sonu sinematigi onu okuyor (`ch10_lie_sprung`). Ikisini ayni
        # bayraga baglamak sahneye "tuzaga dustun" dedirtirdi - oysa
        # oyuncu dusmedi, biri onu once kirdi.
        self.trap_broken = False
        self.lesson_played = False

        # Yanlis sessizlik (docs/korku.md 5.4). Bu koridorda
        # HICBIR SEY olmuyor ve olmamasi isin kendisi:
        # catal odasinin girisi - en yakin dusman 49'da kaldi, sonraki 71'de; arada 22 tile bos koridor var.
        # Oyuncu sessizligi bir alarm sanmayi ogrendi; burada o
        # alarm bos caliyor. B14'te ayni sessizligin ardindan
        # jumpscare geliyor, B15'te ise sessizlik hic gelmiyor
        # ama olay oluyor - ucu birlikte sinyali bozuyor.
        self.false_silence = FalseSilence(Stretch(55, 68))

        self._enter_room(self._room_at(self.player.body.center_x))

    # --- Odalar -------------------------------------------------------------
    def _room_at(self, x: float) -> str:
        tile = int(x) // TILE_SIZE
        name = ROOM_STARTS[0][0]
        for room_name, start in ROOM_STARTS:
            if tile >= start:
                name = room_name
        return name

    def _room_span(self, name: str) -> tuple[int, int]:
        for index, (room_name, start) in enumerate(ROOM_STARTS):
            if room_name != name:
                continue
            end = (ROOM_STARTS[index + 1][1] if index + 1 < len(ROOM_STARTS)
                   else self.tilemap.width)
            return start, end
        return 0, self.tilemap.width

    def _enter_room(self, name: str) -> None:
        self.room = name
        self.room_frames = 0
        if name in self.entered_rooms:
            return
        self.entered_rooms.add(name)
        self._spawn_room(name)
        self._narrate_room(name)

    def _spawn_room(self, name: str) -> None:
        start, end = self._room_span(name)
        for kind, path in ENEMY_CLASSES.items():
            for spot in LEVEL.of(kind):
                if start <= spot.tile_x < end:
                    self.enemies.append(_load(path)(self, spot.x, spot.feet_y))

    def _narrate_room(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "yalniz":
            self.say_player("line.ch10_rey_alone", "line.ch10_ardo_alone")
        elif name == "ders":
            self.say_player("line.ch10_rey_after", "line.ch10_ardo_after")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.false_silence.update(self.game, self)
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        self._update_parting()
        self._update_lure()
        self._update_choice()
        self._update_ally()
        self._update_trap()
        self._update_lesson()
        self._update_chests()
        self._check_exit()

    # --- Ara sahne 1: ayrilik ------------------------------------------------
    def _update_parting(self) -> None:
        if self.parting_played:
            return
        if self.player.body.center_x < SPLIT_TILE * TILE_SIZE:
            return
        self.parting_played = True
        from src.scenes.chapter10_cinematics import PartingCinematic
        self.scenes.push(PartingCinematic, character=self.character)

    # --- Yalan ---------------------------------------------------------------
    def _update_lure(self) -> None:
        """Catal odasina girince Yanki ust yolu isaretliyor."""
        if self.lure_shown or self.room != "catal":
            return
        self.lure_shown = True
        self.say(self._voice_line("line.ch10_echo_lure",
                                  "line.ch10_trace_lure"))
        self.game.play_sound("echo_reveal")

    def _voice_line(self, echo_key: str, trace_key: str):
        """Rey'de Yanki konusuyor, Ardo'da iz gosteriyor.

        Anahtarlar **duz dize** olarak cagirana veriliyor - f-string
        ile kurulani `test_lang.py` goremiyor.
        """
        from src.ui.dialogue import Line
        if self.character == "ardo":
            return Line("ardo", trace_key)
        return Line("echo", echo_key)

    def _update_choice(self) -> None:
        """Oyuncu hangi yolu sectı?

        Karar **bir kez** kaydediliyor: ust yola cikmak "guvendi",
        alt yoldan devam etmek "guvenmedi". Ikisi de gecerli ve ikisi
        de bolumun devamina cikiyor.
        """
        if self.choice or self.room != "catal":
            return
        row = int(self.player.body.feet[1]) // TILE_SIZE
        column = int(self.player.body.center_x) // TILE_SIZE
        if row <= UPPER_ROW + 1 and column > LURE_TILE[0]:
            self.choice = "followed"
            loyalty.followed(self.save_data)
        elif row >= LOWER_ROW - 1 and column > HONEST_TILE[0] + 4:
            self.choice = "ignored"
            loyalty.ignored(self.save_data)
            # **Gorunmez sayac** - oyuncuya hicbir sey soylenmiyor.
            # Yalnizca Yanki'nin tonu degisiyor, o kadar.
            self.say(self._voice_line("line.ch10_echo_ignored",
                                      "line.ch10_trace_ignored"))

    # --- Kalachev: tuzagi kiran ---------------------------------------------
    def _update_ally(self) -> None:
        """`docs/kalachev.md` 5: *"B10 Ayrilik - Rey yalniz kaldiktan
        sonra ilk kez tek basina belirir. **Tuzagi o kirar.**"*

        ## Kirmak, kurtarmak degil

        Oyuncu tuzaga basmadan **once** geliyor ve zemini kendisi
        cokertiyor. Yani gizli bir tehlike gorunur bir deliğe
        donusuyor: oyuncu artik uzerinden atlayacak, icine dusmeyecek.

        Son anda yetisip oyuncuyu cekmek de olabilirdi ama o bir
        **kurtarma** olurdu ve B16'nin isini (karsilikli kurtarma)
        onceden harcardi. Burada kimse kurtarilmiyor - biri yoldan bir
        seyi kaldiriyor ve gidiyor.

        ## Tuzak zaten uyariyordu

        Gicirti (`TRAP_CREAK_FRAMES`) yerinde duruyor: Kalachev
        gelmezse - ki gelmeyebilir, korku katmani kapaliysa muttefik
        de yok - oyuncu yine uyarilmis oluyor. Yeni davranis eskisini
        **bozmuyor**, onun yerine geciyor.
        """
        if self.trap_broken or self.trap_sprung or self.allies:
            return
        if self.room != "catal":
            return
        trap_x = ALLY_TRAP_COLUMN * TILE_SIZE
        gap = trap_x - self.player.body.center_x
        # Oyuncu tuzagin SOLUNDA ve yaklasiyor olmali. Sagindaysa
        # oyunu geriden izliyor demektir; o zaman gec kalmis olurduk.
        if not 0 < gap <= ALLY_TRIGGER_TILES * TILE_SIZE:
            return
        feet_y = (TRAP_ROW) * TILE_SIZE
        ally = self.summon_kalachev(trap_x, feet_y, stay=ALLY_STAY)
        if ally is None:
            return
        self._break_trap()

    def _break_trap(self) -> None:
        """Zemin **oyuncunun altinda degil**, ileride cokuyor."""
        self.trap_broken = True
        for column in TRAP_TILES:
            self.tilemap.set_tile(column, TRAP_ROW, EMPTY)
        x = ALLY_TRAP_COLUMN * TILE_SIZE
        y = TRAP_ROW * TILE_SIZE
        self.juice.explosion(x, y, ImpactWeight.FINISHER)
        self.particles.burst(x, y, 22, path="dust", speed=(0.8, 3.0))
        self.game.play_sound("echo_wall")
        self.show_toast(t("chapter10.trap_broken"), frames=180)

    def on_kalachev_arrived(self, ally) -> None:
        """Kamera bir an oraya bakiyor. Replik yok - tanisma B6'daydi."""
        self.camera.linger(40)

    def _update_trap(self) -> None:
        """Ust yolun ortasinda zemin cokuyor.

        Once **gicirdiyor** (`TRAP_CREAK_FRAMES`): uyarisiz bir tuzak
        haksizlik, uyarili bir tuzak ders. Oyuncu geri donebilirdi.
        """
        if self.trap_sprung or self.trap_broken or self.room != "catal":
            return
        column = int(self.player.body.center_x) // TILE_SIZE
        row = int(self.player.body.feet[1]) // TILE_SIZE
        on_trap = column in TRAP_TILES and abs(row - TRAP_ROW) <= 1
        if not on_trap:
            self.trap_creak = 0
            return
        self.trap_creak += 1
        if self.trap_creak == 1:
            self.game.play_sound("enemy_tell")
            self.show_toast(t("chapter10.creak"), frames=110)
        if self.trap_creak < TRAP_CREAK_FRAMES:
            return
        self._spring_trap()

    def _spring_trap(self) -> None:
        self.trap_sprung = True
        for column in TRAP_TILES:
            self.tilemap.set_tile(column, TRAP_ROW, EMPTY)
        x = self.player.body.center_x
        y = self.player.body.feet[1]
        self.juice.explosion(x, y, ImpactWeight.KILL)
        self.particles.burst(x, y, 24, path="dust", speed=(0.8, 3.0))
        self.game.play_sound("echo_wall")
        self.show_toast(t("chapter10.trap"), frames=200)
        # Tuzak **oldurmuyor**: dusus ve bir dovus. Bir yanlis secim
        # bolumu bastan oynatmamali.

    def _update_lesson(self) -> None:
        """Tuzaktan sonra Yanki konusuyor - ve **ozur dilemiyor.**"""
        if self.lesson_played or self.room != "ders":
            return
        self.lesson_played = True
        from src.scenes.chapter10_cinematics import LieCinematic
        self.scenes.push(LieCinematic, character=self.character,
                         followed=self.choice == "followed",
                         ignored=self.choice == "ignored",
                         sprung=self.trap_sprung)

    # --- Sandik ve cikis ----------------------------------------------------
    def _update_chests(self) -> None:
        for chest in self.chests:
            chest.update()
            if chest.opened:
                continue
            if not chest.rect.colliderect(self.player.body.rect):
                continue
            chest.open()
            self.earned_gold += chest.gold
            self.secret_found = True
            self.pickup_juice(gold=True)

    def _check_exit(self) -> None:
        exit_at = LEVEL.first("exit")
        if self.finished or exit_at is None:
            return
        if self.player.body.center_x < exit_at.x - 8:
            return
        self.finished = True
        self._end_chapter()

    def _end_chapter(self) -> None:
        self.game.play_sound("chapter_end")
        result = ChapterResult(
            chapter_key="chapter.parting",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 10
            data.chapter_name = "chapter.parting"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
        # Bolum 11'e baglaniyor.
        character = self.character

        def _continue() -> None:
            from src.scenes.chapter11 import Chapter11Scene
            self.scenes.set_root(Chapter11Scene, character=character)

        self.scenes.push(ChapterEndScene, result=result,
                         save_data=self.save_data,
                         on_continue=_continue)

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        self._draw_lure(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)

    def _draw_lure(self, surface: pygame.Surface, offset) -> None:
        """Yanki'nin isareti - **tanidik** gorsel dil.

        Kirilabilir duvarlarda sekiz bolumdur kullanilan camgobegi
        parilti. Yeni bir gosterge uydursaydik oyuncu supheye duserdi
        ve yalan ise yaramazdi.

        Secim yapildiktan sonra sonuyor: isaret bir davet, bir etiket
        degil.
        """
        if not self.lure_shown or self.choice or self.trap_sprung:
            return
        ox, oy = offset
        x = LURE_TILE[0] * TILE_SIZE - ox
        y = LURE_TILE[1] * TILE_SIZE - oy
        pulse = 0.5 + 0.5 * math.sin(self.frames * 0.08)
        base = palette.color("echo_bright" if self.character != "ardo"
                             else "bone")
        colour = tuple(int(c * pulse) for c in base)
        for index in range(4):
            surface.fill(colour, (x + index * 4, y + 6 - index, 2, 2))
        surface.fill(colour, (x, y - 4, 14, 1))

    def debug_lines(self) -> list[str]:
        return [f"oda {self.room}  secim={self.choice or '-'}"
                f"  tuzak={self.trap_sprung}"
                f"  sadakat={loyalty.read(self.save_data)}"]
