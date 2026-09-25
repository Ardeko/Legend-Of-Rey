"""Hareket eden hasar kutularinin gorunumu - oklar, bomba, anahtarlar.

23.09.2026'da bulundu: `Hitbox.velocity` ile ucan HICBIR sey
cizilmiyordu. Oyuncunun oku ve bombasi, Okcu'nun oku, Zindanci'nin
anahtar demeti yalnizca hata ayiklama katmaninda kirmizi bir cerceveydi.
En agir sonucu Okcu'da: `CLAUDE.md` 7 her dusman saldirisinin okunabilir
olmasini istiyor, ama havadaki ok gorunmuyordu - oyuncu kacinmasi
gereken seyi goremiyordu.

## Sozlesme

Kutu `visual` alaninda bir ad tasiyor; burasi o adla ciziyor. Ad yoksa
kutu gorunmez kaliyor - yakin dovus savurusunu sprite ve iz zaten
anlatiyor, ustune bir kutu cizmek gurultu olurdu.

## Dusman mermisi = tehlike rengi VE sekil

`CLAUDE.md` 7/10: tehlike asla yalnizca renkle anlatilmaz. Dusman oku
oyuncununkinden iki kanalla ayriliyor: ucu `danger_bright` **ve**
cengelli (iki piksellik kanca). Renk korlugu modunda palet degisiyor,
sekil degismiyor.

## Performans

Oklarin sprite'lari **bir kez** uretiliyor (`CLAUDE.md` 4) ve yon basina
onbellekte. Bomba ve anahtar birkac `fill` - her karede uretmeye degmez
ama onbellege de gerek yok.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow

# Ok sprite'lari - saga bakan hali; sola bakan aynalaniyor.
#   f tuy   s sap   h ucun kanadi   H uc   t uc parlamasi   b kanca
_PLAYER_ARROW = (
    "..........",
    "ff......h.",
    ".fssssssHt",
    "ff......h.",
    "..........",
)
_ENEMY_ARROW = (
    ".......b..",
    "ff.....hh.",
    ".fssssssHt",
    "ff.....hh.",
    ".......b..",
)
_PLAYER_COLOURS = {"f": "bone", "s": "flesh", "h": "stone_light",
                   "H": "stone_light", "t": "white_flash"}
_ENEMY_COLOURS = {"f": "danger", "s": "earth", "h": "danger",
                  "H": "danger_bright", "t": "danger_bright", "b": "danger"}

# Bombanin son bu kadar karesinde govde tehlike renginde yanip sonuyor:
# "patlamak uzere" bilgisi. Sekil kanali: kivilcim da buyuyor.
BOMB_WARN_FRAMES = 30

_cache: dict[tuple[str, int], pygame.Surface] = {}


def clear_cache() -> None:
    _cache.clear()


def _sprite(kind: str, facing: int) -> pygame.Surface:
    key = (kind, facing)
    image = _cache.get(key)
    if image is not None:
        return image
    rows = _ENEMY_ARROW if kind == "enemy_arrow" else _PLAYER_ARROW
    colours = _ENEMY_COLOURS if kind == "enemy_arrow" else _PLAYER_COLOURS
    image = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            name = colours.get(char)
            if name:
                image.set_at((x, y), palette.color(name))
    if facing < 0:
        image = pygame.transform.flip(image, True, False)
    if pygame.display.get_init() and pygame.display.get_surface() is not None:
        image = image.convert_alpha()
    _cache[key] = image
    return image


def draw(surface: pygame.Surface, offset: tuple[int, int], boxes,
         frame: int) -> None:
    """Gorunumu olan butun kutular. Aktorlerden SONRA, parcaciklardan once."""
    ox, oy = offset
    width, height = surface.get_size()
    for box in boxes:
        kind = getattr(box, "visual", "")
        if not kind or box.expired:
            continue
        rect = box.rect.move(-ox, -oy)
        if rect.right < -16 or rect.left > width + 16:
            continue
        if rect.bottom < -16 or rect.top > height + 16:
            continue
        drawer = _DRAWERS.get(kind)
        if drawer is not None:
            drawer(surface, box, rect, frame)


def _facing(box) -> int:
    vx = box.velocity[0]
    if vx:
        return 1 if vx > 0 else -1
    return getattr(box.owner, "facing", 1) or 1


def _draw_arrow(surface: pygame.Surface, box, rect: pygame.Rect,
                frame: int) -> None:
    facing = _facing(box)
    image = _sprite(box.visual, facing)
    x = rect.centerx - image.get_width() // 2
    y = rect.centery - image.get_height() // 2
    # Iz: arkada uc sonuk piksel - hizi okutuyor, ok "isinlanmiyor".
    trail = palette.color("stone_dark" if box.visual == "arrow" else "danger")
    tail_x = x if facing > 0 else x + image.get_width() - 1
    for step, length in ((3, 2), (7, 2)):
        tx = tail_x - facing * step
        surface.fill(trail, (min(tx, tx - facing * (length - 1)),
                             y + 2, length, 1))
    if box.visual == "enemy_arrow":
        # Karanlik odada da gorulsun: hafif tehlike halesi.
        glow = radial_glow(6, palette.color("danger"), peak=0.35)
        head_x = x + (image.get_width() - 2 if facing > 0 else 1)
        surface.blit(glow, (head_x - 6, y + 2 - 6),
                     special_flags=pygame.BLEND_RGB_ADD)
    surface.blit(image, (x, y))


def _draw_bomb(surface: pygame.Surface, box, rect: pygame.Rect,
               frame: int) -> None:
    """Donen bomba: sol-ust parlama sabit, donen seridi 8 FPS."""
    cx, cy = rect.center
    left = box.active_frames - box.frames_alive
    warn = left <= BOMB_WARN_FRAMES and (frame // 4) % 2 == 0
    # Govde karanlik zeminde kaybolmasin diye tasin tonunda; kenar
    # isigi sol-ustte iki piksel (ilk hali `ink_soft` idi - gorunmedi).
    body = palette.color("danger" if warn else "stone_dark")
    outline = palette.color("ink")
    surface.fill(outline, (cx - 3, cy - 2, 7, 5))
    surface.fill(outline, (cx - 2, cy - 3, 5, 7))
    surface.fill(body, (cx - 2, cy - 2, 5, 5))
    surface.fill(body, (cx - 3, cy - 1, 7, 3))
    # Donen demir serit - donmeyi anlatan tek sey.
    spin = (frame // 8) % 4
    band = palette.color("ink_soft")
    if spin in (0, 2):
        surface.fill(band, (cx - 3 if spin == 0 else cx - 2, cy, 6, 1))
    else:
        surface.fill(band, (cx, cy - 3 if spin == 1 else cy - 2, 1, 6))
    rim = palette.color("stone_light")
    surface.fill(rim, (cx - 2, cy - 2, 2, 1))                     # sol-ust isik
    surface.fill(rim, (cx - 3, cy - 1, 1, 1))
    # Fitil ve kivilcim.
    surface.fill(palette.color("earth"), (cx + 1, cy - 4, 1, 1))
    surface.fill(palette.color("earth"), (cx + 2, cy - 5, 1, 1))
    spark = palette.color("gold" if (frame // 3) % 2 else "ember_light")
    size = 2 if left <= BOMB_WARN_FRAMES else 1
    surface.fill(spark, (cx + 2, cy - 6 - (size - 1), size, size))
    glow = radial_glow(5 + size * 2, palette.color("ember"), peak=0.45)
    surface.blit(glow, (cx + 2 - 5 - size * 2, cy - 6 - 5 - size * 2),
                 special_flags=pygame.BLEND_RGB_ADD)


def _draw_keys(surface: pygame.Surface, box, rect: pygame.Rect,
               frame: int) -> None:
    """Zindanci'nin anahtar demeti: halka ve donen iki anahtar.

    Dusman mermisi - tehlike rengi bir kenar (renk) ve donen dislı
    sekil (sekil). Anahtarlar altin: Zindanci'nin kendi rengi.
    """
    cx, cy = rect.center
    ring = palette.color("stone_light")
    pygame.draw.circle(surface, palette.color("danger"), (cx, cy), 4, 1)
    pygame.draw.circle(surface, ring, (cx, cy), 3, 1)
    angle = (frame // 8) * (math.pi / 4) * _facing(box)
    gold = palette.color("gold")
    for spread in (0.0, math.pi * 0.8):
        a = angle + spread
        tip_x = cx + round(math.cos(a) * 6)
        tip_y = cy + round(math.sin(a) * 6)
        pygame.draw.line(surface, gold, (cx + round(math.cos(a) * 3),
                                         cy + round(math.sin(a) * 3)),
                         (tip_x, tip_y))
        surface.fill(gold, (tip_x - 1, tip_y - 1, 2, 2))


def _draw_chain_lash(surface: pygame.Surface, box, rect: pygame.Rect,
                     frame: int) -> None:
    """Zindanci'nin zincir kirbaci - 62 piksellik menzili GORUNUR yapiyor.

    Zincir ilk uc karede uzaniyor (bir anda belirmesi "kutu" gibi
    okunuyordu), ucunda tehlike renginde bir kanca.
    """
    facing = _facing(box)
    reach = rect.width
    grow = min(1.0, (box.frames_alive + 1) / 3.0)
    start_x = rect.left if facing > 0 else rect.right
    end_x = start_x + facing * int(reach * grow)
    y = rect.centery
    light, dark = palette.color("stone_light"), palette.color("stone")
    step = 0
    x = start_x
    while (x - end_x) * facing < 0:
        sag = round(math.sin((x - start_x) / max(1, reach) * math.pi) * 2)
        colour = light if step % 2 == 0 else dark
        surface.fill(colour, (min(x, x + facing * 2), y + sag - (step % 2), 3, 1 + step % 2))
        x += facing * 3
        step += 1
    hook = palette.color("danger_bright")
    surface.fill(hook, (end_x - 1, y - 2, 3, 3))
    surface.fill(hook, (end_x + facing * 2, y - 3, 1, 3))


def _draw_echo_wave(surface: pygame.Surface, box, rect: pygame.Rect,
                    frame: int) -> None:
    """Fisilti'nin bitiricisi: ileri giden mor bir hilal ve iki yanki izi.

    Yanki'nin rengi (`violet`) - oyuncu bunun Rey'in kafasindaki sesin
    disari tasmasi oldugunu ayni renkten okuyor. Sonuna dogru inceliyor:
    menzilin bittigini gormek icin kutunun ne kadar yasadigina bakiliyor.
    """
    facing = _facing(box)
    life = max(1, box.active_frames)
    fade = 1.0 - box.frames_alive / life
    cx, cy = rect.center
    glow = radial_glow(10, palette.color("violet"), peak=0.30 + 0.35 * fade)
    surface.blit(glow, (cx - 10, cy - 10), special_flags=pygame.BLEND_RGB_ADD)
    half = 3 + round(5 * fade)
    for echo, colour in ((0, "violet_bright"), (4, "violet"), (8, "violet_dark")):
        x = cx - facing * echo
        span = max(1, half - echo // 3)
        for dy in range(-span, span + 1):
            # Hilal: ortada one tasiyor, uclar geride.
            bulge = round((1.0 - (dy / (span + 0.5)) ** 2) * 3)
            surface.set_at((x + facing * bulge, cy + dy), palette.color(colour))
    if (frame // 4) % 2 == 0:
        surface.set_at((cx + facing * 4, cy), palette.color("white_flash"))


def _draw_blade_wave(surface: pygame.Surface, box, rect: pygame.Rect,
                     frame: int) -> None:
    """Kilic Dalgasi (yetenek agaci, KESKIN 5): celik bir hilal.

    Fisilti'nin mor dalgasiyla ayni iskelet ama bilerek FARKLI iki
    kanalda: renk celik/kemik (Yanki'nin moru degil - bu kilicin kendisi)
    ve sekil daha uzun, keskin kenarli. Arkasinda uc sonuk kopya hizi
    anlatiyor; menzilin sonuna dogru inceliyor.
    """
    facing = _facing(box)
    life = max(1, box.active_frames)
    fade = 1.0 - box.frames_alive / life
    cx, cy = rect.center
    glow = radial_glow(9, palette.color("bone"), peak=0.18 + 0.30 * fade)
    surface.blit(glow, (cx - 9, cy - 9), special_flags=pygame.BLEND_RGB_ADD)
    half = 4 + round(5 * fade)
    trail = ((0, "white_flash"), (1, "bone"), (4, "stone_light"),
             (8, "stone"), (12, "stone_dark"))
    for echo, colour in trail:
        if echo >= 8 and fade < 0.4:
            continue                      # sonda kuyruk kisaliyor
        x = cx - facing * echo
        span = max(1, half - echo // 4)
        tone = palette.color(colour)
        for dy in range(-span, span + 1):
            bulge = round((1.0 - (dy / (span + 0.5)) ** 2) * 4)
            surface.set_at((x + facing * bulge, cy + dy), tone)
    # Kenardaki parilti - 8 FPS'lik bir kivilcim, sol-ust isik kurali.
    if (frame // 4) % 2 == 0:
        surface.set_at((cx + facing * 5, cy - half + 1),
                       palette.color("white_flash"))


_DRAWERS = {
    "blade_wave": _draw_blade_wave,
    "echo_wave": _draw_echo_wave,
    "arrow": _draw_arrow,
    "enemy_arrow": _draw_arrow,
    "bomb": _draw_bomb,
    "keys": _draw_keys,
    "chain_lash": _draw_chain_lash,
}
