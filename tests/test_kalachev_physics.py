"""Kalachev'in yercekimi: dogum, darbe, cikinti, sessizlik ve cekilme.

Gercek Body/TileMap dongusu kullanilir; yercekimi test tarafinda eklenmez.
Kayitlar yalnizca gecici LORE_SAVE_DIR'e yazilir.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_kalachev_physics_")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from src.combat.hitbox import Hitbox, Team  # noqa: E402
from src.config import GRAVITY, TILE_SIZE  # noqa: E402
from src.entities.kalachev import Kalachev  # noqa: E402
from src.world.tilemap import TileMap  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f" ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def room(rows: list[str] | None = None) -> SimpleNamespace:
    """AI icin dusmansiz oda; carpisma tamamen oyunun haritasinda."""
    return SimpleNamespace(
        tilemap=TileMap(rows or ["." * 30] * 10 + ["#" * 30]),
        enemies=[], player=None,
        game=SimpleNamespace(play_sound=lambda *args: None),
    )


def advance(ally: Kalachev, frames: int) -> list[float]:
    heights = []
    for _ in range(frames):
        ally.update()
        heights.append(ally.body.bottom)
    return heights


def test_airborne_states() -> None:
    floor_y = 10 * TILE_SIZE
    for state in ("active", "silent", "leaving", "expired", "chase", "dead"):
        scene = room()
        ally = Kalachev(scene, 80.0, floor_y - 64.0, silent=state == "silent")
        if state == "leaving":
            ally.leave()
        elif state == "expired":
            ally.stay_frames = 1
        elif state == "chase":
            ally.chase(300.0)
        elif state == "dead":
            ally.perish()
        stay = ally.stay_frames
        ally.update()
        check(abs(ally.body.vy - GRAVITY) < 1e-8,
              f"{state}: kare basina bir kez yercekimi", f"vy={ally.body.vy:.2f}")
        advance(ally, 30)
        check(ally.body.grounded and ally.body.bottom == floor_y,
              f"{state}: havadan gercek zemine indi",
              f"ayak={ally.body.bottom:.1f}, zemin={floor_y}")
        check(not scene.tilemap.solid_overlap(ally.body.rect),
              f"{state}: govde zemine gomulmedi")
        if state == "silent":
            check(ally.stay_frames == stay and ally.body.center_x == 80.0,
                  "sessizlik: sure ve yatay konum korunuyor")
        if state == "chase":
            check(ally.body.center_x > 80.0 and ally.chase_x == 300.0,
                  "senaryolu kosu yercekimiyle devam ediyor")
        if state == "dead":
            check(ally.dead and not ally.gone and not ally.leaving,
                  "olu govde sahnede kaliyor")


def test_knockback_and_recovery() -> None:
    # Ustte tavan da var: eski kod yukari itilen govdeyi orada birakiyordu.
    scene = room(["#" * 30] + ["." * 30] * 9 + ["#" * 30])
    floor_y = 10 * TILE_SIZE
    ally = Kalachev(scene, 80.0, float(floor_y), silent=True)
    box = Hitbox(rect=ally.body.rect, owner=None, targets=Team.PLAYER,
                 damage=1, active_frames=1, knockback=0.0, knockback_up=4.0)
    ally.flash.trigger(14)
    result = ally.take_damage(box, (1.0, 0.0))
    check(result.hit and not result.killed, "darbe aldi, hayatta")
    heights = advance(ally, 120)
    check(min(heights) < floor_y, "darbe govdeyi once yukari savuruyor")
    check(ally.body.grounded and ally.body.bottom == floor_y,
          "yukari savrulduktan sonra zemine donuyor",
          f"ayak={ally.body.bottom:.1f}, zemin={floor_y}")
    check(not ally.flash.active and ally.iframes == 0,
          "darbe flasi ve dokunulmazlik suresi bitiyor")
    check(ally.take_damage(box, (1.0, 0.0)).hit,
          "sonraki darbe yeniden isleniyor")


def test_ledge_and_platform() -> None:
    rows = ["." * 30] * 10 + ["#" * 30]
    rows[5] = "#" * 8 + "." * 22
    scene = room(rows)
    ally = Kalachev(scene, 112.0, 5.0 * TILE_SIZE)
    heights = advance(ally, 120)
    check(ally.body.center_x > 8 * TILE_SIZE + ally.body.width,
          "kendi yolunda cikintinin kenarini asti")
    check(max(heights) > 5 * TILE_SIZE and ally.body.grounded
          and ally.body.bottom == 10 * TILE_SIZE,
          "cikintidan inince havada yurumeden alt zemine dustu")

    rows[5] = "=" * 30
    scene = room(rows)
    ally = Kalachev(scene, 80.0, 32.0, silent=True)
    advance(ally, 60)
    check(ally.body.grounded and ally.body.bottom == 5 * TILE_SIZE,
          "tek yonlu platformun ustune iniyor")


def main() -> int:
    pygame.display.init()
    pygame.display.set_mode((64, 64))
    test_airborne_states()
    test_knockback_and_recovery()
    test_ledge_and_platform()
    pygame.quit()
    print(f"\nKalachev fizik: {len(failures)} basarisiz kontrol.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
