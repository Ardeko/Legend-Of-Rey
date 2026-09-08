"""Bolum 18 "Son" - Cagiran, susturma, kapanis.

`docs/yapi.md` B18: *"Yaratik, Yanki'yi kullanarak Cemo'nun sesiyle
konusur. Rey sesi susturmayi secer - sessizlikte, **yardimsiz**
savasir. Kazanir. Cemo kurtulur. Gun isigi."*

Korunan kurallar:

  * **Yanki acikken Cagiran OLMUYOR.** Bolumun tezi. Iki olum yolu da
    (`take_damage` ve `die`) geri cevriliyor - ilk surumde `die()`
    sahne kancasini cagirmayi unutuyordu ve susturma **hic
    acilmiyordu**, yani bolum bitirilemiyordu.
  * **Ilk diz cokuste susturma aciliyor.** Daha erken acmak karari
    anlamsizlastirirdi (oyuncu neyi biraktigini bilmez), daha gec
    acmak onu bir donguye hapsederdi.
  * **Susturmanin bedeli var**: vurulunca ve tus birakilinca ilerleme
    sifirlaniyor. Ve **geri alinamiyor**.
  * **Sustuktan sonra Cagiran olebiliyor** - yoksa bolum bitmezdi.
  * **Yem yalnizca Yanki acikken var.** Sustuktan sonra `call` bos
    donuyor ve bu goruluyor.
  * **Bolum bastan sona bitirilebiliyor.** Uctan uca oynanarak
    OLCULUYOR - finalin bitirilemez olmasi en pahali hata olurdu.
  * **Bolum sonu EKRANI yok** - final dogrudan kapanisa gidiyor.
  * **Kapanis dort bayragi okuyor** ve Ardo'nun mesafesi degisiyor.
  * Ara sahneler iki karakterde de **cizim dahil** calisiyor.

Calistir:
    python tests/test_chapter18.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA.** (08.09.2026)
#
# Sahneler `read_save()` ile kaydi yukluyor ve `_sync_abilities()` gibi
# yerler `write_save()` ile geri yaziyor - yani bu paketi calistirmak
# Arda'nin gercek ilerlemesini siliyordu. 55 altin ve secilmis balta
# boyle kayboldu; yedek dosyasi da ustune yazildigi icin
# kurtarilamadi.
#
# Bir test, oyuncunun verisine asla dokunmamali. Kayit dizini her
# calistirmada gecici bir klasore aliniyor.
import tempfile  # noqa: E402

os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

# Klasore **varsayilan bir kayit** tohumlaniyor. Bos birakilsaydi
# `read_save()` None donerdi ve sahnelerin `save_data`si None olurdu -
# oysa testler gercek bir kaydin varligina gore yazilmis (bayrak
# okuyor, bolum numarasi yaziyor). Amac oyuncunun dosyasindan
# kurtulmak, testlerin davranisini degistirmek degil.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.systems.save import SaveData as _SaveData  # noqa: E402
from src.systems.save import write_save as _write_save  # noqa: E402

_write_save(_SaveData())

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.combat.hitbox import Hitbox, Team  # noqa: E402
from src.config import (  # noqa: E402
    ECHO_TIER_CLEAR, ECHO_TIER_SILENT, PLAYER_RUN_SPEED, SILENCE_HOLD_FRAMES,
    TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.scenes import chapter18_cinematics as cine  # noqa: E402
from src.scenes.chapter18 import (
    PHASE_ALONE, PHASE_TAKEN, PHASE_TOGETHER, TAKEN_END,
    Chapter18Scene,
)
from src.scenes.ending import ALLY_DISTANCE, DawnCinematic  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402
from src.world.rooms.chapter18 import (  # noqa: E402
    ARENA_SEAL_COLUMN, FLOOR_TOP, LEVEL, ZONE_STARTS,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey", **flags) -> Chapter18Scene:
    base = {"ch15_ghost": True, "ch16_lifted": True,
            "ch16_gesture": "reach", "ch17_tidy": True}
    base.update(flags)
    write_save(SaveData(
        chapter=18, character=character,
        abilities=["sword", "dodge", "echo_sight", "echo_ask"], flags=base))
    game.scenes.set_root(Chapter18Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter18Scene)
    return scene


def step(game, scene, frames: int = 1) -> None:
    """Kare surer; acilan ara sahneyi kapatir."""
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        game.scenes.update()
        game.frame += 1
        if game.scenes.current is not scene and not scene.finished:
            game.scenes.pop()
            game.scenes._flush()


def walk_to_arena(game, scene) -> None:
    body = scene.player.body
    target = (ZONE_STARTS[2][1] + 5) * TILE_SIZE
    guard = 0
    while body.center_x < target and guard < 4000:
        body.set_feet(body.center_x + PLAYER_RUN_SPEED, body.feet[1])
        step(game, scene)
        guard += 1


def hit_boss(game, scene, damage: int = 40) -> None:
    # **Faz 2 vurularak gecilmiyor** (`docs/kalachev.md` 6): kontrol
    # kilitli, dovus yok, sahne kendi cetveliyle isliyor. Vurmaya
    # devam etseydik dongu 120 kez bosa doner ve "susturma acilmadi"
    # derdi - oysa acilmasi gereken yer fazin SONU.
    if scene.phase == PHASE_TAKEN:
        step(game, scene, 40)
        return
    scene.hitboxes.spawn(Hitbox(
        rect=scene.boss.body.rect.copy(), owner=scene.player,
        targets=Team.ENEMY, damage=damage, active_frames=2, knockback=0.0))
    step(game, scene, 4)


# --- 1. Bolumun tezi ★ --------------------------------------------------------
def test_caller_cannot_die_while_echo_is_open() -> None:
    """**Yanki acikken Cagiran olmuyor.** Finalin tek kurali."""
    print("\n--- Yanki acikken olmuyor ---")
    game = Game()
    try:
        scene = start(game)
        walk_to_arena(game, scene)
        check(scene.boss is not None, "arenada boss var")
        check(scene.arena_sealed, "arena muhurlendi")
        check(scene.boss.undying, "olmezlik ACIK - Yanki henuz susmadi")

        for _ in range(120):
            hit_boss(game, scene)
            if scene.boss.dead:
                break
        check(not scene.boss.dead,
              "120 vurusa ragmen OLMEDI", f"can {scene.boss.health}")
        check(scene.boss.rises > 0, "diz cokup kalkti",
              f"{scene.boss.rises} kez")
    finally:
        game.quit()


def test_player_and_boss_share_the_arena() -> None:
    """Tetikleyici muhurun gerisinde olsa da oyuncu iceri alinmali.

    Canli oynanis: Cagiran sagda, oyuncu solda, ortada bir sutun.
    """
    print("\n--- ayni oda ---")
    game = Game()
    try:
        scene = start(game)
        trigger = next(s for s in LEVEL.of("trigger")
                       if s.tile_x >= ZONE_STARTS[2][1])
        scene.player.body.set_feet(trigger.x, FLOOR_TOP * TILE_SIZE)
        scene._fire_trigger(trigger.tile_x)
        edge = (ARENA_SEAL_COLUMN + 1) * TILE_SIZE
        check(scene.arena_sealed, "muhur indi")
        check(scene.player.body.x >= edge, "oyuncu muhurun saginda",
              f"x={scene.player.body.x:.0f} edge={edge}")
        check(scene.boss.body.center_x >= edge, "boss ayni tarafta")
        check(not scene.tilemap.solid_overlap(scene.player.body.rect),
              "oyuncu duvara gomulmedi")
    finally:
        game.quit()


def test_both_death_paths_are_refused() -> None:
    """`die()` yolu da geri cevriliyor - ve **kancayi cagiriyor**.

    Ilk surumde `take_damage` ve `die()` ayri ayri yazilmisti ve
    `die()` sahne kancasini unutuyordu. `Actor` can sifira inince
    `die()` cagirdigi icin GERCEK yol oydu: sonuc, susturma hic
    acilmiyor ve bolum bitirilemiyordu. Uctan uca oynatilinca cikti.
    """
    print("\n--- iki olum yolu da kapali ---")
    game = Game()
    try:
        scene = start(game)
        walk_to_arena(game, scene)
        boss = scene.boss
        boss.rise_frames = 0
        before = boss.rises
        boss.health = 0
        boss.die()                      # dogrudan cagri
        check(not boss.dead, "`die()` geri cevrildi")
        check(boss.health >= 1, "can tabanda", str(boss.health))
        check(boss.rises == before + 1, "dirilis sayildi")
        # Ilk diz artik **faz 2'yi** basliyor (susturma onun sonunda
        # aciliyor). Olculen sey degismedi: `die()` sahne kancasini
        # cagiriyor mu.
        check(scene.phase == PHASE_TAKEN,
              "ve SAHNE KANCASI calisti - faz 2 basladi",
              str(scene.phase))
    finally:
        game.quit()


def test_silence_unlocks_on_first_kneel() -> None:
    """Susturma **ilk diz cokusun ardindan** aciliyor, once degil.

    Ilk diz once faz 2'yi baslatiyor (Kalachev'in olumu, yoldasin
    disarida kalmasi); susturma o fazin sonunda aciliyor. Sira
    bilincli: "yardimsiz savas" teklifi ancak yardim gittikten sonra
    bir teklif.
    """
    print("\n--- susturma zamanlamasi ---")
    game = Game()
    try:
        scene = start(game)
        check(not scene.silence.unlocked, "bolum basinda KAPALI")
        walk_to_arena(game, scene)
        check(not scene.silence.unlocked,
              "boss cikinca da hala kapali - once sorunu gormeli")
        for _ in range(120):
            hit_boss(game, scene)
            if scene.silence.unlocked:
                break
        check(scene.silence.unlocked, "ilk diz cokusun ARDINDAN acildi")
        check(scene.phase == PHASE_ALONE,
              "cunku faz 2 bitti - artik yalniz", str(scene.phase))
        check(scene.boss.rises >= 1, "cunku diz cokmustu")
    finally:
        game.quit()


# --- 2. Susturma ★ ------------------------------------------------------------
def test_silencing_works_and_costs() -> None:
    """Basili tut, ses gitsin. Ve bedeli var."""
    print("\n--- susturma ---")
    game = Game()
    try:
        scene = start(game)
        walk_to_arena(game, scene)
        scene.silence.unlocked = True
        check(scene.echo.tier == ECHO_TIER_CLEAR, "Yanki basta BERRAK",
              str(scene.echo.tier))

        # Vurulunca ilerleme sifirlaniyor.
        for _ in range(SILENCE_HOLD_FRAMES // 2):
            scene.silence.update(scene.echo, True)
        half = scene.silence.hold
        check(half > 0, "ilerleme birikiyor", str(half))
        scene.silence.update(scene.echo, True, hurt=True)
        check(scene.silence.hold == 0, "vurulunca SIFIR - bedel gercek")

        # Tusu birakinca da.
        for _ in range(SILENCE_HOLD_FRAMES // 2):
            scene.silence.update(scene.echo, True)
        scene.silence.update(scene.echo, False)
        check(scene.silence.hold == 0, "tusu birakinca SIFIR")

        # Ve tamamlaniyor.
        done = False
        for _ in range(SILENCE_HOLD_FRAMES + 4):
            if scene.silence.update(scene.echo, True):
                done = True
                break
        check(done, "basili tutunca tamamlandi")
        check(scene.echo.tier == ECHO_TIER_SILENT, "Yanki SUSTU",
              str(scene.echo.tier))
        check(scene.silence.done, "karar kayitli")
    finally:
        game.quit()


def test_silence_is_irreversible() -> None:
    """Geri alinabilseydi karar bir dugmeye donerdi."""
    print("\n--- susturma geri alinamaz ---")
    game = Game()
    try:
        scene = start(game)
        scene.silence.unlocked = True
        for _ in range(SILENCE_HOLD_FRAMES + 4):
            scene.silence.update(scene.echo, True)
        check(scene.silence.done, "susturuldu")
        for _ in range(300):
            scene.silence.update(scene.echo, True)
        check(scene.echo.tier == ECHO_TIER_SILENT, "300 kare sonra da SESSIZ")
        check(scene.silence.done, "karar geri alinmadi")
    finally:
        game.quit()


def test_real_key_silences() -> None:
    """Gercek tusla - sahnenin ECHO'yu susturmaya bagladigi olculuyor."""
    print("\n--- gercek tus susturuyor ---")
    game = Game()
    try:
        scene = start(game)
        walk_to_arena(game, scene)
        scene.silence.unlocked = True
        game.input.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_k))
        step(game, scene, SILENCE_HOLD_FRAMES + 20)
        check(scene.silence.done, "[K] basili tutmak sustdurdu")
        check(not scene.boss.undying, "ve olmezlik KALKTI")
    finally:
        game.quit()


