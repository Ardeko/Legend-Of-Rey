"""Ses efekti icerigi: KORKU KATMANI (`docs/korku.md`).

Bkz. `sfx.py` docstring'i - genel aciklama orada. Butun sesler
`synth.py` ile uretiliyor; bu projede ses kaydi yok.

## Nefes en onemli ses

`docs/korku.md` 5.1 nefesi "en ucuz kazanc" diye isaretliyor ve
kaynakta tek satiri yoktu. Nefes sesi bir efekt degil, oyuncunun
karakterle **ayni bedende** oldugunu hatirlatan sey. O yuzden yuksek
degil: menzili kisa, bandi dar, sadece sessizlikte duyuluyor.

Iki ayri ses: **almak** ve **vermek**. Tek ses dongude calinsaydi
mekanik bir tekrar olurdu; ikisi arasindaki asimetri (alis kisa ve
keskin, verisi uzun ve dagilan) onu canliya benzetiyor.

## Jumpscare sesi bir cigik DEGIL

`docs/korku.md` 9 acikca yasakliyor. Sok sesi cok kisa, cok alcak ve
**ani duran** bir ses: nefes almanin tersi. Kurulum sesin gelmesi degil,
ondan onceki 44 karede hicbir seyin gelmemesi.

## Genlik kisitli

Bu dosyadaki hicbir ses `normalize(peak=...)` ile 0.55'in uzerine
cikmiyor - jumpscare dahil. `systems/horror.py` "azaltilmis" seviyede
ayrica 0.35 ile carpiyor. Ani ses bir tasarim araci; kulaga zarar
verme araci degil.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from src.audio import synth

SFX: dict[str, Callable[[], np.ndarray]] = {}


def _register(name: str) -> Callable:
    def wrap(fn: Callable[[], np.ndarray]) -> Callable[[], np.ndarray]:
        SFX[name] = fn
        return fn
    return wrap


# --- Nefes ------------------------------------------------------------------
# Nefes filtrelenmis gurultu: 700 Hz alcak-geciren bant, gogus boslugunu
# taklit ediyor. Daha yuksek kesim "tislama", daha alcak "ugultu" oluyor.
BREATH_CUTOFF = 700.0


@_register("breath_in")
def _breath_in() -> np.ndarray:
    """Nefes almak - kisa ve keskin. Zarf yavas acilip hizli kapaniyor."""
    seconds = 0.42
    n = synth.samples(seconds)
    body = synth.lowpass(synth.noise(seconds, seed=1471), BREATH_CUTOFF)
    return synth.normalize(body * synth.env_ad(n, attack=0.62, decay=0.38),
                           peak=0.22)


@_register("breath_out")
def _breath_out() -> np.ndarray:
    """Nefes vermek - uzun ve dagilan. Alistan **belirgin farkli** olmali;
    ayni ses iki kez calinsa mekanik bir tekrar gibi duyulurdu."""
    seconds = 0.58
    n = synth.samples(seconds)
    body = synth.lowpass(synth.noise(seconds, seed=907), BREATH_CUTOFF * 0.75)
    return synth.normalize(body * synth.env_ad(n, attack=0.16, decay=0.84),
                           peak=0.18)


@_register("breath_sharp")
def _breath_sharp() -> np.ndarray:
    """Irkilme - ani ve kesik nefes alis. Jumpscare aninda Rey'in tepkisi.

    Oyuncu bunu **kendi** tepkisi gibi duyuyor: ekranda olan sey ile
    kulaktaki ses ayni anda geliyor.
    """
    seconds = 0.20
    n = synth.samples(seconds)
    body = synth.lowpass(synth.noise(seconds, seed=333), 1100.0)
    return synth.normalize(body * synth.env_ad(n, attack=0.10, decay=0.90),
                           peak=0.34)


@_register("heartbeat")
def _heartbeat() -> np.ndarray:
    """Iki vurus - "lub-dub". Tek vurus kalp gibi duyulmuyor, davul gibi.

    Ikinci vurus birinciden alcak ve kisa: gercek kalpte de oyle.
    """
    first = synth.thump(0.16, freq_start=78.0, freq_end=44.0)
    gap = np.zeros(synth.samples(0.11))
    second = synth.thump(0.13, freq_start=64.0, freq_end=38.0) * 0.72
    tail = np.zeros(synth.samples(0.30))
    return synth.normalize(np.concatenate([first, gap, second, tail]),
                           peak=0.30)


# --- Yanki'nin yalani -------------------------------------------------------
@_register("lie_caught")
def _lie_caught() -> np.ndarray:
    """Yalan yakalandi. Yanki'nin **susmadan onceki** son sesi.

    Bir uyari sesi degil: alcalan, kendi icine cekilen bir ton. Oyuncuya
    "dikkat" demiyor, "bir sey geri cekildi" diyor. Ardindan gelen uc
    saniyelik sessizlik asil mesaj (`docs/korku.md` 4.1).
    """
    seconds = 0.7
    n = synth.samples(seconds)
    body = synth.mix(
        synth.sweep(330.0, 96.0, seconds),
        synth.sweep(221.0, 64.0, seconds) * 0.6,
    )
    return synth.normalize(synth.lowpass(body, 1400.0)
                           * synth.env_ad(n, attack=0.06, decay=0.94),
                           peak=0.30)


@_register("phantom_fade")
def _phantom_fade() -> np.ndarray:
    """Yanki Gorusu'nun gosterdigi sey yokmus - parilti sonuyor.

    Cok sonuk, neredeyse duyulmuyor. Amac oyuncunun "duydum mu?"
    demesi; kesin bir sinyal verirse mekanigi ele verir.
    """
    seconds = 0.34
    n = synth.samples(seconds)
    body = synth.chorus((494.0, 622.0), seconds, spread=0.03)
    return synth.normalize(body * synth.env_exp_decay(n, rate=9.0), peak=0.12)


# --- Izleyen ----------------------------------------------------------------
@_register("watcher_notice")
def _watcher_notice() -> np.ndarray:
    """Izleyen fark edildi. Alcak, uzun, neredeyse altyapi sesi.

    Bir tehdit sesi degil - Izleyen saldirmiyor. Odanin dokusu
    degismis gibi duyuluyor.
    """
    seconds = 1.1
    n = synth.samples(seconds)
    body = synth.mix(
        synth.sine(58.0, seconds),
        synth.sine(87.0, seconds) * 0.45,
        synth.lowpass(synth.noise(seconds, seed=2201), 240.0) * 0.5,
    )
    return synth.normalize(body * synth.env_linear_fade(n, 0.30, 0.45),
                           peak=0.20)


@_register("watcher_strike")
def _watcher_strike() -> np.ndarray:
    """JUMPSCARE (`docs/korku.md` 6.1). **Cigik degil.**

    Uc parca: sifirdan aniden acilan alcak bir gurultu patlamasi, ustune
    kisa bir yuksek bilesen, ve **ani kesme**. Ani kesme sesin kendisi
    kadar onemli: uzayan bir ses "tehlike suruyor" der, kesilen ses
    "oldu bitti" der - ve oyuncu bosluga bakakalir.

    Toplam 0.30 saniye. Genlik tavani 0.55 (dosya basligi).
    """
    seconds = 0.30
    n = synth.samples(seconds)
    low = synth.sweep(150.0, 41.0, seconds)
    grit = synth.lowpass(synth.noise(seconds, seed=6661), 1900.0) * 0.85
    body = synth.mix(low, grit)
    # Zarf: 3 karelik acilis, sonra duz, sonra ANI kesme (son %12).
    envelope = np.ones(n)
    rise = max(1, int(n * 0.04))
    envelope[:rise] = np.linspace(0.0, 1.0, rise)
    cut = int(n * 0.88)
    envelope[cut:] = np.linspace(1.0, 0.0, n - cut) ** 3
    return synth.normalize(body * envelope, peak=0.55)


# --- Zindan hatirliyor ------------------------------------------------------
@_register("ghost_seen")
def _ghost_seen() -> np.ndarray:
    """Kendi hayaletini gordun. Yanki'nin tonunda ama **tek** ses -
    hayalet konusmuyor, sadece bakiyor."""
    seconds = 0.9
    n = synth.samples(seconds)
    body = synth.chorus((165.0, 247.0), seconds, spread=0.015)
    return synth.normalize(synth.lowpass(body, 800.0)
                           * synth.env_linear_fade(n, 0.25, 0.55), peak=0.16)


@_register("room_changed")
def _room_changed() -> np.ndarray:
    """Temizlenmis odada bir sey degismis. Neredeyse duyulmayan bir tik.

    Fark eden oyuncu urperiyor, fark etmeyen hicbir sey kaybetmiyor -
    ses de aynen oyle davranmali (`docs/korku.md` 5.5).
    """
    seconds = 0.18
    n = synth.samples(seconds)
    body = synth.lowpass(synth.noise(seconds, seed=88), 520.0)
    return synth.normalize(body * synth.env_exp_decay(n, rate=14.0), peak=0.10)
