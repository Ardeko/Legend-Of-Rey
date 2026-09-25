"""B3 "Mor" sinemasi ve B6'nin adi - Arda'nin iki sikayeti (25.09.2026).

1. *"Ardo ile oynasam da Rey ile oynasam da ekranda Rey cikiyor ve mor
   alev geliyor. Ne oldugu hic anlasilmiyor."*
   - Sahne oynanan karakterle aciliyor.
   - Alev bir kaidede DURUYOR, oyuncu ona yuruyor ve elini uzatiyor
     (`docs/bolum-03.md` Ara Sahne 3). Eskiden alev sagdan ucarak
     oyuncunun ustune geliyordu.
   - Rey'de Yanki bagiriyor ve susuyor, Rey susmayi SOYLUYOR; Ardo'da
     Yanki yok, Ardo kendi gozlemini soyluyor.
   - Iki saniyelik karanlik hizlandirilamiyor, sonrasi hizlanabiliyor.

2. *"Ardo olan bolumun ismini yoldas veya tanisma gibi bir sey yapalim."*
   B6'nin adi karaktere bagli degil; eski kayit yeni ada tasiniyor.

Calistir:
    python tests/test_chapter03_purple.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.systems.save import SaveData, write_save  # noqa: E402

write_save(SaveData(chapter=3, abilities=["sword", "dodge"]))

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.core.game import Game  # noqa: E402
from src.scenes import chapter03_cinematics as purple  # noqa: E402
from src.scenes.chapter03 import Chapter03Scene  # noqa: E402
from src.scenes.chapter06 import Chapter06Scene  # noqa: E402
from src.ui import i18n  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def speakers(panels) -> list[str]:
    return [line.speaker for panel in panels for line in panel.dialogue_lines]


def run(game: Game, character: str) -> None:
    print(f"\n--- {character}: Mor ---")
    write_save(SaveData(chapter=3, character=character,
                        abilities=["sword", "dodge"]))
    game.scenes.set_root(Chapter03Scene, transition=False, character=character)
    game.scenes._flush()
    chapter = game.scenes.current
    chapter._enter_room("mor_alev")
    game.scenes._flush()
    scene = game.scenes.current
    check(isinstance(scene, purple.PurpleCinematic), "oda sinemayi aciyor")
    actor = scene.actor("player")
    check(scene.character == character
          and actor.animator.character == character,
          "sahnede OYNANAN karakter var", actor.animator.character)

    names = [panel.name for panel in scene.panels]
    who = speakers(scene.panels)
    if character == "ardo":
        check("echo" not in who, "Ardo'nun sahnesinde Yanki konusmuyor", str(who))
        check("irkilme" in names and who == ["ardo"],
              "Ardo geri cekiliyor ve kendi gozlemini soyluyor", str(names))
    else:
        check(who == ["echo", "rey"], "Yanki bagiriyor, Rey susmayi soyluyor",
              str(who))
        check(names.index("kukreme") < names.index("sessizlik"),
              "once bagiris, sonra sessizlik")
    for key in ("line.ch03_echo_shout", "line.ch03_rey_silence",
                "line.ch03_ardo_cold"):
        check(i18n.t(key) != key, f"{key} tabloda")

    order = ["titreme", "karanlik", "beliris", "yaklasma", "el"]
    check(names[:5] == order,
          "belgedeki sira: soner, karanlik, belirir, yaklasir, el uzanir",
          str(names[:5]))

    blocked: dict[str, bool] = {}
    positions: dict[str, float] = {}
    for _ in range(2400):
        game.input.begin_frame()
        game.input.end_frame()
        game.scenes.update()
        game.scenes._flush()
        if game.scenes.current is not scene:
            break
        panel = scene.panel
        if panel is None:
            continue
        # Hizlandirma: karanlik ve belirme ASLA; replik yokken yaklasma evet.
        blocked.setdefault(panel.name, not scene.skippable)
        positions[panel.name] = actor.x
    check(game.scenes.current is chapter, "sahne bitince bolum kaldigi yerden")
    check(blocked.get("karanlik") and blocked.get("beliris")
          and blocked.get("titreme"), "karanlik hizlandirilamiyor")
    check(blocked.get("yaklasma") is False,
          "alev belirdikten sonra basili tutunca hizlaniyor (CLAUDE.md 9)")
    check(abs(positions.get("el", 0.0) - purple.STAND_X) < 1.0,
          "oyuncu kaideye YURUYOR (alev ona ucmuyor)",
          f"{positions.get('el', 0.0):.0f} -> kaide {purple.PEDESTAL_X}")
    check(purple.STAND_X < purple.PEDESTAL_X, "alevin onunde duruyor")
    check(not hasattr(scene, "flame_x"), "alevin konumu sabit (hareket kodu yok)")


def check_meeting_name() -> None:
    print("\n--- B6'nin adi ---")
    check(Chapter06Scene.chapter_name_key == "chapter.meeting",
          "B6 karaktere bagli olmayan bir ad kullaniyor")
    for code in ("tr", "en"):
        i18n.set_language(code)
        name = i18n.t("chapter.meeting")
        check(name != "chapter.meeting"
              and "ardo" not in name.lower() and "rey" not in name.lower(),
              f"{code}: ad karakter adi degil", name)
    i18n.set_language("tr")
    old = SaveData.from_dict({"chapter": 6, "chapter_name": "chapter.ardo"})
    check(old.chapter_name == "chapter.meeting",
          "eski kayit karti ham anahtar gostermiyor", old.chapter_name)


def main() -> int:
    game = Game()
    for character in ("rey", "ardo"):
        run(game, character)
    check_meeting_name()
    game.shutdown()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Mor sahnesi karaktere gore, anlasilir; B6'nin adi tarafsiz.")
    return 0


raise SystemExit(main())
