"""Korku katmani kapisi - hangi korku ogesi calisir, hangisi calismaz.

`docs/korku.md` uc katman tanimliyor ve **yalnizca ikisi kapatilabilir**:

    Katman 1  psikolojik omurga   HIKAYENIN KENDISI - asla kapanmaz
    Katman 2  atmosferik dolgu    kapatilabilir
    Katman 3  sok                 kapatilabilir / yumusatilabilir

Katman 1'in kapanmamasi bir eksiklik degil, karar: Yanki'nin yalan
soylemesi bir korku *efekti* degil, oyunun ana mekanigi. Kapatilsaydi
B10, B14 ve B18 anlamsizlasirdi.

## Neden tek yerde toplandi

Kapi dagitilsaydi on sekiz bolume yayilirdi ve biri mutlaka unutulurdu:
"korku kapali" diyen oyuncu on yedi bolumde rahat, birinde irkilirdi.
`CLAUDE.md` 10 erisilebilirligi bastan sart kosuyor; sonradan eklenen
bir kapi hicbir zaman tam kapanmiyor.

## Fotosensitivite ayri bir ayar, korku ayarinin parcasi degil

Ikisini birlestirmek soyle bir tuzak kurardi: korkuyu seven ama
fotosensitif epilepsisi olan oyuncu, guvende olmak icin butun katmani
kapatmak zorunda kalirdi. `flash_limit` bagimsiz: korku tam acikken
bile parlamalar sinirlanabiliyor.

**Bu bir oneri degil sorumluluk.** Tasarim zaten saniyede 3'ten fazla
parlama uretmiyor (`docs/korku.md` 8); bu ayar ikinci emniyet.
"""
from __future__ import annotations

FULL = "full"
REDUCED = "reduced"
OFF = "off"

LEVELS: tuple[str, ...] = (FULL, REDUCED, OFF)

# Ani sesin en yuksek genligi - `REDUCED` seviyesinde uygulanir.
# Sok anlari kalir, kulaga vuran kisim gider.
REDUCED_LOUDNESS = 0.35


def level(settings) -> str:
    """Ayarlardaki korku seviyesi. Ayar yoksa tam.

    `settings` `None` olabiliyor: bazi test sahneleri ve arac betikleri
    ayarsiz sahne kuruyor. Varsayilan **tam korku** - eksik ayar
    yuzunden bir korku ogesinin sessizce kaybolmasi, fazladan
    calismasindan daha kotu (bulmasi cok daha zor).
    """
    if settings is None:
        return FULL
    value = settings.get("horror", FULL)
    return value if value in LEVELS else FULL


def atmosphere(settings) -> bool:
    """Katman 2 calisiyor mu? (nefes, Izleyen, hayalet, zindan degisimi)"""
    return level(settings) != OFF


def shock(settings) -> bool:
    """Katman 3 calisiyor mu? (bes sok ani ve jumpscare)"""
    return level(settings) != OFF


def loud(settings) -> bool:
    """Ani/sert ses calinabilir mi?

    `REDUCED` seviyesinin tanimi tam olarak bu: **sok anlari kalir, ani
    ses gider.** Gorsel korku yerinde durur, kulaga vuran kisim
    yumusar - ses hassasiyeti olan oyuncu oyunun tonunu kaybetmiyor.
    """
    return level(settings) == FULL


def loudness(settings) -> float:
    """Sok sesinin genlik carpani. `REDUCED`'da kisilir, `OFF`'ta sifir."""
    current = level(settings)
    if current == FULL:
        return 1.0
    if current == REDUCED:
        return REDUCED_LOUDNESS
    return 0.0


def flash_allowed(settings) -> bool:
    """Ani parlama cizilebilir mi? (fotosensitivite)

    Parlama **atlanir**, olay atlanmaz: `flash_limit` acikken jumpscare
    yine olur, Izleyen yine belirir - yalnizca beyaz kare cizilmez.
    Erisilebilirlik ayari icerigi kaldirmaz, sunumu degistirir.
    """
    if settings is None:
        return True
    return not bool(settings.get("flash_limit", False))