# --- 3. Sustuktan sonra ★ -----------------------------------------------------
def test_caller_dies_after_silence() -> None:
    """Sustuktan sonra olebiliyor - yoksa bolum bitmezdi."""
    print("\n--- sustuktan sonra olebiliyor ---")
    game = Game()
    try:
        scene = start(game)
        walk_to_arena(game, scene)
        scene.silence.unlocked = True
        for _ in range(SILENCE_HOLD_FRAMES + 4):
            scene.silence.update(scene.echo, True)
        check(not scene.boss.undying, "olmezlik kalkti")
        for _ in range(120):
            hit_boss(game, scene)
            if scene.boss.dead:
                break
        check(scene.boss.dead, "Cagiran OLDU")
        check(scene.boss_defeated, "sahne bunu gordu")
        check(not scene.arena_sealed, "arena acildi")
    finally:
        game.quit()


def test_lures_only_exist_while_echo_is_open() -> None:
    """*"Cemo'nun sesiyle konusur."* Ama yalnizca dinlenirken."""
    print("\n--- yem yalnizca Yanki acikken ---")
    game = Game()
    try:
        scene = start(game)
        walk_to_arena(game, scene)
        boss = scene.boss
        boss.move = "call"
        boss._spawn_attack()
        check(len(boss.lures) == 1, "Yanki acikken yem CIKTI",
              str(len(boss.lures)))
        check(scene.calls == 1, "sahne cagriyi saydı")

        scene.silence.unlocked = True
        for _ in range(SILENCE_HOLD_FRAMES + 4):
            scene.silence.update(scene.echo, True)
        boss._update_lures()
        check(not boss.lures, "sustuktan sonra var olanlar KAYBOLDU")
        boss._spawn_attack()
        check(not boss.lures, "ve yeni cagri BOS donuyor - kimse duymuyor")
    finally:
        game.quit()


