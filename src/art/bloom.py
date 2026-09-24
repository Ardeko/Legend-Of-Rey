"""Isima (bloom) - parlak kaynaklarin cevresine sacilan yumusak isik.

Arda, 24.09.2026: *"grafikleri daha modern gercekci olarak
gelistirebiliyorsan gelistir."*

Modern piksel sanat oyunlarinin (Dead Cells, Blasphemous, Eastward)
"canli" gorunmesinin en buyuk tek nedeni bu: lav, mesale, kristal ve
buyu yalnizca parlak piksel degil, havayi da aydinlatiyor. Sprite'lar
ayni kaliyor; degisen havada asili isik.

## Nasil (ucuz)

    1  kareyi dortte bire kucult           (smoothscale)
    2  esikten dusuk her seyi cikar        (BLEND_RGB_SUB) - yalniz parlaklar kalir
    3  bir kez daha kucult, sonra buyut    (iki olcekli bulanik)
    4  zayiflat ve kareye EKLE             (BLEND_RGB_ADD)

Hepsi pygame'in C tarafinda; numpy yok, kare basina ~1 ms. Ara yuzeyler
bir kez ayriliyor ve yeniden kullaniliyor (her karede tahsis yok).

## `smoothscale` burada serbest

`CLAUDE.md` 4 piksel sanati `smoothscale` ile olceklemeyi yasakliyor -
sprite bulaniklasir. Burada olceklenen sey sprite degil **isik**: sonuc
kareye yalnizca eklemeli bir hale olarak biniyor, hicbir piksel
bulaniklasmiyor. (Ayni ayrim `lore-dev` becerisinde de yazili: "isik/aura
katmaninda serbest".)

## Arayuz isimaz

`PlayScene.draw` bunu dunya ve isik katmanlarindan SONRA, tus gostergesi
ve HUD'dan ONCE cagiriyor. Yazilar keskin kaliyor.

## Erisilebilirlik

Guc "Efekt gucu" ayarindan (`postfx`) geliyor: 0 ise hic calismiyor.
Fotosensitivite ve performans icin ayri bir dugme gerekmiyor - ayni
ayar zaten "ekran efektlerini kis" demek.
"""
from __future__ import annotations

import pygame

# Bu parlakligin (kanal basina) altindaki her sey isimaz. Tas (stone_light
# 126-158) neredeyse hic, karakter tenleri az; kor (ember 176, ember_light
# 236), altin (255), mor parlak (234 mavi), beyaz flas isiyor.
THRESHOLD = 128
# Eklenen halenin gucu (0..255 carpan). Ayar 1.0 iken.
INTENSITY = 255
# Ara olcekler: dortte bir (sik hale) ve sekizde bir (genis hale).
NEAR_DIVISOR = 4
FAR_DIVISOR = 8

_buffers: dict[str, pygame.Surface] = {}


def clear_cache() -> None:
    _buffers.clear()


def _buffer(name: str, size: tuple[int, int]) -> pygame.Surface:
    surface = _buffers.get(name)
    if surface is None or surface.get_size() != size:
        surface = pygame.Surface(size)
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            surface = surface.convert()
        _buffers[name] = surface
    return surface


def apply(target: pygame.Surface, strength: float = 1.0) -> None:
    """`target`e isima ekler. `strength` 0 ise hicbir sey yapmaz."""
    if strength <= 0.0:
        return
    width, height = target.get_size()
    near_size = (max(1, width // NEAR_DIVISOR), max(1, height // NEAR_DIVISOR))
    far_size = (max(1, width // FAR_DIVISOR), max(1, height // FAR_DIVISOR))
    bright = _buffer("bright", (width, height))
    near = _buffer("near", near_size)
    far = _buffer("far", far_size)
    halo = _buffer("halo", (width, height))

    # Esik TAM cozunurlukte: once kucultseydik 3 piksellik lav selalesi
    # ortalamada sonup esigin altina dusuyordu (olculdu - isima yoktu).
    bright.blit(target, (0, 0))
    bright.fill((THRESHOLD, THRESHOLD, THRESHOLD), special_flags=pygame.BLEND_RGB_SUB)
    pygame.transform.smoothscale(bright, near_size, near)
    pygame.transform.smoothscale(near, far_size, far)

    # Genis hale + sik hale ayni yuzeyde; ikisi toplaninca merkez parlak,
    # kenar yumusak kaliyor (tek olcek ya "leke" ya "sis" gibi okunuyordu).
    pygame.transform.smoothscale(far, (width, height), halo)
    level = max(0, min(255, int(INTENSITY * strength)))
    halo.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
    target.blit(halo, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    pygame.transform.smoothscale(near, (width, height), halo)
    level = max(0, min(255, int(INTENSITY * 0.55 * strength)))
    halo.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
    target.blit(halo, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
