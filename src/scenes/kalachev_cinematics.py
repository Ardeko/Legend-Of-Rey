"""Kalachev yuzu - 32 piksellik figuru taninir kilar.

`docs/kalachev.md` 3: Rey icin tanisma, Ardo icin eski bir dost.
Oyunda yururken kim oldugu okunmuyordu: bir balon "onu taniyorsun"
diyordu, adi neredeyse hic soylenmiyordu, yakin plan yoktu.

Bu sahne Jet'in kilic sahnesiyle ayni dil: yaklasma, bakisma, **yuz**,
adi soylenen bir closeup. B5'te suyun iki kiyisinda ilk karsilasma
vardir; Rey adini B6'da Ardo'dan ogrenir. B15 sessiz kalir (suru).
Oteki anlar: B6 tanisma, B10 tuzak, B13 kapi, B18 son.
"""
from __future__ import annotations

from collections.abc import Callable

import pygame

from src.art import palette, tileset
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line
from src.world import cave_backdrop

APPROACH_FRAMES = 70
LOOK_FRAMES = 90
NAME_FRAMES = 110
HOLD_FRAMES = 50

GROUND_Y = INTERNAL_HEIGHT * 0.70
PLAYER_X = INTERNAL_WIDTH * 0.36
KALACHEV_X = INTERNAL_WIDTH * 0.66
KALACHEV_FROM = INTERNAL_WIDTH + 28.0
ALLY_X = PLAYER_X - 36.0
SIGHTING_FADE_FRAMES = 12
SIGHTING_CHARGE_FRAMES = 42
SIGHTING_CHARGE_X = INTERNAL_WIDTH - 74
WATER_LEFT = 202
WATER_RIGHT = 260