# --- 4. Bolum bitirilebiliyor mu ★★ -------------------------------------------
def test_chapter_can_be_finished() -> None:
    """En pahali hata finalin bitirilemez olmasi olurdu. **Olculuyor.**"""
    print("\n--- bolum bastan sona bitiriliyor ---")
    game = Game()
    try:
        scene = start(game)
        walk_to_arena(game, scene)

        # 1) Yanki acikken dov - olmuyor, susturma aciliyor.
        for _ in range(120):
            hit_boss(game, scene)
            if scene.silence.unlocked:
                break
        check(scene.silence.unlocked, "susturma acildi")

        # 2) Sustur.
        game.input.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_k))
        step(game, scene, SILENCE_HOLD_FRAMES + 20)
        check(scene.silence.done, "susturuldu")

        # 3) Oldur.
        for _ in range(160):
            hit_boss(game, scene)
            if scene.boss.dead:
                break
        check(scene.boss.dead, "Cagiran yenildi")

        # 4) Cikisa yuru.
        body = scene.player.body
        exit_at = LEVEL.first("exit")
        guard = 0
        while body.center_x < exit_at.x and not scene.finished and guard < 4000:
            body.set_feet(body.center_x + PLAYER_RUN_SPEED, body.feet[1])
            step(game, scene)
            guard += 1
        check(scene.finished, "BOLUM BITTI")
        game.scenes._flush()
        step(game, scene, 90)
        check(isinstance(game.scenes.current, DawnCinematic),
              "ve kapanis basladi",
              type(game.scenes.current).__name__)
    finally:
        game.quit()


