"""Magara fonu: B2/B9/B17 once/sonra kareleri ve 240 kare cizim olcumu.

Once ``--baseline``, duzenlemeden sonra parametresiz calistir.
Oyuncunun kayit/ayarlarini kullanmaz; cikti build/cave_visuals altindadir.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
OUTPUT = ROOT / "build" / "cave_visuals"
SOURCE = ROOT / "src" / "world" / "cave_backdrop.py"
SAVED = OUTPUT / "baseline_cave_backdrop.py"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.baseline:
        SAVED.write_text(SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Baseline saved: {SAVED}")
        return
    if not SAVED.exists():
        raise SystemExit("Once --baseline ile onceki fonu sakla.")

    with tempfile.TemporaryDirectory(prefix="lore_cave_visuals_") as save_dir:
        os.environ["LORE_SAVE_DIR"] = save_dir
        import pygame
        from src.art import postfx
        from src.core.game import Game
        from src.scenes.catalog import chapter_scene_class
        from src.scenes.play import PlayScene
        from src.systems.save import SaveData, write_save
        from src.world import cave_backdrop

        old = types.ModuleType("cave_baseline")
        exec(compile(SAVED.read_text(encoding="utf-8"), str(SAVED), "exec"),
             old.__dict__)
        current = cave_backdrop.draw
        write_save(SaveData())
        game = Game()
        metrics = {}
        try:
            for chapter in (2, 9, 17):
                write_save(SaveData(chapter=chapter, character="rey",
                                    abilities=["sword", "dodge", "echo_sight"]))
                game.scenes.set_root(chapter_scene_class(chapter), transition=False,
                                     character="rey")
                game.scenes._flush()
                scene = game.scenes.find(PlayScene)
                assert scene is not None
                scene.card = None
                scene.dialogue.stop()
                if chapter == 2:
                    scene.player.body.set_feet(580, scene.player.body.bottom)
                    scene.camera.snap_to(scene.player.body.center_x,
                                         scene.player.body.center_y)
                frames = []
                measures = {}
                for label, renderer in (("before", old.draw), ("after", current)):
                    cave_backdrop.draw = renderer
                    game.frame = 180
                    scene.frames = 180
                    scene.draw(game.canvas)
                    postfx.apply(game.canvas, scene.postfx_grade)
                    shot = pygame.transform.scale(game.canvas, (960, 540))
                    pygame.image.save(shot, OUTPUT / f"b{chapter:02}_{label}.png")
                    frames.append(shot)
                    # Onbelleklerin isinmasi olcume dahil degil.
                    for _ in range(8):
                        scene.draw(game.canvas)
                    started = time.perf_counter()
                    for frame in range(240):
                        game.frame = 180 + frame
                        scene.frames = 180 + frame
                        scene.draw(game.canvas)
                    measures[label + "_scene_ms"] = (
                        (time.perf_counter() - started) * 1000 / 240)
                    started = time.perf_counter()
                    for frame in range(240):
                        renderer(game.canvas, scene.camera.offset, 180 + frame)
                    measures[label + "_backdrop_ms"] = (
                        (time.perf_counter() - started) * 1000 / 240)
                pair = pygame.Surface((1920, 540))
                pair.blit(frames[0], (0, 0))
                pair.blit(frames[1], (960, 0))
                pygame.image.save(pair, OUTPUT / f"b{chapter:02}_comparison.png")
                metrics[str(chapter)] = measures
                print(f"B{chapter}: {json.dumps(measures)}")
            (OUTPUT / "timings.json").write_text(
                json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        finally:
            cave_backdrop.draw = current
            game.shutdown()


if __name__ == "__main__":
    main()
