"""Kayit sistemi - **her zaman iki dosya.**

`save.json` yazilirken oyun cokerse dosya yarim kalir ve oyuncunun saatlerce
ilerlemesi gider. Bu affedilmez (docs/menu-ui.md 11). Bu yuzden:

  1. Once `save.tmp` yazilir
  2. Mevcut `save.json` varsa `save.bak.json`'a kopyalanir
  3. `save.tmp` atomik olarak `save.json` uzerine tasinir

Yukleme once `save.json`'u dener; bozuksa sessizce `save.bak.json`'a duser.
Iki dosya da bozuksa yeni oyun baslar - ama kullaniciya soylenir.

Kayit dizini oyun klasoru degil, kullanicinin veri klasorudur: PyInstaller
ile paketlendiginde oyun klasoru salt okunur olabilir.

## Iki slot - ve neden her cagirana slot parametresi GECMEDIK

09.09.2026'da iki kayit yuvasi eklendi. Dosya adina indis giriyor:

    save1.json  save1.bak.json      save2.json  save2.bak.json

**Dizin degismiyor.** `LORE_SAVE_DIR` 48 test paketinin izolasyonunu
tasiyor (§0.6'daki en pahali hata); slotu dizine tasimak o izolasyonu
ikinci bir degiskene baglardi.

`read_save()` / `write_save()` / `has_save()` imzalari **degismedi**.
Aktif slot modul duzeyinde tutuluyor ve menu onu seciyor. Alternatifi -
her cagirana bir `slot` parametresi eklemek - kirk kusur cagri yeri
demekti, ve "her yeni cagri bir satir eklesin" bu projede bir hatanin
sekli (`summon_kalachev`in yara bayragi, `.spec`in portre listesi).
Biri unutulur, oyun sessizce yanlis slota yazar.

## Eski tek dosya kaybolmuyor

`save.json` (slotsuz surum) varsa ilk erisimde `save1.json`e tasiniyor
(`migrate_legacy`). Arda'nin gercek ilerlemesi orada; bir surum
degisikliginin onu silmesi affedilmez olurdu.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.config import ECHO_TIER_CLEAR

SAVE_VERSION = 1

# Slotsuz eski surumun adlari. **Yalnizca goc icin** duruyorlar.
LEGACY_SAVE_NAME = "save.json"
LEGACY_BACKUP_NAME = "save.bak.json"

# Iki slot: Arda onayladi. Ucuncusu menuye satir ekler, oyuna bir sey
# katmaz - iki karakter var, iki yuva onun karsiligi.
SLOT_COUNT = 2

SETTINGS_NAME = "settings.json"
APP_FOLDER = "LegendOfRey"


# Kayit dizinini disaridan ezme yolu. **Testler icin var.**
#
# 08.09.2026: test paketi oyuncunun GERCEK kaydini eziyordu. Sahneler
# `read_save()` ile kaydi yukluyor, `_sync_abilities()` gibi yerler
# `write_save()` ile geri yaziyor - yani `python tests/test_chapter01.py`
# calistirmak Arda'nin ilerlemesini siliyordu (55 altin ve secilmis
# balta boyle kayboldu, yedek dosyasi da ustune yazildigi icin
# kurtarilamadi).
#
# Testin oyuncunun verisine dokunmasi bir ayrinti degil, bir veri kaybi
# hatasi. Ortam degiskeni her testin basinda gecici bir klasore
# ayarlaniyor (`tests/*.py`).
SAVE_DIR_ENV = "LORE_SAVE_DIR"


def user_data_dir() -> Path:
    """Yazilabilir kullanici veri dizini."""
    override = os.environ.get(SAVE_DIR_ENV)
    if override:
        path = Path(override) / APP_FOLDER
        path.mkdir(parents=True, exist_ok=True)
        return path
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA",
                                   Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME",
                                   Path.home() / ".local" / "share"))
    path = base / APP_FOLDER
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class SaveData:
    """Bir oyun kaydinin tam icerigi."""

    version: int = SAVE_VERSION
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Ilerleme
    chapter: int = 1
    # Bolum adi dil anahtari tutar - kayit dosyasi dilden bagimsiz olmali.
    # Turkce kaydi acan Ingilizce oyuncu "Village" gormeli, "Koy" degil.
    chapter_name: str = "chapter.village"
    checkpoint: str = ""
    playtime_frames: int = 0

    # Karakter
    character: str = "rey"           # rey | ardo
    # Kazanilan yetenekler. **Liste**, bit maskesi degil: yeni yetenek
    # eklemek kayit surumunu degistirmiyor, eski kayitlar sadece ona sahip
    # olmuyor (src/systems/abilities.py).
    abilities: list[str] = field(default_factory=list)
    max_health: int = 80
    health: int = 80

    # Ekonomi ve Yanki
    gold: int = 0
    echo_tier: int = ECHO_TIER_CLEAR

    # Kesif
    secrets_found: int = 0
    secrets_total: int = 0
    chapters_cleared: list[str] = field(default_factory=list)

    # Ekipman ve kilitler
    weapon: str = "sword"
    # **Sahip olunan** silahlar. `weapon` yalnizca KUSANILANI tutuyordu ve
    # Bolum 2'de Hancer/Balta secildikten sonra oyuncu bir daha kilica
    # donemiyordu - duraklatma menusundeki EKIPMAN "Bolum 2'de acilir"
    # diye soz veriyor ama ekran yoktu (Arda, 29.08.2026: *"balta'm veya
    # hancerime gecemedim"*).
    #
    # `abilities`/`skills` ile ayni gerekceyle **liste**: yeni silah
    # eklemek kayit surumunu degistirmiyor, eski kayitlar sadece ona
    # sahip olmuyor. Bos birakilirsa `equipment.owned()` kayittan makul
    # bir varsayilan turetiyor (eski kayitlar bozulmasin).
    owned_weapons: list[str] = field(default_factory=list)
    armor: str = "light"
    charms: list[str] = field(default_factory=list)
    # Sarf malzemeleri: {"arrow": 3, "bomb": 1}. `flags`ta DEGIL - orasi
    # bir "olan/olmayan" sozlugu ve sayilar orada tutulsa her okuma bir
    # tip donusumu olurdu (`src/systems/consumables.py`).
    consumables: dict[str, int] = field(default_factory=dict)

    # Yetenek agaci (src/systems/skilltree.py). Yeteneklerle **ayni**
    # gerekceyle liste: yeni dugum eklemek kayit surumunu degistirmiyor,
    # eski kayitlar sadece o dugume sahip olmuyor. Bit maskesi olsaydi
    # agaci yeniden siralamak eski kayitlarin yeteneklerini kaydirirdi.
    #
    # `skill_points` **kalan** havuz, kazanilan toplam degil: harcanan puan
    # zaten `skills` listesinden okunabiliyor (`skilltree.spent_points`) ve
    # ayni bilgiyi iki yerde tutmak ikisinin ayrismasi demek.
    #
    # Ikisi de varsayilanli, `from_dict` eksik alani doldurmuyor -> bu
    # alanlari hic bilmeyen ESKI KAYITLAR sorunsuz aciliyor, sifir puanla.
    # Bu yuzden SAVE_VERSION artmadi.
    skill_points: int = 0
    skills: list[str] = field(default_factory=list)

    # Bolum 3'un karari - B14'un twist sahnesini etkileyecek
    purple_flame_taken: bool = False

    # Istatistik
    deaths: int = 0
    best_combo: int = 0
    flags: dict[str, Any] = field(default_factory=dict)

    # --- Turetilmis ---------------------------------------------------------
    @property
    def playtime_text(self) -> str:
        """Menu kartinda gosterilecek sure: '3sa 12dk' / '3h 12m'."""
        from src.ui.i18n import t          # gec import: dongusel bagimlilik yok
        total_minutes = self.playtime_frames // (60 * 60)
        hours, minutes = divmod(total_minutes, 60)
        if hours:
            return t("save.playtime_hm", hours=hours, minutes=minutes)
        return t("save.playtime_m", minutes=minutes)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SaveData":
        known = set(cls.__dataclass_fields__)
        # Bilinmeyen alanlari yok say: eski surumden gelen kayit oyunu kirmaz.
        return cls(**{k: v for k, v in raw.items() if k in known})


# --- Slotlar ----------------------------------------------------------------
# Aktif slot **modul duzeyinde**. Menu seciyor, geri kalan her sey
# imzasini degistirmeden calisiyor (gerekce modul basliginda).
_active_slot = 1


def clamp_slot(slot: int) -> int:
    """1..SLOT_COUNT araligina kirpar. Bozuk bir indis oyunu durdurmaz."""
    return max(1, min(SLOT_COUNT, int(slot)))


def active_slot() -> int:
    return _active_slot


def set_active_slot(slot: int) -> None:
    """Hangi yuvaya yazilacagini secer. Menu ve slot ekrani cagirir."""
    global _active_slot
    _active_slot = clamp_slot(slot)


# --- Dosya islemleri --------------------------------------------------------
def save_path(slot: int | None = None) -> Path:
    return user_data_dir() / f"save{clamp_slot(slot or _active_slot)}.json"


def backup_path(slot: int | None = None) -> Path:
    return (user_data_dir()
            / f"save{clamp_slot(slot or _active_slot)}.bak.json")


def _temp_path(slot: int) -> Path:
    """Slot basina ayri gecici dosya.

    Tek bir `save.tmp` de yeterdi (ayni anda tek slot aktif), ama iki
    slot ayni gecici adi paylassaydi bir gun biri otekinin yarim
    yazilmis dosyasini gorurdu. Ayirmanin maliyeti sifir.
    """
    return user_data_dir() / f"save{clamp_slot(slot)}.tmp"


def migrate_legacy() -> bool:
    """Slotsuz `save.json`'u 1. yuvaya tasir. Bir kez, sessizce.

    Arda'nin gercek ilerlemesi o dosyada. Slot surumune gecerken onu
    gormezden gelmek, oyuncunun saatlerini silmek olurdu.

    Yalnizca 1. yuva **bosken** calisiyor: yeni bir kayit varsa eski
    dosya artik bir kalinti ve onun uzerine yazmak veri kaybi olur.
    """
    directory = user_data_dir()
    legacy = directory / LEGACY_SAVE_NAME
    if not legacy.is_file() or save_path(1).is_file():
        return False
    try:
        shutil.move(str(legacy), str(save_path(1)))
        legacy_backup = directory / LEGACY_BACKUP_NAME
        if legacy_backup.is_file() and not backup_path(1).is_file():
            shutil.move(str(legacy_backup), str(backup_path(1)))
    except OSError as exc:
        print(f"[save] eski kayit tasinamadi: {exc}")
        return False
    print("[save] eski kayit 1. yuvaya tasindi")
    return True


def has_save(slot: int | None = None) -> bool:
    """Bu yuvada kayit var mi? Yedegi de sayariz."""
    return save_path(slot).is_file() or backup_path(slot).is_file()


def any_save() -> bool:
    """Herhangi bir yuvada kayit var mi - DEVAM ET bunu soruyor."""
    return any(has_save(i) for i in range(1, SLOT_COUNT + 1))


def used_slots() -> list[int]:
    return [i for i in range(1, SLOT_COUNT + 1) if has_save(i)]


def peek_slot(slot: int) -> "SaveData | None":
    """Bir yuvanin ozeti - **aktif slotu degistirmeden.**

    Slot ekrani iki karti da ayni anda gostermek zorunda; bunun icin
    aktif slotu ileri geri oynatmak, bir istisna aninda oyunu yanlis
    yuvaya bagli birakirdi.
    """
    data = _read(save_path(slot))
    return data if data is not None else _read(backup_path(slot))


def latest_slot() -> int | None:
    """En son oynanan yuva. DEVAM ET dogrudan buraya giriyor."""
    best, newest = None, -1.0
    for index in range(1, SLOT_COUNT + 1):
        data = peek_slot(index)
        if data is not None and data.updated_at > newest:
            best, newest = index, data.updated_at
    return best


def write_save(data: SaveData) -> bool:
    """Kaydi guvenle yazar. Basarisizsa mevcut kayit bozulmaz."""
    data.updated_at = time.time()
    slot = clamp_slot(_active_slot)
    temp = _temp_path(slot)
    target = save_path(slot)
    backup = backup_path(slot)

    try:
        temp.write_text(
            json.dumps(data.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8")
        # Yeni kayit diske yazildiktan SONRA eskisini yedekle - once
        # yedekleyip sonra yazmak, yazma coktuğunde iki bozuk dosya birakir.
        if target.is_file():
            shutil.copy2(target, backup)
        temp.replace(target)         # Atomik
        return True
    except OSError as exc:
        print(f"[save] kaydedilemedi: {exc}")
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def _read(path: Path) -> SaveData | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        return SaveData.from_dict(raw)
    except TypeError:
        return None


def read_save(slot: int | None = None) -> tuple[SaveData | None, str]:
    """Kaydi okur. (veri, durum) doner.

    durum: "ok" | "backup" | "none" - arayuz yedekten donuldugunu
    oyuncuya soyleyebilsin diye.
    """
    migrate_legacy()
    data = _read(save_path(slot))
    if data is not None:
        return data, "ok"
    data = _read(backup_path(slot))
    if data is not None:
        print("[save] ana kayit okunamadi, yedekten donuldu")
        return data, "backup"
    return None, "none"


def delete_save(slot: int | None = None) -> None:
    for path in (save_path(slot), backup_path(slot)):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            print(f"[save] silinemedi {path.name}: {exc}")