def test_no_chapter_end_screen() -> None:
    """Final dogrudan kapanisa gidiyor - istatistik paneli YOK.

    Oyunun son dovusunden cikip bir sayi tablosu gormek anin
    agirligini alirdi. Sayilar jenerige tasindi.
    """
    print("\n--- bolum sonu ekrani yok ---")
    import inspect
    source = inspect.getsource(Chapter18Scene)
    check("ChapterEndScene" not in source,
          "bolum sonu ekrani acilmiyor")
    check("DawnCinematic" in source, "dogrudan kapanis aciliyor")


# --- 5. Kapanis ★ -------------------------------------------------------------
def test_ending_reads_the_four_flags() -> None:
    """Dort bayrak kapanisi **sekillendiriyor**, kilitlemiyor."""
    print("\n--- kapanis bayraklari okuyor ---")
    for key, expected in ALLY_DISTANCE.items():
        game = Game()
        try:
            game.scenes.set_root(DawnCinematic, transition=False,
                                 character="rey", ghost=True, lifted=True,
                                 gesture_key=key, tidy=True, clean=True)
            game.scenes._flush()
            scene = game.scenes.current
            ally = scene.actor("ally")
            player = scene.actor("player")
            check(abs((ally.x - player.x) - expected) < 0.5,
                  f"'{key}' jesti Ardo'yu {expected:.0f} px oteye koyuyor",
                  f"{ally.x - player.x:.0f}")
        finally:
            game.quit()

    game = Game()
    try:
        game.scenes.set_root(DawnCinematic, transition=False, character="rey",
                             ghost=False, lifted=False, gesture_key="nod",
                             tidy=False, clean=False)
        game.scenes._flush()
        scene = game.scenes.current
        check(not scene.ghost and not scene.lifted,
              "bayraksiz kapanis da acilyor - hicbiri KILIT degil")
    finally:
        game.quit()


