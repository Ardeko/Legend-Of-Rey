"""Yetenek agaci EKRANI ve puanin oyuna yayilmasi.

Arda (25.09.2026): *"Yetenek agacini bolume yayilmis puanlar olarak
tekrar yap."* Uc soru:

  1. Puan oyunda GORUNUYOR mu? Bolum sonu ekrani "+1 yetenek puani"
     yaziyor, puan vermeyen bolum yazmiyor, ikinci kez yazmiyor.
  2. Agaca her yerden ULASILIYOR mu? Duraklat menusunde YETENEKLER.
  3. Ekran secimi dogru anlatiyor mu? Karakterin kendi dallari, secim
     ciftinde iki basis, alinan secimin rakibi "secilmedi".

Calistir:
    python tests/test_skill_tree_ui.py
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

write_save(SaveData())

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.core.game import Game  # noqa: E402
from src.scenes.combat_room import CombatRoomScene  # noqa: E402
from src.systems import skilltree  # noqa: E402
from src.ui.chapter_end import ChapterEndScene, ChapterResult  # noqa: E402
from src.ui.pause import PauseScene  # noqa: E402
from src.ui.skill_tree import FORSAKEN, OWNED, SkillTreeScene  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def key(game: Game, code: int) -> None:
    """Gercek dongunun sirasi: girdi -> sahne olayi -> kare."""
    game.input.begin_frame()
    event = pygame.event.Event(pygame.KEYDOWN, key=code)
    game.input.handle_event(event)
    game.scenes.handle_event(event)
    game.input.end_frame()
    game.scenes.update()
    game.scenes._flush()
    up = pygame.event.Event(pygame.KEYUP, key=code)
    game.input.begin_frame()
    game.input.handle_event(up)
    game.input.end_frame()


def result() -> ChapterResult:
    return ChapterResult(chapter_key="chapter.torch_crypt", frames=600,
                         best_combo=4, gold=10, secrets_found=0,
                         secrets_total=0)


def check_chapter_end(game: Game) -> None:
    print("--- bolum sonu: +1 yetenek puani ---")
    data = SaveData(chapter=3)
    game.scenes.push(ChapterEndScene, result=result(), save_data=data)
    game.scenes._flush()
    scene = game.scenes.current
    rows = [label for label, _value, _role in scene._rows()]
    check(data.skill_points == 1, "B3 sonu bir puan verdi", str(data.skill_points))
    check("chapter_end.skill_point" in rows, "ozet ekraninda puan satiri var")
    check(rows[-1] == "chapter_end.skill_point", "puan satiri EN SONDA")
    game.scenes.pop()
    game.scenes._flush()

    game.scenes.push(ChapterEndScene, result=result(), save_data=data)
    game.scenes._flush()
    again = [label for label, _v, _r in game.scenes.current._rows()]
    check(data.skill_points == 1 and "chapter_end.skill_point" not in again,
          "ayni bolum ikinci kez bitince puan ve satir YOK")
    game.scenes.pop()
    game.scenes._flush()

    quiet = SaveData(chapter=5)
    game.scenes.push(ChapterEndScene, result=result(), save_data=quiet)
    game.scenes._flush()
    rows5 = [label for label, _v, _r in game.scenes.current._rows()]
    check(quiet.skill_points == 0 and "chapter_end.skill_point" not in rows5,
          "puan vermeyen bolumde satir yok")
    game.scenes.pop()
    game.scenes._flush()

    ghost = SaveData(chapter=15)
    bonus = ChapterResult(chapter_key="chapter.silence", frames=600,
                          best_combo=0, gold=10, secrets_found=0,
                          secrets_total=0, ghost=True, ghost_bonus=85,
                          skill_points=1)
    game.scenes.push(ChapterEndScene, result=bonus, save_data=ghost)
    game.scenes._flush()
    row = [(label, value) for label, value, _r in game.scenes.current._rows()
           if label == "chapter_end.skill_point"]
    check(row == [("chapter_end.skill_point", "+1")],
          "B15'in hayalet puani ayni satirda gorunuyor", str(row))
    game.scenes.pop()
    game.scenes._flush()


def open_play(game: Game, character: str, points: int):
    write_save(SaveData(chapter=6, character=character, skill_points=points,
                        flags={"ch04_rested": True, "skillpt_ch3": True}))
    game.scenes.set_root(CombatRoomScene, transition=False, character=character)
    game.scenes._flush()
    return game.scenes.current


def check_pause_entry(game: Game) -> None:
    print("\n--- duraklat menusu: YETENEKLER ---")
    play = open_play(game, "rey", 3)
    game.scenes.push(PauseScene, save_data=play.save_data)
    game.scenes._flush()
    pause = game.scenes.current
    labels = [item.label for item in pause.menu.items]
    check("pause.skills" in labels, "menude YETENEKLER var", str(labels))
    check(labels.index("pause.skills") < labels.index("pause.settings"),
          "ekipmanin yaninda, ayarlardan once")
    last = pause.menu.item_rect(len(labels) - 1)
    check(last.bottom <= 135 + 146 // 2 - 6,
          "son oge panelin icinde kaliyor", str(last))
    pause._open_skills()
    game.scenes._flush()
    tree = game.scenes.current
    check(isinstance(tree, SkillTreeScene), "YETENEKLER agaci aciyor")
    check(tree.play is play, "agac canli sahneyi taniyor (aninda etki)")
    surface = pygame.Surface((480, 270))
    game.scenes.draw(surface)
    check(surface.get_bounding_rect().width > 0, "ekran ciziliyor")


def check_tree_screen(game: Game) -> None:
    print("\n--- agac ekrani ---")
    play = open_play(game, "ardo", 6)
    game.scenes.push(SkillTreeScene, save_data=play.save_data, tree=skilltree,
                     play=play)
    game.scenes._flush()
    tree = game.scenes.current
    check([b.key for b in tree.branches] == ["blade", "trace", "stone"],
          "Ardo'da IZ dali var, YANKI YOK",
          str([b.key for b in tree.branches]))
    check(tree.current.key == skilltree.BLADE_EDGE, "imlec ilk dugumde")
    key(game, pygame.K_RIGHT)
    check(tree.current.key == skilltree.TRACE_EYE, "SAG komsu dala geciyor")
    key(game, pygame.K_RETURN)
    check(skilltree.unlocked(play.save_data, skilltree.TRACE_EYE),
          "ONAY dugumu aciyor")
    check(play.tracking.range_scale > 1.0,
          "acilan dugum oyuna ANINDA biniyor (iz menzili)")
    key(game, pygame.K_DOWN)
    key(game, pygame.K_RETURN)
    check(skilltree.unlocked(play.save_data, skilltree.TRACE_PATIENCE),
          "ikinci kademe acildi")
    key(game, pygame.K_DOWN)
    first = tree.current.key
    check(first in (skilltree.TRACE_AMBUSH, skilltree.TRACE_QUIET),
          "ucuncu kademe: secim ciftinde", first)
    key(game, pygame.K_LEFT)
    key(game, pygame.K_RIGHT)
    check(tree.current.key == first, "SOL/SAG cift icinde gezinip geri donuyor")
    before = play.save_data.skill_points
    key(game, pygame.K_RETURN)
    check(not skilltree.unlocked(play.save_data, first)
          and play.save_data.skill_points == before and tree.pending == first,
          "secim ILK basista acilmiyor - uyariyor")
    surface = pygame.Surface((480, 270))
    game.scenes.draw(surface)
    key(game, pygame.K_RETURN)
    check(skilltree.unlocked(play.save_data, first), "ikinci basis onayliyor")
    rival = skilltree.rival(first)
    check(tree.state_of(rival) == FORSAKEN and tree.state_of(
        skilltree.get(first)) == OWNED, "rakip 'secilmedi' durumunda")
    game.scenes.draw(surface)
    check(surface.get_bounding_rect().width > 0, "agac ciziliyor")

    rey = open_play(game, "rey", 0)
    game.scenes.push(SkillTreeScene, save_data=rey.save_data, tree=skilltree,
                     play=rey)
    game.scenes._flush()
    check([b.key for b in game.scenes.current.branches]
          == ["blade", "echo", "stone"], "Rey'de YANKI dali var, IZ YOK")
    key(game, pygame.K_RETURN)
    check(not rey.save_data.skills, "puansiz onay hicbir sey acmiyor")


def main() -> int:
    game = Game()
    check_chapter_end(game)
    check_pause_entry(game)
    check_tree_screen(game)
    game.shutdown()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Agac ekrani ve bolume yayilan puanlar calisiyor.")
    return 0


raise SystemExit(main())
