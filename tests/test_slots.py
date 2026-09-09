"""Iki kayit yuvasi - `DEVIR.md` §0.2, `CLAUDE.md` §9.

Olculen dort sey:

  1. **Yuvalar birbirini gormuyor.** 2'ye yazmak 1'i bozmuyor, birini
     silmek otekini silmiyor, her yuva kendi `.bak`'ini tutuyor.
  2. **Eski tek dosya kaybolmuyor.** Slotsuz `save.json` ilk okumada
     1. yuvaya tasiniyor - Arda'nin gercek ilerlemesi orada ve bir
     surum degisikliginin onu silmesi affedilmez olurdu.
  3. **DEVAM ET dusunmeden calisiyor.** Tek yuva doluysa secim ekrani
     ACILMIYOR (`CLAUDE.md` §9: *"oyuncu enter'a basip devam
     edebilmeli"*); ancak iki yuva da doluysa gercekten bir secim var.
  4. **Yikici eylemde varsayilan IPTAL** ve iptal gercekten silmiyor.

Calistir:
    python tests/test_slots.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA** (`DEVIR.md` §0.6). Bu blok `src`
# import edilmeden ONCE calismali.
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_slot_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from src.core.game import Game  # noqa: E402
from src.systems.save import (  # noqa: E402
    LEGACY_BACKUP_NAME, LEGACY_SAVE_NAME, SLOT_COUNT, SaveData, backup_path,
    delete_save, has_save, latest_slot, peek_slot, read_save, save_path,
    set_active_slot, used_slots, user_data_dir, write_save,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def clear_all() -> None:
    for slot in range(1, SLOT_COUNT + 1):
        delete_save(slot)
    for name in (LEGACY_SAVE_NAME, LEGACY_BACKUP_NAME):
        (user_data_dir() / name).unlink(missing_ok=True)


# --- 1. Yuvalar birbirinden bagimsiz -----------------------------------------
def test_slots_are_independent() -> None:
    print("\n--- yuvalar birbirini gormuyor ---")
    clear_all()

    set_active_slot(1)
    write_save(SaveData(chapter=4, gold=55, character="ardo"))
    set_active_slot(2)
    write_save(SaveData(chapter=15, gold=900, character="rey"))

    one, two = peek_slot(1), peek_slot(2)
    check(one is not None and one.chapter == 4 and one.gold == 55,
          "1. yuva kendi verisini tutuyor",
          f"bolum {one.chapter} altin {one.gold}" if one else "YOK")
    check(two is not None and two.chapter == 15 and two.gold == 900,
          "2. yuva kendi verisini tutuyor",
          f"bolum {two.chapter} altin {two.gold}" if two else "YOK")
    check(save_path(1) != save_path(2), "dosya adlari ayri",
          f"{save_path(1).name} / {save_path(2).name}")
    check(used_slots() == [1, 2], "ikisi de dolu gorunuyor",
          str(used_slots()))

    # Her yuva kendi yedegini tutuyor: ikinci yazma yedegi olusturur.
    set_active_slot(2)
    write_save(SaveData(chapter=16, gold=950, character="rey"))
    check(backup_path(2).is_file(), "2. yuva kendi yedegini olusturdu")
    check(not backup_path(1).is_file(),
          "1. yuvanin yedegi ETKILENMEDI - yazma otekine bulasmiyor")

    # Silmek yalnizca o yuvayi siliyor.
    delete_save(2)
    check(not has_save(2), "2. yuva silindi")
    check(has_save(1), "1. yuva DURUYOR - silme otekine bulasmiyor")


# --- 2. Eski tek dosya goc ediyor -------------------------------------------
def test_legacy_save_migrates() -> None:
    """Slotsuz `save.json` 1. yuvaya tasiniyor - **veri kaybi yok.**"""
    print("\n--- eski kayit goc ediyor ---")
    clear_all()

    legacy = user_data_dir() / LEGACY_SAVE_NAME
    set_active_slot(1)
    write_save(SaveData(chapter=7, gold=120, character="ardo"))
    # Yazilan dosyayi slotsuz ada tasiyip eski durumu taklit ediyoruz.
    save_path(1).replace(legacy)
    check(legacy.is_file() and not save_path(1).is_file(),
          "baslangic: yalnizca slotsuz save.json var")

    data, status = read_save()
    check(data is not None and data.chapter == 7 and data.gold == 120,
          "eski kayit okundu - bolum ve altin yerinde",
          f"bolum {data.chapter} altin {data.gold}" if data else "YOK")
    check(status == "ok", "ana kayit olarak okundu (yedek degil)", status)
    check(save_path(1).is_file(), "1. yuvaya tasindi")
    check(not legacy.is_file(), "slotsuz dosya kaldirildi - kopya kalmadi")

    # Ikinci cagri bir sey yapmamali.
    read_save()
    check(save_path(1).is_file(), "ikinci okuma bozmuyor")


def test_migration_never_overwrites() -> None:
    """1. yuva doluysa goc **calismiyor** - yeni kayit korunur."""
    print("\n--- goc dolu yuvanin uzerine yazmiyor ---")
    clear_all()

    set_active_slot(1)
    write_save(SaveData(chapter=12, gold=700, character="rey"))
    (user_data_dir() / LEGACY_SAVE_NAME).write_text(
        '{"chapter": 2, "gold": 5}', encoding="utf-8")

    data, _ = read_save(1)
    check(data is not None and data.chapter == 12,
          "yeni kayit korundu - eski dosya uzerine YAZMADI",
          f"bolum {data.chapter}" if data else "YOK")
    check((user_data_dir() / LEGACY_SAVE_NAME).is_file(),
          "eski dosya oldugu yerde birakildi (kalinti, ama veri)")


# --- 3. DEVAM ET dusunmeden calisiyor ---------------------------------------
def test_continue_skips_screen_for_single_save() -> None:
    """Tek yuva doluysa secim ekrani ACILMIYOR (`CLAUDE.md` §9)."""
    print("\n--- DEVAM ET dusunmeden ---")
    clear_all()
    set_active_slot(1)
    write_save(SaveData(chapter=6, gold=200, character="rey"))

    game = Game()
    try:
        from src.ui.menu import MainMenuScene
        game.scenes.set_root(MainMenuScene, transition=False)
        game.scenes._flush()
        menu = game.scenes.current
        check(menu.menu.items[0].visible, "DEVAM ET gorunur")
        check(menu.menu.selected.label == "menu.continue",
              "DEVAM ET onceden secili", menu.menu.selected.label)
        check(latest_slot() == 1, "en son oynanan yuva 1", str(latest_slot()))

        menu.menu.activate()
        game.scenes._flush()
        name = type(game.scenes.current).__name__
        check(name != "SlotSelectScene",
              "tek kayitta yuva ekrani ACILMIYOR - dogrudan giriyor", name)

        # Ikinci yuva da dolunca artik gercekten bir secim var.
        set_active_slot(2)
        write_save(SaveData(chapter=9, gold=310, character="ardo"))
        game.scenes.set_root(MainMenuScene, transition=False)
        game.scenes._flush()
        menu = game.scenes.current
        menu.menu.index = 0
        menu.menu.activate()
        game.scenes._flush()
        name = type(game.scenes.current).__name__
        check(name == "SlotSelectScene",
              "iki kayitta yuva ekrani ACILIYOR", name)
        check(game.scenes.current.mode == "continue",
              "ekran 'devam' kipinde", game.scenes.current.mode)
    finally:
        game.quit()


# --- 4. Yikici eylem: varsayilan IPTAL --------------------------------------
def test_overwrite_defaults_to_cancel() -> None:
    print("\n--- uzerine yazma: varsayilan IPTAL ---")
    clear_all()
    set_active_slot(1)
    write_save(SaveData(chapter=11, gold=480, character="rey"))

    game = Game()
    try:
        from src.ui.slot_select import SlotSelectScene
        game.scenes.set_root(SlotSelectScene, transition=False, mode="new")
        game.scenes._flush()
        scene = game.scenes.current

        scene.menu.index = 0                 # dolu yuva
        scene.menu.activate()
        check(scene.confirm is not None, "dolu yuvada onay soruluyor")
        check(scene.confirm.selected.label == "common.cancel",
              "varsayilan secim IPTAL", scene.confirm.selected.label)
        check(scene.confirm.items[1].danger,
              "yikici secenek tehlike olarak isaretli")

        scene.confirm.activate()             # IPTAL
        check(scene.confirm is None, "IPTAL kapatti")
        check(has_save(1), "IPTAL kaydi SILMEDI")

        # Onaylayinca gercekten siliniyor ve aktif yuva o oluyor.
        scene.menu.activate()
        scene.confirm.move(1)                # YINE DE BASLA
        scene.confirm.activate()
        check(not has_save(1), "onay kaydi sildi")
        from src.systems.save import active_slot
        check(active_slot() == 1, "aktif yuva secilen oldu",
              str(active_slot()))
    finally:
        game.quit()


def test_empty_slot_needs_no_confirm() -> None:
    print("\n--- bos yuva onay istemiyor ---")
    clear_all()
    game = Game()
    try:
        from src.ui.slot_select import SlotSelectScene
        game.scenes.set_root(SlotSelectScene, transition=False, mode="new")
        game.scenes._flush()
        scene = game.scenes.current
        scene.menu.index = 1                 # bos yuva
        scene.menu.activate()
        check(scene.confirm is None,
              "bos yuvada onay YOK - silinecek bir sey yok")
    finally:
        game.quit()


def main() -> int:
    test_slots_are_independent()
    test_legacy_save_migrates()
    test_migration_never_overwrites()
    test_continue_skips_screen_for_single_save()
    test_overwrite_defaults_to_cancel()
    test_empty_slot_needs_no_confirm()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Iki yuva bagimsiz, eski kayit goc ediyor, yikici eylem soruyor.")
    return 0


pygame.display.init()
pygame.font.init()
raise SystemExit(main())
