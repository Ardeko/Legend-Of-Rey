"""Epilog "Eve Donus" - kuyunun dibi, sabah koyu, ates basi, jenerik.

`docs/yapi.md` Epilog, `DEVIR.md` 24.09.2026. Arda: *"koye hep beraber
donduklari bir sinematik. belki oraya da bir kisa oynanis veya oyuncuyu
odullendirecek bir sahne."*

Korunan kurallar:

  * **Oyun bitince kayit DISKE yaziliyor.** B18'in `_end_game`'i
    "finished"i yalnizca bellekte isaretliyordu; DEVAM ET oyunu bitiren
    oyuncuyu son boss'a geri indiriyordu.
  * **Zincir kopmuyor:** kapanis -> kuyu -> yukari -> koy -> ates ->
    jenerik -> ana menu. Uctan uca OYNANARAK olculuyor.
  * **"Seslen" Jet'i cagiriyor** - B15'in sozu: *"adimi soylemen
    yeter; burada olacagim."* Ip Jet cevap verdigi AN geriliyor.
  * **Konusmayi kapatan E ayni karede yeni bir sey baslatmiyor.** E hem
    repligi ilerletiyor hem etkilesiyor.
  * **Can calinmadan koy bos; calininca koyluler kapidan cikiyor.**
  * **Koylunun sozu kayittan:** dusus sayisi, B15 hayaleti, karakter.
  * **Eve can calinmadan varilirsa bitis yok** - Cemo cani hatirlatiyor.
  * **Resmin onune gecilmiyor** - bitisin goruntusu o resim.
  * **Yanki epilogda yok**, yoldasa komut yok (ogretici kart da yok).
  * **Kadeh yalnizca Kalachev olduyse;** jenerik panelinde aktor yok.
  * **Oyun sonrasi koy:** bitmis kayitta DEVAM ET buraya getiriyor.
  * Sahneler iki karakterde de **cizim dahil** calisiyor.

Calistir:
    python tests/test_epilogue.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA.** (08.09.2026) Sahneler kaydi okuyup
# yaziyor; kayit dizini her calistirmada gecici bir klasore aliniyor.
import tempfile  # noqa: E402

os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.config import INTERNAL_WIDTH, PLAYER_RUN_SPEED  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.entities import villager as villager_mod  # noqa: E402
from src.entities.kalachev import DEATH_FLAG  # noqa: E402
from src.scenes import epilogue_village as village_mod  # noqa: E402
from src.scenes.chapter18 import Chapter18Scene  # noqa: E402
from src.scenes.ending import DawnCinematic  # noqa: E402
from src.scenes.epilogue_cinematics import HomecomingFireCinematic  # noqa: E402
from src.scenes.epilogue_shaft import GATHER_FRAMES, EpilogueShaftScene  # noqa: E402
from src.scenes.epilogue_village import (  # noqa: E402
    HOME_REACH, EpilogueVillageScene,
)
from src.scenes.vertical_journey import (  # noqa: E402
    VerticalJourneyScene, continue_kwargs,
)
from src.systems.homecoming import (  # noqa: E402
    EPILOGUE_FLAG, HOMECOMING_CHAPTER_NAME, KALACHEV_DEATH_FLAG, Homecoming,
)
from src.systems.save import SaveData, read_save, write_save  # noqa: E402
from src.ui.dialogue import Dialogue  # noqa: E402
from src.ui.menu import MainMenuScene  # noqa: E402

failures: list[str] = []

# Gercek bir kayitta B1-B9'da gorulmus ipuclari. Bunlar olmadan ilk
# replikte "[Enter] devam" ipucu cikiyor - oyuncunun gormeyecegi bir sey.
SEEN_HINTS = {"hint_dialogue": True, "hint_bell": True}


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


# --- Yardimcilar ----------------------------------------------------------------
def seed_save(character: str = "rey", deaths: int = 7, **flags) -> None:
    base = {"ch15_ghost": True, "ch16_lifted": True, "ch16_gesture": "reach",
            "ch17_tidy": True, "ch18_clean": True, DEATH_FLAG: True,
            "finished": True, **SEEN_HINTS}
    base.update(flags)
    write_save(SaveData(chapter=18, character=character, deaths=deaths,
                        abilities=["sword", "dodge"], flags=base))


def frame(game, keys_down=(), keys_up=(), draw: bool = False) -> None:
    game.input.begin_frame()
    for key in keys_down:
        game.input.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
    for key in keys_up:
        game.input.handle_event(pygame.event.Event(pygame.KEYUP, key=key))
    game.input.end_frame()
    game.scenes.update()
    game.scenes._flush()
    if draw:
        game.canvas.fill((0, 0, 0, 255))
        game.scenes.draw(game.canvas)
    game.frame += 1


def tap(game, key: int) -> None:
    frame(game, keys_down=(key,))
    frame(game, keys_up=(key,))


def run(game, frames: int) -> None:
    for _ in range(frames):
        frame(game)


def wait_scene(game, cls, limit: int = 180) -> bool:
    """Gecis (kararma) ortasinda sahne degisiyor - birkac kare surer."""
    for _ in range(limit):
        if isinstance(game.scenes.current, cls):
            return True
        frame(game)
    return isinstance(game.scenes.current, cls)


def open_scene(game, cls, **kwargs):
    game.scenes.set_root(cls, transition=False, **kwargs)
    game.scenes._flush()
    return game.scenes.current


def dialogue_ready(scene) -> bool:
    dialogue = getattr(scene, "dialogue", None)
    return (dialogue is not None and dialogue.current is not None
            and dialogue.complete and dialogue.lock <= 0)


def finish_dialogue(game, scene, limit: int = 3000) -> list[str]:
    """Replikleri Enter ile gecir; gorulen anahtarlari dondur."""
    seen: list[str] = []
    for _ in range(limit):
        if game.scenes.current is not scene or scene.dialogue.done:
            break
        line = scene.dialogue.current
        if line is not None and (not seen or seen[-1] != line.key):
            seen.append(line.key)
        if dialogue_ready(scene):
            tap(game, pygame.K_RETURN)
        else:
            frame(game)
    return seen


def play_until(game, cls, limit: int = 6000) -> list[str]:
    """Enter'la ilerleyerek `cls` sahnesi acilana kadar oyna."""
    seen: list[str] = []
    for _ in range(limit):
        scene = game.scenes.current
        if isinstance(scene, cls):
            break
        dialogue = getattr(scene, "dialogue", None)
        line = dialogue.current if dialogue is not None else None
        if line is not None and (not seen or seen[-1] != line.key):
            seen.append(line.key)
        if dialogue_ready(scene):
            tap(game, pygame.K_RETURN)
        else:
            frame(game)
    return seen


