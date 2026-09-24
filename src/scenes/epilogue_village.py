"""Epilog 2 - Sabah koyu. Oyunun odulu.

`docs/yapi.md` Epilog. B1'in koyu, **ayni evler**, ama safakta ve
tersinden: oyuncu doguda Jet'in ipinin ucunda basliyor, batiya - B1'in
basladigi eve - yuruyor.

## Tek zorunlu hedef: can

Kapilar o geceden beri kapali (`villager.py`: *"koy bir daha
dolmaz"*). Koy cani meydanda; oyuncu onu **Rezonans** ile caliyor -
B8'de Ardo'nun ogrettigi, B9'da canlarda kullanilan ses. Rey icin bu
kez kendi sesi: Yanki B18'de sustu. Can calininca koyluler kapidan
cikip oyuncuya donuyor ve konusulabiliyor.

## Odul bir tablo degil

`DEVIR.md`: *"puan degil hatirlatma."* Koyluler oyuncunun gercek
yolculugunu biliyor: kac kez dustugu (`SaveData.deaths`), B15'te
kimseyi uyandirmadan gecip gecmedigi. Kalachev inmeden once hana para
birakmis (B5'in "ilk icki benden"i). Jet kilicini geri almiyor. Cemo
evin duvarina B13'teki isaretini ve herkesi ciziyor.

Hepsi istege bagli; yalnizca can ve eve varmak sart.

## Oyun sonrasi (`postgame=True`)

Bitmis kayitta DEVAM ET buraya getiriyor: koyluler zaten disarida,
resim duvarda, can istenirse caliniyor. Batidan cikinca ana menu.
Oyuncuya donebilecegi bir yer.
"""
from __future__ import annotations

from src.config import TILE_SIZE
from src.core.input import Action
from src.entities.companion import Companion
from src.entities.npc import Npc
from src.entities.villager import Villager
from src.scenes import epilogue_render
from src.scenes.play import PlayScene
from src.systems.homecoming import (
    EPILOGUE_FLAG, HOMECOMING_CHAPTER_NAME, Homecoming,
)
from src.systems.resonance import ResonanceState
from src.ui.dialogue import Line
from src.world import village_backdrop
from src.world.resonant import Bell
from src.world.rooms.epilogue import (
    BELL_TILE, EPILOGUE_SCENERY, HOLE_TILES, HOME_INDEX, HOUSES, JET_TILE,
    ROPE_POST_TILE, SCAR_TILES, VILLAGE_LEVEL, VILLAGERS,
)
from src.world.tilemap import TileMap

# Varista Jet'in karsilamasi - oyuncu once koye bir baksin.
ARRIVAL_FRAME = 28
# Konusma gostergesi bu kadar yakinda beliriyor (piksel).
TALK_REACH = 26.0
# Can: bu kadar yakinda oyuncu onu fark ediyor ve yorum yapiyor.
BELL_NOTICE = 72.0
# Koyluler kapidan sirayla cikiyor: ilki bu kadar sonra, sonrakiler
# araliklarla. Hepsi ayni karede cikarsa suru gibi okunuyordu.
EMERGE_FIRST = 36
EMERGE_STEP = 44
# Yarigin izinin yanindan gecerken tek replik.
SCAR_REACH = 26.0
# Ev: kapiya bu kadar yaklasinca bitis (ya da can ipucu) basliyor.
# Resmin sag ucunun (kapi + 42) disinda: Cemo "Dur, dur!" diyor ve
# oyuncu orada kaliyor - resmin onunde durup onu kapatmasin.
HOME_REACH = 58.0
# Cemo'nun resmi bu kadar karede tamamlaniyor (~2.5 sn).
DRAW_FRAMES = 150
# Oyun sonrasi: batida bu x'in gerisine gecen menuye doner.
POSTGAME_EXIT_X = 12.0


def _door_x(house: tuple) -> float:
    tx, _ty, tw, _th, _kind = house
    return (tx + tw * 0.5) * TILE_SIZE


