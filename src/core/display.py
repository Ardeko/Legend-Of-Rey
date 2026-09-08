"""Monitor yerlesimi - hangi ekran nerede, calisma alani ne kadar.

## Neden gerekti

Oyun tam ekrana daima **(0, 0)** konumunda, `get_desktop_sizes()[0]`
boyutunda aciliyordu. Tek monitorde dogru; iki monitorde degil.
Olculdu (08.09.2026, Arda'nin makinesi - iki adet 1920x1080):

    pencere ikinci monitorde     -> konum (2100, 200)
    F11'e basildi                -> konum (0, 0)      <-- BIRINCI monitor
    tam ekrandan cikildi         -> konum (240, 135)  <-- yine birinci

Yani oyuncu ikinci ekranda oynuyorsa tam ekran onu **diger ekrana
firlatiyor** ve geri donmuyor. Arda'nin "arada sorun yasiyorum"
demesinin sebebi bu "arada": hata pencerenin hangi ekranda oldugundan
baska hicbir seye bagli degil.

Ikinci hata ayni yerden cikti: pencereli kip masaustunun **tamamini**
kullanilabilir saniyordu. Gorev cubugu 48 piksel yiyor:

    monitor tam alan   1920x1080
    calisma alani      1920x1032   <-- pencere buna sigmali

Ayarlardan elle 4x secilince pencere 1920x1080 oluyor ve alt 48 pikseli
(arti baslik cubugu) ekran disinda kaliyordu. `_best_scale()` bunu
`SCALE_SCREEN_MARGIN` ile onluyordu ama **elle secilen olcek o korumayi
atliyordu**.

## Neden ctypes, neden pygame degil

pygame-ce 2.5.8 monitorlerin **boyutunu** veriyor (`get_desktop_sizes`)
ama **konumunu** vermiyor - iki 1920x1080 ekranin yan yana mi ust uste
mi durdugu sorulamiyor. Gorev cubugunu de bilmiyor. Windows bunu
`EnumDisplayMonitors` ile soyluyor ve `ctypes` standart kutuphanede:
yeni bagimlilik yok (CLAUDE.md 4).

Windows disinda ve ctypes basarisiz olursa `get_desktop_sizes()`'a
donuluyor: ekranlar soldan saga dizili varsayiliyor ve calisma alani
tam alana esit sayiliyor. Dogru olmayabilir ama **calisir** kalir.

## Secim mantigi ayri ve saf

`pick()` monitor listesini disaridan aliyor. Boylece iki monitorlu
yerlesim gercek donanim olmadan test edilebiliyor
(`tests/test_display.py`) - bu hatanin ilk kez uretilmesi gercek bir
ikinci ekran gerektirmisti.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import pygame

from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH


@dataclass(frozen=True)
class Monitor:
    """Tek bir ekran.

    `bounds` tam alan - tam ekran bunu kullanir.
    `work`   gorev cubugu haric - pencereli kip bunu kullanir.
    """

    bounds: pygame.Rect
    work: pygame.Rect
    primary: bool = False


def pick(screens: list[Monitor], point: tuple[int, int]) -> Monitor:
    """`point`'i iceren ekran. Hicbiri icermiyorsa birincil.

    Saf fonksiyon: liste disaridan geliyor, boylece iki monitorlu
    yerlesim gercek donanim olmadan test edilebiliyor.

    Nokta hicbir ekranda degilse (pencere ekran disina surulmus ya da
    bir monitor cikarilmis olabilir) birincile donuyoruz - oyunu
    gorunmeyen bir ekrana acmaktansa yanlis ama **gorunur** bir ekrana
    acmak iyidir.
    """
    if not screens:
        return _fallback_monitor()
    for screen in screens:
        if screen.bounds.collidepoint(point):
            return screen
    for screen in screens:
        if screen.primary:
            return screen
    return screens[0]


def monitors() -> list[Monitor]:
    """Sistemdeki ekranlar. Windows'ta gercek yerlesim, digerinde tahmin."""
    if sys.platform == "win32":
        found = _windows_monitors()
        if found and _agrees_with_pygame(found):
            return found
    return _pygame_monitors()


