"""Korku katmani dogrulamasi - `docs/korku.md`.

Korku, yanlis uygulandiginda oyunu ucuzlatan tek duygu. Belgedeki
kurallar bu yuzden bagalyici ve bu yuzden burada olculuyor:

  * **Katman 1 asla kapanmaz** - Yanki'nin yalani bir korku efekti
    degil, oyunun ana mekanigi. Ayar onu kapatabilseydi B10, B14 ve
    B18 anlamsizlasirdi.
  * **Katman 2 ve 3 tamamen kapanir** - "korku kapali" diyen oyuncu on
    yedi bolumde rahat, birinde irkilirse ayar yalan soylemis olur.
  * **Azaltilmis seviye sok anlarini KORUR**, yalnizca ani sesi kisar.
  * Nefes **surekli degil**: uc kosuldan biri saglanmadan hic duyulmaz.
    Nefesin baslamasi sinyalin kendisi.
  * Fotosensitivite ayari **olayi degil sunumu** degistirir.

Calistir:
    python tests/test_horror.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

# `pygame.init()` DEGIL - joystick taramasi bu makinede 40 saniye
# suruyor (bkz. src/core/game.py). Oyun da tam olarak bu yolu izliyor.
pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.audio import sfx  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.chapter02 import Chapter02Scene  # noqa: E402
from src.systems import breath as breath_mod  # noqa: E402
from src.systems import horror  # noqa: E402

failures: list[str] = []
played: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def main() -> int:
    game = Game()
    # Ayarlar diske YAZILMASIN - oyuncunun gercek dosyasi bozulmasin.
    game.settings.save = lambda *a, **k: None       # type: ignore[method-assign]
    real_play = game.play_sound
    game.play_sound = lambda name, **kw: (          # type: ignore[method-assign]
        played.append(name), real_play(name, **kw))

    def fresh() -> Chapter02Scene:
        """Temiz sahne: dusmansiz, tam canli, ilk odada.

        Dusmanlar temizleniyor cunku itilme `body.vx`'i sifirdan
        cikariyor ve "hareketsizlik" hic birikmiyor. Ilk surumde butun
        senaryolar tek sahnede kosuyordu ve tam bu yuzden yanlis sonuc
        verdi - kod dogruydu, test yanlisti.
        """
        game.scenes.set_root(Chapter02Scene, transition=False,
                             character="rey")
        game.scenes._flush()
        scene = game.scenes.current
        scene.enemies.clear()
        played.clear()
        return scene

    def run(scene, frames: int, walk: bool = False) -> None:
        for _ in range(frames):
            if walk:
                scene.player.body.vx = 1.5
            game.input.begin_frame()
            game.input.end_frame()
            scene.update()
            scene.enemies.clear()

    def breaths() -> int:
        return sum(1 for n in played if n.startswith("breath"))

    # --- 1. Sesler uretiliyor ve genlik tavanina uyuyor --------------------
    # Butun korku sesleri 0.55 tepe genligini asmamali - jumpscare dahil.
    # Ani ses bir tasarim araci, kulaga zarar verme araci degil.
    print("--- sesler ---")
    import numpy as np
    horror_keys = ("breath_in", "breath_out", "breath_sharp", "heartbeat",
                   "lie_caught", "phantom_fade", "watcher_notice",
                   "watcher_strike", "ghost_seen", "room_changed")
    for key in horror_keys:
        check(key in sfx.SFX, f"{key} kayitli")
    loudest = 0.0
    for key in horror_keys:
        peak = float(np.abs(sfx.SFX[key]()).max())
        loudest = max(loudest, peak)
    check(loudest <= 0.5501, "hicbir korku sesi 0.55 tepeyi asmiyor",
          f"en yuksek {loudest:.3f}")

    # --- 2. Nefes SUREKLI degil -------------------------------------------
    print("\n--- nefes: susmasi ---")
    scene = fresh()
    run(scene, 240, walk=True)
    check(breaths() == 0, "saglikli ve yuruyen oyuncu nefes ALMIYOR",
          f"{breaths()} nefes")

    # --- 3. Karanlikta hareketsiz -----------------------------------------
    print("\n--- nefes: karanlikta hareketsiz ---")
    scene = fresh()
    check(scene.dark_ambient, "B2 karanlik isaretli (docs/korku.md 5.1)")
    run(scene, 60)
    check(breaths() == 0,
          f"esik ({breath_mod.STILL_FRAMES} kare) dolmadan nefes yok")
    run(scene, 260)
    check(breaths() > 0, "hareketsiz kalinca nefes basladi",
          f"{breaths()} nefes / 320 kare")

    order = [n for n in played if n in ("breath_in", "breath_out")]
    check(len(order) >= 3 and all(order[i] != order[i + 1]
                                  for i in range(len(order) - 1)),
          "alis ve verisi DONUSUMLU - tek ses tekrari degil",
          " ".join(order[:6]))

    print("\n--- nefes: hareket edince susuyor ---")
    scene = fresh()
    run(scene, 260)
    during = breaths()
    played.clear()
    run(scene, 260, walk=True)
    check(during > 0 and breaths() == 0, "hareket baslayinca nefes kesiliyor",
          f"dururken {during}, yururken {breaths()}")

    # --- 4. Diger iki tetikleyici -----------------------------------------
    print("\n--- nefes: can ve Yanki ---")
    scene = fresh()
    scene.player.health = int(scene.player.max_health * 0.2)
    run(scene, 240, walk=True)
    check(breaths() > 0, "can %25 altinda YURURKEN de nefes var",
          f"{breaths()} nefes")

    scene = fresh()
    scene.player.health = max(1, int(scene.player.max_health * 0.08))
    run(scene, 300)
    check(played.count("heartbeat") > 0, "can %12 altinda kalp atisi",
          f"{played.count('heartbeat')} atis")

    scene = fresh()
    scene.echo_forced = 400        # B2'nin anlatim kancasi sesi acik tutar
    run(scene, 240, walk=True)
    check(breaths() > 0, "Yanki acikken yururken bile nefes var",
          f"{breaths()} nefes")

    # --- 5. Ayar kapisi ----------------------------------------------------
    print("\n--- ayar kapisi ---")
    game.settings.set("horror", horror.OFF)
    check(not horror.atmosphere(game.settings), "KAPALI: Katman 2 kapali")
    check(not horror.shock(game.settings), "KAPALI: Katman 3 kapali")
    scene = fresh()
    scene.player.health = 3
    run(scene, 400)
    check(breaths() == 0 and played.count("heartbeat") == 0,
          "KAPALI iken hicbir nefes/kalp sesi yok", f"{len(played)} ses")

    game.settings.set("horror", horror.REDUCED)
    check(horror.shock(game.settings),
          "AZALTILMIS: sok anlari KORUNUYOR - yalnizca ani ses kisiliyor")
    check(not horror.loud(game.settings), "AZALTILMIS: ani ses kapali")
    check(horror.loudness(game.settings) == horror.REDUCED_LOUDNESS,
          "AZALTILMIS: genlik carpani uygulaniyor",
          str(horror.loudness(game.settings)))
    scene = fresh()
    run(scene, 320)
    check(breaths() > 0, "AZALTILMIS seviyede nefes duruyor",
          f"{breaths()} nefes")

    game.settings.set("horror", horror.FULL)
    check(horror.loudness(game.settings) == 1.0, "TAM: genlik tam")

    # Ayar yoksa **tam korku** - eksik ayar yuzunden bir ogenin sessizce
    # kaybolmasi, fazladan calismasindan cok daha zor bulunur.
    check(horror.level(None) == horror.FULL, "ayarsiz cagri tam korkuya duser")
    check(horror.atmosphere(None) and horror.shock(None),
          "ayarsiz cagri katmanlari acik birakiyor")

    # --- 6. Fotosensitivite ------------------------------------------------
    print("\n--- fotosensitivite ---")
    game.settings.set("flash_limit", False)
    check(horror.flash_allowed(game.settings), "varsayilan: parlama serbest")
    game.settings.set("flash_limit", True)
    check(not horror.flash_allowed(game.settings),
          "sinir acikken parlama cizilmiyor")
    check(horror.shock(game.settings),
          "parlama siniri OLAYI durdurmuyor - yalnizca sunumu degistiriyor")
    game.settings.set("flash_limit", False)

    # --- 7. Cemo'nun sozcukleri (Katman 1 - ASLA kapanmaz) ----------------
    # `docs/korku.md` 11.1: B1'deki replik uc parcaya bolunup B4, B9,
    # B13'e ekiliyor ve B18'de butun olarak patliyor. Bir twist ancak
    # tohumu ekilmisse is gorur.
    print("\n--- Cemo'nun sozcukleri ---")
    game.settings.set("horror", horror.OFF)      # Katman 1 kapanmamali

    def spoken(scene) -> list[str]:
        return [line.key for line in scene.dialogue.lines]

    # B4 - Rey kolyeyi cevirirken
    from src.scenes.chapter04 import Chapter04Scene
    game.scenes.set_root(Chapter04Scene, transition=False, character="rey")
    game.scenes._flush()
    ch04 = game.scenes.current
    ch04._seed_line()
    check("line.ch04_echo_seed" in spoken(ch04),
          "B4: tohum 1/3 soyleniyor (korku KAPALI iken bile)",
          str(spoken(ch04)))

    game.scenes.set_root(Chapter04Scene, transition=False, character="ardo")
    game.scenes._flush()
    ch04a = game.scenes.current
    ch04a._seed_line()
    check("line.ch04_echo_seed" not in spoken(ch04a),
          "B4: Ardo'da tohum YOK - onun Yanki'si yok")

    # B9 - yanlis can
    from src.scenes.chapter09 import Chapter09Scene
    game.scenes.set_root(Chapter09Scene, transition=False, character="rey")
    game.scenes._flush()
    ch09 = game.scenes.current
    ch09._wrong_order()
    check("line.ch09_echo_seed" in spoken(ch09),
          "B9: tohum 2/3 yanlis canda soyleniyor", str(spoken(ch09)))
    ch09.dialogue.stop()
    ch09._wrong_order()
    check("line.ch09_echo_seed" not in spoken(ch09),
          "B9: ikinci yanlista TEKRARLANMIYOR - ayni numara iki kez yok")

    # B13 - Cemo "Rey?" der, Yanki tekrarlar
    from src.scenes.chapter13_cinematics import CageCinematic
    game.scenes.set_root(CageCinematic, transition=False, character="rey")
    game.scenes._flush()
    cage = game.scenes.current
    gorus = next(p for p in cage.panels if p.name == "gorus")
    keys = [line.key for line in (gorus.lines or ((gorus.line,) if gorus.line
                                                  else ()))]
    check(keys == ["line.ch13_cemo_sees", "line.ch13_echo_seed"],
          "B13: Cemo soyler, Yanki BIR BEAT SONRA tekrarlar", str(keys))

    game.scenes.set_root(CageCinematic, transition=False, character="ardo")
    game.scenes._flush()
    cage_a = game.scenes.current
    gorus_a = next(p for p in cage_a.panels if p.name == "gorus")
    check(gorus_a.line is not None and not gorus_a.lines,
          "B13: Ardo'da tek replik - tekrar yok")

    # B18 - tohum patliyor. **B1'in anahtarinin ta kendisi** olmali:
    # ayri bir anahtar acilsaydi ikisi ayrisirdi (Ingilizce cevirisi
    # ilk denemede ayristi bile) ve tohum taninmaz olurdu.
    from src.scenes.chapter18 import Chapter18Scene
    game.scenes.set_root(Chapter18Scene, transition=False, character="rey")
    game.scenes._flush()
    ch18 = game.scenes.current
    ch18._narrate_zone("ses")
    keys18 = spoken(ch18)
    check("line.ch01_cemo_gift" in keys18,
          "B18: yaratik Cemo'nun B1 repligini soyluyor", str(keys18))
    check(keys18.index("line.ch01_cemo_gift") == 0,
          "B18: once yaratik konusuyor, sonra Rey - oyuncu once TANIMALI")

    import json
    with open(ROOT / "src/ui/lang/tr.json", encoding="utf-8") as handle:
        table = json.load(handle)["line"]
    check("ch18_cemo_false" not in table,
          "B18 kendi kopyasini TUTMUYOR - ayrisma imkansiz")

    # --- 8. Yanlis sessizlik (Katman 2) ------------------------------------
    # `docs/korku.md` 5.4: oyun sessizligi bir ALARM olarak ogretiyor
    # (gizli oda, boss). Bu araliklar o bilgiyi bozuyor - muzik
    # kesiliyor ve hicbir sey olmuyor.
    #
    # "Hicbir sey olmamasi" isin kendisi: bir kez bile "aslinda bir sey
    # oluyordu" dersek numara olur ve oyuncu bir daha yutmaz. Bu yuzden
    # araliklarin BOS oldugu da olculuyor.
    print("\n--- yanlis sessizlik ---")
    game.settings.set("horror", horror.FULL)
    from src.config import TILE_SIZE
    from src.scenes.chapter10 import Chapter10Scene
    from src.world.rooms import chapter04 as rooms04
    from src.world.rooms import chapter10 as rooms10

    for label, scene_cls, rooms in (("B4", Chapter04Scene, rooms04),
                                    ("B10", Chapter10Scene, rooms10)):
        game.scenes.set_root(scene_cls, transition=False, character="rey")
        game.scenes._flush()
        scene = game.scenes.current
        stretch = scene.false_silence.stretches[0]

        # Aralik gercekten bos mu? Dusman, sandik, tetikleyici olmamali.
        intruders = [p.kind for p in rooms.LEVEL.placements
                     if stretch.start <= p.tile_x < stretch.end
                     and p.kind not in ("player", "exit")]
        check(not intruders, f"{label}: sessizlik araliginda HICBIR SEY yok",
              str(intruders) if intruders else f"tile {stretch.start}-{stretch.end}")

        # Icine girince muzik kesiliyor mu?
        middle = (stretch.start + stretch.end) // 2
        scene.player.body.set_feet(middle * TILE_SIZE + TILE_SIZE * 0.5,
                                   scene.player.body.bottom)
        game.music_hush = 0.0
        for _ in range(40):
            game.music_hush = 0.0
            scene.false_silence.update(game, scene)
        check(game.music_hush > 0.6, f"{label}: aralikta muzik kesiliyor",
              f"hush {game.music_hush:.2f}")

        # Cikinca geri geliyor mu?
        outside = max(0, stretch.start - 6)
        scene.player.body.set_feet(outside * TILE_SIZE + TILE_SIZE * 0.5,
                                   scene.player.body.bottom)
        for _ in range(120):
            game.music_hush = 0.0
            scene.false_silence.update(game, scene)
        check(game.music_hush < 0.05, f"{label}: aralik disinda muzik donuyor",
              f"hush {game.music_hush:.2f}")

        # Ayar kapaliyken hic calismamali.
        game.settings.set("horror", horror.OFF)
        scene.false_silence.hush = 0.0
        scene.player.body.set_feet(middle * TILE_SIZE + TILE_SIZE * 0.5,
                                   scene.player.body.bottom)
        for _ in range(60):
            game.music_hush = 0.0
            scene.false_silence.update(game, scene)
        check(game.music_hush == 0.0,
              f"{label}: korku KAPALI iken sessizlik yok",
              f"hush {game.music_hush:.2f}")
        game.settings.set("horror", horror.FULL)

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Korku katmani belgedeki kurallara uyuyor.")
    return 0


raise SystemExit(main())
