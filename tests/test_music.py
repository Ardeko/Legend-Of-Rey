"""Muzik gecisleri - sert kesme var mi?

Arda, 08.09.2026: *"muzikler degisirken yumusak gecis olsun."*

Sebep koddaydi ve modulun kendi aciklamasiyla CELISIYORDU: docstring
"`fadeout` + `fade_ms` ile temiz bir sonup-acilma" diyordu ama
`play()` `fadeout()`u hic cagirmiyordu. Dogrudan `load()` ediliyordu
ve `load()` calan parcayi **aninda kesiyor**. Yani her gecis "sert
kesme + yumusak acilma" idi.

Bu paket mixer'i **taklit ediyor**. Sebep basit: muzik dosyalari
(~53 MB MP3) depoda yok (`.gitignore`) ve testin gercek ses cikisina
ihtiyaci de yok - olculen sey CAGRI SIRASI:

    baglam degisti  -> fadeout cagrildi mi? load HENUZ cagrilmadi mi?
    akis bosaldi    -> simdi load + play cagrildi mi?

Calistir:
    python tests/test_music.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA.** Gerekcesi oteki paketlerde yazili.
import tempfile  # noqa: E402

os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.systems.save import SaveData as _SaveData  # noqa: E402
from src.systems.save import write_save as _write_save  # noqa: E402

_write_save(_SaveData())

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.audio import music as music_mod  # noqa: E402
from src.audio.music import (  # noqa: E402
    COMBAT_FADE_IN_MS, FADE_IN_MS, SWITCH_OUT_MS, MusicDirector,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


class FakeMixer:
    """`pygame.mixer.music` yerine gecen kayit defteri.

    Gercek mixer yerine bu kullaniliyor cunku olculen sey ses degil
    **cagri sirasi**. Ayrica muzik dosyalari bu makinede yok.
    """

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.busy = False

    def load(self, path):
        self.calls.append(("load", Path(path).name))

    def play(self, loops=0, fade_ms=0):
        self.calls.append(("play", fade_ms))
        self.busy = True

    def fadeout(self, ms):
        self.calls.append(("fadeout", ms))
        # Gercek `fadeout` hemen susturmuyor; akis bir sure daha "busy".
        # Testler `busy`yi elle indirip sonmeyi tamamliyor.

    def get_busy(self):
        return self.busy

    def set_volume(self, value):
        pass

    def names(self) -> list[str]:
        return [c[0] for c in self.calls]


class FakeSettings:
    def get(self, key, default=None):
        return {"volume_master": 1.0, "volume_music": 1.0}.get(key, default)


def main() -> int:
    fake = FakeMixer()
    pygame.mixer.music = fake                    # type: ignore[assignment]
    # Butun parcalar "var" sayilsin - dosyalar depoda degil.
    music_mod.MUSIC_DIR = Path(__file__).resolve().parent
    original_isfile = Path.is_file
    Path.is_file = lambda self: True             # type: ignore[assignment]

    try:
        # --- 1. Ilk parca: sonecek bir sey yok, dogrudan basliyor -------
        print("--- ilk parca ---")
        director = MusicDirector(FakeSettings())
        director.play("explore")
        check(fake.names() == ["load", "play"],
              "ilk parca DOGRUDAN basliyor - sondurulecek bir sey yok",
              str(fake.names()))
        check(fake.calls[1][1] == FADE_IN_MS, "acilis suresi varsayilan",
              str(fake.calls[1][1]))

        # --- 2. Baglam degisti: ONCE fadeout, load YOK -------------------
        print("\n--- gecis: once sonme ---")
        fake.calls.clear()
        director.play("combat", fade_ms=COMBAT_FADE_IN_MS)
        check(fake.names() == ["fadeout"],
              "yalnizca FADEOUT cagrildi - eski parca kesilmedi",
              str(fake.names()))
        check("load" not in fake.names(),
              "yeni parca HENUZ yuklenmedi (load calani aninda keser)")
        check(fake.calls[0][1] <= SWITCH_OUT_MS,
              "sonme suresi gecis siniri icinde",
              f"{fake.calls[0][1]}ms <= {SWITCH_OUT_MS}ms")
        check(fake.calls[0][1] <= COMBAT_FADE_IN_MS,
              "hizli aciliyorsa hizli da soner - dovus gecikmeli gelmesin",
              f"{fake.calls[0][1]}ms <= {COMBAT_FADE_IN_MS}ms")

        # --- 3. Akis bosalinca yeni parca basliyor -----------------------
        print("\n--- gecis: sonra acilma ---")
        fake.calls.clear()
        director.update()
        check(fake.names() == [],
              "akis hala doluyken yeni parca BASLAMIYOR", str(fake.names()))
        fake.busy = False
        director.update()
        check(fake.names() == ["load", "play"],
              "akis bosalinca yeni parca yuklenip basliyor",
              str(fake.names()))
        check(fake.calls[1][1] == COMBAT_FADE_IN_MS,
              "istenen acilis suresi korundu", str(fake.calls[1][1]))

        # --- 4. Ayni baglam tekrar istenirse hicbir sey olmuyor ----------
        print("\n--- ayni baglam ---")
        fake.calls.clear()
        for _ in range(10):
            director.play("combat")
            director.update()
        check(not fake.calls,
              "ayni baglam tekrar istenince parca BASTAN BASLAMIYOR",
              str(fake.calls))

        # --- 5. Gecis sirasinda fikir degisirse ------------------------
        # Oyuncu dovusten kacip geri girerse bekleyen hedef yanlis olur.
        print("\n--- gecis sirasinda fikir degisti ---")
        fake.busy = True
        director.play("explore")
        fake.calls.clear()
        director.play("combat")          # geri dondu
        fake.busy = False
        director.update()
        check(fake.names().count("load") <= 1,
              "tek parca yukleniyor - eski hedef calinmiyor",
              str(fake.names()))
        check(director.context == "combat",
              "son istenen baglam kazaniyor", director.context)

        # --- 6. stop() bekleyeni de iptal ediyor -------------------------
        print("\n--- stop ---")
        fake.busy = True
        director.play("sad")
        fake.calls.clear()
        director.stop()
        fake.busy = False
        director.update()
        check("load" not in fake.names(),
              "durdurulan muzik bir kare sonra geri GELMIYOR",
              str(fake.names()))
        check(director.context == "", "baglam temizlendi", director.context)

        # --- 7. Kilit korunuyor -----------------------------------------
        print("\n--- senaryolu kilit ---")
        fake.busy = False
        fake.calls.clear()
        director.hold("sad", 60)
        check("load" in fake.names(), "kilitli parca basladi")
        fake.calls.clear()
        director.play("combat")
        check(not fake.calls, "kilit boyunca baglam degismiyor",
              str(fake.calls))
    finally:
        Path.is_file = original_isfile            # type: ignore[assignment]

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Muzik gecisleri iki asamali: once soner, sonra acilir.")
    return 0


raise SystemExit(main())
