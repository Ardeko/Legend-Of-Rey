"""Dunya icindeki etkilesim gostergesi - "burada su tusa bas".

Arda, 23.09.2026: *"Interaksiyon tuslari daha belli olmali, kullanici
hangi tusa basmasi gerektigini anlamiyor."*

## Neden bir toast yetmiyordu

Etkilesim ipuclari `hint_once` ile **bir kez** ekranin ustunde bir yazi
olarak cikiyordu. Iki sorunu vardi:

    Yer     yazi ekranin tepesinde, nesne ise dunyada - goz ikisini
            birlestirmiyor, "hangi seyle?" sorusu cevapsiz kaliyor.
    Zaman   bir kez gosterilip siliniyor. Yirmi dakika sonra ikinci
            vanaya gelen oyuncu tusu hatirlamiyor.

Buradaki gosterge **nesnenin ustunde** ve **her seferinde**: oyuncu
menzile girince tus kapagi belirir, cikinca soner. Hollow Knight'in,
Celeste'in ve Dead Cells'in yaptigi sey - ogretmek degil, hatirlatmak.

## Sozlesme: sahne her kare TEKLIF eder

Sahneler zaten "yakin mi" hesabini yapiyor (vana, mesale, kol...).
Ayni yerde bir satir: `scene.prompts.offer(...)`. Teklif edilmeyen
gosterge kendiliginden soner - "kapat" cagrisi yok, unutulacak bir sey yok.

Anahtar (`key`) gostergenin kimligi: ayni nesne her kare ayni anahtarla
teklif ediliyor, boylece belirme/sonme gecisi kesintisiz.

## Tus adi atama tablosundan

`Input.binding_label` son kullanilan cihaza gore etiket veriyor - gamepad
elindeyse gamepad dugmesi, klavyedeyse tus. Sabit "E" yazmak tusu
degistiren oyuncuya yalan soylerdi (`hint_once` ile ayni gerekce).

## Isik katmaninin USTUNDE

Karanlik bolumlerde nesne golgede kalabilir; gosterge kalmamali. O yuzden
`PlayScene.draw` onu dunya, isik ve Yanki katmanlarindan sonra, HUD'dan
hemen once ciziyor.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from src.art import palette
from src.core.input import Action
from src.ui import text
from src.ui.i18n import t

# Belirme/sonme hizi (kare basina alfa). 6 karede tam gorunur: aninda
# cikan bir kapak "zipladi" gibi okunuyor, yavas cikan "gec kaldi".
FADE_IN = 1.0 / 6.0
FADE_OUT = 1.0 / 8.0

# Kapak nesnenin bu kadar ustunde duruyor, 8 FPS'lik bir salinimla.
LIFT = 5
BOB_PERIOD = 60                  # kare
BOB_AMPLITUDE = 1                # piksel - tam sayi (CLAUDE.md 9)

CAP_PAD_X = 3
CAP_HEIGHT = 11
CAP_DEPTH = 2                    # Tusun alt kenari - basilinca kapanir
VERB_GAP = 3
POINTER_SIZE = 3


@dataclass
class _Prompt:
    x: float
    y: float
    action: Action
    verb_key: str
    alpha: float = 0.0
    offered: bool = True
    # 0..1 ise basili tutma cubugu ciziliyor (B16 kurtarma gibi).
    hold: float | None = None
    pressed_frames: int = 0


class InteractPrompts:
    """Sahnenin butun etkilesim gostergeleri."""

    def __init__(self) -> None:
        self._prompts: dict[str, _Prompt] = {}
        # (etiket, fiil) -> hazir yuzey. Her kare metin uretmek yerine
        # (CLAUDE.md 4: her karede yeniden uretme).
        self._cache: dict[tuple[str, str, bool, bool], pygame.Surface] = {}

    # --- Sahne tarafi -------------------------------------------------------
    def begin_frame(self) -> None:
        for prompt in self._prompts.values():
            prompt.offered = False

    def offer(self, key: str, x: float, y: float,
              action: Action = Action.INTERACT, verb_key: str = "",
              hold: float | None = None) -> None:
        """Bu kare `(x, y)` dunya noktasinin ustunde gosterge iste.

        `y` nesnenin UST kenari: kapak onun `LIFT` piksel yukarisinda.
        """
        prompt = self._prompts.get(key)
        if prompt is None:
            prompt = _Prompt(x, y, action, verb_key)
            self._prompts[key] = prompt
        prompt.x, prompt.y = x, y
        prompt.action = action
        prompt.verb_key = verb_key
        prompt.hold = hold
        prompt.offered = True

    def clear(self) -> None:
        self._prompts.clear()

    def active(self, key: str) -> bool:
        prompt = self._prompts.get(key)
        return prompt is not None and prompt.offered

    def update(self, input_state) -> None:
        dead = []
        for key, prompt in self._prompts.items():
            if prompt.offered:
                prompt.alpha = min(1.0, prompt.alpha + FADE_IN)
                if input_state is not None and input_state.pressed(prompt.action):
                    prompt.pressed_frames = 6
            else:
                prompt.alpha -= FADE_OUT
                if prompt.alpha <= 0.0:
                    dead.append(key)
            if prompt.pressed_frames > 0:
                prompt.pressed_frames -= 1
        for key in dead:
            del self._prompts[key]

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int],
             input_state, frame: int) -> None:
        if not self._prompts:
            return
        ox, oy = offset
        for prompt in self._prompts.values():
            if prompt.alpha <= 0.0:
                continue
            label = _label(input_state, prompt.action)
            pressed = prompt.pressed_frames > 0
            cap_w = _cap_width(label)
            anchor = int(prompt.x) - ox
            image = self._image(label, prompt.verb_key, pressed, False)
            x = anchor - cap_w // 2
            if x + image.get_width() > surface.get_width() - 2:
                # Ekranin sag kenarinda fiil kapagin SOLUNA geciyor -
                # kapak (ve oku) nesnenin ustunde kalmali, kaydirilamaz.
                image = self._image(label, prompt.verb_key, pressed, True)
                x = anchor + cap_w // 2 - image.get_width()
                if cap_w % 2:
                    x += 1
            # Salinim 8 FPS adimli ve tam sayi - piksel art titremesin.
            step = (frame // 8) * 8
            bob = round(math.sin(step / BOB_PERIOD * math.tau) * BOB_AMPLITUDE)
            # Belirirken 3 piksel asagidan yukari kayiyor: goz hareketi
            # yakaliyor, sabit bir belirme kolayca kaciriliyor.
            rise = round((1.0 - prompt.alpha) * 3)
            y = int(prompt.y) - oy - LIFT - image.get_height() + bob + rise
            if prompt.alpha < 1.0:
                image = image.copy()
                image.set_alpha(int(255 * prompt.alpha))
            surface.blit(image, (x, y))
            if prompt.hold is not None:
                _draw_hold(surface, anchor - cap_w // 2,
                           y + image.get_height() + 1,
                           cap_w, prompt.hold, prompt.alpha)

    def _image(self, label: str, verb_key: str, pressed: bool,
               verb_left: bool) -> pygame.Surface:
        cache_key = (label, verb_key, pressed, verb_left)
        image = self._cache.get(cache_key)
        if image is None:
            image = _render(label, t(verb_key) if verb_key else "", pressed,
                            verb_left)
            if len(self._cache) > 64:
                self._cache.clear()
            self._cache[cache_key] = image
        return image


def _label(input_state, action: Action) -> str:
    if input_state is None:
        return "?"
    label = input_state.binding_label(action)
    return label or "?"


def _cap_width(label: str) -> int:
    return max(CAP_HEIGHT, text.text_width(label) + CAP_PAD_X * 2)


def _render(label: str, verb: str, pressed: bool,
            verb_left: bool = False) -> pygame.Surface:
    """Tus kapagi + fiil + nesneyi gosteren ok, tek yuzeyde.

    Kapak gercek bir tus gibi: ust yuz, alt kenarda koyu bir derinlik
    seridi. Basilinca derinlik kapaniyor ve yuz bir piksel iniyor -
    oyuncu tusun "tuttugunu" goruyor.
    """
    cap_w = _cap_width(label)
    verb_w = text.text_width(verb) + VERB_GAP + 2 if verb else 0
    width = cap_w + verb_w
    height = CAP_HEIGHT + CAP_DEPTH + POINTER_SIZE + 1
    image = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
    cap = _render_cap(label, pressed, cap_w, height)
    if verb_left:
        image.blit(cap, (verb_w, 0))
        text.draw(image, verb, 1, 2, color=palette.role("ui_text"), outline=True)
    else:
        image.blit(cap, (0, 0))
        text.draw(image, verb, cap_w + VERB_GAP, 2,
                  color=palette.role("ui_text"), outline=True)
    return image


def _render_cap(label: str, pressed: bool, cap_w: int,
                height: int) -> pygame.Surface:
    image = pygame.Surface((cap_w, height), pygame.SRCALPHA)

    face_y = CAP_DEPTH if pressed else 0
    depth = 0 if pressed else CAP_DEPTH
    edge = palette.color("stone_light")
    face = palette.color("ink")
    rim = palette.color("stone_darkest")
    # Derinlik seridi (tusun yani) - kapagin altinda.
    image.fill(rim, (1, face_y + CAP_HEIGHT - 1, cap_w - 2, depth + 1))
    # Kenar: koseleri kirpik, yuvarlak tus hissi.
    image.fill(edge, (1, face_y, cap_w - 2, CAP_HEIGHT))
    image.fill(edge, (0, face_y + 1, cap_w, CAP_HEIGHT - 2))
    image.fill(face, (1, face_y + 1, cap_w - 2, CAP_HEIGHT - 2))
    # Sol-ust isik kurali: ust kenarda tek piksellik parlama.
    image.fill(palette.color("stone"), (2, face_y + 1, cap_w - 4, 1))
    text.draw(image, label, cap_w // 2, face_y + 2, align="center",
              color=palette.role("ui_text_bright"))

    # Nesneyi gosteren ok - kapagin ortasindan asagi.
    tip_y = CAP_HEIGHT + CAP_DEPTH + POINTER_SIZE
    cx = cap_w // 2
    for row in range(POINTER_SIZE):
        half = POINTER_SIZE - 1 - row
        image.fill(edge, (cx - half, tip_y - POINTER_SIZE + row, half * 2 + 1, 1))
    return image


def _draw_hold(surface: pygame.Surface, x: int, y: int, width: int,
               progress: float, alpha: float) -> None:
    """Basili tutma ilerlemesi - kapagin hemen altinda ince bir cubuk."""
    bar = pygame.Surface((width, 3), pygame.SRCALPHA)
    bar.fill(palette.color("ink"))
    fill = int((width - 2) * max(0.0, min(1.0, progress)))
    if fill > 0:
        bar.fill(palette.color("gold"), (1, 1, fill, 1))
    if alpha < 1.0:
        bar.set_alpha(int(255 * alpha))
    surface.blit(bar, (x, y))
