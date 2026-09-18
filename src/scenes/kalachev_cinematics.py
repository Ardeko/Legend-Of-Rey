"""Kalachev yuzu - 32 piksellik figuru taninir kilar.

`docs/kalachev.md` 3: Rey icin tanisma, Ardo icin eski bir dost.
Oyunda yururken kim oldugu okunmuyordu: bir balon "onu taniyorsun"
diyordu, adi neredeyse hic soylenmiyordu, yakin plan yoktu.

Bu sahne Jet'in kilic sahnesiyle ayni dil: yaklasma, bakisma, **yuz**,
adi soylenen bir closeup. B5 kelimesiz kalir (ilk gorus), B15 sessiz
kalir (suru). Burasi yurudugu anlar: B6 tanisma, B10 tuzak, B13 kapi,
B18 son.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

APPROACH_FRAMES = 70
LOOK_FRAMES = 90
NAME_FRAMES = 110
HOLD_FRAMES = 50

GROUND_Y = INTERNAL_HEIGHT * 0.70
PLAYER_X = INTERNAL_WIDTH * 0.36
KALACHEV_X = INTERNAL_WIDTH * 0.66
KALACHEV_FROM = INTERNAL_WIDTH + 28.0
ALLY_X = PLAYER_X - 36.0


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
                 **kwargs: object) -> None:
        self.character = character
        self.beat = beat
        self.ACTORS = self._build_actors()
        super().on_enter(**kwargs)
        self.vignette = 0.38
        self.add_light(int(KALACHEV_X) - 8, int(GROUND_Y) - 28, 70,
                       palette.color("bone"), peak=0.42)
        self._write()

    def _build_actors(self) -> tuple[ActorSpec, ...]:
        actors = [
            ActorSpec("player", self.character, PLAYER_X, GROUND_Y,
                      facing=1, state="idle", scale=2),
            ActorSpec("kalachev", "kalachev", KALACHEV_FROM, GROUND_Y,
                      facing=-1, state="run", scale=2, silhouette=True),
        ]
        if self.beat in ("meet", "last"):
            actors.insert(0, ActorSpec(
                "ally", other_character(self.character), ALLY_X, GROUND_Y,
                facing=1, state="idle", scale=2))
        return tuple(actors)

    def _write(self) -> None:
        """Repliki panolara yazar. Anahtarlar duz dize."""
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
                                  else p.wait_for_input))
            for p in self.panels
        )

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
        surface.fill(palette.color("abyss_dark"))
        ground = int(GROUND_Y)
        surface.fill(palette.color("earth_dark"),
                     (0, ground, INTERNAL_WIDTH, INTERNAL_HEIGHT - ground))
        surface.fill(palette.color("earth"), (0, ground, INTERNAL_WIDTH, 1))

    def on_finished(self) -> None:
        self.scenes.pop()
