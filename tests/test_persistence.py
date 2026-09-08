"""Ilerleme gercekten DISKE yaziliyor mu?

Arda, 08.09.2026: *"menuye dondugumde save sistemi duzgun
calismiyor"* ve *"hancer balta falan hafizada kalmiyor"*.

Ikisi **ayni hataydi**. `write_save` yalnizca uc yerde cagriliyordu:

    character_select.py   yeni oyun
    death.py              olum
    pause.py              duraklat -> ANA MENU

Yani bir bolumu bitiren oyuncunun ilerlemesi, silah secimi ve ekipman
degisikligi **yalnizca bellekte** kaliyordu. Oyunu kapatinca ya da
duraklat menusunu kullanmadan menuye donunce hepsi yok oluyordu.

Bellekte dogru gorunen bir sey diskte yanlis olabilir ve bu, elle
oynayarak **fark edilmesi en zor** hata sinifi: oyun oturum boyunca
dogru davraniyor.

Bu paket her karar noktasindan sonra **dosyayi tekrar okuyup**
bakiyor - bellege degil.

Calistir:
    python tests/test_persistence.py
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA.** (08.09.2026)
#
# Sahneler `read_save()` ile kaydi yukluyor ve `_sync_abilities()` gibi
# yerler `write_save()` ile geri yaziyor - yani bu paketi calistirmak
# Arda'nin gercek ilerlemesini siliyordu. 55 altin ve secilmis balta
# boyle kayboldu; yedek dosyasi da ustune yazildigi icin
# kurtarilamadi.
#
# Bir test, oyuncunun verisine asla dokunmamali. Kayit dizini her
# calistirmada gecici bir klasore aliniyor.
import tempfile  # noqa: E402

os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

# Klasore **varsayilan bir kayit** tohumlaniyor. Bos birakilsaydi
# `read_save()` None donerdi ve sahnelerin `save_data`si None olurdu -
# oysa testler gercek bir kaydin varligina gore yazilmis (bayrak
# okuyor, bolum numarasi yaziyor). Amac oyuncunun dosyasindan
# kurtulmak, testlerin davranisini degistirmek degil.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.systems.save import SaveData as _SaveData  # noqa: E402
from src.systems.save import write_save as _write_save  # noqa: E402

_write_save(_SaveData())

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_TEMP = os.environ["LORE_SAVE_DIR"]

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.combat import weapons  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.systems.save import SaveData, read_save, save_path, write_save  # noqa: E402
from src.ui import equipment  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def on_disk() -> SaveData | None:
    """Diskteki kayit - **bellektekine bakmiyoruz**, hatanin tamami buydu."""
    data, _ = read_save()
    return data


def main() -> int:
    print(f"gecici kayit dizini: {_TEMP}")
    game = Game()

    # --- 1. Temel yazma/okuma ---------------------------------------------
    print("\n--- temel ---")
    data = SaveData(character="rey", gold=0)
    check(write_save(data), "kayit yazilabiliyor")
    check(save_path().is_file(), "dosya diskte var", str(save_path().name))
    check(on_disk() is not None, "kayit geri okunabiliyor")

    # --- 2. Bolum sonu ekrani -----------------------------------------------
    # ESKI HATA: `ChapterEndScene` hicbir sey yazmiyordu. Bolumu bitirip
    # menuye donen oyuncu butun ilerlemesini kaybediyordu.
    print("\n--- bolum sonu ekrani ---")
    from src.ui.chapter_end import ChapterEndScene, ChapterResult

    data = on_disk()
    data.chapter = 1
    data.gold = 10
    write_save(data)

    data.chapter = 2
    data.gold = 175
    data.chapter_name = "chapter.first_descent"
    result = ChapterResult("chapter.first_descent", 1200, 9, 165, 1, 1)
    game.scenes.set_root(ChapterEndScene, transition=False,
                         result=result, save_data=data)
    game.scenes._flush()

    stored = on_disk()
    check(stored is not None and stored.chapter == 2,
          "bolum sonu ekrani BOLUMU diske yazdi",
          f"diskte chapter={stored.chapter if stored else '-'}")
    check(stored is not None and stored.gold == 175,
          "altin da yazildi", f"diskte gold={stored.gold if stored else '-'}")

    # --- 3. Silah secimi ----------------------------------------------------
    # ESKI HATA: secim bir KARAR ekrani ama yalnizca bellege yaziliyordu.
    print("\n--- silah secimi ---")
    data = on_disk()
    data.weapon = weapons.SWORD
    data.owned_weapons = [weapons.SWORD]
    write_save(data)

    equipment.grant(data, weapons.DAGGER)
    data.weapon = weapons.DAGGER
    write_save(data)
    stored = on_disk()
    check(stored is not None and stored.weapon == weapons.DAGGER,
          "secilen silah diske yazildi", stored.weapon if stored else "-")
    check(stored is not None and weapons.DAGGER in stored.owned_weapons,
          "sahip olunan silahlar listesi diske yazildi",
          str(stored.owned_weapons if stored else []))

    # --- 4. Ekipman ekrani --------------------------------------------------
    # ESKI HATA: silah degisimi bellekte kaliyordu; ancak oyuncu hemen
    # ardindan duraklat menusunden ANA MENU'ye giderse kayda geciyordu.
    print("\n--- ekipman ekrani ---")
    from src.ui.equipment import EquipmentScene

    data = on_disk()
    data.owned_weapons = [weapons.SWORD, weapons.DAGGER, weapons.AXE]
    data.weapon = weapons.SWORD
    write_save(data)

    game.scenes.set_root(EquipmentScene, transition=False,
                         save_data=data, player=None)
    game.scenes._flush()
    screen = game.scenes.current
    screen.index = screen.items.index(weapons.AXE)
    screen._equip()

    stored = on_disk()
    check(stored is not None and stored.weapon == weapons.AXE,
          "ekipman ekranindan yapilan degisiklik DISKE yazildi",
          stored.weapon if stored else "-")

    # Ayni silahi tekrar kusanmak yazma tetiklememeli (gereksiz disk).
    before = save_path().stat().st_mtime_ns
    screen._equip()
    check(save_path().stat().st_mtime_ns == before,
          "zaten kusanilan silah tekrar YAZILMIYOR")

    # --- 5. Kayit bozulmasina karsi yedek -----------------------------------
    print("\n--- yedek ---")
    from src.systems.save import backup_path

    data = on_disk()
    data.gold = 999
    write_save(data)
    check(backup_path().is_file(), "yedek dosyasi olusuyor")
    save_path().write_text("{bozuk json", encoding="utf-8")
    recovered = on_disk()
    check(recovered is not None,
          "bozuk kayit YEDEKTEN kurtariliyor - ilerleme kaybolmuyor",
          f"gold={recovered.gold if recovered else '-'}")

    game.shutdown()
    shutil.rmtree(_TEMP, ignore_errors=True)

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Ilerleme her karar noktasinda diske yaziliyor.")
    return 0


raise SystemExit(main())
