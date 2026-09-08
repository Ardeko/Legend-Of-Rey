"""Uzaktan dovus - ok ve bomba.

Arda, 08.09.2026: *"me sale satan ... tek kullanimlik bomba ve ok gibi
seyler de eklesin, karakterlere yeni bir uzaktan dovus mekanigi
eklenmis olsun."*

Korunan kurallar:

  * **Ok, kilicin uzaktan kopyasi DEGIL.** Tek hedefte kilictan zayif;
    degeri ulasilamayan yeri vurmasi. Bomba kalabalikta iyi. Ikisi de
    kilicin yerine gecmiyor, kilicin yapamadigini yapiyor.
  * Bomba patlamasi **radyal ve delici** (`docs/derinlestirme.md` 1.2).
    Delici olmasaydi ilk dusmanda tukenir ve "alan hasari" diye bir sey
    kalmazdi - ayni tuzaga Sismek'te bir kez dusuldu.
  * Sayac **dusuyor** ve bitince atilamiyor.
  * Firlatma zincirin ortasinda calismiyor - iki sistem birbirini
    yemesin.
  * Elde bir sey yokken tus **sessizce gecmiyor** (ret sesi).

Calistir:
    python tests/test_consumables.py
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

from src.config import CHAIN  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.scenes.chapter02 import Chapter02Scene  # noqa: E402
from src.systems import consumables  # noqa: E402
from src.systems.save import SaveData  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def main() -> int:
    game = Game()
    game.settings.save = lambda *a, **k: None    # type: ignore[method-assign]

    # --- 1. Ikisi gercekten FARKLI ----------------------------------------
    print("--- ok ve bomba ayni sey degil ---")
    arrow = consumables.get(consumables.ARROW)
    bomb = consumables.get(consumables.BOMB)
    check(arrow.gravity == 0.0, "ok duz uçuyor", str(arrow.gravity))
    check(bomb.gravity > 0.0, "bomba yay ciziyor", str(bomb.gravity))
    check(arrow.blast == 0, "okun patlamasi yok")
    check(bomb.blast > 0, "bombanin alan hasari var", str(bomb.blast))
    check(bomb.damage == 0,
          "bomba CARPMA hasari vermiyor - isi patlamak", str(bomb.damage))
    check(arrow.speed > bomb.speed, "ok bombadan hizli",
          f"{arrow.speed} > {bomb.speed}")
    check(bomb.cost > arrow.cost, "bomba daha pahali",
          f"{bomb.cost} > {arrow.cost}")

    # Ok kilicin kopyasi olmamali: tek hedefte zincirden ZAYIF.
    chain_total = sum(spec.damage for spec in CHAIN)
    check(arrow.damage < chain_total,
          "ok tek hedefte kilic zincirinden ZAYIF - kopyasi degil",
          f"{arrow.damage} < {chain_total}")

    # --- 2. Sayim ----------------------------------------------------------
    print("\n--- canta ---")
    data = SaveData()
    check(consumables.count(data, consumables.ARROW) == 0, "bastan bos")
    check(not consumables.spend(data, consumables.ARROW),
          "yokken harcanamiyor")
    consumables.add(data, consumables.ARROW, 3)
    check(consumables.count(data, consumables.ARROW) == 3, "uc ok eklendi")
    consumables.add(data, consumables.ARROW, 99)
    check(consumables.count(data, consumables.ARROW) == consumables.MAX_CARRY,
          f"tasima siniri {consumables.MAX_CARRY} asilmiyor",
          str(consumables.count(data, consumables.ARROW)))
    check(consumables.spend(data, consumables.ARROW), "harcanabiliyor")
    check(consumables.count(data, consumables.ARROW)
          == consumables.MAX_CARRY - 1, "sayac dustu")

    # --- 3. Secim ----------------------------------------------------------
    print("\n--- secim ---")
    fresh = SaveData()
    check(consumables.selected(fresh) == "", "elde bir sey yokken secim bos")
    consumables.add(fresh, consumables.BOMB, 1)
    check(consumables.selected(fresh) == consumables.BOMB,
          "tek cesit varsa kendiliginden o seciliyor")
    consumables.add(fresh, consumables.ARROW, 2)
    consumables.select(fresh, consumables.ARROW)
    check(consumables.selected(fresh) == consumables.ARROW, "secim tutuyor")
    consumables.select_next(fresh)
    check(consumables.selected(fresh) == consumables.BOMB,
          "sirayla geciyor", consumables.selected(fresh))

    # Secili olan biterse **kendiliginden** elde olana geciyor: oyuncu
    # bos bir yuvaya basip "tus calismiyor" sanmasin.
    consumables.select(fresh, consumables.BOMB)
    consumables.spend(fresh, consumables.BOMB)
    check(consumables.count(fresh, consumables.BOMB) == 0, "bomba bitti")
    check(consumables.selected(fresh) == consumables.ARROW,
          "biten malzemeden elde olana KENDILIGINDEN geciyor",
          consumables.selected(fresh))

    # --- 4. Firlatma sahnede -----------------------------------------------
    print("\n--- firlatma ---")
    game.scenes.set_root(Chapter02Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current
    scene.enemies.clear()
    if scene.save_data is None:
        scene.save_data = SaveData()
    consumables.add(scene.save_data, consumables.ARROW, 3)
    consumables.select(scene.save_data, consumables.ARROW)

    before_boxes = scene.hitboxes.active_count
    scene.throw(consumables.ARROW)
    check(scene.hitboxes.active_count == before_boxes + 1,
          "ok bir hitbox uretti")
    box = scene.hitboxes.boxes[-1]
    check(box.velocity[0] != 0, "ok hareket ediyor", str(box.velocity))
    check(box.stop_on_solid, "ok duvarda duruyor")
    check(box.owner is scene.player, "sahibi oyuncu - kendine vurmuyor")

    start_x = box.rect.x
    for _ in range(10):
        box.update()
    check(box.rect.x != start_x, "ok gercekten ilerliyor",
          f"{start_x} -> {box.rect.x}")

    # --- 5. Bomba yay cizip PATLIYOR ---------------------------------------
    print("\n--- bomba ---")
    consumables.add(scene.save_data, consumables.BOMB, 1)
    scene.hitboxes.boxes.clear()
    scene.throw(consumables.BOMB)
    shell = scene.hitboxes.boxes[-1]
    check(shell.gravity > 0, "bomba yercekimi aliyor")
    check(shell.pierce, "bomba carpinca yok OLMUYOR - isi patlamak")
    first_vy = shell.velocity[1]
    for _ in range(5):
        shell.update()
    check(shell.velocity[1] > first_vy, "dikey hiz artiyor - yay ciziyor",
          f"{first_vy:.2f} -> {shell.velocity[1]:.2f}")

    # Tukenince patlama aciliyor mu?
    scene.hitboxes.boxes.clear()
    scene.throw(consumables.BOMB)
    shell = scene.hitboxes.boxes[-1]
    shell.expired = True
    scene.hitboxes.update({})
    blast = [b for b in scene.hitboxes.boxes if b.pierce and b.damage > 0]
    check(bool(blast), "tukenince PATLAMA hitbox'i aciliyor",
          f"{len(scene.hitboxes.boxes)} kutu")
    if blast:
        check(blast[0].rect.width >= bomb.blast,
              "patlama genis - alan hasari", f"{blast[0].rect.width}px")
        check(blast[0].pierce,
              "patlama DELICI - ilk dusmanda tukenmiyor")

    # --- 6. Girdi kurallari ------------------------------------------------
    print("\n--- girdi kurallari ---")
    played: list[str] = []
    real_play = game.play_sound
    game.play_sound = lambda name, **kw: (          # type: ignore[method-assign]
        played.append(name), real_play(name, **kw))

    def press_throw() -> None:
        game.input.begin_frame()
        game.input.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        game.input.end_frame()
        scene._update_throw()
        game.input.begin_frame()
        game.input.handle_event(
            pygame.event.Event(pygame.KEYUP, key=pygame.K_r))
        game.input.end_frame()

    # Elde bir sey yokken: ret sesi, sessiz gecmiyor.
    scene.save_data.consumables = {}
    played.clear()
    press_throw()
    check("ui_deny" in played,
          "elde bir sey yokken RET SESI - sessizce gecmiyor", str(played))

    # Elde varken atiliyor ve sayac dusuyor.
    consumables.add(scene.save_data, consumables.ARROW, 2)
    consumables.select(scene.save_data, consumables.ARROW)
    scene.hitboxes.boxes.clear()
    press_throw()
    check(consumables.count(scene.save_data, consumables.ARROW) == 1,
          "atinca sayac dustu",
          str(consumables.count(scene.save_data, consumables.ARROW)))
    check(scene.hitboxes.active_count > 0, "mermi uretildi")

    # Zincirin ortasinda atilamiyor.
    scene.hitboxes.boxes.clear()
    before = consumables.count(scene.save_data, consumables.ARROW)
    scene.player.chain.start(0)
    press_throw()
    check(consumables.count(scene.save_data, consumables.ARROW) == before,
          "zincir sirasinda ATILMIYOR - iki sistem birbirini yemiyor")

    # --- 7. Dukkanda satiliyor ---------------------------------------------
    print("\n--- dukkan ---")
    from src.scenes.chapter03 import TRADE_OFFERS
    repeatable = [o for o in TRADE_OFFERS if o.repeatable]
    check(len(repeatable) == 2, "iki tekrarlanabilir teklif var",
          str([o.key for o in repeatable]))
    from src.systems import economy
    for offer in repeatable:
        check(not economy.already_bought(SaveData(), offer),
              f"{offer.key} tekrar alinabiliyor")
        check(offer.item in consumables.CONSUMABLES,
              f"{offer.key} gercek bir malzeme veriyor", offer.item)
    once = [o for o in TRADE_OFFERS if not o.repeatable]
    check(len(once) == 3, "tekil teklifler bozulmadi", str(len(once)))

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Uzaktan dovus: ok ve bomba farkli, sayac dusuyor, dukkan satiyor.")
    return 0


raise SystemExit(main())