def teleport(game, scene, x: float, settle: int = 4) -> None:
    body = scene.player.body
    body.set_feet(x, body.feet[1])
    run(game, settle)


def arrive(game, character: str = "rey", **kwargs) -> EpilogueVillageScene:
    """Koye gir, Jet'in karsilamasini gecir."""
    scene = open_scene(game, EpilogueVillageScene, character=character,
                       **kwargs)
    run(game, village_mod.ARRIVAL_FRAME + 2)
    finish_dialogue(game, scene)
    return scene


def ring_bell(game, scene) -> None:
    teleport(game, scene, scene.bell.rect.centerx + 18)
    finish_dialogue(game, scene)           # "cani kendi sesimle"
    tap(game, pygame.K_g)
    run(game, 30)


# --- 1. Kayit ★ -----------------------------------------------------------------
def test_end_game_writes_to_disk() -> None:
    """B18 bitince "finished" **diskte**. Eskiden yalnizca bellekteydi."""
    print("\n--- B18 sonu kaydi diske yaziyor ---")
    game = Game()
    try:
        seed_save("rey", finished=False)
        scene = open_scene(game, Chapter18Scene, character="rey")
        scene._end_game()
        data, _status = read_save()
        check(bool(data and data.flags.get("finished")),
              "finished diske yazildi")
        check(data is not None and "ch18_clean" in data.flags,
              "ch18_clean diske yazildi (jenerik okuyor)")
        check(wait_scene(game, DawnCinematic),
              "ve kapanis acildi", type(game.scenes.current).__name__)
    finally:
        game.quit()


