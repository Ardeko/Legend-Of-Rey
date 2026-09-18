"""Jet çıkışları ve Kalachev konuşmaları: gerçek sahne akışı ve kayıt."""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_TEMP = tempfile.TemporaryDirectory(prefix="lore_story_")
os.environ["LORE_SAVE_DIR"] = _TEMP.name
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame

from src.core.game import Game
from src.scenes.catalog import chapter_scene_class
from src.scenes.jet_cinematics import ENCOUNTERS, JetReturnCinematic, play_jet_once
from src.scenes.kalachev_cinematics import KalachevCinematic
from src.scenes.play import PlayScene
from src.systems.save import SaveData, read_save, write_save
from src.ui import i18n
from src.ui.chapter_end import ChapterEndScene
from src.ui.dialogue import MAX_LINES, _wrap


def tick(game: Game, frame: int) -> None:
    game.input.begin_frame()
    event = pygame.event.Event(pygame.KEYDOWN if frame % 2 else pygame.KEYUP,
                               key=pygame.K_RETURN)
    game.input.handle_event(event)
    game.input.end_frame()
    game.scenes.update()
    game.frame += 1


def run_cinematic(game: Game, scene, shot: str = "") -> None:
    seen: set[str] = set()
    captured: set[str] = set()
    for frame in range(1400):
        line = scene.dialogue.current
        if line is not None:
            seen.add(line.key)
            text = scene.dialogue.full_text
            assert not text.startswith("["), line.key
            assert not re.search(r"\w\?\w", text), text
            assert len(_wrap(text, scene.dialogue._wrap_width())) <= MAX_LINES
        if scene.panel is not None and (frame % 8 == 0 or
                                       (shot and scene.dialogue.complete)):
            scene.draw(game.canvas)
            name = scene.panel.name
            if (shot and name not in captured and scene.dialogue.complete
                    and scene.panel_frames > 12):
                target = ROOT / "build" / "testshots" / f"{shot}_{name}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                pygame.image.save(pygame.transform.scale(game.canvas, (960, 540)), target)
                captured.add(name)
        tick(game, frame)
        if scene.finished:
            break
    assert scene.finished, "Sinematik bitişe ulaşmadı"
    expected = {line.key for panel in scene.panels for line in panel.dialogue_lines}
    assert seen == expected, (seen, expected)


def test_jet(game: Game, chapter: int, character: str, language: str) -> None:
    write_save(SaveData(chapter=chapter, character=character,
                        abilities=["sword", "dodge"]))
    game.scenes.set_root(chapter_scene_class(chapter), transition=False,
                         character=character)
    game.scenes._flush()
    play = game.scenes.find(PlayScene)
    assert play is not None
    while game.scenes.current is not play:
        game.scenes.pop()
        game.scenes._flush()
    play.finished = True
    play._end_chapter()
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, JetReturnCinematic)
    assert bool(scene.actor("companion")) == (chapter == 9)
    flag = ENCOUNTERS[chapter][0]
    assert not play.save_data.flags.get(flag), "İzlenmeden görülmüş sayıldı"
    assert play_jet_once(play, play._end_chapter), "Aynı anda ikinci sahne açılmamalı"
    run_cinematic(game, scene,
                  f"jet_b{chapter}_{character}" if language == "tr" else "")
    assert isinstance(game.scenes.current, ChapterEndScene)
    disk, _ = read_save()
    assert disk is not None and disk.flags.get(flag)
    scene.on_finished()
    game.scenes._flush()
    assert isinstance(game.scenes.current, ChapterEndScene), "Bitiş iki kez işledi"
    # Oyunu yeniden açmış gibi kayıttan kur; görülmüş sahne yinelenmesin.
    game.scenes.set_root(chapter_scene_class(chapter), transition=False,
                         character=character)
    game.scenes._flush()
    replay = game.scenes.find(PlayScene)
    assert replay is not None
    assert not play_jet_once(replay, replay._end_chapter)
    print(f"OK Jet B{chapter} {character} {language}: akis, cizim, kalici bayrak")


def main() -> None:
    write_save(SaveData())
    game = Game()
    try:
        for language in ("tr", "en"):
            i18n.set_language(language)
            for character in ("rey", "ardo"):
                for chapter in ENCOUNTERS:
                    test_jet(game, chapter, character, language)
                for beat in ("meet", "trap", "gate", "last"):
                    game.scenes.set_root(KalachevCinematic, transition=False,
                                         character=character, beat=beat)
                    game.scenes._flush()
                    scene = game.scenes.current
                    assert any(line.speaker == "kalachev"
                               for panel in scene.panels for line in panel.dialogue_lines)
                    run_cinematic(game, scene,
                                  "kalachev_meet" if (language, character, beat)
                                  == ("tr", "ardo", "meet") else "")
                    print(f"OK Kalachev {beat} {character} {language}: akis ve cizim")
    finally:
        game.shutdown()
        _TEMP.cleanup()


if __name__ == "__main__":
    main()
