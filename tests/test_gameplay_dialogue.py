"""Oynanis yazilari: guvenli girdi, okuma suresi, sira ve sinematik ayrimi."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_TEMP = tempfile.TemporaryDirectory(prefix="lore_dialogue_")
os.environ["LORE_SAVE_DIR"] = _TEMP.name
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from src.core.game import Game
from src.scenes.combat_room import CombatRoomScene
from src.scenes.play import PlayScene
from src.systems.save import SaveData, write_save
from src.ui import i18n
from src.ui.dialogue import Dialogue, Line, READ_MIN_FRAMES, READ_MAX_FRAMES
from src.ui.pause import PauseScene


def frame(game: Game, dialogue: Dialogue, key: int | None = None) -> None:
    game.input.begin_frame()
    if key is not None:
        game.input.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        game.input.handle_event(pygame.event.Event(pygame.KEYUP, key=key))
    game.input.end_frame()
    dialogue.update(game)


def main() -> None:
    write_save(SaveData())
    game = Game()
    try:
        first = Line("cemo", "line.ch01_cemo_gift")
        second = Line("rey", "line.ch01_rey_thanks")
        for language in ("tr", "en"):
            i18n.set_language(language)
            dialogue = Dialogue()
            dialogue.start((first, second), gameplay=True)
            frame(game, dialogue, pygame.K_SPACE)
            assert dialogue.revealed == 2, "Ziplamak yaziyi hizlandirdi"
            while not dialogue.complete:
                frame(game, dialogue, pygame.K_e)
            for key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
                frame(game, dialogue, key)
                assert dialogue.current == first, "Oynanis tusu repligi gecti"
            hold = dialogue.hold_frames
            assert READ_MIN_FRAMES <= hold <= READ_MAX_FRAMES
            while dialogue.current == first:
                frame(game, dialogue)
            assert dialogue.current == second, "Siradaki replik kayboldu"
            for _ in range(READ_MAX_FRAMES + 200):
                frame(game, dialogue)
            assert dialogue.done, "Tus basmadan kapanmadi"
            dialogue.start((second,), gameplay=True)
            short = dialogue.hold_frames
            dialogue.start((first,), gameplay=True)
            assert dialogue.hold_frames >= short
            print(f"OK {language}: otomatik okuma suresi, Space/E/Enter guvenli")

        scene = PlayScene(game)
        scene.dialogue = Dialogue()
        scene.lies = SimpleNamespace(silenced=False)
        scene.say(first)
        frame(game, scene.dialogue)
        progress = scene.dialogue.revealed
        scene.say(second)
        scene.say(second)
        assert scene.dialogue.lines == (first, second)
        assert scene.dialogue.revealed == progress
        scene.say(Line("echo", "line.ch01_echo_alone"))
        scene.dialogue.silence("echo")
        assert scene.dialogue.lines == (first, second)
        scene.dialogue.start((Line("echo", "line.ch01_echo_alone"), second),
                             gameplay=True)
        scene.dialogue.silence("echo")
        assert scene.dialogue.current == second and scene.dialogue.gameplay
        scene.dialogue.stop()
        scene.say(second)
        assert scene.dialogue.lines == (second,), "Eski kuyruk yeniden basladi"
        print("OK siralama, tekrar korumasi, susan Yanki, kuyruk temizligi")

        scene.say(first, auto_advance=False)
        for _ in range(READ_MAX_FRAMES * 2):
            frame(game, scene.dialogue)
        assert scene.dialogue.current == first, "Onemli konusma onaysiz gecti"
        frame(game, scene.dialogue, pygame.K_RETURN)
        assert scene.dialogue.done
        scene.say(first, timed=True)
        for _ in range(200):
            frame(game, scene.dialogue)
        assert scene.dialogue.done, "Sureli sahnenin ritmi bozuldu"
        print("OK onay bekleyen konusma ve sureli sinematik ayrimi")

        game.scenes.set_root(CombatRoomScene, transition=False)
        game.scenes._flush()
        world = game.scenes.current
        world.enemies.clear()
        for _ in range(45):
            game.input.begin_frame()
            game.input.end_frame()
            game.scenes.update()
        world.dialogue.stop()
        world.say(first)
        before = world.player.body.feet[1]
        game.input.begin_frame()
        game.input.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        game.input.end_frame()
        game.scenes.update()
        assert world.player.body.feet[1] < before, "Yazi ziplama kontrolunu engelledi"
        assert world.dialogue.current == first and world.dialogue.revealed == 2
        world.dialogue.revealed = len(world.dialogue.full_text)
        game.scenes.push(PauseScene, save_data=world.save_data)
        game.scenes._flush()
        before_hold = world.dialogue.hold
        for _ in range(120):
            game.input.begin_frame()
            game.input.end_frame()
            game.scenes.update()
        assert world.dialogue.hold == before_hold, "Duraklatmada okuma suresi tukendi"
        print("OK gercek sahnede Space ziplar; duraklatmada yazi suresi durur")
    finally:
        game.shutdown()


if __name__ == "__main__":
    main()
