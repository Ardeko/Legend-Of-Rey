"""Epilog 3 - Ates basi ve jenerik.

B8'in ates basi: iki siluet, bir yara, bir ders. Burada ayni ates,
ama koyun meydaninda ve kalabalik. B1'de evlerine kacan koy bu gece
atesin basinda; koylunun kendi cumlesi: *"Kimse evine kacmiyor."*

## Son panel: Cemo'nun resmi

Evin duvari yakindan: kapi ve iki yaninda Cemo'nun resmi - isaret,
Rey, Ardo, Cemo, Emre abi ve en buyuk figur olarak bagiran amca.
Jenerik sagda akiyor, **resmin ustune binmiyor**: ilk surumde yazi
resmin ve aktorlerin ustunden geciyordu ve hicbiri okunmuyordu.
Oyunun son goruntusu bir cocugun resmi.

## Meydan

Koyun epilogdaki hali (`EPILOGUE_SCENERY`: han, can iskelesi) ayni
kameradan. Evler meydanin **karsi yakasinda** (`HOUSE_BASE_Y`):
2x aktorler 1x evlerle ayni zemine basinca evler kulube gibi
kaliyordu; arada meydan acilinca olcek fark derinlik olarak okunuyor.

## Kurallar

* **Yanki konusmuyor.** Rey'in kafasi sessiz; son cumlesi bunu
  soyluyor ama etrafi gurultulu.
* **Romantik yay sozle soylenmiyor** (`docs/yapi.md`). B16'da yoldasi
  kaldirdiysan soru panelinde kalp balonu var; kaldirmadiysan yok.
* Yoldasin mesafesi B16'daki jeste gore (`ending.ALLY_DISTANCE`).
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes import epilogue_render
from src.scenes.ending import ALLY_DISTANCE
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.systems.homecoming import Homecoming
from src.ui import balloon, credits
from src.ui.dialogue import Line
from src.world import village_backdrop
from src.world.rooms.epilogue import EPILOGUE_SCENERY, HOME_INDEX, HOUSES

GROUND_Y = 200
FIRE_X = INTERNAL_WIDTH // 2
PLAYER_X = FIRE_X - 88.0
CEMO_X = FIRE_X - 46.0
JET_X = FIRE_X + 50.0
VILLAGER_XS = (FIRE_X + 96.0, FIRE_X + 140.0, FIRE_X - 196.0)
# Yoldas oyuncunun gerisinde; B16 jestine gore ne kadar geride.
ALLY_BEHIND = 18.0
# Atesten kivilcim - bu kadar karede bir, kucuk bir demet.
SPARK_EVERY = 9
# Meydanin karsi yakasi: evlerin tabani. Aktorler GROUND_Y'de, onde.
HOUSE_BASE_Y = 172
# Kamera koyun bu x'ine bakiyor: ates hanla kucuk evin arasindaki
# acikta. (x=0'da B1'in kuyusu atesin tam arkasina dusuyordu.)
SQUARE_CAMERA_X = 296
# Son panel: duvar yakindan, 3x. Kapi solda, jenerik sagda.
WALL_SCALE = 3
WALL_GROUND_Y = 236
WALL_DOOR_X = 140
CREDITS_X = 376


class HomecomingFireCinematic(StagedScene):
    """Aksam, meydanda ates. Son sozler, sonra Cemo'nun resmi ve jenerik."""

    background = "void"
    wait_for_input = True
    postfx_grade = "village"

    def on_enter(self, character: str = "rey",
                 homecoming: Homecoming | None = None,
                 **kwargs: object) -> None:
        self.character = character
        if homecoming is None:
            from src.systems.save import read_save
            data, _status = read_save()
            homecoming = Homecoming.from_save(data, character)
        self.homecoming = homecoming
        self.credit_lines = credits.lines_for(
            homecoming.ghost, homecoming.lifted, homecoming.tidy,
            homecoming.clean)
        self.credit_scroll = 0.0
        self.ACTORS = self._actors()
        self.PANELS = self._panels()
        super().on_enter(**kwargs)
        self.motes = MoteField(20, drift=-0.25, sway=0.4, tone="ember_light")
        self.add_light(FIRE_X, GROUND_Y - 16, 150,
                       palette.color("ember_light"), peak=0.50)
        total = sum(p.frames for p in self.PANELS) + 400
        self.game.music.hold("emotional", total)

    # --- Kurulum ------------------------------------------------------------
    def _actors(self) -> tuple[ActorSpec, ...]:
        home = self.homecoming
        behind = ALLY_DISTANCE.get(home.gesture, ALLY_DISTANCE["nod"]) - 44.0
        ally_x = PLAYER_X - ALLY_BEHIND - behind
        actors = [
            ActorSpec("ally", home.ally, ally_x, GROUND_Y, facing=1, scale=2),
            ActorSpec("player", self.character, PLAYER_X, GROUND_Y, facing=1,
                      scale=2),
            ActorSpec("cemo", "cemo", CEMO_X, GROUND_Y, facing=1, scale=2),
            ActorSpec("jet", "jet_unarmed", JET_X, GROUND_Y, facing=-1,
                      scale=2),
        ]
        for index, x in enumerate(VILLAGER_XS):
            facing = -1 if x > FIRE_X else 1
            actors.append(ActorSpec(f"koylu{index}", "villager", x, GROUND_Y,
                                    facing=facing, scale=2))
        return tuple(actors)

    def _panels(self) -> tuple[Panel, ...]:
        """Anahtarlar **duz dize** - hesaplanmis ad testten kaciyor."""
        home = self.homecoming
        question = (Line("cemo", "line.epi_cemo_leaving") if home.ardo
                    else Line("cemo", "line.epi_cemo_voices"))
        answer = (Line("ardo", "line.epi_ardo_fire") if home.ardo
                  else Line("rey", "line.epi_rey_fire"))
        panels = [
            Panel(80, "ates", wait_for_input=False, fade_in=36),
            Panel(60, "koy", lines=(
                Line("villager", "line.epi_villager_fire"),
                Line("jet", "line.epi_jet_fire"))),
        ]
        # Kadeh yalnizca Kalachev gercekten olduyse (`ending.py` ile ayni
        # kural: sahne olmamis bir seye uzulmesin).
        if home.kalachev:
            panels.append(Panel(60, "kadeh", lines=(
                Line("ardo", "line.epi_ardo_efe"),)))
        panels.append(Panel(60, "soru", lines=(question, answer),
                            cues=(Cue("cemo", face=-1),)))
        # Jenerik tus beklemiyor; basili tutunca 3x hizlaniyor
        # (`CLAUDE.md` 9 - sert kesme yok).
        frames = int(credits.length(self.credit_lines) / credits.SCROLL_SPEED) + 40
        # Duvar yakindan: aktorler cekimde yok.
        hidden = tuple(Cue(spec.name, visible=False) for spec in self.ACTORS)
        panels.append(Panel(frames, "resim", wait_for_input=False,
                            fade_in=30, cues=hidden))
        return tuple(panels)

    # --- Dongu --------------------------------------------------------------
    def update_cinematic(self) -> None:
        super().update_cinematic()
        panel = self.panel
        if panel is None:
            return
        if panel.name == "resim":
            self.credit_scroll += credits.SCROLL_SPEED
        elif self.frame % SPARK_EVERY == 0:
            self.burst(FIRE_X, GROUND_Y - 20, "spark", count=3)

    # --- Cizim --------------------------------------------------------------
    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        if panel.name == "resim":
            self._draw_drawing_wall(surface)
            return
        village_backdrop.draw_sky(surface, SQUARE_CAMERA_X, self.frame)
        # Evlerin tabani (B1'de y=192) meydanin karsi yakasina otursun.
        village_backdrop.draw(surface, (SQUARE_CAMERA_X, 192 - HOUSE_BASE_Y),
                              self.frame, village_backdrop.NIGHT,
                              EPILOGUE_SCENERY)
        surface.fill(palette.color("earth_dark"),
                     (0, HOUSE_BASE_Y, INTERNAL_WIDTH,
                      INTERNAL_HEIGHT - HOUSE_BASE_Y))
        surface.fill(palette.color("earth"),
                     (0, HOUSE_BASE_Y, INTERNAL_WIDTH, 1))
        epilogue_render.draw_bonfire(surface, FIRE_X, GROUND_Y, self.frame,
                                     size=2)

    def _draw_drawing_wall(self, surface: pygame.Surface) -> None:
        """Evin duvari, yakindan: kapi, iki yaninda resim; jenerik sagda."""
        scale = WALL_SCALE
        surface.fill(palette.color("ink_soft"))
        for row in range(3, INTERNAL_HEIGHT, 4 * scale):
            surface.fill(palette.color("void"), (0, row, INTERNAL_WIDTH, 1))
        surface.fill(palette.color("earth_dark"),
                     (0, WALL_GROUND_Y, INTERNAL_WIDTH,
                      INTERNAL_HEIGHT - WALL_GROUND_Y))
        surface.fill(palette.color("earth"),
                     (0, WALL_GROUND_Y, INTERNAL_WIDTH, 1))
        door = epilogue_render.door_size(HOUSES[HOME_INDEX])
        door_left, door_right = epilogue_render.draw_door(
            surface, WALL_DOOR_X, WALL_GROUND_Y, door, scale)
        left, right = epilogue_render.drawing_halves(door_left, door_right,
                                                     scale)
        base = WALL_GROUND_Y - epilogue_render.DRAWING_LIFT * scale
        epilogue_render.draw_chalk_drawing(surface, left, right, base, 1.0,
                                           scale=scale)
        credits.draw(surface, self.credit_scroll, self.credit_lines,
                     CREDITS_X)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        if panel.name == "soru" and self.homecoming.lifted:
            # B16'da onu kaldirdiysan burada bir kalp var - sozsuz.
            balloon.draw(surface, "heart", int(PLAYER_X - 10),
                         int(GROUND_Y) - 76, frame=self.frame,
                         colour=palette.color("blood_bright"))

    def on_finished(self) -> None:
        from src.ui.menu import MainMenuScene
        self.scenes.set_root(MainMenuScene)
