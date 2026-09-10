"""Korku katmaninin dort soku - `docs/korku.md` §6.

    1  B3   mesaleyi birakinca isigin kenarinda bir sekil
    2  B11  aynadaki yansiman bir kez GEC donuyor
    3  B13  Cemo tasinirken kenarda Izleyen - ve Cemo ona bakiyor
    ★  B14  jumpscare (`tests/test_horror.py` olcuyor)
    4  B18  Cemo'nun sesi ilk duyuldugunda - sessizlik

Her sok icin uc sey olculuyor, cunku `docs/korku.md` §3'un kurallari
tam olarak bunlar:

  * **Oluyor** - ve gorunur yerde (B5'in ilk gorusu ekranin 21 tile
    otesinde oynamisti; ayni hata B3'te de ilk surumde vardi).
  * **Bir kez** - kural 2: *"ayni numara iki kez yok."*
  * **Korku kapaliyken olmuyor** - §8 erisilebilirlik.

Calistir:
    python tests/test_shocks.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA** (`DEVIR.md` §0.6). `src` import
# edilmeden ONCE.
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_shock_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from src.config import INTERNAL_WIDTH, TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.systems import horror  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402

failures: list[str] = []
ABILITIES = ["sword", "dodge", "echo_sight", "echo_ask"]


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def open_scene(game, scene_cls, chapter: int, level: str = horror.FULL,
               **kwargs):
    """Ayar ONCE yaziliyor: sinematikler aktorlerini `on_enter`de kuruyor.

    Seviye **her seferinde acikca** veriliyor - ayarlar gecici kayit
    dizinine yaziliyor ve bir onceki testin "kapali"si bir sonrakine
    sizardi.
    """
    game.settings.set("horror", level)
    write_save(SaveData(chapter=chapter, character="rey",
                        abilities=list(ABILITIES)))
    game.scenes.set_root(scene_cls, transition=False, character="rey",
                         **kwargs)
    game.scenes._flush()
    scene = game.scenes.current
    if hasattr(scene, "dialogue"):
        scene.dialogue.stop()
    return scene


# --- Ortak kapi ---------------------------------------------------------------
def test_gate() -> None:
    print("\n--- try_shock kapisi ---")
    from src.scenes.chapter03 import Chapter03Scene
    game = Game()
    try:
        scene = open_scene(game, Chapter03Scene, 3)
        check(scene.try_shock("deneme"), "ilk cagri: ACIK")
        check(not scene.try_shock("deneme"), "ikinci cagri: KAPALI (kural 2)")
        check(scene.try_shock("baska"), "baska bir sok kendi hakkini tutuyor")

        scene = open_scene(game, Chapter03Scene, 3, horror.OFF)
        check(not scene.try_shock("deneme"),
              "korku kapaliyken hic acilmiyor (§8)")
        scene = open_scene(game, Chapter03Scene, 3, horror.REDUCED)
        check(scene.try_shock("deneme"),
              "AZALTILMIS seviyede sok kaliyor - yalnizca ani ses gidiyor")
    finally:
        game.quit()


# --- Sok 1: B3 ----------------------------------------------------------------
def test_b3_edge_shape() -> None:
    print("\n--- sok 1: B3 isigin kenari ---")
    from src.scenes.chapter03 import Chapter03Scene
    game = Game()
    try:
        scene = open_scene(game, Chapter03Scene, 3)
        body = scene.player.body
        body.set_feet(TILE_SIZE * 16, body.feet[1])
        for _ in range(20):
            scene.update()
        scene.camera.snap_to(body.center_x, body.center_y)
        scene.update()

        scene._edge_shock()
        shape = scene.edge_shape
        check(shape is not None, "mesale birakilinca sekil beliriyor")
        if shape is not None:
            view_x = shape.x - scene.camera.offset[0]
            check(0 <= view_x <= INTERNAL_WIDTH,
                  "sekil KAMERANIN ICINDE - gorulebilir yerde",
                  f"ekran x={view_x:.0f}")
            away = shape.x - body.center_x
            check(away * shape.facing > 0,
                  "isiktan UZAGA yuruyor - yaklasan degil uzaklasan")
        scene._edge_shock()
        check(scene.edge_shape is shape, "ikinci birakista YENI sekil yok")

        for _ in range(80):
            scene.update()
        check(scene.edge_shape is None, "sekil kendiliginden sondu")
        check(game.music.hush == 0.0, "muzik kisilmasi GERI ALINDI",
              str(game.music.hush))

        scene = open_scene(game, Chapter03Scene, 3, horror.OFF)
        body = scene.player.body
        body.set_feet(TILE_SIZE * 16, body.feet[1])
        scene.update()
        scene._edge_shock()
        check(scene.edge_shape is None, "korku kapaliyken sekil YOK")
    finally:
        game.quit()


# --- Sok 2: B11 ---------------------------------------------------------------
def _stand_by_mirror(scene, facing: int) -> None:
    rect = scene._mirror_rect()
    body = scene.player.body
    body.set_feet(rect.centerx - 30, rect.bottom)
    scene.player.facing = facing
    for _ in range(3):
        scene.update()
    scene.player.body.set_feet(rect.centerx - 30, rect.bottom)


def test_b11_reflection_lags_once() -> None:
    print("\n--- sok 2: B11 yansima gec donuyor ---")
    from src.scenes.chapter11 import MIRROR_LAG, Chapter11Scene
    game = Game()
    try:
        scene = open_scene(game, Chapter11Scene, 11)
        _stand_by_mirror(scene, 1)
        check(scene._near_wall_mirror(), "oyuncu aynanin onunde")
        check(scene._reflection_alpha() > 0, "yansima gorunuyor")
        check(scene.reflect_facing == 1, "once yansima seninle ayni yone bakiyor")

        scene.player.facing = -1
        scene._update_reflection()
        check(scene.reflect_facing == 1 and scene.reflect_hold > 0,
              "sen dondun - yansima DONMEDI", f"bekleme {scene.reflect_hold}")
        for _ in range(MIRROR_LAG + 1):
            scene._update_reflection()
        check(scene.reflect_facing == -1,
              "bir sanat karesi sonra yetisiyor", f"{MIRROR_LAG} kare")

        scene.player.facing = 1
        scene._update_reflection()
        check(scene.reflect_facing == 1 and scene.reflect_hold == 0,
              "IKINCI donuste gecikme yok - bir kez (kural 2)")

        # Aynadan uzakta donmek soku harcamiyor.
        scene = open_scene(game, Chapter11Scene, 11)
        scene.player.body.set_feet(TILE_SIZE * 5, scene.player.body.feet[1])
        scene.player.facing = -scene.reflect_facing
        scene._update_reflection()
        check("b11_reflection" not in scene._shocks_fired,
              "uzakta donmek soku HARCAMIYOR")

        scene = open_scene(game, Chapter11Scene, 11, horror.OFF)
        _stand_by_mirror(scene, 1)
        scene.player.facing = -1
        scene._update_reflection()
        check(scene.reflect_facing == -1,
              "korku kapaliyken yansima hep esit - ayna yine AYNA")
    finally:
        game.quit()


# --- Sok 3: B13 ---------------------------------------------------------------
def test_b13_watcher_in_cage_scene() -> None:
    print("\n--- sok 3: B13 Cemo ona bakiyor ---")
    from src.scenes.chapter13_cinematics import CageCinematic
    game = Game()
    try:
        scene = open_scene(game, CageCinematic, 13)
        check(scene.actor("watcher") is not None, "Izleyen sahnede")
        carried = next(p for p in scene.panels if p.name == "tasiniyor")
        actors = [c.actor for c in carried.cues]
        check("watcher" in actors, "tasinirken beliriyor")
        turns = [c for c in carried.cues if c.actor == "cemo" and c.face == 1]
        check(bool(turns), "Cemo ONA donuyor - kardesinden gozunu ayiriyor")
        check(all(not c.sound for c in carried.cues if c.actor == "watcher"),
              "Izleyen ses cikarmiyor (kural 3)")

        scene = open_scene(game, CageCinematic, 13, horror.OFF)
        check(scene.actor("watcher") is None, "korku kapaliyken Izleyen YOK")
        carried = next(p for p in scene.panels if p.name == "tasiniyor")
        turns = [c for c in carried.cues if c.actor == "cemo" and c.face == 1]
        check(not turns, "ve Cemo sebepsiz yere DONMUYOR")
    finally:
        game.quit()


# --- Sok 4: B18 ---------------------------------------------------------------
def test_b18_voice_silence() -> None:
    print("\n--- sok 4: B18 Cemo'nun sesi ---")
    from src.scenes.chapter18 import SHOCK_HUSH_FRAMES, Chapter18Scene
    game = Game()
    try:
        scene = open_scene(game, Chapter18Scene, 18)
        scene._voice_shock()
        check(game.music.hush == 1.0, "muzik TAMAMEN kesildi (kural 3)",
              str(game.music.hush))
        scene._voice_shock()
        check(scene.silence_shock_frames <= SHOCK_HUSH_FRAMES,
              "ikinci cagri sureyi uzatmiyor")
        for _ in range(SHOCK_HUSH_FRAMES + 2):
            scene._update_shock_hush()
        check(game.music.hush == 0.0, "sessizlik kendini GERI aliyor",
              str(game.music.hush))

        scene = open_scene(game, Chapter18Scene, 18, horror.OFF)
        scene._voice_shock()
        check(game.music.hush == 0.0, "korku kapaliyken muzik kesilmiyor",
              str(game.music.hush))
    finally:
        game.quit()


def main() -> int:
    test_gate()
    test_b3_edge_shape()
    test_b11_reflection_lags_once()
    test_b13_watcher_in_cage_scene()
    test_b18_voice_silence()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Dort sok: oluyor, bir kez oluyor, korku kapaliyken olmuyor.")
    return 0


pygame.display.init()
pygame.font.init()
raise SystemExit(main())
