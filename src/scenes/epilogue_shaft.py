"""Epilog 1 - Kuyunun dibi. Jet'in ipi.

`docs/yapi.md` Epilog. Kapanisin isigi (`DawnCinematic`) tunelin
ucundaki kuyunun agzi: Jet B4'te *"yukari cikmak isteyen olursa diye
bir ip bagladim"* demisti, B15'te *"donuste bagirmana gerek yok. Adimi
soylemen yeter; burada olacagim."* Bu oda o sozun **oynanis**
karsiligi: oyuncu ipe yurur ve tus ona "Seslen" diyor.

## Kisa ve dovussuz

Otuz saniyelik bir oda. Dusman yok, bulmaca yok; tek eylem Jet'e
seslenmek. Oyuncu kontrolu geri aliyor - kapanis boyunca izleyen biri
ilk kez yeniden yuruyor. `chapter_number` 0: bolum karti ve ilerleme
damgasi yok, cunku bu bir bolum degil kapanisin devami.

## Mum Bekcisi'nin son mumu (25.09.2026)

B3'te bes mumla oturuyordu, her gorunuste bir eksik: B7 dort, B12 uc,
B16 iki. B12'de Ardo sordu: *"Her indigimde bir mum eksik. Sonuncusunda
ne olacak?"* Cevap burada: ipe giden yolda **tek mumuyla** oturuyor,
oyuncu yaklasinca son mumu kendisi sonduruyor ve karanliga karisiyor.
Konusmuyor - hic konusmadi. Yukarida gunes var; mumuna gerek kalmadi.

## Yanki yok

`self.echo = None` (vinyet de gidiyor). Rey sesi B18'de susturdu;
kapanisin kurali *"Rey'in kafasi ilk kez sessiz"* burada da gecerli.
Ardo'nun Iz Surme'si de kapali - epilogda duyu mekanigi yok.
"""
from __future__ import annotations

from src.config import TILE_SIZE
from src.core.input import Action
from src.entities.companion import Companion
from src.entities.npc import Npc
from src.scenes import epilogue_render
from src.scenes.play import PlayScene
from src.systems.homecoming import Homecoming
from src.ui.dialogue import Line
from src.world import cave_backdrop
from src.entities.candle_keeper import CandleKeeper
from src.world.rooms.epilogue import (
    KEEPER_TILE, ROPE_COLUMN, SHAFT_LEVEL, SHAFT_MOUTH,
)
from src.world.tilemap import TileMap

# Cemo isigi gorunce konusuyor - oyuncu once bir iki adim atsin.
LIGHT_LINE_FRAME = 40
# Oyuncu ipe bu kadar yaklasinca "Seslen" beliriyor (piksel).
ROPE_REACH = 22.0
# Konusma bitince tirmanisa gecmeden once herkes ipin dibinde toplanir.
GATHER_FRAMES = 50
# Ip, Jet cevap verince bu kadar sallaniyor ve bu hizla duruluyor.
TUG_DECAY = 0.012
# Bekci: bu kadar yaklasinca oyuncu onu fark ediyor (piksel).
KEEPER_REACH = 44.0
# Soz bittikten bu kadar sonra son mumu sonduruyor, sonra bu kadar
# karede karanliga karisiyor.
KEEPER_SNUFF_AT = 24
KEEPER_FADE_FRAMES = 72


