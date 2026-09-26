"""Oyuncunun cizimi - uc kip: sprite, siluet, kutu.

Davranis `player.py`'de, cizim burada. Ayirmanin iki sebebi var: dosya basina
tek sorumluluk (CLAUDE.md 11) ve kutu kipinin oynanis kodunu kirletmemesi.

**Kutu kipi (F4)** gecici bir sey degil, kalici bir arac: "kutularla eglenceli
mi?" sorusunu sprite'lari atmadan sormanin yolu (DEVIR gorev 1 ve 5).
Bir gun dovus hissi bozuldugunda ilk bakilacak yer orasi.
"""
from __future__ import annotations

import pygame

from src.art import contact_shadow, palette, rimlight
from src.combat.combo import AttackPhase
from src.combat.hitbox import melee_rect

IFRAME_BLINK_ALPHA = 140
IFRAME_BLINK_PERIOD = 3

# Eski Kalkan - sirtta tasinan yuvarlak tahta kalkan (7x7).
#   o kontur  E isik (sol-ust)  e tahta  d golge (sag-alt)  B demir gobek
#   b gobegin parlamasi
_SHIELD_ROWS = (
    "..ooo..",
    ".oEEeo.",
    "oEeeeeo",
    "oeebBdo",
    "oeeBBdo",
    ".oeddo.",
    "..ooo..",
)
_SHIELD_COLOURS = {"E": "flesh_light", "e": "earth", "d": "earth_dark",
                   "B": "stone_light", "b": "bone"}
_shield_cache: dict[int, pygame.Surface] = {}
# Kalkanin govde merkezinden sirta uzakligi ve omuzdan asagi inisi (piksel).
SHIELD_BACK_OFFSET = 6
SHIELD_SHOULDER_DROP = 2


def draw_player(player, surface: pygame.Surface,
                offset: tuple[int, int]) -> None:
    """Oyuncuyu gecerli cizim kipinde cizer."""
    if player.scene.game.box_mode:
        _draw_box(player, surface, offset)
        _draw_attack_arc(player, surface, offset)
        return

    image = player.animator.render(
        player.facing,
        flash=player.flash.active,
        squash=player.squash.current,
        silhouette_mode=player.scene.game.silhouette_mode,
        alpha=_alpha(player),
        shadow=False,
    )
    if image is None:
        _draw_box(player, surface, offset)
        return

    ox, oy = offset
    # Iz sprite'tan ONCE: kilicin ARKASINDA kalan bir sey, onunde degil.
    # Sonra cizilseydi karakterin uzerine binerdi ve "efekt" gibi
    # okunurdu; altta kalinca "hava yarilmis" gibi okunuyor.
    player.trail.draw(surface, offset)
    contact_shadow.draw(surface, player, offset, _alpha(player) / 255.0)
    # Sprite hucresi govdeden buyuk: yatayda merkezle, dikeyde sprite'in
    # **taban cizgisini** govdenin altina hizala. Hucrenin altini hizalamak
    # karakteri havada birakir. Squash yuksekligi degistirdigi icin taban
    # cizgisi de olceklenir.
    foot = player.sprite_foot_y * player.squash.current[1]
    x = int(player.body.center_x - image.get_width() * 0.5) - ox
    y = int(player.body.bottom - foot) - oy
    surface.blit(image, (x, y))
    # Derinde golge kenarina ortamin rengi (`src/art/rimlight.py`).
    rimlight.draw(surface, image, (x, y), getattr(player.scene, "rim_light", None),
                  foot_row=int(foot))
    # Kalkan SIRTTA ama sprite'in USTUNDE: arkasina cizilen ilk surumde
    # govde ve pelerin onu tamamen yutuyordu (ekran goruntusunde yoktu).
    # Sirtin dis kenarinda, omuz hizasinda duruyor - elde degil, o yuzden
    # "kalkanla savunuyor" diye okunmuyor; tusu yok, kendiliginden
    # karsiliyor (`Player._shield_absorbs`).
    _draw_shield(player, surface, offset)

    if player.dodge.counter_ready:
        _draw_counter_hint(player, surface, offset)


def _shield_image(facing: int) -> pygame.Surface:
    """Kalkan sprite'i - bir kez uretilir, yon basina onbellekte."""
    image = _shield_cache.get(facing)
    if image is not None:
        return image
    image = pygame.Surface((7, 7), pygame.SRCALPHA)
    outline = palette.outline()
    for y, row in enumerate(_SHIELD_ROWS):
        for x, char in enumerate(row):
            if char == ".":
                continue
            colour = outline if char == "o" else palette.color(_SHIELD_COLOURS[char])
            image.set_at((x, y), colour)
    if pygame.display.get_surface() is not None:
        image = image.convert_alpha()
    # Isik HEP sol-ustten (CLAUDE.md 6) - sola bakarken aynalanmiyor,
    # yalnizca sirt tarafi degisiyor.
    _shield_cache[facing] = image
    return image


