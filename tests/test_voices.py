"""Kim neyi duyuyor - Yanki'nin sinirlari ve yakin plan portresi.

`docs/gdd.md` 4: Yanki **Rey'in laneti**. Ardo onu duymaz - bir istisna
disinda. Arda (25.09.2026): *"Ardo'da cikmamasi gereken Yanki repligi
cikmasin. Ama hikayeye uygun 1-2 Yanki duyabilir."*

Korunan kurallar:

  * **B2 inisinin alayi yalnizca Rey'de.** Ardo'nun dehlizi sessiz.
  * **B15'te Ardo sesi ILK kez duyuyor** - Kalachev'e yaklasinca tek
    yorum ve hemen ardindan kendi cevabi. Suru uyaninca gelen ikinci
    yorum yalnizca Rey'de. (B18'de Cagiran zaten herkese konusuyor.)
  * **Yakin plan panelinde diyalog portresi kapali.** Yuz tam ekranda;
    ayni yuzu iki olcekte gostermek karmasa. Kural bir donem uc sahnede
    ayri yaziliydi ve 41 yakin plan panelinin cogunda yuz iki kez
    gorunuyordu. Prolog portreyi hic acmiyor.

Calistir:
    python tests/test_voices.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA.** (08.09.2026)
import tempfile  # noqa: E402

os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.core.game import Game  # noqa: E402
from src.scenes.chapter02_cinematics import DescentCinematic  # noqa: E402
from src.scenes.chapter15 import Chapter15Scene  # noqa: E402
from src.scenes.ending import DawnCinematic  # noqa: E402
from src.scenes.kalachev_cinematics import KalachevCinematic  # noqa: E402
from src.scenes.prologue import ArdoPrologue, ReyPrologue  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def open_scene(game, cls, **kwargs):
    game.scenes.set_root(cls, transition=False, **kwargs)
    game.scenes._flush()
    return game.scenes.current


def spoken(scene) -> list[str]:
    return [line.key for line in scene.dialogue.lines] if scene.dialogue.active else []


# --- 1. B2: dehlizdeki alay -------------------------------------------------------
def test_descent_voice() -> None:
    print("\n--- B2 inisi: alay yalnizca Rey'de ---")
    for character, expected in (("rey", True), ("ardo", False)):
        game = Game()
        try:
            scene = open_scene(game, DescentCinematic, character=character)
            keys = [line.key for panel in scene.panels
                    for line in panel.dialogue_lines]
            check(("line.ch02_echo_fall" in keys) == expected,
                  f"{character}: Yanki'nin alayi "
                  f"{'var' if expected else 'YOK'}", str(keys))
            check([panel.name for panel in scene.panels][-1] == "dehliz",
                  f"{character}: dehliz paneli yerinde")
        finally:
            game.quit()


# --- 2. B15: Ardo sesi ilk kez duyuyor ------------------------------------------
def test_kalachev_voice() -> None:
    print("\n--- B15: Kalachev yorumu - kim duyuyor ---")
    for character in ("rey", "ardo"):
        game = Game()
        try:
            write_save(SaveData(chapter=15, character=character,
                                abilities=["sword", "dodge"],
                                flags={"resonance": True}))
            scene = open_scene(game, Chapter15Scene, character=character)
            scene.dialogue.stop()
            scene._enter_room("suru")
            ally = scene.allies[0]
            body = scene.player.body
            body.set_feet(ally.body.center_x - 20, body.feet[1])
            scene.update()
            expected = (["line.ch15_echo_kalachev"] if character == "rey"
                        else ["line.ch15_echo_kalachev", "line.ch15_ardo_hears"])
            check(spoken(scene) == expected,
                  f"{character}: yaklasinca {' + '.join(expected)}",
                  str(spoken(scene)))

            scene.dialogue.stop()
            # Sahnenin kendi yoluyla ve oyuncuya EN YAKIN uyuyan: uzaktaki
            # biri uyanirsa oyuncuyu goremiyor ve farkindaligi ayni karede
            # sonuyor - Kalachev'in uyanmasi o kareyi kaciriyordu.
            nearest = min((e for e in scene.enemies if e.asleep),
                          key=lambda e: abs(e.body.center_x - body.center_x))
            nearest.wake()
            scene.update()
            woke = "line.ch15_echo_kalachev_wakes" in spoken(scene)
            check(woke == (character == "rey"),
                  f"{character}: suru uyaninca ikinci yorum "
                  f"{'var' if character == 'rey' else 'YOK'}",
                  str(spoken(scene)))
        finally:
            game.quit()


# --- 3. Yakin plan: portre bir kez ----------------------------------------------
def _portrait_by_panel(scene) -> list[tuple[str, bool, bool]]:
    """Her paneli basindan baslat: (ad, yakin plan mi, portre acik mi)."""
    out = []
    for index, panel in enumerate(scene.panels):
        scene.panel_index = index
        scene._start_panel()
        out.append((panel.name, bool(panel.closeup),
                    scene.dialogue.show_portrait))
    return out


def test_closeup_portrait() -> None:
    print("\n--- yakin plan: yuz bir kez ---")
    cases = (
        (DawnCinematic, {"character": "rey"}, "kapanis"),
        (KalachevCinematic, {"character": "rey", "beat": "meet"},
         "Kalachev tanisma"),
        (KalachevCinematic, {"character": "ardo", "beat": "walk"},
         "Kalachev yuruyus"),
    )
    for cls, kwargs, label in cases:
        game = Game()
        try:
            scene = open_scene(game, cls, **kwargs)
            rows = _portrait_by_panel(scene)
            closeups = [name for name, closeup, _ in rows if closeup]
            wrong = [name for name, closeup, shown in rows
                     if shown == closeup]
            check(bool(closeups), f"{label}: yakin plan paneli var",
                  str(closeups))
            check(not wrong,
                  f"{label}: yakin planda portre KAPALI, digerlerinde acik",
                  str(wrong))
        except TypeError as exc:
            check(False, f"{label}: sahne acilmadi", str(exc))
        finally:
            game.quit()

    for cls in (ReyPrologue, ArdoPrologue):
        game = Game()
        try:
            scene = open_scene(game, cls)
            rows = _portrait_by_panel(scene)
            check(all(not shown for _name, _c, shown in rows),
                  f"{cls.__name__}: portre hic acilmiyor (panel zaten yuz)")
        finally:
            game.quit()


def main() -> int:
    test_descent_voice()
    test_kalachev_voice()
    test_closeup_portrait()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Sesler yerinde - Yanki Rey'in, Ardo bir kez duyuyor, yuz bir kez.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
