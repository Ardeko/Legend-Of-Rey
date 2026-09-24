"""Ses darbesi: uc ince basinc halkasi, ortak B8/B9/B15 cizimi."""
from __future__ import annotations

import pygame

from src.art import palette
from src.systems.resonance import ResonanceState


def draw(surface: pygame.Surface, offset: tuple[int, int],
         pulse: ResonanceState, character: str) -> None:
    if not pulse.active:
        return
    center = (round(pulse.x) - offset[0], round(pulse.y) - offset[1])
    radius = round(pulse.radius)
    fade = 1.0 - pulse.progress
    base = palette.color("echo_bright" if character != "ardo" else "ember_light")
    # Dis halka gercek temas menzilinde. Icerideki izler sesi daha
    # buyuk bir hasar patlamasi gibi gostermeden yayilmayi anlatir.
    for lag, strength in ((12, 0.18), (5, 0.30), (0, 0.78)):
        r = radius - lag
        if r < 2:
            continue
        tone = tuple(round(c * strength * (0.35 + 0.65 * fade)) for c in base)
        pygame.draw.circle(surface, tone, center, r, 1)