def _draw_shield(player, surface: pygame.Surface,
                 offset: tuple[int, int]) -> None:
    """Canta'da Eski Kalkan varsa sirtta gorunur (diegetik gosterge)."""
    if player.dead:
        return
    from src.systems import consumables
    data = getattr(player.scene, "save_data", None)
    if consumables.count(data, consumables.SHIELD) <= 0:
        return
    image = _shield_image(player.facing)
    ox, oy = offset
    lift = int(player.body.height * (1.0 - player.squash.current[1]))
    x = int(player.body.center_x - player.facing * SHIELD_BACK_OFFSET) - 3 - ox
    y = int(player.body.y + SHIELD_SHOULDER_DROP + lift) - oy
    surface.blit(image, (x, y))


def _alpha(player) -> int:
    """Dokunulmazlik boyunca yanip sonme - durumu gizlemeden bildirir."""
    if player.iframes > 0 and (player.iframes // IFRAME_BLINK_PERIOD) % 2 == 0:
        return IFRAME_BLINK_ALPHA
    return 255


def _draw_counter_hint(player, surface: pygame.Surface,
                       offset: tuple[int, int]) -> None:
    """Karsi vurus penceresi acik - oyuncu firsatini gormeli."""
    ox, oy = offset
    rect = player.body.rect.move(-ox, -oy)
    surface.fill(palette.color("violet_bright"),
                 (rect.centerx - 3, rect.top - 5, 6, 2))


def _squashed_rect(player, offset: tuple[int, int]) -> pygame.Rect:
    ox, oy = offset
    rect = player.body.rect.move(-ox, -oy)
    scale_x, scale_y = player.squash.current
    if scale_x == 1.0 and scale_y == 1.0:
        return rect
    width = max(2, int(rect.width * scale_x))
    height = max(2, int(rect.height * scale_y))
    return pygame.Rect(rect.centerx - width // 2, rect.bottom - height,
                       width, height)


def _draw_box(player, surface: pygame.Surface,
              offset: tuple[int, int]) -> None:
    """Kutu kipi: sanat yok, dovusun kendisi eglenceli mi diye bak."""
    rect = _squashed_rect(player, offset)
    surface.fill(_body_colour(player), rect)
    pygame.draw.rect(surface, palette.outline(), rect, 1)
    _draw_facing_marker(player, surface, rect)


def _body_colour(player) -> palette.RGB:
    """Kutu rengi durumu anlatir - sprite olmadan da okunabilsin."""
    if player.flash.active:
        return palette.role("hit_flash")
    if player.dodge.invulnerable:
        return palette.color("echo_bright")
    if player.iframes > 0 and (player.iframes // IFRAME_BLINK_PERIOD) % 2 == 0:
        return palette.color("stone_light")
    if player.chain.phase is AttackPhase.WINDUP:
        return palette.color("gold")
    if player.dodge.counter_ready:
        return palette.color("violet_bright")
    return palette.color(player.stats.body_color)


def _draw_facing_marker(player, surface: pygame.Surface,
                        rect: pygame.Rect) -> None:
    """Bakis yonu isareti - kutuda yon okunabilmeli."""
    marker_x = rect.right - 3 if player.facing > 0 else rect.left
    surface.fill(palette.color(player.stats.accent_color),
                 (marker_x, rect.top + 3, 3, 3))


def _draw_attack_arc(player, surface: pygame.Surface,
                     offset: tuple[int, int]) -> None:
    """Aktif karelerde vurus yayi - hitbox'in nerede oldugu gorunsun.

    Yalnizca kutu kipinde: sprite kipinde kilicin kendisi bu isi yapiyor.
    """
    if player.chain.phase is not AttackPhase.ACTIVE:
        return
    from src.entities.player import (
        ATTACK_HEIGHT, ATTACK_REACH, FINISHER_HEIGHT, FINISHER_REACH,
    )
    ox, oy = offset
    finisher = player.chain.is_finisher
    reach = FINISHER_REACH if finisher else ATTACK_REACH
    height = FINISHER_HEIGHT if finisher else ATTACK_HEIGHT
    arc = melee_rect(player.body, player.facing, reach, height).move(-ox, -oy)
    colour = (palette.color("violet_bright") if player.last_hit_was_counter
              else palette.color("bone"))
    surface.fill(colour, arc)
    pygame.draw.rect(surface, palette.outline(), arc, 1)
