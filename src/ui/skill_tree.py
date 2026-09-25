"""Yetenek agaci ekrani - uc dal, bes kademe, 3. kademede secim.

Arda (25.09.2026): *"Yetenek agacini bolume yayilmis puanlar olarak
tekrar yap. Yeni hareketler versin."* Mantik `src/systems/skilltree.py`'de;
burasi yalnizca goruntu ve gezinme.

## Nereden aciliyor

Duraklat menusundeki **YETENEKLER** (her bolumde) ve B4'un kampi. Eskiden
yalnizca kamp vardi: puan kazanilsa bile baska yerde harcanamiyordu.

## Ekran degil, BINDIRME

`ChapterEndScene` ile ayni desen: alttaki sahne donuyor ama gorunur
kaliyor (`blocks_update=True`, `blocks_draw=False`) ve arkasi bu sahne
tarafindan bulaniklastiriliyor.

## Uc dal yan yana, bes kademe yukaridan asagi

Dallar sutun, kademeler satir. 3. kademede iki dugum yan yana: biri
alininca oteki **kalici** kilitleniyor - o yuzden iki basista aciliyor
(ilk basis uyarir, ikincisi onaylar). `CLAUDE.md` 9: geri alinamayan
eylemde varsayilan IPTAL.

Gezinme satir icinde: SOL/SAG ayni kademede bir sonraki dugume (secim
ciftinde once ciftin otekine, sonra komsu dala) gidiyor; YUKARI/ASAGI
en yakin sutundaki dugume.

Oteki karakterin dali (Ardo'da YANKI, Rey'de IZ) ekranda **hic yok**.
Eskiden soluk ciziliyordu ve "alamayacagin bir sey" diye bagiriyordu.

## Durum RENKLE DEGIL, uc kanalla anlatiliyor

Renk korlugu icin (CLAUDE.md 10) her durum **renk + sekil + parlaklik**:

    ACIK        dolu daire, parlak, baglanti cizgisi kalin
    ALINABILIR  halka + nabiz, orta parlaklik
    KILITLI     ince halka, sonuk, cizgi noktali
    SECILMEDI   ince halka + capraz (secim kademesinde oteki alindi)

Yeni bir HAREKET veren dugumun ustunde kucuk bir elmas var - oyuncu
"sayi" ile "fiil" arasindaki farki agaca bakarak goruyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.ui import text, widgets
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.i18n import t

# Yerlesim. Bes satir 28 piksel arayla; dal adlari ilk satirin 18 piksel
# ustunde, baslik ve puan sayaci onlarin ustunde. Ayrinti paneli altta.
HEADER_Y = 10
TREE_TOP = 60
ROW_STEP = 28
NODE_RADIUS = 6
# Secim ciftinin sutun ortasindan yatay uzakligi.
PAIR_OFFSET = 20
DETAIL_TOP = INTERNAL_HEIGHT - 62
DETAIL_WIDTH = INTERNAL_WIDTH - 40
# Acilis ani: dugumden genisleyen halka.
UNLOCK_FLASH_FRAMES = 24

OWNED = "acik"
AVAILABLE = "alinabilir"
LOCKED = "kilitli"
FORSAKEN = "secilmedi"


class SkillTreeScene(Scene):
    """Yetenek agaci bindirmesi. Alttaki sahne donar, gorunur kalir."""

    blocks_update = True
    blocks_draw = False

    def on_enter(self, save_data=None, tree=None, play=None,
                 **kwargs: object) -> None:
        """`tree` `src/systems/skilltree.py` modulu, `save_data` kayit.

        `play` canli oyun sahnesi (varsa): acilan dugum oyuncuya HEMEN
        biniyor (`PlayScene.learn_skill`). Yoksa etki bir sonraki bolumde.
        """
        self.save_data = save_data
        self.tree = tree
        self.play = play
        self.row = 0
        self.column_x = self._column_x(0)
        self.frames = 0
        self.pending = ""            # ikinci basis bekleyen secim dugumu
        self.flash_key = ""
        self.flash_frames = 0
        self._blurred: pygame.Surface | None = None

    # --- Veri ---------------------------------------------------------------
    @property
    def character(self) -> str:
        return "ardo" if getattr(self.save_data, "character", "rey") == "ardo" else "rey"

    @property
    def branches(self) -> tuple:
        if self.tree is None:
            return ()
        finder = getattr(self.tree, "branches_for", None)
        if finder is not None:
            return finder(self.character)
        return getattr(self.tree, "BRANCHES", ())

    def _column_x(self, index: int) -> int:
        count = max(1, len(self.branches)) if self.tree is not None else 3
        span = INTERNAL_WIDTH // count
        return span * index + span // 2

    def _slots(self, row: int) -> list[tuple[int, object]]:
        """Bu satirdaki dugumler, soldan saga: (x, dugum)."""
        slots: list[tuple[int, object]] = []
        for index, branch in enumerate(self.branches):
            if row >= len(branch.tiers):
                continue
            tier = branch.tiers[row]
            base = self._column_x(index)
            if len(tier) == 1:
                slots.append((base, tier[0]))
            else:
                for side, node in zip((-1, 1), tier):
                    slots.append((base + side * PAIR_OFFSET, node))
        return slots

    @property
    def row_count(self) -> int:
        return max((len(b.tiers) for b in self.branches), default=0)

    @property
    def current(self):
        """Secili dugum - satirdaki `column_x`e en yakin olan."""
        slots = self._slots(self.row)
        if not slots:
            return None
        return min(slots, key=lambda slot: abs(slot[0] - self.column_x))[1]

    # --- Gezinme ------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        inp = self.game.input
        if inp.pressed(Action.CANCEL) or inp.pressed(Action.PAUSE):
            self.game.play_sound("ui_back")
            self.scenes.pop()
            return
        if inp.pressed(Action.LEFT):
            self._step_slot(-1)
        elif inp.pressed(Action.RIGHT):
            self._step_slot(1)
        elif inp.pressed(Action.UP):
            self._step_row(-1)
        elif inp.pressed(Action.DOWN):
            self._step_row(1)
        elif inp.pressed(Action.CONFIRM):
            self._try_unlock()

    def _step_slot(self, direction: int) -> None:
        slots = self._slots(self.row)
        if not slots:
            return
        xs = [x for x, _node in slots]
        here = min(range(len(xs)), key=lambda i: abs(xs[i] - self.column_x))
        self.column_x = xs[(here + direction) % len(xs)]
        self.pending = ""
        self.game.play_sound("ui_tick")

    def _step_row(self, direction: int) -> None:
        if not self.row_count:
            return
        self.row = (self.row + direction) % self.row_count
        # Sutun hafizasi: secim ciftinden cikinca dalin ortasina dus.
        slots = self._slots(self.row)
        if slots:
            nearest = min(slots, key=lambda slot: abs(slot[0] - self.column_x))
            self.column_x = nearest[0]
        self.pending = ""
        self.game.play_sound("ui_tick")

    def _try_unlock(self) -> None:
        node = self.current
        if node is None or self.tree is None or self.save_data is None:
            return
        if not self.tree.can_unlock(self.save_data, node.key):
            # Reddedilen giris SESSIZ kalmamali - oyuncu tusun calismadigini
            # mi yoksa kosulun saglanmadigini mi bilmiyor.
            self.pending = ""
            self.game.play_sound("ui_deny")
            return
        rival = self.tree.rival(node.key)
        if rival is not None and self.pending != node.key:
            # Geri alinamaz secim: ilk basis yalnizca uyariyor.
            self.pending = node.key
            self.game.play_sound("ui_tick")
            return
        self.pending = ""
        if not self.tree.unlock(self.save_data, node.key):
            self.game.play_sound("ui_deny")
            return
        self.flash_key = node.key
        self.flash_frames = UNLOCK_FLASH_FRAMES
        self.game.play_sound("ui_confirm")
        self.game.play_sound("necklace_warm")
        if self.play is not None:
            learn = getattr(self.play, "learn_skill", None)
            if learn is not None:
                learn(node.key)

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        self.frames += 1
        if self.flash_frames > 0:
            self.flash_frames -= 1

    # --- Durum --------------------------------------------------------------
    def state_of(self, node) -> str:
        if self.tree is None or self.save_data is None:
            return LOCKED
        if self.tree.unlocked(self.save_data, node.key):
            return OWNED
        if self.tree.rival_taken(self.save_data, node.key):
            return FORSAKEN
        if self.tree.can_unlock(self.save_data, node.key):
            return AVAILABLE
        return LOCKED

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        self._draw_backdrop(surface)
        self._draw_header(surface)
        for index, branch in enumerate(self.branches):
            self._draw_branch(surface, index, branch)
        self._draw_detail(surface)

    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        """Alttaki sahne bulanik ve koyu - oyun duruyor ama kaybolmuyor."""
        if self._blurred is None:
            self._blurred = widgets.blur(surface.copy())
        surface.blit(self._blurred, (0, 0))
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 180))
        surface.blit(veil, (0, 0))

    def _draw_header(self, surface: pygame.Surface) -> None:
        text.draw(surface, text.tr_upper(t("skilltree.title")),
                  INTERNAL_WIDTH // 2, HEADER_Y, align="center",
                  color=palette.role("ui_text_bright"), outline=True)
        points = 0
        if self.tree is not None and self.save_data is not None:
            points = self.tree.available_points(self.save_data)
        text.draw(surface, t("skilltree.points", count=points),
                  INTERNAL_WIDTH // 2, HEADER_Y + GLYPH_HEIGHT + 3,
                  align="center",
                  color=palette.color("gold" if points else "stone_light"))

    def _draw_branch(self, surface: pygame.Surface, index: int,
                     branch) -> None:
        x = self._column_x(index)
        text.draw(surface, text.tr_upper(t(branch.label_key)), x,
                  TREE_TOP - 18, align="center",
                  color=palette.role("ui_text_dim"))
        previous: list[tuple[int, object]] = []
        for row, tier in enumerate(branch.tiers):
            y = TREE_TOP + row * ROW_STEP
            here = self._tier_positions(x, tier)
            for px, _above in previous:
                for nx, node in here:
                    self._draw_link(surface, (px, y - ROW_STEP), (nx, y), node)
            for nx, node in here:
                selected = row == self.row and node is self.current
                self._draw_node(surface, nx, y, node, selected)
            previous = here

    @staticmethod
    def _tier_positions(x: int, tier) -> list[tuple[int, object]]:
        if len(tier) == 1:
            return [(x, tier[0])]
        return [(x + side * PAIR_OFFSET, node)
                for side, node in zip((-1, 1), tier)]

    def _draw_link(self, surface: pygame.Surface, start: tuple[int, int],
                   end: tuple[int, int], node) -> None:
        """Onkosul cizgisi. Acik yol KALIN altin, kapali yol NOKTALI.

        Cizgi olmasaydi oyuncu on bes ayri dugum gorurdu, bir YOL degil.
        """
        state = self.state_of(node)
        (x0, y0), (x1, y1) = start, end
        length = math.hypot(x1 - x0, y1 - y0)
        if length <= NODE_RADIUS * 2:
            return
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        a = (x0 + ux * (NODE_RADIUS + 1), y0 + uy * (NODE_RADIUS + 1))
        b = (x1 - ux * (NODE_RADIUS + 1), y1 - uy * (NODE_RADIUS + 1))
        if state == OWNED:
            pygame.draw.line(surface, palette.color("gold"), a, b, 2)
            return
        if state == FORSAKEN:
            return                          # terk edilen yol cizilmiyor
        tone = palette.color("stone_light" if state == AVAILABLE
                             else "stone_dark")
        steps = int(math.hypot(b[0] - a[0], b[1] - a[1]) // 3)
        for step in range(steps + 1):
            f = step / max(1, steps)
            surface.fill(tone, (round(a[0] + (b[0] - a[0]) * f),
                                round(a[1] + (b[1] - a[1]) * f), 1, 1))

    def _draw_node(self, surface: pygame.Surface, x: int, y: int,
                   node, selected: bool) -> None:
        """Durum uc kanalla: sekil + parlaklik + renk (CLAUDE.md 10)."""
        state = self.state_of(node)
        if state == OWNED:
            pygame.draw.circle(surface, palette.color("gold"), (x, y),
                               NODE_RADIUS)
            surface.fill(palette.color("white_flash"), (x - 2, y - 3, 1, 1))
        elif state == AVAILABLE:
            pulse = 0.5 + 0.5 * math.sin(self.frames * 0.08)
            tone = (palette.color("gold") if pulse > 0.5
                    else palette.color("ember_light"))
            pygame.draw.circle(surface, tone, (x, y), NODE_RADIUS, 2)
        elif state == FORSAKEN:
            tone = palette.color("stone_darkest")
            pygame.draw.circle(surface, tone, (x, y), NODE_RADIUS, 1)
            r = NODE_RADIUS - 2
            pygame.draw.line(surface, tone, (x - r, y - r), (x + r, y + r))
            pygame.draw.line(surface, tone, (x - r, y + r), (x + r, y - r))
        else:
            pygame.draw.circle(surface, palette.color("stone_dark"),
                               (x, y), NODE_RADIUS, 1)

        if getattr(node, "is_move", False) and state != FORSAKEN:
            self._draw_move_badge(surface, x + NODE_RADIUS, y - NODE_RADIUS,
                                  state)
        if node.key == self.flash_key and self.flash_frames > 0:
            grow = 1.0 - self.flash_frames / UNLOCK_FLASH_FRAMES
            radius = NODE_RADIUS + 2 + int(grow * 10)
            pygame.draw.circle(surface, palette.color("gold"), (x, y),
                               radius, 1)
        if selected:
            # Secim cercevesi dugumun DISINDA - uzerine binerse durum
            # okunmaz hale geliyor.
            rect = pygame.Rect(x - NODE_RADIUS - 4, y - NODE_RADIUS - 4,
                               (NODE_RADIUS + 4) * 2, (NODE_RADIUS + 4) * 2)
            colour = ("danger_bright" if self.pending == node.key
                      else "violet_bright")
            pygame.draw.rect(surface, palette.color(colour), rect, 1)

    @staticmethod
    def _draw_move_badge(surface: pygame.Surface, x: int, y: int,
                         state: str) -> None:
        """Yeni hareket rozeti: kucuk bir elmas (sekil kanali)."""
        tone = palette.color("gold" if state in (OWNED, AVAILABLE)
                             else "stone")
        surface.fill(tone, (x, y - 1, 1, 3))
        surface.fill(tone, (x - 1, y, 3, 1))

    def _draw_detail(self, surface: pygame.Surface) -> None:
        """Secili dugumun adi, aciklamasi ve durumu.

        Agac ikonik ama bir ILERLEME ekraninda "bu ne ise yarar"
        belirsizligi ceza olur - metin sart.
        """
        node = self.current
        if node is None:
            return
        rect = pygame.Rect((INTERNAL_WIDTH - DETAIL_WIDTH) // 2,
                           DETAIL_TOP - 6, DETAIL_WIDTH, 60)
        widgets.panel(surface, rect)
        state = self.state_of(node)
        name = text.tr_upper(t(node.label_key))
        if getattr(node, "is_move", False):
            name = f"{name}  ·  {text.tr_upper(t('skilltree.new_move'))}"
        text.draw(surface, name, INTERNAL_WIDTH // 2, DETAIL_TOP,
                  align="center",
                  color=palette.color("gold") if state == OWNED
                  else palette.role("ui_text_bright"))
        lines = text.wrap(t(node.desc_key), DETAIL_WIDTH - 16)[:2]
        for index, line in enumerate(lines):
            text.draw(surface, line, INTERNAL_WIDTH // 2,
                      DETAIL_TOP + (GLYPH_HEIGHT + 2) * (index + 1),
                      align="center", color=palette.role("ui_text_dim"))
        footer, colour = self._footer(node, state)
        text.draw(surface, footer, INTERNAL_WIDTH // 2,
                  DETAIL_TOP + (GLYPH_HEIGHT + 2) * 3 + 1, align="center",
                  color=colour)

    def _footer(self, node, state: str) -> tuple[str, tuple[int, int, int]]:
        dim = palette.role("ui_text_dim")
        if state == OWNED:
            return t("skilltree.owned"), dim
        if state == FORSAKEN:
            return t("skilltree.forsaken"), dim
        if state == AVAILABLE:
            rival = self.tree.rival(node.key) if self.tree else None
            if rival is not None and self.pending == node.key:
                return (t("skilltree.confirm_choice", other=t(rival.label_key)),
                        palette.color("danger_bright"))
            if rival is not None:
                return (t("skilltree.cost_choice", count=node.cost),
                        palette.color("gold"))
            return t("skilltree.cost", count=node.cost), palette.color("gold")
        return t("skilltree.locked"), dim
