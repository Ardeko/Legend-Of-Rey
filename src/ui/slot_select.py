"""Kayit yuvasi secim ekrani - iki slot yan yana.

`DEVIR.md` §0.2 (Arda onayladi). `CLAUDE.md` §9'un uc kurali burada
bagliyor:

  * **DEVAM ET** en ustte ve onceden secili; kayit yoksa **gorunmez**
  * Uzerine yazmada varsayilan secim daima **IPTAL**
  * Her yuva kendi `.bak`'ini tutar (`systems/save.py`)

## Ekran ne zaman aciliyor - ve ne zaman ACILMIYOR

`CLAUDE.md` §9: *"Oyuncu enter'a basip devam edebilmeli -
dusunmeden."* Tek kayitli oyuncuya bir secim ekrani gostermek tam
olarak bunu bozardi. O yuzden:

    DEVAM ET   tek yuva doluysa  -> dogrudan girer, ekran ACILMAZ
               ikisi de doluysa  -> ekran acilir
    YENI OYUN  her zaman         -> ekran acilir (nereye baslanacagi
                                    bir karar, ve dolu yuva IPTAL
                                    varsayilanli onay ister)

## Kart iceriginin isi hatirlatmak

Uc hafta sonra donen oyuncu hangi yuvada ne birakti bilmiyor. Kart
ana menudeki DEVAM ET kartiyla **ayni satirlari** gosteriyor - iki
yerde iki farkli ozet, oyuncuyu ikisini karsilastirmaya zorlardi.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.systems.save import (
    SLOT_COUNT, delete_save, has_save, peek_slot, set_active_slot,
)
from src.ui import text
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.i18n import t, t_or_raw
from src.ui.widgets import Menu, MenuItem, panel

# Yuva adlari **duz dize** olarak yazili. `f"slot.slot{n}"` daha kisa
# olurdu ama `tests/test_lang.py` hesaplanmis anahtari goremiyor ve
# "olu anahtar" diye kirilir - bu tuzaga projede dort kez dusuldu.
SLOT_LABELS = ("slot.slot1", "slot.slot2")
assert len(SLOT_LABELS) == SLOT_COUNT, "yuva sayisi ile etiketler ayristi"

TITLE_Y = 30
CARD_WIDTH = 150
CARD_HEIGHT = 104
CARD_Y = 60
CARD_GAP = 20


def _character_name(key: str) -> str:
    """Karakter etiketi - anahtarlar **duz dize**.

    `t(f"speaker.{key}")` bir satir kisa olurdu ve `test_lang.py`
    ikisini de "olu anahtar" sayardi.
    """
    if key == "ardo":
        return t("speaker.ardo")
    if key == "rey":
        return t("speaker.rey")
    return key


def _card_rect(index: int) -> pygame.Rect:
    """`index` 0 tabanli. Iki kart ekranin ortasinda simetrik."""
    total = SLOT_COUNT * CARD_WIDTH + (SLOT_COUNT - 1) * CARD_GAP
    left = INTERNAL_WIDTH // 2 - total // 2
    return pygame.Rect(left + index * (CARD_WIDTH + CARD_GAP), CARD_Y,
                       CARD_WIDTH, CARD_HEIGHT)


class SlotSelectScene(Scene):
    """Iki yuva. `mode` "continue" ya da "new"."""

    def on_enter(self, mode: str = "continue", **kwargs: object) -> None:
        self.mode = mode if mode in ("continue", "new") else "continue"
        self.frame = 0
        self.confirm: Menu | None = None
        self.pending_slot = 0
        self._refresh()

    def _refresh(self) -> None:
        # Kart verisi **her tazelemede** yeniden okunuyor: oyuncu bir
        # yuvayi silip donunce ekran eski ozeti gostermemeli.
        self.cards = [peek_slot(i) for i in range(1, SLOT_COUNT + 1)]
        self.menu = self._build_menu()

    def _build_menu(self) -> Menu:
        items: list[MenuItem] = []
        for index in range(SLOT_COUNT):
            slot = index + 1
            filled = self.cards[index] is not None
            # "Devam et" kipinde bos yuva secilemez - orada devam
            # edilecek bir sey yok. Gri degil, **secilemez**: kart
            # zaten "bos" yaziyor, ikinci bir sinyal gerekmiyor.
            items.append(MenuItem(
                SLOT_LABELS[index], self._make_choose(slot),
                enabled=filled or self.mode == "new"))
        items.append(MenuItem("common.back", self._back, gap_before=True))
        return Menu(items, INTERNAL_WIDTH // 2, CARD_Y + CARD_HEIGHT + 14,
                    width=150, centered=True, on_sound=self.game.play_sound)

    # --- Eylemler -----------------------------------------------------------
    def _make_choose(self, slot: int):
        def choose() -> None:
            self._choose(slot)
        return choose

    def _choose(self, slot: int) -> None:
        if self.mode == "continue":
            if not has_save(slot):
                return
            set_active_slot(slot)
            self._continue_slot(slot)
            return
        # Yeni oyun: dolu yuvanin uzerine yazmak yikici bir eylem.
        if has_save(slot):
            self.pending_slot = slot
            self._ask_overwrite()
            return
        set_active_slot(slot)
        self._go_character_select()

    def _continue_slot(self, slot: int) -> None:
        data = peek_slot(slot)
        if data is None:
            return
        from src.scenes.vertical_journey import VerticalJourneyScene
        self.scenes.replace(VerticalJourneyScene, transition=False,
                            direction="down", chapter=data.chapter,
                            character=data.character)

    def _ask_overwrite(self) -> None:
        # **Varsayilan secim daima IPTAL** (`CLAUDE.md` §9).
        self.confirm = Menu([
            MenuItem("common.cancel", self._cancel_overwrite),
            MenuItem("menu.overwrite_confirm", self._confirm_overwrite,
                     danger=True),
        ], INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 16, width=150,
            centered=True, on_sound=self.game.play_sound)

    def _cancel_overwrite(self) -> None:
        self.confirm = None
        self.pending_slot = 0

    def _confirm_overwrite(self) -> None:
        slot = self.pending_slot
        self.confirm = None
        self.pending_slot = 0
        if not slot:
            return
        # Eski kayit **simdi** siliniyor, karakter seciminde degil:
        # oyuncu vazgecip geri donerse yarim silinmis bir yuva
        # kalmasin.
        delete_save(slot)
        set_active_slot(slot)
        self._go_character_select()

    def _go_character_select(self) -> None:
        from src.ui.character_select import CharacterSelectScene
        self.scenes.replace(CharacterSelectScene)

    def _back(self) -> None:
        self.scenes.pop()

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            (self.confirm or self.menu).click(self.game)
        elif event.type == pygame.KEYDOWN:
            if self.game.input.pressed(Action.CANCEL):
                if self.confirm:
                    self._cancel_overwrite()
                else:
                    self._back()

    def update(self) -> None:
        self.frame += 1
        (self.confirm or self.menu).update(self.game)

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        title = "slot.title_new" if self.mode == "new" else "slot.title"
        text.draw(surface, t(title), INTERNAL_WIDTH // 2, TITLE_Y,
                  color=palette.role("ui_text_bright"), align="center")

        for index in range(SLOT_COUNT):
            self._draw_card(surface, index)

        self.menu.draw(surface)
        if self.confirm:
            self._draw_overwrite(surface)
        (self.confirm or self.menu).draw_cursor(surface, self.game)

    def _draw_card(self, surface: pygame.Surface, index: int) -> None:
        rect = _card_rect(index)
        selected = self.menu.index == index
        panel(surface, rect)
        if selected:
            # Secili kartin cercevesi vurgulaniyor - imlec asagida,
            # gozun hangi karta baktigi kenardan okunmali.
            pygame.draw.rect(surface, palette.role("ui_text_bright"), rect, 1)

        data = self.cards[index]
        line_y = rect.y + 6
        text.draw(surface, t(SLOT_LABELS[index]), rect.x + 8, line_y,
                  color=palette.role("ui_text_bright"))
        line_y += GLYPH_HEIGHT + 4
        pygame.draw.line(surface, palette.color("stone_dark"),
                         (rect.x + 8, line_y), (rect.right - 8, line_y))
        line_y += 5

        if data is None:
            text.draw(surface, t("slot.empty"), rect.centerx, line_y + 18,
                      color=palette.role("ui_text_dim"), align="center")
            return

        text.draw(surface, t("save.chapter", chapter=data.chapter),
                  rect.x + 8, line_y, color=palette.role("ui_text"))
        line_y += GLYPH_HEIGHT + 1
        text.draw(surface, f"\"{t_or_raw(data.chapter_name)}\"",
                  rect.x + 8, line_y, color=palette.role("ui_text_dim"))
        line_y += GLYPH_HEIGHT + 3

        rows = (
            (t("save.playtime"), data.playtime_text),
            (t("save.gold"), str(data.gold)),
            (t("slot.character"), _character_name(data.character)),
        )
        for label, value in rows:
            text.draw(surface, label, rect.x + 8, line_y,
                      color=palette.role("ui_text_dim"))
            text.draw(surface, value, rect.right - 8, line_y,
                      color=palette.role("ui_text"), align="right")
            line_y += GLYPH_HEIGHT + 1

    def _draw_overwrite(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 190))
        surface.blit(veil, (0, 0))

        rect = pygame.Rect(INTERNAL_WIDTH // 2 - 108,
                           INTERNAL_HEIGHT // 2 - 46, 216, 92)
        panel(surface, rect)
        text.draw(surface, t("menu.overwrite_warning"), INTERNAL_WIDTH // 2,
                  rect.y + 10, color=palette.role("ui_text"), align="center")
        data = peek_slot(self.pending_slot) if self.pending_slot else None
        if data is not None:
            detail = (t(SLOT_LABELS[self.pending_slot - 1]) + " · "
                      + t("save.chapter", chapter=data.chapter) + " · "
                      + data.playtime_text)
            text.draw(surface, detail, INTERNAL_WIDTH // 2, rect.y + 24,
                      color=palette.role("ui_text_dim"), align="center")
        self.confirm.draw(surface)

    def debug_lines(self) -> list[str]:
        return [f"slot ekrani ({self.mode})  secili {self.menu.index + 1}"]