def test_continue_after_finish() -> None:
    """Bitmis kayitta DEVAM ET koye **cikiyor**, bitmemiste bolume iniyor."""
    print("\n--- DEVAM ET: bitmis kayit koye ---")
    done = continue_kwargs(SaveData(chapter=18, character="ardo",
                                    flags={"finished": True}))
    check(done.get("direction") == "up" and done.get("variant") == "dawn",
          "bitmis kayit: safakta yukari")
    check(done.get("next_scene") is EpilogueVillageScene,
          "varis sabah koyu")
    extra = done.get("next_kwargs") or {}
    check(extra.get("postgame") is True and extra.get("character") == "ardo",
          "oyun sonrasi modu, karakter korunuyor")
    open_run = continue_kwargs(SaveData(chapter=7, character="rey"))
    check(open_run == {"direction": "down", "chapter": 7, "character": "rey"},
          "bitmemis kayit: eskisi gibi bolume iniyor", str(open_run))


def test_flags_agree() -> None:
    """Kalachev bayragi iki yerde ayni dize - biri degisirse kadeh kaybolur."""
    print("\n--- bayraklar ayni ---")
    check(KALACHEV_DEATH_FLAG == DEATH_FLAG,
          "homecoming ve kalachev ayni olum bayragini okuyor")


# --- 2. Zincir ★★ ---------------------------------------------------------------
def test_chain_end_to_end() -> None:
    """Kapanistan ana menuye - **oynanarak**. Kopan tek halka epilogu siler."""
    for character in ("rey", "ardo"):
        print(f"\n--- zincir uctan uca ({character}) ---")
        game = Game()
        try:
            seed_save(character)
            scene = open_scene(game, DawnCinematic, character=character,
                               ghost=True, lifted=True, gesture_key="reach",
                               tidy=True, clean=True, kalachev=True)
            seen = play_until(game, EpilogueShaftScene)
            check("line.ch18_cemo_dawn" in seen,
                  "kolyede Cemo soruyor ('Iki kere dusundu mu?')")
            check(isinstance(game.scenes.current, EpilogueShaftScene),
                  "kapanis -> kuyunun dibi")

            shaft = game.scenes.current
            run(game, 50)
            finish_dialogue(game, shaft)
            teleport(game, shaft, shaft.rope_x - 4)
            tap(game, pygame.K_e)
            play_until(game, VerticalJourneyScene)
            journey = game.scenes.current
            check(isinstance(journey, VerticalJourneyScene)
                  and journey.variant == "dawn", "kuyu -> safakta yukari")
            play_until(game, EpilogueVillageScene)
            village = game.scenes.current
            check(isinstance(village, EpilogueVillageScene)
                  and not village.postgame, "yolculuk -> sabah koyu")

            run(game, village_mod.ARRIVAL_FRAME + 2)
            finish_dialogue(game, village)
            ring_bell(game, village)
            finish_dialogue(game, village)
            teleport(game, village, village.home_door_x + 10)
            play_until(game, HomecomingFireCinematic)
            check(isinstance(game.scenes.current, HomecomingFireCinematic),
                  "koy -> ates basi")
            data, _status = read_save()
            check(bool(data and data.flags.get(EPILOGUE_FLAG)),
                  "epilog kayda yazildi")
            check(bool(data and data.chapter_name == HOMECOMING_CHAPTER_NAME),
                  "yuvada bolum adi 'Eve Donus'")
            play_until(game, MainMenuScene, limit=8000)
            check(isinstance(game.scenes.current, MainMenuScene),
                  "ates -> jenerik -> ana menu")
        finally:
            game.quit()


# --- 3. Kuyunun dibi ------------------------------------------------------------
def test_call_reaches_jet() -> None:
    """Ipte "Seslen" -> Jet cevap veriyor, ip o AN geriliyor, sonra yukari."""
    print("\n--- ipte seslen ---")
    game = Game()
    try:
        seed_save("rey")
        scene = open_scene(game, EpilogueShaftScene, character="rey")
        check(scene.echo is None and scene.tracking is None,
              "Yanki ve Iz Surme epilogda yok")
        run(game, 50)
        finish_dialogue(game, scene)
        tap(game, pygame.K_e)
        check(not scene.called, "iple arasi uzakken E hicbir sey yapmiyor")

        teleport(game, scene, scene.rope_x - 4)
        check(scene.prompts.active("rope"), "ipin dibinde 'Seslen' beliriyor")
        tap(game, pygame.K_e)
        check(scene.called, "E ile seslenildi")
        tug_at_answer = -1.0
        for _ in range(1500):
            line = scene.dialogue.current
            if line is not None and line.key == "line.epi_jet_answer":
                tug_at_answer = scene.tug
                break
            if dialogue_ready(scene):
                tap(game, pygame.K_RETURN)
            else:
                frame(game)
        check(tug_at_answer > 0.8, "Jet cevap verirken ip gerili",
              f"{tug_at_answer:.2f}")
        finish_dialogue(game, scene)
        run(game, GATHER_FRAMES + 5)
        wait_scene(game, VerticalJourneyScene)
        current = game.scenes.current
        check(isinstance(current, VerticalJourneyScene)
              and current.next_scene is EpilogueVillageScene,
              "toplanma bitince safak yolculugu, varis koy")
    finally:
        game.quit()


