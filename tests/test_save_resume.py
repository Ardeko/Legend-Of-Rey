"""Gercek menu rotasi: duraklat -> kaydet -> ana menu -> DEVAM ET.

Bolum, oda, karakter ve ekipman iki yuvada da korunmali. Bozuk ana
kayit ve basarisiz yazma da eldeki saglam yedegi kaybettirmemeli.

Calistir: python tests/test_save_resume.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# `src` importundan once: oyuncunun dosyalarina asla dokunma.
_TEMP = tempfile.TemporaryDirectory(prefix="lore_save_resume_")
os.environ["LORE_SAVE_DIR"] = _TEMP.name
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402

from src.config import TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.catalog import chapter_scene_class  # noqa: E402
from src.scenes.play import PlayScene  # noqa: E402
from src.scenes.vertical_journey import VerticalJourneyScene  # noqa: E402
from src.systems.save import (  # noqa: E402
    SLOT_COUNT, SaveData, active_slot, backup_path, delete_save, read_save,
    save_path, set_active_slot, write_save,
)
from src.ui.menu import MainMenuScene  # noqa: E402
from src.ui.pause import PauseScene  # noqa: E402
from src.ui.slot_select import SlotSelectScene  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    print(("OK " if condition else "!! ") + label)
    if not condition:
        failures.append(label)


def finish_transition(game: Game) -> None:
    """Yalnizca menunun perdesi; oyun fizigini ilerletmeden kuyrugu bosalt."""
    for _ in range(game.scenes.transition.frames + 1):
        game.scenes.transition.update()
        game.scenes._flush()


def close_overlays(game: Game, scene: PlayScene) -> None:
    game.scenes._flush()
    while game.scenes.current is not scene:
        game.scenes.pop()
        game.scenes._flush()


def prepare_room(game: Game, chapter: int, room: str, character: str,
                 slot: int, two_slots: bool) -> PlayScene:
    for index in range(1, SLOT_COUNT + 1):
        delete_save(index)
    if two_slots:
        set_active_slot(3 - slot)
        write_save(SaveData(chapter=4, character="rey", gold=19))
    set_active_slot(slot)
    write_save(SaveData(chapter=chapter, character=character, gold=137,
                        weapon="axe", owned_weapons=["sword", "axe"],
                        abilities=["sword", "dodge", "echo_sight", "echo_ask"]))
    game.scenes.set_root(chapter_scene_class(chapter), transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.find(PlayScene)
    assert scene is not None
    close_overlays(game, scene)
    start, _ = scene._room_span(room)
    x, y = scene.free_spot_near((start + 8) * TILE_SIZE,
                              14 * TILE_SIZE, scene.player.body)
    scene.player.body.set_feet(x, y)
    scene.player.body.grounded = True
    scene._enter_room(room)
    close_overlays(game, scene)
    scene._update_checkpoint()
    scene.save_data.gold = 237  # Yeni kazanim, disk henuz eski altini tasiyor.
    return scene


def exercise_menu_route(game: Game, chapter: int, room: str, character: str,
                        slot: int, two_slots: bool) -> None:
    scene = prepare_room(game, chapter, room, character, slot, two_slots)
    other_before = save_path(3 - slot).read_bytes() if two_slots else None
    game.scenes.push(PauseScene, save_data=scene.save_data)
    game.scenes._flush()
    pause = game.scenes.current
    assert isinstance(pause, PauseScene)
    pause.menu.index = 3
    pause.menu.activate()
    assert pause.confirm_quit is not None
    pause.confirm_quit.index = 1
    pause.confirm_quit.activate()
    finish_transition(game)
    menu = game.scenes.current
    assert isinstance(menu, MainMenuScene)
    menu.menu.activate()
    game.scenes._flush()
    if two_slots:
        slots = game.scenes.current
        assert isinstance(slots, SlotSelectScene)
        slots.menu.index = slot - 1
        slots.menu.activate()
        game.scenes._flush()
    journey = game.scenes.current
    assert isinstance(journey, VerticalJourneyScene)
    journey.on_finished()
    game.scenes._flush()
    resumed = game.scenes.find(PlayScene)
    assert resumed is not None
    label = f"B{chapter} {character} yuva {slot} ({'iki' if two_slots else 'tek'} kayit)"
    check(resumed.chapter_number == chapter and resumed.room == room,
          f"{label}: DEVAM ET kayitli bolum ve odada")
    check(resumed.character == character and active_slot() == slot,
          f"{label}: karakter ve aktif yuva korundu")
    check(resumed.save_data.gold == 237
          and resumed.save_data.weapon == "axe"
          and "axe" in resumed.save_data.owned_weapons
          and "dodge" in resumed.player.abilities,
          f"{label}: son altin, ekipman ve yetenekler korundu")
    check(resumed._room_at(resumed.player.body.center_x) == room
          and not resumed.tilemap.solid_overlap(resumed.player.body.rect),
          f"{label}: fiziksel konum da kayitli odada ve boslukta")
    if two_slots:
        check(save_path(3 - slot).read_bytes() == other_before,
              f"{label}: oteki yuvanin dosyasi degismedi")


def test_pause_write_failure(game: Game) -> None:
    scene = prepare_room(game, 2, "patlayanlar", "rey", 1, False)
    before = save_path().read_bytes()
    game.scenes.push(PauseScene, save_data=scene.save_data)
    game.scenes._flush()
    pause = game.scenes.current
    assert isinstance(pause, PauseScene)
    with patch("src.ui.pause.write_save", return_value=False):
        with patch.object(game, "play_sound") as sound:
            pause._ask_quit()
            check(pause.saved_notice == 0 and not pause._save_succeeded,
                  "yazma basarisizsa kaydedildi bildirimi yok")
            check(not any(call.args == ("save_written",)
                          for call in sound.call_args_list),
                  "yazma basarisizsa basari sesi yok")
            check(not pause.confirm_quit.items[1].enabled,
                  "yazma basarisizsa ilerlemeyi terk eden secenek kapali")
            pause._to_main_menu()
            finish_transition(game)
            check(game.scenes.find(PlayScene) is scene,
                  "yazma basarisizsa canli oyun korunuyor")
            check(save_path().read_bytes() == before,
                  "yazma basarisizsa onceki disk kaydi korunuyor")
    pause._cancel_quit()
    pause._ask_quit()
    check(pause._save_succeeded and pause.confirm_quit.items[1].enabled,
          "yeniden deneme basariliysa menuye donulebiliyor")


def test_backup_survives_failed_recovery_write() -> None:
    set_active_slot(1)
    write_save(SaveData(chapter=11, checkpoint="salon", gold=501))
    write_save(SaveData(chapter=11, checkpoint="salon", gold=502))
    backup_before = backup_path().read_bytes()
    for malformed in ("{yarim", "[]", "null", '"yanlis tip"'):
        save_path().write_text(malformed, encoding="utf-8")
        restored, status = read_save()
        check(status == "backup" and restored is not None
              and restored.chapter == 11 and restored.gold == 501,
              f"bozuk ana kayit {malformed!r}: saglam yedekten devam")
    assert restored is not None
    with patch.object(Path, "replace", side_effect=OSError("test: disk hatasi")):
        check(not write_save(restored), "atomik degisim hatasi raporlandi")
    check(backup_path().read_bytes() == backup_before,
          "kurtarma yazmasi basarisiz olsa da saglam yedek ezilmedi")
    recovered, status = read_save()
    check(status == "backup" and recovered is not None and recovered.gold == 501,
          "ikinci acilista da yedekten devam edilebiliyor")
    check(write_save(recovered), "disk duzelince kurtarilan veri yazilabiliyor")


def main() -> int:
    game = Game()
    try:
        for chapter, room in ((2, "patlayanlar"), (11, "salon"), (13, "zindan")):
            for character in ("rey", "ardo"):
                for slot, two_slots in ((2, False), (1, True), (2, True)):
                    exercise_menu_route(game, chapter, room, character,
                                        slot, two_slots)
        test_pause_write_failure(game)
        test_backup_survives_failed_recovery_write()
    finally:
        game.shutdown()
        _TEMP.cleanup()
    if failures:
        print(f"\n{len(failures)} BASARISIZ: " + "; ".join(failures))
        return 1
    print("\nKaydet -> menu -> DEVAM ET: 18 gercek UI rotasi ve hata kurtarma gecti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
