"""Zemin golgesi: ziplarken yerde kalir, cukurda kaybolur, botu kirpmaz."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_shadow_")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pygame

from src.art import animator, caches, contact_shadow, palette
from src.art.animation import CHARACTERS
from src.entities.actor import Body
from src.world.tilemap import EMPTY, TileMap


def render(actor: SimpleNamespace) -> pygame.Surface:
    surface = pygame.Surface((192, 160), pygame.SRCALPHA).convert_alpha()
    contact_shadow.draw(surface, actor, (0, 0))
    return surface


def main() -> None:
    pygame.display.init()
    pygame.display.set_mode((192, 160))
    body = Body(74, 64, 12, 32)
    floor = TileMap(["." * 12] * 6 + ["#" * 12] * 4)
    actor = SimpleNamespace(body=body, scene=SimpleNamespace(tilemap=floor))
    grounded = render(actor)
    assert grounded.get_bounding_rect().top == 95
    body.set_feet(80, 64)
    airborne = render(actor)
    assert airborne.get_bounding_rect().top == 95
    assert pygame.surfarray.array_alpha(airborne).sum() < \
        pygame.surfarray.array_alpha(grounded).sum()
    assert airborne.get_at((80, 64)).a == 0
    print("OK yukselen karakterin golgesi zeminde kaliyor ve soluyor")

    actor.scene.tilemap = TileMap(["." * 12] * 10)
    assert render(actor).get_bounding_rect().width == 0
    body.set_feet(-1, 96)
    assert render(actor).get_bounding_rect().width == 0
    print("OK cukur ve harita disinda gorunmez zemin golgesi yok")

    actor.scene.tilemap = TileMap(["." * 12] * 6 + ["#####......."] * 4)
    body.set_feet(79, 96)
    edge = render(actor).get_bounding_rect()
    assert edge.width > 0 and edge.right == 80
    print("OK cikinti kenarindaki golge cukura tasmiyor")

    actor.scene.tilemap = TileMap(["." * 12] * 6 + [".....=......"]
                                 + ["." * 12] * 3)
    body.set_feet(88, 72)
    assert render(actor).get_bounding_rect().top == 95
    actor.scene.tilemap.set_tile(5, 6, EMPTY)
    assert render(actor).get_bounding_rect().width == 0
    print("OK tek yonlu platform golge aliyor; kaldirilinca golge kayboluyor")

    actor.scene.tilemap = floor
    body.set_feet(80, 96 - contact_shadow.MAX_HEIGHT)
    assert render(actor).get_bounding_rect().width == 0
    assert contact_shadow._image(16, 16) is contact_shadow._image(16, 16)
    caches.invalidate_all()
    assert not contact_shadow._cache
    print("OK uzak golge sonuyor; yuzey onbellegi tekrar kullanilip temizleniyor")

    for name in ("rey_armed", "ardo_armed", "shambler", "kalachev"):
        normal = animator.sprite_set(name)
        projected = animator.sprite_set(name, shadow=False)
        assert projected is animator.sprite_set(name, shadow=False)
        for state, frames in normal.items():
            assert len(frames) == len(projected[state])
            for before, after in zip(frames, projected[state]):
                old = pygame.surfarray.array_alpha(before)
                new = pygame.surfarray.array_alpha(after)
                # Golge ayak hizasinda. Govde, yuz, sac ve havadaki silah
                # pikselleri kirpilmadan ayni konumda durmali.
                foot = int(CHARACTERS[name].foot_y)
                assert np.array_equal(old[:, :foot - 3], new[:, :foot - 3])
                rgb = pygame.surfarray.array3d(before)
                shadow_tones = [palette.color(tone) for tone in
                                palette.SHADE_CHAINS["shadow"]]
                body_pixels = old > 0
                for tone in shadow_tones:
                    body_pixels &= np.any(rgb != tone, axis=2)
                assert np.all(new[body_pixels] > 0), (name, state)
    print("OK iki atlas ayni poz sayisinda; bot, silah ve govde pikselleri korunuyor")
    pygame.quit()


if __name__ == "__main__":
    main()
