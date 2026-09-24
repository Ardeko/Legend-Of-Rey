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

from src.config import TILE_SIZE
from src.core.game import Game
from src.scenes.catalog import chapter_scene_class
from src.scenes.chapter05 import (
    Chapter05Scene, SIGHTING_COLUMN, SIGHTING_NEAR_TILES,
    SIGHTING_PACK_OFFSETS, SIGHTING_WATER_DROP,
)
from src.scenes.jet_cinematics import ENCOUNTERS, JetReturnCinematic, play_jet_once
from src.scenes.kalachev_cinematics import KalachevCinematic
from src.scenes.play import PlayScene
from src.systems.save import SaveData, read_save, write_save
from src.ui import i18n
from src.ui.chapter_end import ChapterEndScene
from src.ui.dialogue import MAX_LINES, _wrap
from src.world.rooms.chapter05 import WATER_HIGH, WATER_LOW


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


def test_kalachev_sighting(game: Game, character: str, language: str) -> None:
    flag = "ch05_kalachev_intro_seen"
    near_x = (SIGHTING_COLUMN - SIGHTING_NEAR_TILES) * TILE_SIZE
    feet_y = 13 * TILE_SIZE
    # Eski bir B5 kaydi: yeni sinematik bayragi henuz yok.
    write_save(SaveData(chapter=5, character=character,
                        checkpoint="vana_odasi", checkpoint_x=near_x,
                        checkpoint_y=feet_y, abilities=["sword", "dodge"]))

    def load_checkpoint() -> Chapter05Scene:
        game.scenes.set_root(Chapter05Scene, transition=False,
                             character=character, resume_save=True)
        game.scenes._flush()
        play = game.scenes.find(Chapter05Scene)
        assert play is not None and game.scenes.current is play
        assert play.checkpoint_room == "vana_odasi"
        return play

    def trigger(play: Chapter05Scene) -> None:
        play.water.level = WATER_LOW - SIGHTING_WATER_DROP
        play.water.set_target(WATER_HIGH)
        play.player.body.set_feet(near_x, feet_y)
        play._update_sighting()
        game.scenes._flush()

    play = load_checkpoint()
    play._update_sighting()
    game.scenes._flush()
    assert game.scenes.current is play and not play.sighting_done, "Su alcak"
    play.water.level = WATER_LOW - SIGHTING_WATER_DROP
    play.player.body.set_feet(near_x - TILE_SIZE, feet_y)
    play._update_sighting()
    game.scenes._flush()
    assert game.scenes.current is play and not play.sighting_done, "Oyuncu uzak"

    trigger(play)
    intro = game.scenes.current
    assert isinstance(intro, KalachevCinematic) and intro.beat == "sighting"
    assert intro.actor("ally") is None, "B5'te diger oyuncu yoldas degil"
    for frame in range(24):
        tick(game, frame)
    assert not intro.finished and not play.save_data.flags.get(flag)
    disk, _ = read_save()
    assert disk is not None and not disk.flags.get(flag), "Yarim sahne kaydedildi"

    # Sahne yarida kapatilirsa yeniden yuklemede atlanmamali.
    play = load_checkpoint()
    trigger(play)
    intro = game.scenes.current
    assert isinstance(intro, KalachevCinematic) and intro.beat == "sighting"
    assert len(play.allies) == 1
    ally = play.allies[0]
    pack = tuple(play.sighting_pack)
    assert len(pack) == len(SIGHTING_PACK_OFFSETS)
    assert all(enemy in play.enemies for enemy in pack)

    def actor_state(actor) -> tuple:
        body = actor.body
        animator = actor.animator
        return (id(actor), body.x, body.y, body.vx, body.vy, actor.health,
                actor.dead, animator.state, animator.index, animator.hold)

    def world_state() -> tuple:
        return (play.frames, play.room_frames, play.water.level, play.water.frame,
                actor_state(play.player), tuple(map(actor_state, play.enemies)),
                tuple(map(actor_state, play.allies)), ally.stay_frames,
                ally.attack_frames, ally.swing_frames, ally.kills)

    frozen = world_state()
    run_cinematic(game, intro,
                  f"kalachev_b5_{character}" if language == "tr" else "")
    assert game.scenes.current is play, "Sinematik oyuna donmedi"
    assert world_state() == frozen, "Sinematikte su veya aktorler ilerledi"
    assert tuple(play.sighting_pack) == pack and play.allies[0] is ally
    assert play.save_data.flags.get(flag)
    disk, _ = read_save()
    assert disk is not None and disk.flags.get(flag), "Tamamlanan sahne kaydedilmedi"

    # Cift bitis callback'i alttaki oynanabilir sahneyi yiginindan atmiyor.
    intro.on_finished()
    game.scenes._flush()
    assert game.scenes.current is play
    previous_water = play.water.level
    previous_stay = ally.stay_frames
    for frame in range(90):
        tick(game, frame)
    assert play.water.level < previous_water, "Oyun donunce su ilerlemedi"
    assert ally.stay_frames < previous_stay, "Kalachev AI'i devam etmedi"
    assert any(enemy.health < enemy.max_health for enemy in pack), "Gercek dovus yok"

    # Izlenmis kayitta yalniz sinematik atlanir; suru ve dovus yine var.
    play = load_checkpoint()
    trigger(play)
    assert game.scenes.current is play, "Izlenmis sahne tekrar acildi"
    assert len(play.allies) == 1 and len(play.sighting_pack) == len(pack)
    print(f"OK Kalachev B5 {character} {language}: tetik, donma, dovus, kayit")


def main() -> None:
    write_save(SaveData())
    game = Game()
    try:
        for language in ("tr", "en"):
            i18n.set_language(language)
            for character in ("rey", "ardo"):
                for chapter in ENCOUNTERS:
                    test_jet(game, chapter, character, language)
                test_kalachev_sighting(game, character, language)
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
