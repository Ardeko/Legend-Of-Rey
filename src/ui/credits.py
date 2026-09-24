"""Jenerik - isim listesi ve oyuncunun kendi yolu.

Eskiden `ending.py`'nin icindeydi ve **kapanisin devami** olarak orada
akiyordu. Epilog (24.09.2026) jenerigi koydeki ates basinin sonuna
tasidi; cizim iki yerde yazilmasin diye burada.

Kurallar oldugu gibi korundu:

* **Kontur sart.** Ilk surum `ink` rengi kullanmisti ve yazi karanlik
  zeminde kayboluyordu - render edilip bakilinca cikti. Acik renk +
  kontur her zeminde okunuyor.
* **Senin yolun bir puan tablosu degil.** Dort bayrak birer cumleye
  donuyor; hicbiri yoksa baslik da yok.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.ui import text
from src.ui.i18n import t

LINE_STEP = 14
# Kare basina kayma (piksel). Ondalik birikiyor, cizimde tam sayiya
# yuvarlaniyor - `CLAUDE.md` 9: kaydirma ofseti daima tam sayi.
SCROLL_SPEED = 0.55


def lines_for(ghost: bool, lifted: bool, tidy: bool, clean: bool) -> list[str]:
    """Jenerigin satirlari - isimler, sonra (varsa) oyuncunun yolu."""
    lines = [
        t("credits.title"), "",
        t("credits.studio"), "",
        t("credits.design"), t("credits.code"), t("credits.art"),
        "", t("credits.thanks"),
    ]
    path = [key for flag, key in (
        (ghost, "credits.path_ghost"),
        (lifted, "credits.path_lifted"),
        (tidy, "credits.path_tidy"),
        (clean, "credits.path_clean"),
    ) if flag]
    if path:
        lines += ["", t("credits.path")] + [t(key) for key in path]
    return lines


def length(lines: list[str]) -> int:
    """Listenin ekranin altindan ustune tamamen gecmesi icin gereken yol."""
    return INTERNAL_HEIGHT + len(lines) * LINE_STEP + 12


def draw(surface: pygame.Surface, scroll: float, lines: list[str],
         centre_x: int = INTERNAL_WIDTH // 2) -> None:
    """Satirlari `scroll` kadar yukari kaymis halde cizer."""
    y = INTERNAL_HEIGHT - int(round(scroll))
    for line in lines:
        if -12 < y < INTERNAL_HEIGHT:
            text.draw(surface, line, centre_x, y,
                      color=palette.color("bone"), align="center",
                      outline=True)
        y += LINE_STEP