def test_keeper_last_candle() -> None:
    """Mum Bekcisi son mumunu sonduruyor - B12'deki sorunun cevabi.

    B3'te bes mum, her gorunuste bir eksik. Ardo B12'de sordu:
    *"Sonuncusunda ne olacak?"* Burada: tek mumuyla oturuyor, oyuncu
    yaklasinca sonduruyor ve kayboluyor. O an bitmeden Jet'e seslenilmiyor
    - konusmalar birbirinin ustune yazmasin.
    """
    for character in ("rey", "ardo"):
        print(f"\n--- Mum Bekcisi'nin son mumu ({character}) ---")
        game = Game()
        try:
            seed_save(character)
            scene = open_scene(game, EpilogueShaftScene, character=character)
            run(game, 50)
            finish_dialogue(game, scene)
            check(scene.keeper.lit == 1, "tek mum yaniyor")
            teleport(game, scene, scene.keeper.x - 20)
            line = scene.dialogue.current
            expected = ("line.epi_ardo_keeper" if character == "ardo"
                        else "line.epi_rey_keeper")
            check(line is not None and line.key == expected,
                  "yaklasinca son mumu fark ediyor", line and line.key)
            finish_dialogue(game, scene)
            teleport(game, scene, scene.rope_x - 4)
            check(not scene.prompts.active("rope"),
                  "bekci kaybolmadan 'Seslen' cikmiyor")
            for _ in range(300):
                frame(game)
                if scene.keeper_state == "gone":
                    break
            check(scene.keeper.lit == 0 and scene.keeper.fade == 0.0,
                  "son mumu sondurdu ve karanliga karisti")
            keys = [item.key for item in scene.dialogue.lines]
            check(bool(keys) and keys[0] == "line.epi_cemo_keeper",
                  "Cemo nereye gittigini soruyor", str(keys))
            finish_dialogue(game, scene)
            run(game, 3)
            check(scene.prompts.active("rope"), "sonra 'Seslen' beliriyor")
        finally:
            game.quit()


def test_closing_press_does_not_call() -> None:
    """Cemo'nun repligini kapatan E ayni karede Jet'e seslenmiyor."""
    print("\n--- konusmayi kapatan E seslenmiyor ---")
    game = Game()
    try:
        seed_save("rey")
        scene = open_scene(game, EpilogueShaftScene, character="rey")
        teleport(game, scene, scene.rope_x - 4, settle=1)
        for _ in range(400):
            if scene.dialogue.current is not None and dialogue_ready(scene):
                break
            frame(game)
        check(scene.dialogue.current is not None,
              "Cemo isigi gordu, replik acik ve oyuncu ipin dibinde")
        tap(game, pygame.K_e)
        check(scene.dialogue.done and not scene.called,
              "E replik kapatti ama seslenmedi")
        run(game, 2)
        tap(game, pygame.K_e)
        check(scene.called, "ikinci E seslendi")
    finally:
        game.quit()


# --- 4. Sabah koyu --------------------------------------------------------------
def test_bell_brings_the_village_out() -> None:
    """Can calinmadan koy bos; calininca sirayla, en yakin kapi once."""
    print("\n--- can ve koyluler ---")
    game = Game()
    try:
        seed_save("rey")
        scene = arrive(game)
        check(scene.echo is None and not scene.companion_orders,
              "Yanki yok, yoldasa komut yok")
        check(all(v.hidden for v in scene.villagers),
              "can calinmadan kimse disarida degil")
        ring_bell(game, scene)
        check(scene.bell_rung, "Rezonans cani caldi")
        emerging = [v for v in scene.villagers
                    if v.state == villager_mod.EMERGE]
        check(len(emerging) == len(scene.villagers),
              "butun kapilar aciliyor", f"{len(emerging)}")
        order = sorted(scene.villagers, key=lambda v: v.delay)
        distances = [abs(v.door_x - scene.bell.rect.centerx) for v in order]
        check(distances == sorted(distances),
              "cana en yakin kapi once aciliyor")
        finish_dialogue(game, scene)
        run(game, village_mod.EMERGE_FIRST
            + village_mod.EMERGE_STEP * len(scene.villagers) + 200)
        check(all(v.greeting for v in scene.villagers),
              "hepsi disarida ve oyuncuya donuk")
    finally:
        game.quit()


