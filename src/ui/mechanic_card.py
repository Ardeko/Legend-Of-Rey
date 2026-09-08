"""Mekanik tanitim karti - "yeni bir sey ogrendin, tusu bu."

Arda, 08.09.2026: *"yeni mekanik acilan her bolum icin guzel
grafiklerle ve belirgin UX UI ile ipuclari versin oyun."*

## Bildirim (toast) neden yetmiyordu

Oyunda `hint_once()` vardi ve dogru calisiyordu: tusu bir kez
soyluyor, tus adini atama tablosundan okuyor, kayda isaretliyor. Ama
ciktisi ekranin ustunde 3.5 saniye duran **kucuk gri bir yazi** -
dovus bildirimleriyle, combo sayaciyla ve hasar yazilariyla ayni yer,
ayni bicim.

Yani oyunun "bu senin yeni yetenegin" demesiyle "14 COMBO" demesi
gorsel olarak ayni seydi. Bir mekanigin dogdugu an, bir combo
sayacindan daha onemli.

Kart farki **bicimle** kuruyor: ortada, cerceveli, ikonlu ve tus
kapakli. Oyuncu onu bir daha hicbir yerde gormuyor - o yuzden
gorunce duruyor.

## Ama oynanisi DURDURMUYOR

`ChapterCard` ile ayni ilke (`CLAUDE.md` 9). Oyuncu ilk kareden
itibaren yuruyebiliyor; kart ustunde soner. Durdursaydik her yeni
mekanik bir kesinti olurdu ve oyuncu okumak yerine gecmeye calisirdi -
tam da onlemek istedigimiz sey.

## Ikon **cizilir**, harf degil

Bir tus kapaginin icine "G" yazip birakmak tusu soyler ama **ne ise
yaradigini** soylemez. Her mekanigin kendi kucuk ikonu var: rezonans
icin genisleyen halkalar, firlatma icin yukari ok, karakter degisimi
icin iki siluet. Ikon "ne", tus kapagi "nasil".

Zamanlama - toplam 260 kare (~4.3 sn):
    0-24     kart asagidan suzulerek belirir
    24-60    ikon cizilir, halka darbesi
    60-200   durur (okuma suresi)
    200-260  soner
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.ui import text
from src.ui.dialogue import _wrap
from src.ui.font_data import GLYPH_HEIGHT, GLYPH_WIDTH, TRACKING
from src.ui.i18n import t
from src.ui.widgets import panel

# **Baslik anahtarlari DUZ DIZE.** Ilk surum `f"{message_key}_title"`
# ile kuruyordu; PyInstaller ve oyun icin sorun yok ama
# `tests/test_lang.py` kaynak taramasi onlari goremiyor ve "olu
# anahtar" diye bildiriyor. Bu tuzaga projede DORT kez dusuldu (dil
# anahtarlari, ses adlari, panel onekleri, yetenek etiketleri) ve
# kural her seferinde ayni: anahtarlar her yerde duz yazilir.
TITLES: dict[str, str] = {
    "hint.bell": "hint.bell_title",
    "hint.resonance": "hint.resonance_title",
    "hint.boost": "hint.boost_title",
    "hint.switch": "hint.switch_title",
    "hint.companion_wait": "hint.companion_wait_title",
    "hint.inventory": "hint.inventory_title",
    "hint.rescue": "hint.rescue_title",
}


def title_for(message_key: str) -> str:
    """Gövde anahtarindan baslik anahtari. Yoksa govdenin kendisi.

    Eksik bir baslik karti bozmamali: metin iki kez cikar, ama oyun
    calisir ve eksiklik ekranda gorunur - sessizce kaybolmaz.
    """
    return TITLES.get(message_key, message_key)


CARD_IN = 24
ICON_IN = 60
HOLD_UNTIL = 200
TOTAL = 260

WIDTH = 188
HEIGHT = 70
CENTER_Y = INTERNAL_HEIGHT // 2 - 30

# Tus kapagi - ikonun sagindaki kucuk cerceve.
CAP_HEIGHT = 13
CAP_PADDING = 4

# Govde metni bu genislikte sariliyor. Kart 188 piksel, ikon 46 yiyor,
# sag kenarda 8 piksel pay: (188-46-8) / karakter genisligi.
BODY_COLUMNS = (WIDTH - 46 - 8) // (GLYPH_WIDTH + TRACKING)
BODY_LINES = 2
LINE_STEP = GLYPH_HEIGHT + 2


def _ease_out(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1.0 - (1.0 - value) * (1.0 - value)


class MechanicCard:
    """Tek bir mekanigin tanitimi. Sahne `update()`/`draw()` cagirir.

    `icon` asagidaki cizicilerden birinin adi; bilinmeyen ad sessizce
    genel bir isaret ciziyor - bir ikon eksikligi oyunu durdurmamali.
    """

    __slots__ = ("title_key", "body_key", "icon", "key_label", "frames",
                 "active")

    def __init__(self, title_key: str, body_key: str, icon: str,
                 key_label: str) -> None:
        self.title_key = title_key
        self.body_key = body_key
        self.icon = icon
        self.key_label = key_label
        self.frames = 0
        self.active = True

    @property
    def done(self) -> bool:
        return not self.active

    def update(self) -> None:
        if not self.active:
            return
        self.frames += 1
        if self.frames >= TOTAL:
            self.active = False

    # --- Cizim --------------------------------------------------------------
    def _alpha(self) -> float:
        if self.frames < CARD_IN:
            return _ease_out(self.frames / CARD_IN)
        if self.frames > HOLD_UNTIL:
            return max(0.0, 1.0 - (self.frames - HOLD_UNTIL)
                       / (TOTAL - HOLD_UNTIL))
        return 1.0

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        alpha = self._alpha()
        if alpha <= 0.01:
            return

        # Asagidan suzulerek gelir - `ChapterCard` ile ayni hareket.
        rise = int(round((1.0 - _ease_out(self.frames / CARD_IN)) * 10))
        rect = pygame.Rect(INTERNAL_WIDTH // 2 - WIDTH // 2,
                           CENTER_Y + rise, WIDTH, HEIGHT)

        card = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel(card, pygame.Rect(0, 0, WIDTH, HEIGHT))
        self._draw_icon(card)
        self._draw_text(card)
        card.set_alpha(int(255 * alpha))
        surface.blit(card, rect.topleft)

    def _draw_text(self, card: pygame.Surface) -> None:
        left = 46
        text.draw(card, t(self.title_key), left, 8,
                  color=palette.color("violet_bright"), outline=True)

        # **Govde SARILIYOR.** Ilk surum tek satir ciziyordu ve Turkce
        # metin kartin sag kenarindan tasip kirpiliyordu ("G ile sesini
        # gonder - ça|"). Ekran goruntusu yakaladi; olcum degil GOZ.
        #
        # **`key` yer tutucusu da doldurulmali** - onceki surum
        # `t(body_key)` diyordu ve ekranda ham "{key}" yaziyordu; font
        # `{` karakterini bile tanimiyor (konsola uyari dusuyordu).
        body = t(self.body_key, key=self.key_label)
        y = 21
        for row in _wrap(body, BODY_COLUMNS)[:BODY_LINES]:
            text.draw(card, row, left, y, color=palette.role("ui_text_dim"))
            y += LINE_STEP
        self._draw_keycap(card, left, y + 2)

    def _draw_keycap(self, card: pygame.Surface, x: int, y: int) -> None:
        """Tus kapagi - **atama tablosundan gelen** etiketle.

        Sabit "G" yazsaydik tusu degistiren oyuncuya yalan soylerdik;
        `hint_once` ile ayni gerekce (`src/scenes/play.py`).
        """
        label = self.key_label or "?"
        width = text.text_width(label) + CAP_PADDING * 2
        cap = pygame.Rect(x, y, width, CAP_HEIGHT)
        card.fill(palette.role("ui_border"), cap)
        card.fill(palette.color("ink"), cap.inflate(-2, -2))
        text.draw(card, label, x + CAP_PADDING, y + 3,
                  color=palette.role("ui_text_bright"))

    # --- Ikonlar ------------------------------------------------------------
    def _draw_icon(self, card: pygame.Surface) -> None:
        """Ikon **cizilir**: "ne" sorusunu tus kapagi degil bu cevapliyor.

        Ilerleme 0..1 - ikon kartla birlikte kuruluyor, hazir gelmiyor.
        """
        progress = max(0.0, min(1.0, (self.frames - CARD_IN)
                                / max(1, ICON_IN - CARD_IN)))
        cx, cy = 25, HEIGHT // 2
        drawer = {
            "resonance": _icon_resonance,
            "boost": _icon_boost,
            "switch": _icon_switch,
            "companion": _icon_companion,
            "inventory": _icon_inventory,
        }.get(self.icon, _icon_generic)
        drawer(card, cx, cy, progress, self.frames)


def _icon_resonance(card, cx: int, cy: int, progress: float,
                    frame: int) -> None:
    """Genisleyen halkalar - ses dalgasi. Rezonansin tamami bu."""
    colour = palette.color("violet_bright")
    card.fill(colour, (cx - 1, cy - 1, 3, 3))
    for index in range(3):
        # Halkalar sirayla aciliyor ve surekli nabiz atiyor: durgun
        # bir halka "ses" gibi okunmuyordu.
        phase = (frame * 0.05 + index * 0.45) % 1.0
        if phase > progress + 0.34:
            continue
        radius = int(4 + phase * 12)
        tone = "violet_bright" if index == 0 else "violet"
        pygame.draw.circle(card, palette.color(tone), (cx, cy), radius, 1)


def _icon_boost(card, cx: int, cy: int, progress: float, frame: int) -> None:
    """Yukari ok + altinda iki el - "seni yukari atiyor"."""
    colour = palette.color("gold")
    height = int(12 * progress)
    card.fill(colour, (cx - 1, cy + 6 - height, 2, height))
    for step in range(4):
        card.fill(colour, (cx - 1 - step, cy - 6 + step + (12 - height), 2, 1))
        card.fill(colour, (cx + step, cy - 6 + step + (12 - height), 2, 1))
    # Iki el: alt kenarda iki kisa cizgi.
    card.fill(palette.color("stone_light"), (cx - 6, cy + 8, 4, 2))
    card.fill(palette.color("stone_light"), (cx + 2, cy + 8, 4, 2))


def _icon_switch(card, cx: int, cy: int, progress: float, frame: int) -> None:
    """Iki siluet, aralarinda gidip gelen bir isaret."""
    left = palette.color("abyss_light")
    right = palette.color("stone_light")
    card.fill(left, (cx - 9, cy - 5, 4, 11))
    card.fill(right, (cx + 5, cy - 5, 4, 11))
    swing = int(round(math.sin(frame * 0.09) * 3))
    card.fill(palette.color("violet_bright"), (cx - 1 + swing, cy - 1, 3, 2))


def _icon_companion(card, cx: int, cy: int, progress: float,
                    frame: int) -> None:
    """Bir siluet duruyor, oteki uzakta - "burada bekle"."""
    card.fill(palette.color("abyss_light"), (cx - 8, cy - 5, 4, 11))
    card.fill(palette.color("stone_light"), (cx + 4, cy - 3, 3, 9))
    for x in range(cx - 2, cx + 3, 2):
        card.fill(palette.role("ui_text_dim"), (x, cy, 1, 1))


def _icon_inventory(card, cx: int, cy: int, progress: float,
                    frame: int) -> None:
    """Uc yuva, ortadaki secili."""
    for index, offset in enumerate((-9, -1, 7)):
        rect = pygame.Rect(cx + offset, cy - 5, 7, 10)
        card.fill(palette.role("ui_border"), rect)
        card.fill(palette.color("ink"), rect.inflate(-2, -2))
        if index == 1:
            card.fill(palette.color("gold"), rect.inflate(-4, -4))


def _icon_generic(card, cx: int, cy: int, progress: float,
                  frame: int) -> None:
    """Bilinmeyen ikon adi - kart yine de calisiyor.

    Eksik bir ikon yuzunden oyunun durmasi kabul edilemez; bir mekanik
    tanitimi, ikonundan onemli.
    """
    pygame.draw.circle(card, palette.color("violet"), (cx, cy), 7, 1)
    card.fill(palette.color("violet_bright"), (cx - 1, cy - 4, 2, 5))
    card.fill(palette.color("violet_bright"), (cx - 1, cy + 3, 2, 2))
