"""Karaktere ozel ve ortak silahlar: kaide, alma, kalicilik, bitiriciler.

Arda, 23.09.2026: *"oyuna silah cesitliligi de ekleyelim ... karakterlere
ozel bir silah mi ... ilerde acilacak yeni bir silah mi"* - ikisi de:
B10'da Rey'e Fisilti / Ardo'ya Iz Mizragi, B14'te ikisine Zincir Orak.

Kayitlar yalnizca gecici `LORE_SAVE_DIR`e yaziliyor.

Calistir:
    python tests/test_weapon_shrine.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_weapons_")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.combat import weapons  # noqa: E402
from src.config import SPEAR_LUNGE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.scenes.play import PlayScene  # noqa: E402
from src.systems.save import SaveData, read_save, write_save  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f" ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_scene(game: Game, number: int, character: str) -> PlayScene:
    cls = f"Chapter{number:02d}Scene"
    module = __import__(f"src.scenes.chapter{number:02d}", fromlist=[cls])
    game.scenes.set_root(getattr(module, cls), transition=False,
                         character=character)
    game.scenes._flush()
    while not isinstance(game.scenes.current, PlayScene):
        game.scenes._do_pop()
    scene = game.scenes.current
    scene.card = None
    scene.dialogue.stop()
    scene.enemies = []
    return scene


def step(game: Game, scene, frames: int, action: Action | None = None,
         every: int = 0) -> list[str]:
    """Kareleri surer; gorunen mermi adlarini toplar."""
    seen: list[str] = []
    for frame in range(frames):
        game.input.begin_frame()
        if action is not None and (frame == 0 or (every and frame % every == 0)):
            game.input._activate(action)
            game.input._deactivate(action)
        game.input.end_frame()
        scene.update()
        seen.extend(box.visual for box in scene.hitboxes.boxes if box.visual)
    return seen


def fresh_save(chapter: int, character: str) -> None:
    write_save(SaveData(chapter=chapter, character=character, weapon="sword",
                        abilities=["sword"]))


def test_table() -> None:
    print("\n--- silah tablosu ---")
    for key in (weapons.WHISPER, weapons.SPEAR, weapons.SICKLE):
        weapon = weapons.get(key)
        check(weapon.key == key, f"{key} tanimli")
        normal = {hit.hitstop for hit in weapon.chain[:-1]}
        check(normal == {3} and weapon.chain[-1].hitstop == 7,
              f"{key}: hitstop 3/7 (dovus-sistemi baglayici)",
              f"{normal} / {weapon.chain[-1].hitstop}")
        check(not weapon.chain[-1].cancelable,
              f"{key}: bitirici iptal edilemiyor")
    check(weapons.usable_by(weapons.WHISPER, "rey")
          and not weapons.usable_by(weapons.WHISPER, "ardo"),
          "Fisilti yalnizca Rey'in")
    check(weapons.usable_by(weapons.SPEAR, "ardo")
          and not weapons.usable_by(weapons.SPEAR, "rey"),
          "Iz Mizragi yalnizca Ardo'nun")
    check(weapons.usable_by(weapons.SICKLE, "rey")
          and weapons.usable_by(weapons.SICKLE, "ardo"),
          "Zincir Orak ikisinin de")


def test_shrines(game: Game) -> None:
    print("\n--- kaideler ---")
    expected = {(10, "rey"): weapons.WHISPER, (10, "ardo"): weapons.SPEAR,
                (14, "rey"): weapons.SICKLE, (14, "ardo"): weapons.SICKLE}
    for (number, character), key in expected.items():
        fresh_save(number, character)
        scene = make_scene(game, number, character)
        shrine = scene.shrine
        check(shrine is not None and shrine.weapon_key == key
              and not shrine.taken,
              f"B{number} {character}: {key} kaidesi hazir")
        if shrine is None:
            continue
        check(not scene.tilemap.solid_overlap(
                  __import__("pygame").Rect(int(shrine.x) - 9,
                                            int(shrine.feet_y) - 14, 18, 14)),
              f"B{number} {character}: kaide zeminde, duvarda degil")
    for number in (2, 9, 13, 18):
        fresh_save(number, "rey")
        scene = make_scene(game, number, "rey")
        check(scene.shrine is None, f"B{number}: kaide yok")


def test_take_and_persist(game: Game) -> None:
    print("\n--- alma ve kalicilik ---")
    fresh_save(10, "rey")
    scene = make_scene(game, 10, "rey")
    shrine = scene.shrine
    scene.player.body.set_feet(shrine.x - 10, shrine.feet_y)
    step(game, scene, 3)
    check(scene.prompts.active("weapon_shrine"), "yakinda 'Al' gostergesi")
    step(game, scene, 1, Action.INTERACT)
    check(shrine.taken, "INTERACT silahi aliyor")
    check(scene.player.weapon == weapons.WHISPER, "hemen kusaniliyor")
    saved, _ = read_save()
    check(saved is not None and saved.weapon == weapons.WHISPER
          and weapons.WHISPER in saved.owned_weapons
          and weapons.SWORD in saved.owned_weapons,
          "kayda yazildi; kilic envanterde kaliyor",
          f"{getattr(saved, 'owned_weapons', None)}")
    step(game, scene, 3)
    check(not scene.prompts.active("weapon_shrine"),
          "alinmis kaide bir daha teklif etmiyor")

    scene = make_scene(game, 10, "rey")
    check(scene.shrine is not None and scene.shrine.taken,
          "bolume geri donunce kaide BOS")
    check(scene.player.weapon == weapons.WHISPER,
          "kayittaki silah bolum basinda kusaniliyor")

    write_save(SaveData(chapter=11, character="ardo", weapon=weapons.WHISPER,
                        abilities=["sword"]))
    scene = make_scene(game, 11, "ardo")
    check(scene.player.weapon != weapons.WHISPER,
          "Ardo kayitta Fisilti olsa bile onu kusanmiyor")


def test_finishers(game: Game) -> None:
    print("\n--- bitiriciler ---")
    fresh_save(10, "rey")
    scene = make_scene(game, 10, "rey")
    scene.player.equip_weapon(weapons.WHISPER)
    seen = step(game, scene, 80, Action.ATTACK, every=8)
    check("echo_wave" in seen, "Fisilti bitiricisi ses dalgasi firlatiyor")

    fresh_save(10, "ardo")
    scene = make_scene(game, 10, "ardo")
    scene.player.equip_weapon(weapons.SPEAR)
    top_speed = 0.0
    for frame in range(90):
        step(game, scene, 1, Action.ATTACK if frame % 8 == 0 else None)
        if scene.player.chain.is_finisher:
            top_speed = max(top_speed, abs(scene.player.body.vx))
    check(top_speed >= SPEAR_LUNGE - 1e-6,
          "Iz Mizragi bitiricisi one atiliyor", f"{top_speed:.2f}")

    fresh_save(14, "rey")
    scene = make_scene(game, 14, "rey")
    scene.player.equip_weapon(weapons.SICKLE)
    scene.player.facing = 1
    behind = False
    for frame in range(110):
        step(game, scene, 1, Action.ATTACK if frame % 8 == 0 else None)
        centre = scene.player.body.center_x
        for box in scene.hitboxes.boxes:
            if box.owner is scene.player and box.rect.right <= centre:
                behind = True
    check(behind, "Zincir Orak bitiricisi arkayi da biciyor")


def main() -> int:
    game = Game()
    test_table()
    test_shrines(game)
    test_take_and_persist(game)
    test_finishers(game)
    game.shutdown()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for label in failures:
            print("  - " + label)
        return 1
    print("Silahlar: kaide, alma, kalicilik ve bitiriciler calisiyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