def test_cinematics_play_for_both() -> None:
    """Bes sahne, iki karakter, **cizim dahil**."""
    print("\n--- ara sahneler (iki karakter, cizim dahil) ---")
    scenes = (cine.DescentCinematic, cine.VoiceCinematic,
              cine.NameCinematic, cine.SilenceCinematic, DawnCinematic)
    for cls in scenes:
        for character in ("rey", "ardo"):
            game = Game()
            try:
                game.scenes.set_root(cls, transition=False,
                                     character=character)
                game.scenes._flush()
                for _ in range(240):
                    game.input.begin_frame()
                    game.input.end_frame()
                    game.scenes.update()
                    game.canvas.fill((0, 0, 0, 255))
                    game.scenes.draw(game.canvas)
                    game.frame += 1
                check(True, f"{cls.__name__} ({character}) cokmeden oynuyor")
            except Exception as exc:       # noqa: BLE001 - test raporluyor
                check(False, f"{cls.__name__} ({character})",
                      f"{type(exc).__name__}: {exc}")
            finally:
                game.quit()


def test_chapter_shape() -> None:
    print("\n--- bolum sekli ---")
    check(len(ZONE_STARTS) == 3, "uc bolge", str(len(ZONE_STARTS)))
    check(len(LEVEL.of("trigger")) == 3, "uc ara sahne tetikleyicisi")
    kinds = {p.kind for p in LEVEL.placements}
    check("exit" in kinds, "cikis var")
    # Final yalniz oynaniyor - `docs/yapi.md` "yardimsiz".
    enemies = [p for p in LEVEL.placements
               if p.kind not in ("player", "exit", "trigger")]
    check(not enemies, "haritada dusman YOK - tek dusman Cagiran, sahne koyuyor")


