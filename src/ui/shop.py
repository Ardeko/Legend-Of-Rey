"""Dukkan paneli - Mum Bekcisi'nin tabagi, her yerde ayni.

Ilk surum `chapter03.py` icinde yaziliydi: bir baslik, yazilar, fiyatlar.
Arda, 23.09.2026: *"Daha fazla dukkan olmali"* - bekci artik B6, B9, B12
ve B15'te de beliriyor. Panel bolume ait olmaktan cikti; ciziminin tek
yeri burasi.

## Ne degisti (UX)

    Ikon      her satirin solunda cizilmis bir nesne (ok demeti, bomba,
              mesale, fitil, mum). Yazi okumadan "ne" anlasiliyor.
    Altin     panelin ustunde oyuncunun altini, sikke ikonuyla.
              Onceden fiyat vardi ama "param yetiyor mu" icin HUD'a
              bakmak gerekiyordu.
    Yetmiyor  fiyat kan renginde **ve** ustu cizili - renk korlugu icin
              sekil kanali (`CLAUDE.md` 10).
    Canta     sarf malzemelerinde elde kac tane oldugu (`3/9`). Dolu
              cantaya almak paranin cope gitmesi demekti ve oyuncu
              bunu goremiyordu.
    Tuslar    alt satirdaki ipucu **atama tablosundan**: "[Esc]" sabit
              yazisi tusu degistiren oyuncuya yalan soyluyordu.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_WIDTH
from src.core.input import Action
from src.systems import consumables, economy
from src.ui import text
from src.ui.i18n import t
from src.ui.widgets import panel

WIDTH = 214
ROW = 15
TOP = 52
HEADER = 30
FOOTER = 16


def step_index(input_state, index: int, count: int) -> int:
    """Yukari/asagi ile secim - uclar birbirine bagli."""
    if count <= 0:
        return 0
    if input_state.pressed(Action.UP):
        return (index - 1) % count
    if input_state.pressed(Action.DOWN):
        return (index + 1) % count
    return index


def wants_close(input_state) -> bool:
    return input_state.pressed(Action.CANCEL) or input_state.pressed(Action.PAUSE)


def wants_buy(input_state) -> bool:
    return input_state.pressed(Action.CONFIRM)


def draw(surface: pygame.Surface, offers, index: int, save_data,
         title_key: str, input_state, frame: int = 0) -> None:
    """Paneli ciz. Durum (acik mi, secim) sahnede; burasi yalnizca goruntu."""
    height = HEADER + len(offers) * ROW + FOOTER + 4
    rect = pygame.Rect(INTERNAL_WIDTH // 2 - WIDTH // 2, TOP, WIDTH, height)
    panel(surface, rect)
    # Ust serit - bekcinin mor alevi, panelin kimligi.
    surface.fill(palette.color("violet_dark"), (rect.x + 1, rect.y + 1,
                                                rect.width - 2, 17))
    text.draw(surface, t(title_key), rect.x + 8, rect.y + 5,
              color=palette.color("violet_bright"))
    gold = getattr(save_data, "gold", 0) if save_data is not None else 0
    _draw_coin(surface, rect.right - 12, rect.y + 9)
    text.draw(surface, str(gold), rect.right - 18, rect.y + 5,
              color=palette.color("gold"), align="right")

    for i, offer in enumerate(offers):
        y = rect.y + HEADER + i * ROW
        _draw_row(surface, rect, y, offer, i == index, save_data, frame)

    footer = t("shop.footer",
               buy=_label(input_state, Action.CONFIRM),
               leave=_label(input_state, Action.CANCEL))
    text.draw(surface, footer, rect.centerx, rect.bottom - 12,
              color=palette.role("ui_text_dim"), align="center")


def _label(input_state, action: Action) -> str:
    if input_state is None:
        return "?"
    return input_state.binding_label(action) or "?"


def _draw_row(surface: pygame.Surface, rect: pygame.Rect, y: int, offer,
              selected: bool, save_data, frame: int) -> None:
    bought = economy.already_bought(save_data, offer)
    full = (offer.repeatable and offer.item
            and consumables.count(save_data, offer.item) >= consumables.MAX_CARRY)
    affordable = economy.can_afford(save_data, offer.cost)
    if selected:
        surface.fill(palette.color("ink_soft"),
                     (rect.x + 3, y - 3, rect.width - 6, ROW - 1))
        surface.fill(palette.color("violet_bright"), (rect.x + 3, y - 3, 2, ROW - 1))
    dim = bought or full
    colour = (palette.role("ui_text_dim") if dim
              else palette.color("bone") if selected
              else palette.role("ui_text"))
    _draw_icon(surface, rect.x + 14, y + 3, _icon_for(offer), frame, dim)
    text.draw(surface, t(offer.label_key), rect.x + 24, y, color=colour)

    if offer.repeatable and offer.item:
        have = consumables.count(save_data, offer.item)
        text.draw(surface, f"{have}/{consumables.MAX_CARRY}", rect.right - 58, y,
                  color=palette.role("ui_text_dim"), align="right")

    if bought:
        text.draw(surface, t("chapter03.trade_owned"), rect.right - 8, y,
                  color=palette.role("ui_text_dim"), align="right")
        return
    if full:
        text.draw(surface, t("shop.full"), rect.right - 8, y,
                  color=palette.role("ui_text_dim"), align="right")
        return
    price_colour = palette.color("gold") if affordable else palette.color("blood_bright")
    area = text.draw(surface, str(offer.cost), rect.right - 16, y,
                     color=price_colour, align="right")
    _draw_coin(surface, rect.right - 11, y + 3)
    if not affordable:
        # Sekil kanali: yetmeyen fiyatin ustu cizili.
        surface.fill(price_colour, (area.x - 1, area.centery, area.width + 2, 1))


def _icon_for(offer) -> str:
    if offer.item == consumables.ARROW:
        return "arrow"
    if offer.item == consumables.BOMB:
        return "bomb"
    return {"candle_keeper_torch": "torch", "eternal_wick": "wick",
            "death_candle": "candle"}.get(offer.key, "torch")


def _draw_coin(surface: pygame.Surface, cx: int, cy: int) -> None:
    surface.fill(palette.color("ember_dark"), (cx - 2, cy - 3, 5, 7))
    surface.fill(palette.color("ember_dark"), (cx - 3, cy - 2, 7, 5))
    surface.fill(palette.color("gold"), (cx - 2, cy - 2, 5, 5))
    surface.fill(palette.color("bone"), (cx - 1, cy - 2, 1, 1))


def _draw_icon(surface: pygame.Surface, cx: int, cy: int, kind: str,
               frame: int, dim: bool) -> None:
    """Satir ikonu - 9x9 kutuda, sol-ust isik kurali."""
    wood = palette.color("stone" if dim else "earth")
    metal = palette.color("stone_light" if dim else "bone")
    fire = palette.color("stone" if dim else "ember_light")
    flicker = (frame // 8) % 2
    if kind == "arrow":
        for dx in (-2, 0, 2):
            surface.fill(wood, (cx + dx, cy - 3, 1, 7))
            surface.fill(metal, (cx + dx, cy - 4, 1, 1))
        surface.fill(palette.color("stone_light"), (cx - 3, cy + 3, 7, 1))
    elif kind == "bomb":
        body = palette.color("stone_dark" if dim else "ink_soft")
        surface.fill(body, (cx - 3, cy - 1, 7, 5))
        surface.fill(body, (cx - 2, cy - 2, 5, 7))
        surface.fill(palette.color("stone"), (cx - 2, cy - 1, 1, 1))
        surface.fill(wood, (cx + 1, cy - 4, 1, 2))
        if not dim:
            surface.fill(fire, (cx + 2, cy - 5 + flicker, 1, 1))
    elif kind == "torch":
        surface.fill(wood, (cx, cy - 1, 2, 6))
        surface.fill(fire, (cx - 1, cy - 4, 3, 3))
        surface.fill(palette.color("gold" if not dim else "stone"),
                     (cx, cy - 4 + flicker, 1, 1))
    elif kind == "wick":
        surface.fill(palette.color("violet" if not dim else "stone"),
                     (cx - 1, cy - 4 + flicker, 3, 3))
        surface.fill(metal, (cx - 2, cy, 5, 4))
    else:  # candle
        surface.fill(metal, (cx - 1, cy - 1, 3, 5))
        surface.fill(palette.color("blood_bright" if not dim else "stone"),
                     (cx, cy - 4 + flicker, 1, 2))