class EpilogueVillageScene(PlayScene):
    """Sabah koyu - can, koyluler, han, Cemo'nun resmi."""

    footstep_sound = "step_earth"
    postfx_grade = "dawn"
    companion_orders = False
    ambience_preset = "dust"
    music_context = "companion"

    def on_enter(self, character: str = "rey",
                 homecoming: Homecoming | None = None,
                 postgame: bool = False, **kwargs: object) -> None:
        self.homecoming = homecoming
        self.postgame = postgame
        super().on_enter(character=character, **kwargs)

    # --- Kurulum ------------------------------------------------------------
    def setup(self) -> None:
        if self.homecoming is None:
            self.homecoming = Homecoming.from_save(self.save_data,
                                                   self.character)
        self.tilemap = TileMap(VILLAGE_LEVEL.terrain_rows)
        spawn = VILLAGE_LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        self.player.facing = -1
        self.echo = None
        self.tracking = None
        self.ground_y = spawn.feet_y

        self.companion_key = self.homecoming.ally
        self.companion = Companion(self, spawn.x + 18, spawn.feet_y,
                                   self.companion_key)
        self.cemo = Npc("cemo", spawn.x - 20, spawn.feet_y, facing=-1,
                        gap=20.0, speed=1.2)
        self.jet = Npc("jet_unarmed", JET_TILE * TILE_SIZE + 8, spawn.feet_y,
                       facing=1)
        self._build_villagers()

        self.bell = Bell(*BELL_TILE, index=0)
        self.resonance = ResonanceState(unlocked=True)

        home = HOUSES[HOME_INDEX]
        self.home_door_x = _door_x(home)
        self.frames = 0
        self.arrived = self.postgame
        self.jet_talked = False
        self.scar_said = False
        self.bell_said = self.postgame
        self.bell_rung = self.postgame
        self.bell_hinted = False
        self.drawing = 1.0 if self.postgame else 0.0
        self.drawing_state = ""
        self.finished = False
        # Diyalog bir onceki karede acik miydi? E hem repligi ilerletiyor
        # hem konusma baslatiyor; son repligi kapatan basis ayni karede
        # yanindaki koyluyle yeniden konusmaya baslamamali.
        self._dialogue_was_open = False

    def _build_villagers(self) -> None:
        """Her rol bir kapi. Epilogda iceride dogarlar; oyun sonrasi disarida."""
        self.villagers: list[Villager] = []
        for index, (house_index, role, stand) in enumerate(VILLAGERS):
            door_x = _door_x(HOUSES[house_index])
            villager = Villager(door_x + stand, self.ground_y, door_x,
                                seed=index, inside=not self.postgame,
                                role=role)
            if self.postgame:
                villager.greet()
            self.villagers.append(villager)

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        px = self.player.body.center_x
        self.companion.update()
        self._update_cemo(px)
        self.jet.face(px)
        self.jet.update()
        for villager in self.villagers:
            villager.face(px)
            villager.update()
        self._update_bell(px)
        if self.finished:
            return
        self._update_arrival()
        self._update_talk(px)
        self._update_scar(px)
        self._update_home(px)
        if self.postgame and px < POSTGAME_EXIT_X:
            self._leave_to_menu()
        self._dialogue_was_open = not self.dialogue.done

    @property
    def free_to_talk(self) -> bool:
        """Konusma yok ve bu kare bir konusma kapanmadi."""
        return self.dialogue.done and not self._dialogue_was_open

    def _update_cemo(self, px: float) -> None:
        if self.drawing_state:
            self.cemo.walk_to(self.home_door_x)
            if self.cemo.arrived:
                self.cemo.face(self.home_door_x - 20)
        else:
            self.cemo.follow(px, self.player.facing)
        self.cemo.update()

    def _update_arrival(self) -> None:
        """Jet ipin basinda: "Hos geldiniz." Cemo ona ilk kez Emre diyor."""
        if self.arrived or self.frames < ARRIVAL_FRAME:
            return
        self.arrived = True
        self.say(Line("jet", "line.epi_jet_welcome"),
                 Line("cemo", "line.epi_cemo_thanks"),
                 Line("jet", "line.epi_jet_name"))

    # --- Konusma ------------------------------------------------------------
    def _talk_target(self, px: float):
        """En yakin konusulabilir kisi: Jet (bir kez) ya da disaridaki koylu."""
        best, best_distance = None, TALK_REACH
        candidates = [v for v in self.villagers if v.greeting]
        if self.arrived and not self.jet_talked:
            candidates.append(self.jet)
        for who in candidates:
            distance = abs(who.x - px)
            if distance < best_distance:
                best, best_distance = who, distance
        return best

    def _update_talk(self, px: float) -> None:
        if not self.free_to_talk:
            return
        target = self._talk_target(px)
        if target is None:
            return
        self.prompts.offer("talk", target.x, self.ground_y - 34,
                           verb_key="prompt.talk")
        if not self.game.input.pressed(Action.INTERACT):
            return
        if target is self.jet:
            self._talk_to_jet()
        else:
            self.say(*self.lines_for(target.role))

    def _talk_to_jet(self) -> None:
        """B1'in kilici geri veriliyor. Jet almiyor."""
        self.jet_talked = True
        ardo = self.homecoming.ardo
        self.say(Line(self.character, "line.epi_ardo_sword" if ardo
                      else "line.epi_rey_sword"),
                 Line("jet", "line.epi_jet_road" if ardo
                      else "line.epi_jet_guardian"))

    def lines_for(self, role: str) -> tuple[Line, ...]:
        """Koylunun sozu - bazilari oyuncunun **gercek** yolculugundan.

        Anahtarlar duz dize (`tests/test_lang.py`): hesaplanmis ad
        tarayicidan kacar.
        """
        home = self.homecoming
        if role == "door":
            return (Line("villager", "line.epi_villager_door"),)
        if role == "seven":
            return (Line("villager", "line.epi_villager_seven"),)
        if role == "elder":
            return (Line("villager", "line.epi_villager_stranger" if home.ardo
                         else "line.epi_villager_name"),)
        if role == "falls":
            if home.deaths > 0:
                return (Line("villager", "line.epi_villager_falls",
                             (("count", home.deaths),)),)
            return (Line("villager", "line.epi_villager_nofall"),)
        if role == "rooster":
            return (Line("villager", "line.epi_villager_ghost" if home.ghost
                         else "line.epi_villager_rooster"),)
        if role == "inn":
            # Kalachev'in parasi. Kadehi Ardo kaldiriyor - iki oynanista
            # da orada: Rey ile yoldas, Ardo ile oyuncunun kendisi.
            return (Line("innkeeper", "line.epi_innkeeper_money"),
                    Line("innkeeper", "line.epi_innkeeper_note"),
                    Line("ardo", "line.epi_ardo_toast"))
        return ()

    def _update_scar(self, px: float) -> None:
        if self.scar_said or not self.dialogue.done:
            return
        start, width = SCAR_TILES
        centre = (start + width * 0.5) * TILE_SIZE
        if abs(px - centre) < SCAR_REACH:
            self.scar_said = True
            self.say_player("line.epi_rey_scar", "line.epi_ardo_scar")

    # --- Can ----------------------------------------------------------------
    def _update_bell(self, px: float) -> None:
        self.resonance.update()
        self.bell.update()
        if self.bell.done:
            # Can caldi ve durdu: yeniden calinabilir (oyun sonrasi eglence).
            self.bell.reset()
        near = abs(px - self.bell.rect.centerx) < BELL_NOTICE
        if near and not self.bell_said and self.dialogue.done:
            self.bell_said = True
            self.say_player("line.epi_rey_bell", "line.epi_ardo_bell")
            self.hint_once("hint_bell", "hint.bell", Action.RESONATE,
                           icon="resonance")
        self.offer_resonate([self.bell])
        if self.game.input.pressed(Action.RESONATE):
            if self.resonance.pulse(self.player.body.center_x,
                                    self.player.body.center_y):
                self.game.play_sound("swing_light")
        if not self.bell.triggered and self.resonance.reaches(self.bell):
            self._ring()

    def _ring(self) -> None:
        self.bell.strike()
        self.game.play_sound("bell_village")
        self.particles.burst(self.bell.rect.centerx, self.bell.rect.centery,
                             16, path="spark", speed=(0.5, 2.0))
        if self.bell_rung:
            return
        self.bell_rung = True
        self.say_player("line.epi_rey_rang", "line.epi_ardo_rang")
        # Canin sesine en yakin kapi once acilir.
        order = sorted(self.villagers,
                       key=lambda v: abs(v.door_x - self.bell.rect.centerx))
        for step, villager in enumerate(order):
            villager.emerge(EMERGE_FIRST + step * EMERGE_STEP)

    # --- Ev ve resim --------------------------------------------------------
    def _update_home(self, px: float) -> None:
        if self.postgame:
            return
        if self.drawing_state:
            self._hold_back()
        if not self.drawing_state:
            if px - self.home_door_x > HOME_REACH:
                return
            if not self.bell_rung:
                if not self.bell_hinted and self.dialogue.done:
                    self.bell_hinted = True
                    self.say(Line("cemo", "line.epi_cemo_bellhint"))
                return
            self.drawing_state = "walk"
            self.say(Line("cemo", "line.epi_cemo_wait"))
            return
        if self.drawing_state == "walk" and self.cemo.arrived:
            self.drawing_state = "draw"
        elif self.drawing_state == "draw":
            self.drawing = min(1.0, self.drawing + 1.0 / DRAW_FRAMES)
            if self.drawing >= 1.0 and self.dialogue.done:
                self.drawing_state = "talk"
                ardo = self.homecoming.ardo
                self.say(Line("cemo", "line.epi_cemo_sister" if ardo
                              else "line.epi_cemo_drawing"),
                         Line(self.character, "line.epi_ardo_drawing" if ardo
                              else "line.epi_rey_drawing"))
        elif self.drawing_state == "talk" and self.dialogue.done:
            self.drawing_state = "done"
            self._finish()

    def _hold_back(self) -> None:
        """Cemo "Dur, dur!" dedi: oyuncu resmin onune gecmiyor.

        Kontrolu almak (`control_locked`) Rey'i yere seriyordu - o bayrak
        sarsinti icin. Burada yalnizca bir sinir var: oyuncu yuruyebilir,
        doner, bakar; resmin ustune basamaz.
        """
        body = self.player.body
        limit = self.home_door_x + HOME_REACH
        if body.center_x < limit:
            body.set_feet(limit, body.feet[1])
            body.vx = max(0.0, body.vx)

    def _finish(self) -> None:
        """Eve varildi. Kayit yaziliyor, aksam ates basi."""
        self.finished = True
        data = self.save_data
        if data is not None:
            data.flags[EPILOGUE_FLAG] = True
            data.chapter_name = HOMECOMING_CHAPTER_NAME
            from src.systems.save import write_save
            write_save(data)
        from src.scenes.epilogue_cinematics import HomecomingFireCinematic
        self.scenes.set_root(HomecomingFireCinematic,
                             character=self.character,
                             homecoming=self.homecoming)

    def _leave_to_menu(self) -> None:
        self.finished = True
        from src.ui.menu import MainMenuScene
        self.scenes.set_root(MainMenuScene)

    # --- Cizim --------------------------------------------------------------
    def drawing_origin(self) -> tuple[int, int, int]:
        """Resmin iki yarisinin dunya x'leri ve taban y'si.

        Kapi govdenin ortasinda (`village_backdrop._draw_house` ile ayni
        hesap); yarilar kapinin iki yaninda, Cemo'nun boyunda.
        """
        home = HOUSES[HOME_INDEX]
        tx, ty, tw, _th, _kind = home
        door_w, _door_h = epilogue_render.door_size(home)
        door_left = tx * TILE_SIZE + tw * TILE_SIZE // 2 - door_w // 2
        base = (ty + 1) * TILE_SIZE - epilogue_render.DRAWING_LIFT
        left, right = epilogue_render.drawing_halves(door_left,
                                                     door_left + door_w)
        return left, right, base

    def draw_background(self, surface, offset) -> None:
        ox, oy = offset
        village_backdrop.draw_sky(surface, ox, self.game.frame,
                                  village_backdrop.DAWN)
        village_backdrop.draw(surface, offset, self.game.frame,
                              village_backdrop.DAWN, EPILOGUE_SCENERY)
        if self.drawing > 0.0:
            left, right, base = self.drawing_origin()
            epilogue_render.draw_chalk_drawing(surface, left - ox, right - ox,
                                               base - oy, self.drawing)

    def draw_foreground(self, surface, offset) -> None:
        start, width = SCAR_TILES
        epilogue_render.draw_scar(surface, offset, start * TILE_SIZE,
                                  width * TILE_SIZE, int(self.ground_y))
        hole, hole_w = HOLE_TILES
        epilogue_render.draw_rope_post(surface, offset,
                                       ROPE_POST_TILE * TILE_SIZE + 6,
                                       hole * TILE_SIZE, hole_w * TILE_SIZE,
                                       int(self.ground_y))
        self.bell.draw(surface, offset)
        for villager in self.villagers:
            villager.draw(surface, offset)
        self.jet.draw(surface, offset)
        self.cemo.draw(surface, offset)
        self.companion.draw(surface, offset)
        from src.art import resonance_view
        resonance_view.draw(surface, offset, self.resonance, self.character)

    def debug_lines(self) -> list[str]:
        out = [v.state for v in self.villagers]
        return super().debug_lines() + [
            f"epilog koy: can={self.bell_rung} resim={self.drawing:.2f} "
            f"{self.drawing_state or '-'}  koyluler {out}"]
