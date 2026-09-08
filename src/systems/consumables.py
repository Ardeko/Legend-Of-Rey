"""Sarf malzemeleri - ok ve bomba. **Uzaktan dovus.**

Arda, 08.09.2026: *"mesale satan ... tek kullanimlik bomba ve ok gibi
seyler de eklesin, karakterlere yeni bir uzaktan dovus mekanigi
eklenmis olsun."*

## Neden tek tus, secili malzeme

`Action` listesi doluydu: standart bir kolun sekiz dugmesi de
kullaniliyor ve ayarlardaki tus sekmesi 14/14 idi. Iki ayri tus
(ok icin bir, bomba icin bir) oradan bir seyi cikarmak demekti.

Tek tus (`Action.THROW`) elindeki **secili** malzemeyi firlatiyor;
secim envanter ekranindan degisiyor. Ayrica tasarim olarak da dogru:
oyuncu "hangisini atacagim" kararini dovusun ORTASINDA degil, oncesinde
veriyor - bir dovus icinde iki farkli mermi arasinda gecis yapmak
zaten bu oyunun temposunda degil.

## Ikisi ayni sey degil

    OK      hizli, duz ucar, TEK hedef, ucuz
    BOMBA   yay cizer, yerde patlar, ALAN hasari, pahali

Ok bir kilicin uzaktan kopyasi olmamali; olcusu su: tek hedefte ok
kilictan zayif (12 < 47 zincir toplami), ama **ulasilamayan** yeri
vuruyor. Bomba ise kalabalikta kiliçtan iyi - yani ikisi de kilicin
yerine gecmiyor, kilicin yapamadigi seyi yapiyor.

Bomba `docs/derinlestirme.md` 1.2 ile de tutarli: patlama **radyal**,
yonlu degil.

## Sayilar kayitta, `flags`ta degil

`SaveData.consumables` ayri bir alan. `flags` bir "olan/olmayan"
sozlugu; sayilar orada tutulsa her okuma bir tip donusumu olurdu ve
eksi degerler sessizce girebilirdi.
"""
from __future__ import annotations

from dataclasses import dataclass

ARROW = "arrow"
BOMB = "bomb"

# Envanterde ve secim dongusunde bu sirayla gorunuyor.
ORDER: tuple[str, ...] = (ARROW, BOMB)

# Bir seferde tasinabilecek en fazla adet. Sinirsiz olsaydi altin
# biriktiren oyuncu bolumu uzaktan temizlerdi ve dovus sistemi
# anlamsizlasirdi.
MAX_CARRY = 9

SELECTED_KEY = "consumable_selected"


@dataclass(frozen=True)
class Consumable:
    """Tek bir sarf malzemesi.

    `label_key` dil anahtari tutar, hazir metin degil.
    """

    key: str
    label_key: str
    desc_key: str
    cost: int                   # Mum Bekcisi'ndeki fiyati (tek adet)
    damage: int
    speed: float                # piksel / kare, yatay
    lift: float = 0.0           # baslangic dikey hizi (eksi = yukari)
    gravity: float = 0.0        # 0 = duz ucar
    life: int = 90              # kare
    blast: int = 0              # 0 = tek hedef, >0 = patlama yaricapi
    blast_damage: int = 0


CONSUMABLES: dict[str, Consumable] = {
    # Ok: hizli, duz, tek hedef. Kilictan ZAYIF ama uzagi vuruyor.
    ARROW: Consumable(
        key=ARROW, label_key="item.arrow", desc_key="item.arrow_desc",
        cost=6, damage=12, speed=6.2, life=80,
    ),
    # Bomba: yay cizer, yerde patlar, ALAN hasari. Pahali ve az tasiniyor.
    BOMB: Consumable(
        key=BOMB, label_key="item.bomb", desc_key="item.bomb_desc",
        cost=18, damage=0,          # carpma hasari YOK - patlama vuruyor
        speed=3.4, lift=-3.2, gravity=0.22, life=110,
        blast=46, blast_damage=26,
    ),
}


def get(key: str) -> Consumable | None:
    return CONSUMABLES.get(key)


# --- Sayim -------------------------------------------------------------------
def _bag(save_data) -> dict:
    if save_data is None:
        return {}
    bag = getattr(save_data, "consumables", None)
    if not isinstance(bag, dict):
        bag = {}
        save_data.consumables = bag
    return bag


def count(save_data, key: str) -> int:
    try:
        return max(0, int(_bag(save_data).get(key, 0)))
    except (TypeError, ValueError):
        return 0


def add(save_data, key: str, amount: int = 1) -> int:
    """Cantaya ekler, `MAX_CARRY`i asmaz. Yeni adedi doner."""
    if save_data is None or key not in CONSUMABLES:
        return 0
    bag = _bag(save_data)
    total = min(MAX_CARRY, count(save_data, key) + max(0, amount))
    bag[key] = total
    return total


def spend(save_data, key: str) -> bool:
    """Bir adet harcar. Yoksa hicbir sey yapmaz ve `False` doner."""
    if count(save_data, key) <= 0:
        return False
    _bag(save_data)[key] = count(save_data, key) - 1
    return True


def carried(save_data) -> list[str]:
    """Elde en az bir adet olan malzemeler - **ORDER sirasinda**."""
    return [key for key in ORDER if count(save_data, key) > 0]


# --- Secim -------------------------------------------------------------------
def selected(save_data) -> str:
    """Su an secili malzeme.

    Secili olan bitmisse elde olan ilkine **kendiliginden** geciyor:
    oyuncu bos bir yuvaya basip "tus calismiyor" sanmasin.
    """
    if save_data is None:
        return ""
    chosen = save_data.flags.get(SELECTED_KEY, "")
    if chosen in CONSUMABLES and count(save_data, chosen) > 0:
        return chosen
    have = carried(save_data)
    return have[0] if have else ""


def select(save_data, key: str) -> bool:
    if save_data is None or key not in CONSUMABLES:
        return False
    save_data.flags[SELECTED_KEY] = key
    return True


def select_next(save_data) -> str:
    """Elde olanlar arasinda sirayla gecer. Bos ise hicbir sey yapmaz."""
    have = carried(save_data)
    if not have:
        return ""
    current = selected(save_data)
    index = have.index(current) + 1 if current in have else 0
    chosen = have[index % len(have)]
    select(save_data, chosen)
    return chosen
