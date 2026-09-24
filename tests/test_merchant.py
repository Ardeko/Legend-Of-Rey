"""Gezgin Mum Bekcisi, olumde ok/bomba iadesi ve dunya ici tus gostergesi.

Arda, 23.09.2026: *"Firlatilabilir itemler olunce sifirlanacak mi? ...
Daha fazla dukkan olmali"* ve *"Interaksiyon tuslari daha belli olmali."*

Gercek sahneler kuruluyor (B7, B12, B16, B5); kayitlar yalnizca gecici
`LORE_SAVE_DIR`e yaziliyor.

Calistir:
    python tests/test_merchant.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# **Oyuncunun kaydina DOKUNMA** (bkz. tests/test_lang.py basligi).
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_merchant_")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from src.config import TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.scenes.play import PlayScene  # noqa: E402
from src.systems import consumables, merchant  # noqa: E402
from src.systems.save import SaveData  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f" ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_scene(game: Game, number: int) -> PlayScene:
    cls = f"Chapter{number:02d}Scene"
    module = __import__(f"src.scenes.chapter{number:02d}", fromlist=[cls])
    game.scenes.set_root(getattr(module, cls), transition=False,
                         character="rey")
    game.scenes._flush()
    while not isinstance(game.scenes.current, PlayScene):
        game.scenes._do_pop()
    scene = game.scenes.current
    if scene.save_data is None:
        scene.save_data = SaveData()
    scene.card = None
    scene.dialogue.stop()
    return scene


def idle(game: Game, scene, frames: int) -> None:
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        scene.update()


def press(game: Game, scene, action: Action) -> None:
    game.input.begin_frame()
    game.input._activate(action)
    game.input._deactivate(action)
    game.input.end_frame()
    scene.update()


def stand_by_keeper(scene) -> None:
    keeper = scene.merchant.keeper
    scene.player.body.set_feet(keeper.x + 10, keeper.feet_y)
    scene.player.body.vx = scene.player.body.vy = 0.0
    scene.enemies = []


def test_placement(game: Game) -> None:
    print("\n--- yerlesim ---")
    expected = {7: 4, 12: 3, 16: 2}
    for number, candles in expected.items():
        scene = make_scene(game, number)
        shop = scene.merchant
        check(shop is not None, f"B{number}: bekci var")
        if shop is None:
            continue
        keeper = shop.keeper
        body = pygame.Rect(int(keeper.x) - 6, int(keeper.feet_y) - 20, 12, 20)
        below = pygame.Rect(int(keeper.x) - 6, int(keeper.feet_y), 12, 1)
        check(not scene.tilemap.solid_overlap(body)
              and scene.tilemap.solid_overlap(below),
              f"B{number}: zemine oturmus, duvarda degil")
        check(keeper.candles == candles,
              f"B{number}: her gorunuste bir mum eksik", f"{keeper.candles}")
    scene = make_scene(game, 12)
    check(scene.candle_keeper is scene.merchant.keeper,
          "B12: tek bekci - hikaye repligi ve tezgah ayni govde")
    for number in (1, 2, 5, 9, 15, 18):
        scene = make_scene(game, number)
        check(scene.merchant is None, f"B{number}: dukkan yok")


def test_trade(game: Game) -> None:
    print("\n--- tezgah ---")
    scene = make_scene(game, 7)
    stand_by_keeper(scene)
    idle(game, scene, 2)
    check(scene.prompts.active("merchant"), "yakinda tus gostergesi var")
    press(game, scene, Action.INTERACT)
    check(scene.merchant.open, "INTERACT tezgahi aciyor")
    check(scene.modal_active, "tezgah modal - duraklatma tusu calinmiyor")

    data = scene.save_data
    data.gold = 100
    data.consumables = {}
    bottom = scene.player.body.bottom
    press(game, scene, Action.JUMP)
    idle(game, scene, 3)
    check(scene.player.body.bottom == bottom,
          "tezgah acikken oyuncu ziplamiyor (girdi notr)")

    offer = merchant.TRAVEL_OFFERS[0]
    press(game, scene, Action.CONFIRM)
    check(consumables.count(data, consumables.ARROW) == offer.amount
          and data.gold == 100 - offer.cost,
          "CONFIRM secili teklifi aliyor, altin dusuyor")
    check(scene.merchant.open, "alimdan sonra tezgah acik kaliyor")

    data.consumables = {consumables.ARROW: consumables.MAX_CARRY}
    gold = data.gold
    check(not merchant.buy(scene, offer) and data.gold == gold,
          "dolu cantaya satis yok - altin da gitmiyor")
    data.gold = 0
    check(not merchant.buy(scene, merchant.TRAVEL_OFFERS[1]),
          "yetersiz altinla alinmiyor")

    enemy = SimpleNamespace(dead=False, aware=True, body=SimpleNamespace(
        center_x=scene.player.body.center_x + 40,
        center_y=scene.player.body.center_y))
    scene.enemies = [enemy]
    scene.merchant.update(scene)
    check(not scene.merchant.open, "uyanik dusman yaklasinca tezgah kapaniyor")
    scene.merchant.update(scene)
    check(not scene.prompts.active("merchant"),
          "dovus surerken tezgah teklif edilmiyor")


def test_refund(game: Game) -> None:
    """Gercek akis: kayit diskte, olumde `on_enter` diskten yeniden okuyor."""
    print("\n--- olumde iade ---")
    from src.systems.save import write_save
    write_save(SaveData(chapter=5, character="rey",
                        consumables={consumables.ARROW: 4,
                                     consumables.BOMB: 2}))
    scene = make_scene(game, 5)
    consumables.select(scene.save_data, consumables.ARROW)
    idle(game, scene, 3)
    check(scene.checkpoint_bag.get(consumables.ARROW) == 4,
          "oda girisinde canta hatirlandi", f"{scene.checkpoint_bag}")

    def arrows() -> int:
        return consumables.count(scene.save_data, consumables.ARROW)

    for _ in range(2):
        press(game, scene, Action.THROW)
        idle(game, scene, 20)
    check(arrows() == 2, "iki ok atildi", f"{arrows()}")
    # Duraklatma menusu diske yaziyor: atilan oklar artik diskte de yok.
    write_save(scene.save_data)
    scene.restart()
    check(arrows() == 4, "yeniden denemede atilan oklar geri geldi "
          "(arada disk yazilmis olsa bile)", f"{arrows()}")
    check(consumables.count(scene.save_data, consumables.BOMB) == 2,
          "atilmayan bombalar degismedi")

    press(game, scene, Action.THROW)
    idle(game, scene, 20)
    scene.restart()
    check(arrows() == 4, "ikinci olumde cift iade yok - oda girisini asmiyor",
          f"{arrows()}")


def test_projectiles_visible(game: Game) -> None:
    print("\n--- mermiler gorunur ---")
    scene = make_scene(game, 5)
    data = scene.save_data
    data.consumables = {consumables.ARROW: 3}
    consumables.select(data, consumables.ARROW)
    idle(game, scene, 3)
    press(game, scene, Action.THROW)
    visuals = [box.visual for box in scene.hitboxes.boxes if box.visual]
    check("arrow" in visuals, "atilan okun gorunumu var", f"{visuals}")
    from src.entities.enemies import archer  # noqa: F401 - kaynak taramasi
    source = (ROOT / "src" / "entities" / "enemies" / "archer.py").read_text(
        encoding="utf-8")
    check('visual="enemy_arrow"' in source, "Okcu'nun oku ciziliyor")
    gaoler = (ROOT / "src" / "entities" / "bosses" / "gaoler.py").read_text(
        encoding="utf-8")
    check('visual="keys"' in gaoler and 'visual="chain_lash"' in gaoler,
          "Zindanci'nin anahtarlari ve zinciri ciziliyor")


def test_prompts(game: Game) -> None:
    print("\n--- tus gostergesi ---")
    from src.world.rooms import chapter05 as rooms
    scene = make_scene(game, 5)
    tx, ty = rooms.VALVE_LOW_TILE
    scene.player.body.set_feet(tx * TILE_SIZE + 4, (ty + 1) * TILE_SIZE)
    idle(game, scene, 3)
    check(scene.prompts.active("valve"), "vananin ustunde gosterge")
    scene.player.body.set_feet(tx * TILE_SIZE + 200, (ty + 1) * TILE_SIZE)
    idle(game, scene, 30)
    check(not scene.prompts.active("valve") and not scene.prompts._prompts,
          "uzaklasinca gosterge soner ve silinir")
    surface = pygame.Surface((480, 270))
    game.input.last_device = "keyboard"
    scene.prompts.offer("x", 100, 100)
    scene.prompts.update(game.input)
    scene.prompts.draw(surface, (0, 0), game.input, 0)
    check(surface.get_bounding_rect().width > 0, "gosterge cizim uretiyor")


def main() -> int:
    game = Game()
    test_placement(game)
    test_trade(game)
    test_refund(game)
    test_projectiles_visible(game)
    test_prompts(game)
    game.shutdown()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for label in failures:
            print("  - " + label)
        return 1
    print("Dukkanlar, iade ve tus gostergeleri calisiyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