class EpilogueShaftScene(PlayScene):
    """Kuyunun dibi - ipe yuru, Jet'e seslen."""

    footstep_sound = "step_stone"
    postfx_grade = "dawn"
    companion_orders = False
    ambience_preset = "dust"
    music_context = "explore"

    def on_enter(self, character: str = "rey",
                 homecoming: Homecoming | None = None,
                 **kwargs: object) -> None:
        # `setup()` super().on_enter icinde cagriliyor - once yazilmali.
        self.homecoming = homecoming
        super().on_enter(character=character, **kwargs)

    def setup(self) -> None:
        if self.homecoming is None:
            self.homecoming = Homecoming.from_save(self.save_data,
                                                   self.character)
        self.tilemap = TileMap(SHAFT_LEVEL.terrain_rows)
        spawn = SHAFT_LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        self.echo = None
        self.tracking = None

        self.companion_key = self.homecoming.ally
        self.companion = Companion(self, spawn.x - 22, spawn.feet_y,
                                   self.companion_key)
        cemo_at = SHAFT_LEVEL.first("cemo")
        self.cemo = Npc("cemo", cemo_at.x, cemo_at.feet_y, gap=20.0,
                        speed=1.2)

        rope = SHAFT_LEVEL.first("trigger")
        self.rope_x = ROPE_COLUMN * TILE_SIZE + TILE_SIZE // 2
        self.rope_bottom = int(rope.feet_y) - 12
        self.floor_y = int(rope.feet_y)

        keeper_x = KEEPER_TILE * TILE_SIZE + TILE_SIZE // 2
        self.keeper = CandleKeeper(keeper_x, self.floor_y, candles=1)
        # wait -> seen -> snuff -> fade -> gone
        self.keeper_state = "wait"
        self.keeper_frames = 0

        self.frames = 0
        self.light_said = False
        self.called = False
        self.tug = 0.0
        self.answered = False
        self.gather_frames = 0
        self.leaving = False
        # E hem repligi ilerletiyor hem "Seslen" diyor: Cemo'nun repligini
        # kapatan basis ayni karede Jet'e seslenmemeli.
        self._dialogue_was_open = False

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.companion.update()
        self._update_cemo()
        self.tug = max(0.0, self.tug - TUG_DECAY)

        if not self.light_said and self.frames >= LIGHT_LINE_FRAME:
            self.light_said = True
            self.say(Line("cemo", "line.epi_cemo_light"))

        self._update_keeper()
        if not self.called:
            self._offer_call()
        else:
            self._watch_answer()
            if self.dialogue.done and not self.leaving:
                self._gather()
        self._dialogue_was_open = not self.dialogue.done

    def _update_cemo(self) -> None:
        if self.called and self.dialogue.done:
            # Konusma bitti: herkes ipin dibinde.
            self.cemo.walk_to(self.rope_x - 14)
        else:
            self.cemo.follow(self.player.body.center_x, self.player.facing)
        self.cemo.update()

    def _update_keeper(self) -> None:
        """Son mum: fark et, sondur, karis, sor."""
        keeper = self.keeper
        keeper.update()
        state = self.keeper_state
        if state == "wait":
            near = (abs(self.player.body.center_x - keeper.x)
                    < KEEPER_REACH)
            if near and self.light_said and self.dialogue.done:
                self.keeper_state = "seen"
                self.say_player("line.epi_rey_keeper", "line.epi_ardo_keeper")
        elif state == "seen":
            if self.dialogue.done:
                self.keeper_state = "snuff"
                self.keeper_frames = 0
        elif state == "snuff":
            self.keeper_frames += 1
            if self.keeper_frames >= KEEPER_SNUFF_AT:
                keeper.lit = 0
                x, y = keeper.candle_point()
                self.particles.burst(x, y, 6, path="soot",
                                     speed=(0.2, 0.7))
                self.game.play_sound("phantom_fade")
                self.keeper_state = "fade"
                self.keeper_frames = 0
        elif state == "fade":
            self.keeper_frames += 1
            keeper.fade = max(0.0, 1.0 - self.keeper_frames
                              / KEEPER_FADE_FRAMES)
            if keeper.fade <= 0.0 and self.dialogue.done:
                self.keeper_state = "gone"
                self.say(Line("cemo", "line.epi_cemo_keeper"),
                         Line(self.character,
                              "line.epi_ardo_keeper_gone"
                              if self.homecoming.ardo
                              else "line.epi_rey_keeper_gone"))

    @property
    def keeper_busy(self) -> bool:
        """Bekcinin ani suruyor mu - Jet'e seslenmek o bitince."""
        return self.keeper_state not in ("wait", "gone")

    def _offer_call(self) -> None:
        near = abs(self.player.body.center_x - self.rope_x) < ROPE_REACH
        if (not near or not self.dialogue.done or self._dialogue_was_open
                or self.keeper_busy):
            return
        self.prompts.offer("rope", self.rope_x, self.rope_bottom - 24,
                           verb_key="prompt.call")
        if self.game.input.pressed(Action.INTERACT):
            self._call()

    def _call(self) -> None:
        """B15'in sozu: bagirmak yok, adini soylemek yeter.

        Ardo once bagiriyor, sonra hatirliyor - Rey dogrudan fisildar
        gibi soyluyor. Ayni an, iki karakter, iki huy.
        """
        self.called = True
        ardo = self.homecoming.ardo
        self.say(Line(self.character, "line.epi_ardo_call" if ardo
                      else "line.epi_rey_call"),
                 Line("jet", "line.epi_jet_answer"),
                 Line("cemo", "line.epi_cemo_who"),
                 Line(self.character, "line.epi_ardo_who" if ardo
                      else "line.epi_rey_who"))

    def _watch_answer(self) -> None:
        """Jet cevap verdigi AN ip geriliyor - replikle ayni karede."""
        current = self.dialogue.current
        if (not self.answered and current is not None
                and current.key == "line.epi_jet_answer"):
            self.answered = True
            self.tug = 1.0
            self.game.play_sound("swing_light")

    def _gather(self) -> None:
        self.gather_frames += 1
        if self.gather_frames < GATHER_FRAMES:
            return
        self.leaving = True
        self._climb()

    def _climb(self) -> None:
        """Yukari: oyunun basindaki dikey yolculugun safak aynasi."""
        from src.scenes.epilogue_village import EpilogueVillageScene
        from src.scenes.vertical_journey import VerticalJourneyScene
        self.scenes.replace(
            VerticalJourneyScene, direction="up", variant="dawn",
            character=self.character, next_scene=EpilogueVillageScene,
            next_kwargs={"character": self.character,
                         "homecoming": self.homecoming})

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame, depth=0.0)
        epilogue_render.draw_light_beam(
            surface, offset, SHAFT_MOUTH[0] * TILE_SIZE,
            SHAFT_MOUTH[1] * TILE_SIZE, 0, self.floor_y)

    def draw_foreground(self, surface, offset) -> None:
        self.keeper.draw(surface, offset)
        epilogue_render.draw_rope(surface, offset, self.rope_x, 0,
                                  self.rope_bottom, self.game.frame, self.tug)
        self.companion.draw(surface, offset)
        self.cemo.draw(surface, offset)

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"epilog kuyu: seslendi={self.called} cevap={self.answered} "
            f"toplanma={self.gather_frames}"]
