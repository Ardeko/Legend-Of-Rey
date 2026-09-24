"""Silah profilleri - yumruk/hancer/balta/kilic ayni zincir motorunu kullanir.

Arda'nin karari (22.08.2026): Rey artik tamamen silahsiz baslamiyor,
**yumrukla** basliyor - kilici Bolum 1'de buluyor. `ChainState`
(`combat/combo.py`) hangi tabloyu okuyacagini bilmiyordu, hep modul
seviyesi `CHAIN` sabitine bakiyordu; artik `Player.equip()` hangi silahi
kusandiysa onun tablosunu veriyor.

## Karaktere ozel ve ortak silahlar (23.09.2026)

Arda: *"karakterlere ozel bir silah mi tasarlariz veya hancer veya
baltanin yanina ilerde acilacak yeni bir silah mi ekleriz"* - ikisi de:

    Fisilti      yalnizca Rey   B10  bitirici ses dalgasi (mermi)
    Iz Mizragi   yalnizca Ardo  B10  uzun, dar; bitirici one atilma
    Zincir Orak  ikisi de       B14  dort vurus; bitirici iki yana

Silah artik yalnizca bir zincir tablosu degil: menzil, bitirici etkisi
ve iz rengi de silahin. Sayilar `config.py`de (sihirli sayi yok).
Karaktere ozel silah `owner` tasiyor; oteki karakter onu hic gormuyor
(`usable_by`).

## Sprite

Her silahin kendi sekli var (`animation.py`: `rey_whisper`,
`ardo_spear`, `rey_sickle`, `ardo_sickle`). Ayni iskelet, yalnizca silah
degisiyor - tutarlilik bedava (CLAUDE.md 6).
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import (AXE_CHAIN, CHAIN, ChainHit, DAGGER_CHAIN, FIST_CHAIN,
                        SICKLE_CHAIN, SICKLE_REACH_BONUS, SPEAR_CHAIN,
                        SPEAR_HEIGHT_TRIM, SPEAR_REACH_BONUS, WHISPER_CHAIN)

FISTS = "fists"
SWORD = "sword"
DAGGER = "dagger"
AXE = "axe"
WHISPER = "whisper"
SPEAR = "spear"
SICKLE = "sickle"

# Bitirici etkileri (`Player._finisher_effect`).
FINISHER_WAVE = "wave"
FINISHER_LUNGE = "lunge"
FINISHER_SWEEP = "sweep"


@dataclass(frozen=True)
class Weapon:
    key: str
    label_key: str          # Dil anahtari - hazir metin degil
    chain: tuple[ChainHit, ...]
    # "" ise cizim taban (silahsiz) sprite'ini kullanir - yumrugun kendi
    # sprite'i zaten "silahsiz Rey" oldugu icin ek varyant gerekmiyor.
    sprite_suffix: str = "_armed"
    # Vurus kutusuna eklenen menzil / cikarilan yukseklik (piksel).
    reach_bonus: int = 0
    height_trim: int = 0
    # Bitiricinin ek etkisi: "" | wave | lunge | sweep.
    finisher: str = ""
    # "" herkes; "rey"/"ardo" yalnizca o karakter.
    owner: str = ""
    # Savurma izinin golge zinciri (`src/art/trail.py`).
    trail_chain: str = "bone_pale"


WEAPONS: dict[str, Weapon] = {
    FISTS: Weapon(FISTS, "weapon.fists", FIST_CHAIN, sprite_suffix=""),
    SWORD: Weapon(SWORD, "weapon.sword", CHAIN, sprite_suffix="_armed"),
    # Kendi silah sekilleri var (`animation.py`: `rey_dagger`/`rey_axe`,
    # `ardo_dagger`/`ardo_axe`). Bir ara ikisi de "_armed" ile kilica
    # benziyordu; secim bir KARAR ekrani oldugu icin secilen seyin elde
    # gorunmemesi kabul edilemezdi.
    DAGGER: Weapon(DAGGER, "weapon.dagger", DAGGER_CHAIN, sprite_suffix="_dagger"),
    AXE: Weapon(AXE, "weapon.axe", AXE_CHAIN, sprite_suffix="_axe"),
    WHISPER: Weapon(WHISPER, "weapon.whisper", WHISPER_CHAIN,
                    sprite_suffix="_whisper", finisher=FINISHER_WAVE,
                    owner="rey", trail_chain="arcane"),
    SPEAR: Weapon(SPEAR, "weapon.spear", SPEAR_CHAIN, sprite_suffix="_spear",
                  reach_bonus=SPEAR_REACH_BONUS, height_trim=SPEAR_HEIGHT_TRIM,
                  finisher=FINISHER_LUNGE, owner="ardo"),
    SICKLE: Weapon(SICKLE, "weapon.sickle", SICKLE_CHAIN,
                   sprite_suffix="_sickle", reach_bonus=SICKLE_REACH_BONUS,
                   finisher=FINISHER_SWEEP, trail_chain="steel"),
}

# B10'da karakterin kendi silahi.
PERSONAL: dict[str, str] = {"rey": WHISPER, "ardo": SPEAR}


def get(key: str) -> Weapon:
    return WEAPONS.get(key, WEAPONS[FISTS])


def usable_by(key: str, character: str) -> bool:
    """Bu karakter bu silahi kusanabilir mi? (Karaktere ozel silahlar.)"""
    weapon = WEAPONS.get(key)
    if weapon is None:
        return False
    return not weapon.owner or weapon.owner == character


def starting_weapon(character: str) -> str:
    """Ikisi de yumrukla baslar; kilici Bolum 1'de Jet verir."""
    return FISTS
