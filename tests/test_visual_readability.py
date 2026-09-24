"""Karanlikta gorus, gizli duvar ve Ardo'nun dar gecit yonlendirmesi."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="lore_readability_") as isolated:
        os.environ["LORE_SAVE_DIR"] = isolated
        import pygame
        from src.art import lighting, palette
        from src.config import TILE_SIZE
        from src.core.game import Game
        from src.core.input import Action
        from src.scenes.chapter07 import Chapter07Scene
        from src.scenes.play import PlayScene
        from src.systems.light import LightState
        from src.systems.save import SaveData, write_save
        from src.world.rooms.chapter07 import GAP_TILE, GAP_ROWS, WINCH_TILE
        from src.world.tilemap import TileMap

        write_save(SaveData(chapter=7, character="ardo"))
        game = Game()
        try:
            sample = pygame.Surface((120, 80)).convert()
            base = palette.color("bone")
            sample.fill(base)
            state = LightState()
            lighting.render(sample, (0, 0), state)
            unlit = sum(sample.get_at((50, 40))[:3])
            assert unlit >= sum(base) * 0.33, "Isiksiz zeminin silueti kayboldu"
            state.set_static("test", 40, 40, 30)
            sample.fill(base)
            lighting.render(sample, (0, 0), state)
            assert sum(sample.get_at((55, 40))[:3]) > unlit * 1.7
            assert not state.in_light(100, 40), "Gorsel duzeltme mekanik menzili buyuttu"
            print("OK karanlik: zemin gorunur, isik cekirdegi acik, mekanik menzil ayni")

            normal = TileMap([".....", ".###.", ".###.", "....."])
            hidden = TileMap([".....", ".#B#.", ".B##.", "....."])
            a, b = pygame.Surface((80, 64)), pygame.Surface((80, 64))
            a.fill(base)
            b.fill(base)
            normal.draw(a, (0, 0))
            hidden.draw(b, (0, 0))
            assert pygame.image.tobytes(a, "RGB") == pygame.image.tobytes(b, "RGB")
            print("OK yeni taslar: kirilabilir duvar gorsel olarak ele verilmiyor")

            game.scenes.set_root(Chapter07Scene, transition=False, character="ardo")
            game.scenes._flush()
            scene = game.scenes.find(PlayScene)
            assert isinstance(scene, Chapter07Scene)
            scene.player.body.set_feet((GAP_TILE - 1) * TILE_SIZE,
                                       GAP_ROWS.stop * TILE_SIZE)
            scene.dialogue.stop()
            game.input.rebind(Action.INTERACT, (pygame.K_f,))
            assert "[F]" in scene._order_hint_text()
            game.canvas.fill(base)
            before = pygame.image.tobytes(game.canvas, "RGB")
            scene.draw_overlay(game.canvas)
            assert pygame.image.tobytes(game.canvas, "RGB") != before
            for _ in range(500):
                scene._update_orders()
            assert not scene.rey_sent, "Sadece yaklasmak otomatik emir verdi"
            game.input.begin_frame()
            game.input.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f))
            game.input.end_frame()
            scene._update_orders()
            assert scene.rey_sent
            destination = WINCH_TILE[0] * TILE_SIZE
            assert scene.companion.hold_x == destination
            scene.companion.body.set_feet(scene.gap.rect.right + 24,
                                          GAP_ROWS.stop * TILE_SIZE)
            scene._update_gap()
            assert scene.companion.hold_x == destination, "Sinematik Rey'i geri cagirdi"
            game.canvas.fill(base)
            scene.draw_overlay(game.canvas)
            assert pygame.image.tobytes(game.canvas, "RGB") == before
            print("OK Ardo: kalici F ipucu, gercek emir, Rey ilerler, ipucu kapanir")
        finally:
            game.shutdown()


if __name__ == "__main__":
    main()