class KalachevCinematic(StagedScene):
    """Golge yurur, isiga cikar, adi soylenir."""

    background = "void"
    wait_for_input = True

    PANELS = (
        Panel(APPROACH_FRAMES, "yaklasma", wait_for_input=False, cues=(
            Cue("kalachev", state="run", face=-1, silhouette=True,
                move_to=(KALACHEV_X, GROUND_Y), move_frames=64,
                move_ease="out", sound="swing_heavy"),
            Cue("player", state="idle", face=1),
        )),
        Panel(LOOK_FRAMES, "bakisma"),
        Panel(NAME_FRAMES, "isim", closeup="kalachev"),
        Panel(HOLD_FRAMES, "dur", wait_for_input=False, cues=(
            Cue("kalachev", state="idle", face=-1),
            Cue("player", state="idle", face=1),
        )),
    )

    def on_enter(self, character: str = "rey", beat: str = "meet",
                 on_complete: Callable[[], None] | None = None,
                 **kwargs: object) -> None:
        self.character = character
        self.beat = beat
        self._on_complete = on_complete
        self._completed = False
        if beat == "sighting":
            self.PANELS = self._sighting_panels()
        self.ACTORS = self._build_actors()
        super().on_enter(**kwargs)
        self.vignette = 0.38
        self.add_light(int(KALACHEV_X) - 8, int(GROUND_Y) - 28, 70,
                       palette.color("bone"), peak=0.42)
        if beat == "sighting":
            self.add_light(int(PLAYER_X), int(GROUND_Y) - 24, 60,
                           palette.color("stone"), peak=0.24)
        self._write()

    def _sighting_panels(self) -> tuple[Panel, ...]:
        """Iki kiyi, soru, yakin plan ve suruye dogru hamle."""
        return (
            Panel(APPROACH_FRAMES, "yaklasma", wait_for_input=False,
                  fade_in=SIGHTING_FADE_FRAMES, cues=(
                      Cue("kalachev", state="run", face=1,
                          move_to=(KALACHEV_X, GROUND_Y), move_frames=64,
                          move_ease="out"),
                  )),
            Panel(LOOK_FRAMES, "bakisma"),
            Panel(NAME_FRAMES, "isim", closeup="kalachev",
                  fade_in=SIGHTING_FADE_FRAMES),
            Panel(LOOK_FRAMES, "karar", fade_in=SIGHTING_FADE_FRAMES),
            Panel(APPROACH_FRAMES, "dur", wait_for_input=False,
                  fade_out=SIGHTING_FADE_FRAMES, cues=(
                      Cue("kalachev", state="run", face=1,
                          move_to=(SIGHTING_CHARGE_X, GROUND_Y),
                          move_frames=SIGHTING_CHARGE_FRAMES),
                      Cue("kalachev", state="attack2",
                          delay=SIGHTING_CHARGE_FRAMES, sound="swing_heavy"),
                  )),
        )

    def _build_actors(self) -> tuple[ActorSpec, ...]:
        actors = [
            ActorSpec("player", (f"{self.character}_armed"
                                 if self.beat == "sighting" else self.character),
                      PLAYER_X, GROUND_Y,
                      facing=1, state="idle", scale=2),
            ActorSpec("kalachev", "kalachev",
                      WATER_RIGHT + 18 if self.beat == "sighting" else KALACHEV_FROM,
                      GROUND_Y,
                      facing=-1, state="run", scale=2, silhouette=True),
        ]
        if self.beat in ("meet", "last"):
            actors.insert(0, ActorSpec(
                "ally", other_character(self.character), ALLY_X, GROUND_Y,
                facing=1, state="idle", scale=2))
        return tuple(actors)

    def _write(self) -> None:
        """Repliki panolara yazar. Anahtarlar duz dize."""
        if self.beat == "sighting":
            beats = self._sighting_beats()
        else:
            beats = (self._meet_beats() if self.beat == "meet"
                     else self._walk_beats())
        faces: dict[str, tuple[Cue, ...]] = {
            "bakisma": (
                Cue("kalachev", silhouette=False, state="idle", face=-1),
                Cue("player", state="idle", face=1),
                Cue("ally", state="idle", face=1),
            ),
            "isim": (
                Cue("kalachev", state="idle", face=-1),
                Cue("player", state="idle", face=1),
            ),
        }
        self.panels = tuple(
            Panel(p.frames, p.name, lines=beats.get(p.name, ()),
                  cues=p.cues or faces.get(p.name, ()),
                  closeup=p.closeup,
                  wait_for_input=(True if p.wait_for_input is None
                                  else p.wait_for_input),
                  fade_in=p.fade_in, fade_out=p.fade_out)
            for p in self.panels
        )

    def _sighting_beats(self) -> dict[str, tuple[Line, ...]]:
        """B5: Rey yabanciya seslenir; Ardo eski dostuyla atisir."""
        if self.character == "ardo":
            return {
                "bakisma": (
                    Line("ardo", "line.ch05_ardo_kalachev_call"),
                    Line("kalachev", "line.ch05_kalachev_late"),
                ),
                "isim": (
                    Line("ardo", "line.ch05_ardo_kalachev_pack"),
                    Line("kalachev", "line.ch05_kalachev_count"),
                ),
                "karar": (
                    Line("ardo", "line.ch05_ardo_kalachev_back"),
                    Line("kalachev", "line.ch05_kalachev_below"),
                ),
            }
        return {
            "bakisma": (
                Line("rey", "line.ch05_rey_kalachev_call"),
                Line("kalachev", "line.ch05_kalachev_quiet"),
            ),
            "isim": (
                Line("rey", "line.ch05_rey_kalachev_child"),
                Line("kalachev", "line.ch05_kalachev_valve"),
            ),
            "karar": (
                Line("rey", "line.ch05_rey_kalachev_stay"),
                Line("kalachev", "line.ch05_kalachev_pack"),
            ),
        }

    def _meet_beats(self) -> dict[str, tuple[Line, ...]]:
        """B6: Rey bir yabanciyla, Ardo eski dostuyla karsilasir."""
        if self.character == "ardo":
            return {
                "bakisma": (
                    Line("ardo", "line.ch06_ardo_kalachev"),
                    Line("kalachev", "line.ch06_kalachev_familiar"),
                ),
                "isim": (
                    Line("ardo", "line.ch06_kalachev_ardo_know"),
                    Line("kalachev", "line.ch06_kalachev_debt"),
                ),
            }
        return {
            "bakisma": (Line("ardo", "line.ch06_kalachev_ardo_intro"),),
            "isim": (
                Line("rey", "line.ch06_kalachev_rey_ask"),
                Line("ardo", "line.ch06_kalachev_ardo_stay"),
                Line("kalachev", "line.ch06_kalachev_meet"),
                Line("echo", "line.ch06_echo_kalachev"),
            ),
        }

    def _walk_beats(self) -> dict[str, tuple[Line, ...]]:
        """B10 / B13 / B18: gozlem yerine kisa bir karsilik."""
        ardo = self.character == "ardo"
        if self.beat == "trap":
            line = (Line("ardo", "line.ch10_ardo_kalachev") if ardo
                    else Line("rey", "line.ch10_rey_kalachev"))
            reply = ("line.ch10_kalachev_detour" if ardo
                     else "line.ch10_kalachev_crack")
        elif self.beat == "gate":
            line = (Line("ardo", "line.ch13_ardo_kalachev") if ardo
                    else Line("rey", "line.ch13_rey_kalachev"))
            reply = ("line.ch13_kalachev_late" if ardo
                     else "line.ch13_kalachev_child")
        else:
            line = (Line("ardo", "line.ch18_ardo_kalachev") if ardo
                    else Line("rey", "line.ch18_rey_kalachev"))
            reply = ("line.ch18_kalachev_debt" if ardo
                     else "line.ch18_kalachev_gate")
        return {"bakisma": (line,),
                "isim": (Line("kalachev", reply),)}

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        if self.beat == "sighting":
            cave_backdrop.draw(surface, (0, 0), self.frame)
        else:
            surface.fill(palette.color("abyss_dark"))
        ground = int(GROUND_Y)
        surface.fill(palette.color("earth_dark"),
                     (0, ground, INTERNAL_WIDTH, INTERNAL_HEIGHT - ground))
        surface.fill(palette.color("earth"), (0, ground, INTERNAL_WIDTH, 1))
        if self.beat == "sighting":
            stones = tileset.shared()
            for x in range(0, INTERNAL_WIDTH, TILE_SIZE):
                for y in range(ground, INTERNAL_HEIGHT, TILE_SIZE):
                    surface.blit(stones.wall(x // TILE_SIZE, y // TILE_SIZE,
                                              y == ground), (x, y))
            self._draw_sighting_water(surface, ground)

    def _draw_sighting_water(self, surface: pygame.Surface, ground: int) -> None:
        """Iki tas kiyi arasinda akan su ve karsi duvardaki ust vana."""
        for x in (38, 430):
            surface.fill(palette.color("stone_darkest"),
                         (x, 28, 18, ground - 28))
            surface.fill(palette.color("stone_dark"), (x, 28, 2, ground - 28))
        width = WATER_RIGHT - WATER_LEFT
        surface.fill(palette.color("abyss_dark"),
                     (WATER_LEFT, ground, width, INTERNAL_HEIGHT - ground))
        surface.fill(palette.color("stone_dark"),
                     (WATER_LEFT, ground + 12, width, INTERNAL_HEIGHT - ground))
        for row in range(ground + 12, INTERNAL_HEIGHT, 8):
            drift = (self.frame // 3 + row) % (width - 16)
            surface.fill(palette.color("stone_light"),
                         (WATER_LEFT + drift, row, 14, 1))
        center = (430, ground - 48)
        tone = palette.color("earth")
        pygame.draw.circle(surface, tone, center, 11, 2)
        pygame.draw.line(surface, tone, (419, center[1]), (441, center[1]), 2)
        pygame.draw.line(surface, tone, (430, center[1] - 11),
                         (430, center[1] + 11), 2)

    def on_finished(self) -> None:
        if self._completed:
            return
        self._completed = True
        self.scenes.pop()
        if self._on_complete is not None:
            self._on_complete()
