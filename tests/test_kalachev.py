"""Kalachev - `docs/kalachev.md`.



Arda: *"Rey ve Ardo'ya gore cok daha agresif olsa, direkt dusmanlara

saldiran cinsten."*



Korunan kurallar:



  * **`Companion` DEGIL.** Ondan turetilseydi `hold()`, `release()`,

    tasma mantigi miras kalirdi ve Kalachev ikinci bir Ardo olurdu -

    B10-B15'in yalnizligi iptal olurdu (belgenin en onemli karari).

  * Tell **okumuyor**, mesafe **kapatiyor**, kacinmasi **yok**.

  * Vurulunca **durmuyor** - poise cok yuksek.

  * Kalici olarak **olmuyor**: cani bitince cekiliyor. Olumu senaryolu

    ve B18'e ait; rastgele bir Suruklenen'in onu oldurmesi finalin

    agirligini calardi.

  * Bolum basina **bir kez**.

  * Silueti Ardo'ya **benzemiyor** - ikisi de agir yapili ve ikisi de

    yaninda dovusuyor; oyuncu uzaktan ayirt etmeli.



Calistir:

    python tests/test_kalachev.py

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



from src.core.game import Game  # noqa: E402

from src.entities.companion import Companion  # noqa: E402

from src.entities.kalachev import (  # noqa: E402

    ATTACK_RANGE, DEFAULT_STAY, SIGHT, Kalachev,

)

from src.scenes.chapter02 import Chapter02Scene  # noqa: E402



failures: list[str] = []





def check(condition: bool, label: str, detail: str = "") -> None:

    print(("OK " if condition else "!! ") + label

          + (f"  ({detail})" if detail else ""))

    if not condition:

        failures.append(label)





def main() -> int:

    game = Game()

    game.settings.save = lambda *a, **k: None    # type: ignore[method-assign]



    def fresh() -> Chapter02Scene:

        game.scenes.set_root(Chapter02Scene, transition=False,

                             character="rey")

        game.scenes._flush()

        scene = game.scenes.current

        scene.enemies.clear()

        return scene



    # --- 1. Companion DEGIL -------------------------------------------------

    print("--- Companion degil ---")

    check(not issubclass(Kalachev, Companion),

          "`Companion`dan TUREMIYOR - ikinci bir Ardo olmuyor")

    for banned in ("hold", "release", "assist", "downed"):

        check(not hasattr(Kalachev, banned),

              f"`{banned}` miras alinmadi - emir verilemiyor")



    # --- 2. Agresif: tell yok, mesafe kapatiyor ----------------------------

    print("\n--- agresiflik ---")

    scene = fresh()

    ally = scene.summon_kalachev(scene.player.body.center_x,

                                 scene.player.body.feet[1])

    check(ally is not None, "sahneye girdi")

    check(scene.summon_kalachev(0, 0) is None,

          "BOLUM BASINA BIR KEZ - ikincisi ilkini ucuzlatirdi")

    check(ally not in scene.enemies, "`enemies` listesinde DEGIL")



    # Uzaga bir dusman koy: mesafeyi kapatmali.

    from src.entities.enemies.shambler import Shambler

    far_x = ally.body.center_x + SIGHT * 0.7

    enemy = Shambler(scene, far_x, ally.body.feet[1])

    enemy.echo_visible = True

    scene.enemies.append(enemy)



    start = ally.body.center_x

    for _ in range(90):

        ally.update()

        enemy.body.set_feet(far_x, ally.body.feet[1])   # dusman sabit

    check(ally.body.center_x > start,

          "dusmana dogru MESAFE KAPATIYOR", f"{start:.0f} -> {ally.body.center_x:.0f}")



    # Menzile girince vuruyor - **tell beklemeden**.

    ally.body.set_feet(enemy.body.center_x - ATTACK_RANGE * 0.5,

                       ally.body.feet[1])

    scene.hitboxes.boxes.clear()

    ally.attack_frames = 0

    ally.update()

    boxes = [b for b in scene.hitboxes.boxes if b.owner is ally]

    check(bool(boxes), "menzilde ANINDA vuruyor - tell yok",

          f"{len(boxes)} hitbox")

    if boxes:

        check(boxes[0].targets & scene.enemies[0].team,

              "vurusu dusmanlari hedefliyor")



    # --- 3. Vurulunca DURMUYOR ---------------------------------------------

    print("\n--- vurulunca durmuyor ---")

    check(Kalachev.poise >= 30,

          "poise cok yuksek - sendelemiyor", str(Kalachev.poise))

    from src.entities.player import Player

    check(Kalachev.poise > Player.poise if hasattr(Player, "poise") else True,

          "oyuncudan daha dayanikli")



    # --- 4. Kalici olarak OLMUYOR ------------------------------------------

    print("\n--- olmuyor, cekiliyor ---")

    scene = fresh()

    ally = scene.summon_kalachev(scene.player.body.center_x,

                                 scene.player.body.feet[1])

    from src.combat.hitbox import Hitbox, Team

    box = Hitbox(rect=ally.body.rect.copy(), owner=None,

                 targets=Team.PLAYER, damage=9999, active_frames=2)

    ally.take_damage(box, (1.0, 0.0))

    check(ally.health > 0, "cani sifira DUSMUYOR", str(ally.health))

    check(ally.leaving, "cani bitince CEKILIYOR - olmuyor")

    check(not getattr(ally, "dead", False), "olu isaretlenmedi")



    for _ in range(80):

        ally.update()

    check(ally.gone, "cekilme tamamlaniyor")

    scene.update()

    check(ally not in scene.allies, "sahneden temizleniyor")



    # --- 5. Suresi dolunca gidiyor -----------------------------------------

    print("\n--- kalici degil ---")

    scene = fresh()

    ally = scene.summon_kalachev(scene.player.body.center_x,

                                 scene.player.body.feet[1], stay=30)

    for _ in range(40):

        ally.update()

    check(ally.leaving, "sure dolunca kendiliginden cekiliyor")

    check(DEFAULT_STAY < 60 * 60,

          "varsayilan kalis suresi bir dakikadan KISA - yoldas degil",

          f"{DEFAULT_STAY} kare")



    # --- 6. Silueti Ardo'ya benzemiyor -------------------------------------

    # Ikisi de agir yapili ve ikisi de yaninda dovusuyor; oyuncu

    # uzaktan hangisinin geldigini anlamali (CLAUDE.md 6, siluet testi).

    print("\n--- siluet ayrisiyor ---")

    import numpy as np

    from src.art.animation import CHARACTERS

    from src.art.animator import Animator



    def shape(name: str) -> tuple[int, int, int]:

        anim = Animator(name)

        anim.play("idle")

        anim.update()

        alpha = pygame.surfarray.array_alpha(anim.render(1))

        cols, rows = np.nonzero(alpha)

        return (int(rows.max() - rows.min() + 1),

                int(cols.max() - cols.min() + 1),

                int(np.count_nonzero(alpha)))



    k_h, k_w, k_mass = shape("kalachev")

    a_h, a_w, a_mass = shape("ardo")

    check(k_h <= 32, "CLAUDE.md 6: 32 piksel siniri", f"{k_h}px")

    check((k_h, k_w) != (a_h, a_w),

          "olculeri Ardo'dan farkli", f"kalachev {k_h}x{k_w}  ardo {a_h}x{a_w}")



    spec_k = CHARACTERS["kalachev"]

    spec_a = CHARACTERS["ardo"]

    check(spec_k.hood and not spec_a.hood,

          "KUKULETA yalnizca Kalachev'de - siluet isareti")

    check(spec_a.cape and not spec_k.cape,

          "PELERIN yalnizca Ardo'da - onun isareti")

    check(spec_k.weapon != spec_a.weapon,

          "farkli silah - siluetten disari tasan sekil farkli",

          f"{spec_k.weapon} / {spec_a.weapon}")

    check(spec_k.hunch > spec_a.hunch,

          "Kalachev kambur, Ardo dimdik",

          f"{spec_k.hunch} > {spec_a.hunch}")




    # --- YERLESTIRME (docs/kalachev.md 5) ---------------------------------
    print("\n--- bolumlere yerlestirme ---")

    import inspect as _inspect
    import json as _json

    # B4: iskelet ONUN degil, yoldasinin. Kod bir donem tersini
    # soyluyordu - panel "iskeletin sahibi" deyip onun yuzunu
    # gosteriyordu, yani onu olu ilan ediyordu. Ama Kalachev B5'te
    # goruluyor ve B18'de oluyor.
    _lang = _json.loads(
        (ROOT / "src" / "ui" / "lang" / "tr.json").read_text(encoding="utf-8"))
    camp = _lang["line"]["ch04_echo_name"]
    check("değil" in camp,
          "B4: iskelet Kalachev'in DEGIL - replik bunu soyluyor", camp)

    # B5: ilk gorus.
    from src.config import TILE_SIZE as _TILE
    from src.scenes.chapter05 import (
        SIGHTING_NEAR_TILES, SIGHTING_PACK_OFFSETS, SIGHTING_ROW)
    from src.world.rooms.chapter05 import WATER_HIGH
    check(SIGHTING_ROW * _TILE < WATER_HIGH + 32,
          "B5: dovus CIKINTIDA - zeminde olsa suru bogulurdu",
          f"satir {SIGHTING_ROW}")
    check(SIGHTING_NEAR_TILES < 15,
          "B5: tetik ekran yarim genisliginden dar - olay GORULUYOR",
          f"{SIGHTING_NEAR_TILES} < 15 tile")
    check(len(SIGHTING_PACK_OFFSETS) >= 3,
          "B5: bir SURU var, tek dusman degil",
          str(len(SIGHTING_PACK_OFFSETS)))

    # B10: tuzagi o kiriyor - ve oyuncu DUSMUYOR.
    from src.scenes.chapter10 import (
        ALLY_TRAP_COLUMN, ALLY_TRIGGER_TILES, Chapter10Scene)
    from src.world.rooms.chapter10 import TRAP_TILES
    check(ALLY_TRAP_COLUMN in TRAP_TILES,
          "B10: tuzagin uzerinde beliriyor", str(ALLY_TRAP_COLUMN))
    check(ALLY_TRIGGER_TILES < 15,
          "B10: tetik gorus mesafesinde", f"{ALLY_TRIGGER_TILES} tile")
    src10 = _inspect.getsource(Chapter10Scene)
    check("self.trap_broken" in src10 and "self.trap_sprung" in src10,
          "B10: 'kirildi' ve 'oyuncu dustu' AYRI bayraklar")
    check("sprung=self.trap_sprung" in src10,
          "B10: bolum sonu sahnesi hala 'dustun mu' diye soruyor")

    # Muttefikin kesim sayaci gercekten artiyor mu.
    from src.scenes.play import PlayScene as _PS
    check("box.owner in self.allies" in _inspect.getsource(_PS.on_hit),
          "muttefik kesim sayaci BAGLI - `kills` bir donem hic artmiyordu")

    # B6: tanisma. Ardo dusuyor, ucunu biciyor - Kalachev de orada.
    from src.scenes.chapter06 import Chapter06Scene
    src06 = _inspect.getsource(Chapter06Scene)
    check("summon_kalachev" in src06 and "_rescue" in src06,
          "B6: kurtarma aninda beliriyor - tanisma sahnesi")

    # B12: Ardo'nun izlerinin yaninda ONUN izleri de var.
    from src.world.rooms.chapter12 import MARKS
    kinds = [m[4] for m in MARKS]
    check("pair" in kinds, "B12: 'iki kisinin izi' isareti haritada",
          str(kinds))
    check(kinds.count("pair") == 1,
          "B12: bir tane - ikincisi bir olayi bir dokuya cevirirdi")

    # B13: yara GORUNUR kaliyor - ve bunu ekranda kanitliyoruz.
    from src.entities.kalachev import WOUND_FLAG, Kalachev as _K
    from src.art.animator import Animator as _An
    from src.art import palette as _pal

    def _shot(facing: int, wounded: bool):
        anim = _An("kalachev"); anim.play("idle"); anim.update()
        image = anim.render(facing).copy()
        if wounded:
            fake = type("F", (), {"facing": facing, "wounded": True})()
            _K._blit_wound(fake, image)
        return image

    clean, hurt = _shot(1, False), _shot(1, True)
    size = clean.get_size()
    changed = [(x, y) for y in range(size[1]) for x in range(size[0])
               if clean.get_at((x, y)) != hurt.get_at((x, y))]
    check(len(changed) >= 5, "B13: yara EKRANDA - sprite degisiyor",
          f"{len(changed)} piksel")
    bloods = {_pal.color("blood_bright"), _pal.color("blood_dark")}
    check(all(hurt.get_at(pos)[:3] in bloods for pos in changed),
          "yara kan renginde - palet disi renk yok")
    check(all(clean.get_at(pos)[3] > 0 for pos in changed),
          "yara GOVDENIN uzerinde - havada leke yok")

    mirrored = _shot(-1, True)
    left = [(x, y) for y in range(size[1]) for x in range(size[0])
            if _shot(-1, False).get_at((x, y)) != mirrored.get_at((x, y))]
    check({(size[0] - 1 - x, y) for x, y in left} == set(changed),
          "yon degisince yara da AYNALANIYOR - adamla birlikte donuyor")

    check("KALACHEV_WOUND_FLAG"
          in _inspect.getsource(_PS.summon_kalachev),
          "yara KAYITTAN okunuyor - her bolum ayri satir yazmiyor")

    game.shutdown()



    print("\n=== SONUC ===")

    if failures:

        print(f"{len(failures)} BASARISIZ:")

        for item in failures:

            print(f"  - {item}")

        return 1

    print("Kalachev: agresif, gecici, yoldas degil.")

    return 0





raise SystemExit(main())

