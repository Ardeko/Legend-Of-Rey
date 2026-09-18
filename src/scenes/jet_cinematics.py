"""Jet'in B4, B9 ve B15 çıkışlarındaki kısa karşılaşmaları.

Jet ayrı geçitleri araştırıp dönüş yolunu açık tutar; savaş yoldaşı
olmaz. Bölüm bitişinde oynar: bulmacayı, kovalamacayı veya uyuyan
sürüyü kesmez. Tamamlanan karşılaşma kayıt yuvasında bir kez görülür.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.systems.save import write_save
from src.ui.dialogue import Line

if TYPE_CHECKING:
    from src.scenes.play import PlayScene

GROUND_Y = 190
PLAYER_X = 176
JET_X = 310
ENTRANCE_X = 374
MOVE_FRAMES = 38
ARRIVE_FRAMES = 48
TALK_FRAMES = 72
LEAVE_FRAMES = 48
FADE_FRAMES = 12

# Düz anahtarlar dil tarayıcısının bütün karakter varyantlarını görmesini sağlar.
ENCOUNTERS = {
    4: ("ch04_jet_return_seen", "line.ch04_jet_return",
        "line.ch04_rey_jet_return", "line.ch04_ardo_jet_return",
        "line.ch04_jet_route", "line.ch04_jet_promise"),
    9: ("ch09_jet_return_seen", "line.ch09_jet_return",
        "line.ch09_rey_jet_return", "line.ch09_ardo_jet_return",
        "line.ch09_jet_route", "line.ch09_jet_promise"),
    15: ("ch15_jet_return_seen", "line.ch15_jet_return",
         "line.ch15_rey_jet_return", "line.ch15_ardo_jet_return",
         "line.ch15_jet_route", "line.ch15_jet_promise"),
}


def play_jet_once(scene: PlayScene, on_finished: Callable[[], None]) -> bool:
    """Çıkış sahnesini açar; görülmüşse normal bölüm bitişine izin verir."""
    flag = ENCOUNTERS[scene.chapter_number][0]
    data = scene.save_data
    if getattr(scene, "_jet_return_seen", False) or (
            data is not None and data.flags.get(flag)):
        return False
    if getattr(scene, "_jet_return_pending", False):
        return True
    scene._jet_return_pending = True

    def complete() -> None:
        scene._jet_return_seen = True
        scene._jet_return_pending = False
        if data is not None:
            data.flags[flag] = True
            write_save(data)
        on_finished()

    scene.scenes.push(JetReturnCinematic, character=scene.character,
                      chapter=scene.chapter_number, on_complete=complete)
    return True


class JetReturnCinematic(StagedScene):
    """Giriş, kısa konuşma, Jet'in yüzü ve kendi yoluna dönüşü."""

    background = "abyss_dark"
    wait_for_input = True

    def on_enter(self, character: str = "rey", chapter: int = 4,
                 on_complete: Callable[[], None] | None = None,
                 **kwargs: object) -> None:
        self.character = character
        self.chapter = chapter
        self._on_complete = on_complete
        self._completed = False
        actors = [
            ActorSpec("player", f"{character}_armed", PLAYER_X, GROUND_Y,
                      facing=1, scale=2),
            ActorSpec("jet", "jet_unarmed", ENTRANCE_X, GROUND_Y,
                      facing=-1, scale=2),
        ]
        if chapter == 9:
            companion = "rey" if character == "ardo" else "ardo"
            actors.append(ActorSpec("companion", f"{companion}_armed",
                                    PLAYER_X - 62, GROUND_Y, scale=2))
        self.ACTORS = tuple(actors)
        self.PANELS = self._panels()
        self.motes = MoteField(count=12, drift=-0.10, tone="stone_dark")
        super().on_enter(**kwargs)
        self.add_light(264, GROUND_Y - 54, 115,
                       palette.color("ember_light"), peak=0.32)

    def _panels(self) -> tuple[Panel, ...]:
        _flag, opening, rey_reply, ardo_reply, route, promise = ENCOUNTERS[
            self.chapter]
        reply = ardo_reply if self.character == "ardo" else rey_reply
        return (
            Panel(ARRIVE_FRAMES, "gelis", fade_in=FADE_FRAMES,
                  wait_for_input=False, cues=(
                Cue("jet", state="run", face=-1,
                    move_to=(JET_X, GROUND_Y), move_frames=MOVE_FRAMES),
                Cue("jet", state="idle", delay=MOVE_FRAMES),
            )),
            Panel(TALK_FRAMES, "karsilasma", lines=(
                Line("jet", opening), Line(self.character, reply),
                Line("jet", route),
            )),
            Panel(TALK_FRAMES, "soz", closeup="jet",
                  line=Line("jet", promise), fade_in=FADE_FRAMES),
            Panel(LEAVE_FRAMES, "ayrilis", fade_in=FADE_FRAMES,
                  fade_out=FADE_FRAMES, wait_for_input=False, cues=(
                      Cue("jet", state="run", face=1,
                          move_to=(INTERNAL_WIDTH + 32, GROUND_Y),
                          move_frames=LEAVE_FRAMES),
                  )),
        )

    def on_stage_panel(self, panel: Panel) -> None:
        # Yakın planda aynı yüzü diyalog kutusunda ikinci kez çizme.
        self.dialogue.show_portrait = not bool(panel.closeup)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        surface.fill(palette.color("abyss_dark"))
        surface.fill(palette.color("stone_darkest"),
                     (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
        surface.fill(palette.color("stone"), (0, GROUND_Y, INTERNAL_WIDTH, 2))
        for x in (42, 406):
            surface.fill(palette.color("stone_dark"), (x, 30, 20, GROUND_Y - 30))
            surface.fill(palette.color("stone"), (x - 3, 28, 26, 4))
        for y in range(48, GROUND_Y, 32):
            surface.fill(palette.color("stone_darkest"),
                         (62, y, 344, 1))
        if self.chapter == 9:
            self._draw_bells(surface)
        elif self.chapter == 15:
            self._draw_gate(surface)
        else:
            surface.fill(palette.color("earth_dark"), (234, GROUND_Y - 5, 44, 5))
        # Aynı sıcak ışık üç görünümü birbirine bağlar; Yankı'nın moru yok.
        surface.fill(palette.color("earth"), (262, 130, 4, 30))
        surface.fill(palette.color("ember"), (260, 123, 8, 12))
        surface.fill(palette.color("gold"), (263, 120, 3, 10))

    def _draw_bells(self, surface: pygame.Surface) -> None:
        for index, x in enumerate((154, 240, 326)):
            y = 48 + index % 2 * 9
            surface.fill(palette.color("stone"), (x, 24, 2, y - 24))
            pygame.draw.polygon(surface, palette.color("earth"), (
                (x - 8, y), (x + 9, y), (x + 14, y + 20), (x - 13, y + 20)))
            surface.fill(palette.color("gold"), (x - 13, y + 20, 28, 2))
            surface.fill(palette.color("stone_light"), (x - 1, y + 22, 4, 4))

    def _draw_gate(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("ink"), (64, 56, 54, GROUND_Y - 56))
        for x in range(67, 118, 10):
            surface.fill(palette.color("stone"), (x, 56, 3, GROUND_Y - 56))
        surface.fill(palette.color("stone_light"), (64, 108, 54, 3))

    def on_finished(self) -> None:
        if self._completed:
            return
        self._completed = True
        self.scenes.pop()
        if self._on_complete is not None:
            self._on_complete()