def test_villager_lines_follow_the_save() -> None:
    """Koylunun sozu oyuncunun **gercek** yolculugundan."""
    print("\n--- koylu replikleri kayittan ---")
    game = Game()
    try:
        seed_save("rey")
        cases = (
            (Homecoming(character="rey", deaths=7, ghost=True), "rey"),
            (Homecoming(character="ardo", deaths=0, ghost=False), "ardo"),
        )
        for home, name in cases:
            scene = open_scene(game, EpilogueVillageScene, character=name,
                               homecoming=home)
            falls = scene.lines_for("falls")
            rooster = scene.lines_for("rooster")
            elder = scene.lines_for("elder")
            inn = scene.lines_for("inn")
            if home.deaths:
                box = Dialogue()
                box.start(falls)
                check(falls[0].key == "line.epi_villager_falls"
                      and "7" in box.full_text
                      and "{count}" not in box.full_text,
                      f"{name}: 7 dusus sayiyla soyleniyor")
            else:
                check(falls[0].key == "line.epi_villager_nofall",
                      f"{name}: hic dusmeyene ayri soz")
            check(rooster[0].key == ("line.epi_villager_ghost" if home.ghost
                                     else "line.epi_villager_rooster"),
                  f"{name}: B15 hayaleti horoz sozunu seciyor")
            check(elder[0].key == ("line.epi_villager_stranger" if home.ardo
                                   else "line.epi_villager_name"),
                  f"{name}: yasli karaktere gore konusuyor")
            check([line.speaker for line in inn]
                  == ["innkeeper", "innkeeper", "ardo"],
                  f"{name}: hanci Kalachev'in notunu okuyor, Ardo kadeh kaldiriyor")
    finally:
        game.quit()


def test_home_waits_for_the_bell() -> None:
    """Can calinmadan eve varmak bitirmiyor - Cemo cani hatirlatiyor."""
    print("\n--- ev cani bekliyor ---")
    game = Game()
    try:
        seed_save("rey")
        scene = arrive(game)
        teleport(game, scene, scene.home_door_x + 10)
        seen = finish_dialogue(game, scene)
        check("line.epi_cemo_bellhint" in seen, "Cemo cani hatirlatiyor")
        check(not scene.drawing_state and not scene.finished,
              "resim ve bitis baslamadi")
    finally:
        game.quit()


def test_drawing_keeps_the_player_back() -> None:
    """Cemo "Dur, dur!" diyor; oyuncu resmin ustune basamiyor."""
    print("\n--- resmin onune gecilmiyor ---")
    game = Game()
    try:
        seed_save("rey")
        scene = arrive(game)
        ring_bell(game, scene)
        finish_dialogue(game, scene)
        teleport(game, scene, scene.home_door_x + 10)
        check(scene.drawing_state != "", "evde resim basladi")
        limit = scene.home_door_x + HOME_REACH
        closest = scene.player.body.center_x
        body = scene.player.body
        for _ in range(120):
            body.set_feet(body.center_x - PLAYER_RUN_SPEED, body.feet[1])
            frame(game)
            closest = min(closest, body.center_x)
            if dialogue_ready(scene):
                tap(game, pygame.K_RETURN)
        check(closest >= limit - 0.5, "oyuncu resmin sag ucunun disinda kaldi",
              f"kapi+{closest - scene.home_door_x:.0f}")
        left, right, _base = scene.drawing_origin()
        check(left < scene.home_door_x < right,
              "resim kapinin iki yaninda")
        camera_left = limit - INTERNAL_WIDTH // 2
        check(camera_left > 0, "kamera evi ortalayabiliyor (bati yolu var)",
              f"{camera_left:.0f}")
    finally:
        game.quit()