# --- Uc faz (docs/kalachev.md 6) ★ -------------------------------------------
def test_three_phases() -> None:
    """Belgenin finali: **dorduniz -> aliniyor -> yalniz.**

    Olculen sey bir anlati degil bir zincir: her fazin bir oncekinden
    ne aldigi. Faz 2 senaryolu ve kacinilmaz oldugu icin uctan uca
    calistirilabiliyor - oyuncunun becerisine bagli bir yeri yok.
    """
    print()
    print("--- uc faz ---")
    from src.entities.kalachev import DEATH_FLAG
    game = Game()
    try:
        scene = start(game)
        # FAZ 1: dorduniz birlikte.
        check(scene.phase == PHASE_TOGETHER, "faz 1 ile basliyor")
        check(scene.companion is not None,
              "yoldas YANINDA - B17'yi ikisi bitirdi")
        walk_to_arena(game, scene)
        check(scene.kalachev is not None, "arenada Kalachev de var")
        check(scene.kalachev in scene.allies, "muttefik listesinde")
        ahead = scene.kalachev.body.center_x > scene.player.body.center_x
        check(ahead, "oyuncunun ONUNDE duruyor - hep once o girer")
        check(not scene.boss_defeated, "Cemo kafeste, dovus basliyor")

        # FAZ 2: ilk diz her seyi aliyor.
        boss = scene.boss
        boss.rise_frames = 0
        boss.health = 0
        boss.die()
        check(scene.phase == PHASE_TAKEN, "ilk diz faz 2'yi baslatti")
        check(boss.rise_frames > TAKEN_END,
              "yaratik cetvel boyunca diz cokuk KALIYOR",
              str(boss.rise_frames))

        saw_lure = False
        saw_gate = False
        for _ in range(TAKEN_END + 30):
            scene.update()
            saw_lure = saw_lure or bool(boss.lures)
            saw_gate = saw_gate or scene.gate_open
        check(saw_lure, "Cemo'nun sesi bir YEM olarak belirdi")
        check(saw_gate, "muhur acildi - yaratik onlari AYIRDI")
        check(scene.kalachev.dead, "Kalachev OLDU")
        check(not scene.kalachev.gone,
              "govdesi sahnede kaliyor - 'gitti mi, oldu mu' sorusu yok")
        check(scene.companion is None, "yoldas disarida kaldi")
        check(scene.arena_sealed, "kapi tekrar indi")
        check(scene.save_data.flags.get(DEATH_FLAG),
              "olum KAYDA yazildi - kapanistaki bakis buna bagli")

        # FAZ 3: yalniz, ve susturma ancak SIMDI acildi.
        check(scene.phase == PHASE_ALONE, "faz 3 - yalniz")
        check(scene.silence.unlocked,
              "susturma ancak yardim gittikten SONRA acildi")
        check(scene.player.control_locked == 0, "kontrol geri geldi")
    finally:
        game.quit()


def test_phase_two_takes_no_skill() -> None:
    """Faz 2 **kacinilmaz.** Oyuncu hicbir sey yapmasa da bitiyor.

    Bir kacis yolu olsaydi iyi oynayan oyuncu Kalachev'i kurtarabilir
    sanirdi ve olum bir ceza gibi okunurdu - oysa bir BEDEL.
    """
    print()
    print("--- faz 2 kacinilmaz ---")
    game = Game()
    try:
        scene = start(game)
        walk_to_arena(game, scene)
        boss = scene.boss
        boss.rise_frames = 0
        boss.health = 0
        boss.die()
        locked = 0
        for _ in range(TAKEN_END):
            scene.update()
            if scene.player.control_locked > 0:
                locked += 1
        check(locked > TAKEN_END - 10,
              "kontrol butun faz boyunca kilitli", f"{locked}/{TAKEN_END}")
        scene.update()
        check(scene.phase == PHASE_ALONE, "faz kendiliginden bitti")
    finally:
        game.quit()


def main() -> int:
    test_caller_cannot_die_while_echo_is_open()
    test_player_and_boss_share_the_arena()
    test_both_death_paths_are_refused()
    test_three_phases()
    test_phase_two_takes_no_skill()
    test_silence_unlocks_on_first_kneel()
    test_silencing_works_and_costs()
    test_silence_is_irreversible()
    test_real_key_silences()
    test_caller_dies_after_silence()
    test_lures_only_exist_while_echo_is_open()
    test_chapter_can_be_finished()
    test_no_chapter_end_screen()
    test_ending_reads_the_four_flags()
    test_cinematics_play_for_both()
    test_chapter_shape()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Bolum 18 tutarli - ses susmadan yaratik olmuyor, sustuktan "
          "sonra oluyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