def current(window_size: tuple[int, int] | None = None) -> Monitor:
    """Pencerenin **su an** uzerinde oldugu ekran.

    Pencerenin merkezine bakiyor, sol ust kosesine degil: kose iki ekran
    sinirinin bir piksel solunda kalabiliyor ve pencerenin govdesi
    komsu ekranda olmasina ragmen yanlis ekran secilir.

    **`set_mode`'dan ONCE cagrilmali.** `set_mode` pencereyi tasiyabilir;
    sonra sorunca zaten tasinmis olani ogreniriz ve tam ekran yine
    yanlis ekrana acilir.
    """
    screens = monitors()
    position = _window_position()
    if position is None:
        return pick(screens, (0, 0))
    if window_size is None:
        window_size = _window_size()
    centre = (position[0] + window_size[0] // 2,
              position[1] + window_size[1] // 2)
    return pick(screens, centre)


# --- Windows -----------------------------------------------------------------
def _windows_monitors() -> list[Monitor]:
    """`EnumDisplayMonitors` ile gercek yerlesim.

    Herhangi bir sey ters giderse bos liste donuyor ve cagiran taraf
    pygame'e donuyor: bir ekran sorgusu oyunu acilmaz yapmamali.
    """
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        class RECT(ctypes.Structure):
            _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                        ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT),
                        ("rcWork", RECT), ("dwFlags", wintypes.DWORD)]

        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
            ctypes.POINTER(RECT), wintypes.LPARAM)

        found: list[Monitor] = []

        def collect(handle, _hdc, _rect, _param) -> bool:
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if not user32.GetMonitorInfoW(handle, ctypes.byref(info)):
                return True
            found.append(Monitor(
                bounds=_rect_of(info.rcMonitor),
                work=_rect_of(info.rcWork),
                # MONITORINFOF_PRIMARY = 1
                primary=bool(info.dwFlags & 1),
            ))
            return True

        user32.EnumDisplayMonitors(None, None, callback_type(collect), 0)
        return found
    except Exception:
        # Genis yakalama bilincli: ctypes yapisi, eksik DLL, izin,
        # beklenmedik bir surum farki... hangisi olursa olsun cevap ayni
        # ve dogru olan o - pygame'e don, oyunu acilmaz yapma.
        return []


def _rect_of(rect) -> pygame.Rect:
    return pygame.Rect(rect.left, rect.top,
                       rect.right - rect.left, rect.bottom - rect.top)


def _agrees_with_pygame(found: list[Monitor]) -> bool:
    """ctypes ve pygame ayni ekrani ayni boyda mi goruyor?

    Gormezlerse aradaki fark neredeyse kesin **DPI olcekleme**: SDL
    surecin DPI farkindaligini kendi ayarliyor ve iki taraf farkli
    koordinat uzayinda konusuyor olabilir. Boyle bir durumda ctypes'in
    piksel sayilariyla pencere kurmak, pygame'in olctugu ekrana
    uymayan bir pencere uretir.

    Kontrol ucuz, kazanci buyuk: uyusmazlikta bilinen-calisan yola
    (pygame) donuyoruz.
    """
    try:
        sizes = pygame.display.get_desktop_sizes()
    except (pygame.error, AttributeError):
        return False
    if not sizes:
        return False
    for screen in found:
        if screen.primary:
            return screen.bounds.size == tuple(sizes[0])
    return found[0].bounds.size == tuple(sizes[0])


# --- pygame yedegi -----------------------------------------------------------
def _pygame_monitors() -> list[Monitor]:
    """Yalnizca boyutlardan yerlesim tahmini.

    Ekranlar soldan saga dizili ve gorev cubugu yok varsayiliyor. Ikisi
    de yanlis olabilir; ama tek monitorde (cogunluk) dogru ve coklu
    monitorde bile eskisinden kotu degil.
    """
    try:
        sizes = pygame.display.get_desktop_sizes()
    except (pygame.error, AttributeError):
        sizes = []
    if not sizes:
        return [_fallback_monitor()]

    screens: list[Monitor] = []
    x = 0
    for index, (width, height) in enumerate(sizes):
        if width <= 0 or height <= 0:
            continue
        bounds = pygame.Rect(x, 0, width, height)
        screens.append(Monitor(bounds=bounds, work=bounds.copy(),
                               primary=index == 0))
        x += width
    return screens or [_fallback_monitor()]


def _fallback_monitor() -> Monitor:
    """Hicbir sey sorulamadi. 3x pencere sigacak kadar bir ekran varsay."""
    bounds = pygame.Rect(0, 0, INTERNAL_WIDTH * 3, INTERNAL_HEIGHT * 3)
    return Monitor(bounds=bounds, work=bounds.copy(), primary=True)


# --- Pencere sorgulari -------------------------------------------------------
def _window_position() -> tuple[int, int] | None:
    try:
        return tuple(pygame.display.get_window_position())
    except (pygame.error, AttributeError, TypeError):
        return None


def _window_size() -> tuple[int, int]:
    try:
        surface = pygame.display.get_surface()
        if surface is not None:
            return surface.get_size()
    except pygame.error:
        pass
    return (INTERNAL_WIDTH, INTERNAL_HEIGHT)