def test_postgame_village() -> None:
    """Oyun sonrasi: koy dolu, resim duvarda, tabeladan cikis menuye."""
    print("\n--- oyun sonrasi koy ---")
    game = Game()
    try:
        seed_save("rey")
        scene = open_scene(game, EpilogueVillageScene, character="rey",
                           postgame=True)
        run(game, 60)
        check(all(v.greeting for v in scene.villagers),
              "koyluler bastan disarida")
        check(scene.drawing >= 1.0, "Cemo'nun resmi duvarda")
        check(scene.dialogue.done, "karsilama tekrar oynamiyor")
        teleport(game, scene, 4.0, settle=3)
        check(isinstance(game.scenes.current, EpilogueVillageScene),
              "bati kenarina yurumek KAZARA cikarmiyor")
        teleport(game, scene, scene.sign_x + 6, settle=3)
        check(scene.prompts.active("leave"), "tabelada 'Yola cik' beliriyor")
        tap(game, pygame.K_e)
        wait_scene(game, MainMenuScene)
        check(isinstance(game.scenes.current, MainMenuScene),
              "tabeladan ana menuye", type(game.scenes.current).__name__)
    finally:
        game.quit()


# --- 5. Ates basi ve jenerik ----------------------------------------------------
def test_fire_panels() -> None:
    """Kadeh yalnizca Kalachev olduyse; jenerikte aktor yok."""
    print("\n--- ates basi panelleri ---")
    for kalachev in (True, False):
        game = Game()
        try:
            seed_save("ardo")
            scene = open_scene(game, HomecomingFireCinematic,
                               character="ardo",
                               homecoming=Homecoming(character="ardo",
                                                     kalachev=kalachev))
            names = [panel.name for panel in scene.PANELS]
            check(("kadeh" in names) == kalachev,
                  f"Kalachev {'oldu' if kalachev else 'yasiyor'}: kadeh "
                  f"{'var' if kalachev else 'yok'}")
            closing = scene.PANELS[-1]
            hidden = {cue.actor for cue in closing.cues
                      if cue.visible is False}
            check(closing.name == "resim"
                  and hidden == {spec.name for spec in scene.ACTORS},
                  "jenerik panelinde butun aktorler gizli")
        finally:
            game.quit()


# --- 6. Cizim ---------------------------------------------------------------------
def test_scenes_draw_for_both() -> None:
    """Epilogun her sahnesi, iki karakter, **cizim dahil**."""
    print("\n--- epilog sahneleri (iki karakter, cizim dahil) ---")
    for character in ("rey", "ardo"):
        cases = (
            (EpilogueShaftScene, {}),
            (VerticalJourneyScene, {"direction": "up", "variant": "dawn",
                                    "next_scene": EpilogueVillageScene,
                                    "next_kwargs": {"character": character}}),
            (EpilogueVillageScene, {}),
            (EpilogueVillageScene, {"postgame": True}),
            (HomecomingFireCinematic, {}),
        )
        for cls, extra in cases:
            game = Game()
            label = f"{cls.__name__}{' (oyun sonrasi)' if extra.get('postgame') else ''}"
            try:
                seed_save(character)
                open_scene(game, cls, character=character, **extra)
                for _ in range(240):
                    frame(game, draw=True)
                check(True, f"{label} ({character}) cokmeden oynuyor")
            except Exception as exc:       # noqa: BLE001 - test raporluyor
                check(False, f"{label} ({character})",
                      f"{type(exc).__name__}: {exc}")
            finally:
                game.quit()


def test_no_tutorial_cards() -> None:
    """Yoldas komutu kapali: ogretici kart epilogda hic acilmiyor."""
    print("\n--- ogretici kart yok ---")
    game = Game()
    try:
        write_save(SaveData(chapter=18, character="rey",
                            flags={"finished": True, **SEEN_HINTS}))
        for cls in (EpilogueShaftScene, EpilogueVillageScene):
            open_scene(game, cls, character="rey")
            run(game, 30)
            data = game.scenes.current.save_data
            check(not data.flags.get("hint_companion"),
                  f"{cls.__name__}: 'yoldasa komut' karti acilmadi")
    finally:
        game.quit()


def main() -> int:
    test_end_game_writes_to_disk()
    test_continue_after_finish()
    test_flags_agree()
    test_call_reaches_jet()
    test_keeper_last_candle()
    test_closing_press_does_not_call()
    test_bell_brings_the_village_out()
    test_villager_lines_follow_the_save()
    test_home_waits_for_the_bell()
    test_drawing_keeps_the_player_back()
    test_postgame_village()
    test_fire_panels()
    test_no_tutorial_cards()
    test_scenes_draw_for_both()
    test_chain_end_to_end()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Epilog tutarli - ip, can, koy, resim, ates ve jenerik zincirde.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
