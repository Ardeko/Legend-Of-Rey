"""Butun boss arenalarinda olum spawn'u ve DEVAM ET.

Oyuncu (ve varsa yoldas / Kalachev) muhurun ARKASINDA dogmamali.
Duraklatip kaydedince DEVAM ET kayitli odaya, bolum basina degil.

Calistir:
    python tests/test_boss_resume.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_boss_")

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

from src.config import TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.catalog import chapter_scene_class  # noqa: E402
from src.scenes.chapter02 import Chapter02Scene  # noqa: E402
from src.scenes.chapter03 import Chapter03Scene  # noqa: E402
from src.scenes.chapter06 import Chapter06Scene  # noqa: E402
from src.scenes.chapter13 import Chapter13Scene  # noqa: E402
from src.scenes.chapter14 import Chapter14Scene  # noqa: E402
from src.scenes.chapter18 import Chapter18Scene  # noqa: E402
from src.scenes.vertical_journey import VerticalJourneyScene  # noqa: E402
from src.systems.save import SaveData, read_save, write_save  # noqa: E402
from src.world.rooms.chapter02 import ARENA_DOOR_COLUMN as B2_DOOR  # noqa: E402
from src.world.rooms.chapter03 import ARENA_DOOR_COLUMN as B3_DOOR  # noqa: E402
from src.world.rooms.chapter06 import ARENA_DOOR_TILE as B6_DOOR  # noqa: E402
from src.world.rooms.chapter18 import ARENA_SEAL_COLUMN as B18_DOOR  # noqa: E402

failures: list[str] = []

ABILITIES = ["sword", "dodge", "echo_sight", "echo_ask"]

# (bolum, sinif, oda, ayak satiri, yoldas, Kalachev, kurtarma)
FIGHTS: tuple[tuple[int, type, str, int, bool, bool, bool], ...] = (
    (2, Chapter02Scene, "miniboss", 13, False, False, False),
    (3, Chapter03Scene, "sonmus_olan", 13, False, False, False),
    (6, Chapter06Scene, "arena", 13, True, False, True),
    (13, Chapter13Scene, "zindan", 13, False, True, False),
    (14, Chapter14Scene, "arena", 13, False, False, False),
    (18, Chapter18Scene, "arena", 14, True, True, False),
)


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def drain(game: Game, scene) -> object:
    """Olum / tanisma bindirmelerini kapat; sahne bitmisse dokunma."""
    game.scenes._flush()
    while game.scenes.current is not scene:
        if getattr(scene, "finished", False):
            break
        game.scenes.pop()
        game.scenes._flush()
    return game.scenes.current


def seal_left(scene) -> float:
    """Muhrun sag kenari (govde solunun gecmesi gereken x)."""
    room = getattr(scene, "room", "")
    start, _ = scene._room_span(room)
    body = scene.player.body
    top = max(0, int(body.top) // TILE_SIZE)
    bottom = max(top, int(body.bottom - 1) // TILE_SIZE)
    last = None
    for col in range(start, start + 8):
        blocked = any(scene.tilemap.is_solid(col, row)
                      for row in range(top, bottom + 1))
        if blocked:
            last = col
        elif last is not None:
            break
    if last is not None:
        return float((last + 1) * TILE_SIZE)
    known = {
        2: (B2_DOOR + 1) * TILE_SIZE,
        3: (B3_DOOR + 1) * TILE_SIZE,
        6: (B6_DOOR + 1) * TILE_SIZE,
        18: (B18_DOOR + 1) * TILE_SIZE,
    }
    if scene.chapter_number in known:
        return float(known[scene.chapter_number])
    return float((start + 4) * TILE_SIZE)


def open_fight(game: Game, chapter: int, cls: type, room: str,
               tile_y: int, rescue: bool):
    write_save(SaveData(chapter=chapter, character="rey",
                        abilities=list(ABILITIES)))
    game.scenes.set_root(cls, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current
    if rescue:
        scene._rescue()
        drain(game, scene)
        scene = game.scenes.current
    start, _ = scene._room_span(room)
    feet = float((tile_y + 1) * TILE_SIZE)
    scene.player.body.set_feet((start + 1) * TILE_SIZE, feet)
    scene.player.body.grounded = True
    scene.room = room
    scene._update_checkpoint()
    return scene, start, feet


def assert_inside(scene, label: str) -> None:
    edge = seal_left(scene)
    check(getattr(scene, "arena_sealed", False), f"{label}: muhur indi")
    check(scene.player.body.x >= edge, f"{label}: oyuncu icerde",
          f"x={scene.player.body.x:.1f} kenar={edge:.1f}")
    check(not scene.tilemap.solid_overlap(scene.player.body.rect),
          f"{label}: oyuncu kati tile'da degil")
    companion = getattr(scene, "companion", None)
    if companion is not None:
        check(companion.body.x >= edge, f"{label}: yoldas icerde",
              f"x={companion.body.x:.1f}")
        check(not scene.tilemap.solid_overlap(companion.body.rect),
              f"{label}: yoldas kati tile'da degil")
    for ally in getattr(scene, "allies", ()):
        if getattr(ally, "gone", False) or getattr(ally, "dead", False):
            continue
        check(ally.body.x >= edge, f"{label}: Kalachev icerde",
              f"x={ally.body.x:.1f}")
        check(not scene.tilemap.solid_overlap(ally.body.rect),
              f"{label}: Kalachev kati tile'da degil")


def test_death_inside_every_boss() -> None:
    print("\n--- olum: her boss muhurun icinde ---")
    for chapter, cls, room, tile_y, want_comp, want_kal, rescue in FIGHTS:
        game = Game()
        try:
            scene, start, feet = open_fight(
                game, chapter, cls, room, tile_y, rescue)
            scene.player.body.set_feet((start + 8) * TILE_SIZE, feet)
            scene.player.health = 0
            scene.player.die()
            scene.restart()
            scene = drain(game, scene)
            check(scene.room == room, f"B{chapter}: odada devam", scene.room)
            if want_comp:
                check(getattr(scene, "companion", None) is not None,
                      f"B{chapter}: yoldas yaninda")
            if want_kal:
                check(bool(getattr(scene, "allies", ())),
                      f"B{chapter}: Kalachev yaninda")
            assert_inside(scene, f"B{chapter} olum")
        finally:
            game.quit()


def test_continue_from_pause_every_boss() -> None:
    print("\n--- DEVAM ET: her boss kayitli odada ---")
    for chapter, cls, room, tile_y, want_comp, want_kal, rescue in FIGHTS:
        game = Game()
        try:
            scene, start, feet = open_fight(
                game, chapter, cls, room, tile_y, rescue)
            # Kayit oda girisini tutuyor - muhur o noktanin onune iner.
            scene._persist_checkpoint()
            write_save(scene.save_data)
            disk, _ = read_save()
            check(disk is not None and disk.chapter == chapter,
                  f"B{chapter}: kayit bolumu",
                  str(getattr(disk, "chapter", None)))
            check(disk is not None and disk.checkpoint == room,
                  f"B{chapter}: kayit odasi",
                  str(getattr(disk, "checkpoint", None)))

            game.scenes.set_root(VerticalJourneyScene, transition=False,
                                 direction="down", chapter=chapter,
                                 character="rey")
            game.scenes._flush()
            game.scenes.current.on_finished()
            game.scenes._flush()
            scene = drain(game, game.scenes.current)
            check(isinstance(scene, cls), f"B{chapter}: DEVAM ET sahnesi",
                  type(scene).__name__)
            check(not isinstance(scene, chapter_scene_class(1))
                  or chapter == 1,
                  f"B{chapter}: koy acilmadi")
            check(scene.room == room, f"B{chapter}: kayitli oda", scene.room)
            if want_comp:
                check(getattr(scene, "companion", None) is not None,
                      f"B{chapter}: DEVAM yoldas")
            if want_kal:
                check(bool(getattr(scene, "allies", ())),
                      f"B{chapter}: DEVAM Kalachev")
            assert_inside(scene, f"B{chapter} devam")
        finally:
            game.quit()


def main() -> int:
    test_death_inside_every_boss()
    test_continue_from_pause_every_boss()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Alti boss: olum ve DEVAM ET muhurun icinde.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
