"""Yetenek agaci dogrulamasi - `src/systems/skilltree.py`.

Arda (25.09.2026): *"Yetenek agacini bolume yayilmis puanlar olarak
tekrar yap. Yeni hareketler versin."* Buradaki kontroller kodun
calistigini degil, agacin bir **secim** olmaya devam ettigini koruyor:

  * Sekil - karakter basina uc dal, bes kademe, 3. kademe iki dugumlu secim
  * Onkosul - kademe atlanamaz; secim kademesinin IKISI de onkosul sayilir
  * Secim - biri alininca oteki kalici kilitleniyor
  * Karakter - Ardo YANKI'yi, Rey IZ'i alamiyor
  * Puan kaynaklari - bolume yayilmis, her kaynak BIR kez, eski kayda geri
    doldurma bir kez
  * Butce - agac asla tamamlanamiyor
  * Etkiler carpan/bonus - `docs/dovus-sistemi.md`'nin taban degerlerine
    dokunulmuyor (CLAUDE.md 7)
  * ESKI KAYIT - `skill_points`/`skills` alanlarini hic bilmeyen bir kayit
    sorunsuz aciliyor, eski anahtarlar yasiyor

Pygame'e ihtiyaci yok: agac saf mantik, kayit saf veri.

Calistir:
    python tests/test_skilltree.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA.** (08.09.2026) - bkz. test_combat.py.
import tempfile  # noqa: E402

os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.systems.save import SaveData as _SaveData  # noqa: E402
from src.systems.save import write_save as _write_save  # noqa: E402

_write_save(_SaveData())

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    ARDO_CHAIN_WINDOW, CHAIN_WINDOW_FRAMES, COMBO_THRESHOLD_MID,
    DODGE_IFRAMES, DODGE_TOTAL_FRAMES, REY_CHAIN_WINDOW, REY_DODGE_CHARGES,
    REY_MAX_HEALTH, SKILL_BRANCH_LEVELS, SKILL_COST_BY_LEVEL,
    SKILL_POINT_CHAPTERS,
)
from src.systems import skilltree as tree  # noqa: E402
from src.systems.echo import COMBO_TO_RESTORE  # noqa: E402
from src.systems.save import SaveData  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def near(value: float, want: float) -> bool:
    return abs(value - want) < 1e-6


# --- Sahte oyuncu -----------------------------------------------------------
# Kosullu etkiler oyuncunun O ANKI durumuna bakiyor (charms.py deseni).
class FakeCombo:
    def __init__(self, count: int = 0) -> None:
        self.count = count


class FakeSense:
    def __init__(self, active: bool = True) -> None:
        self.active = active


class FakeScene:
    def __init__(self, echo=None, tracking=None) -> None:
        self.echo = echo
        self.tracking = tracking


class FakePlayer:
    def __init__(self, combo: int = 0, echo=None, tracking=None) -> None:
        self.combo = FakeCombo(combo)
        self.scene = FakeScene(echo, tracking)


def fresh(points: int = 0, character: str = "rey", chapter: int = 1) -> SaveData:
    return SaveData(character=character, skill_points=points, chapter=chapter)


def branch(key: str) -> tree.Branch:
    return next(b for b in tree.BRANCHES if b.key == key)


def check_shape() -> None:
    print("--- sekil: karakter basina 3 dal x 5 kademe ---")
    check(len(tree.BRANCHES) == 4, "dort dal (ikisi ortak, biri Rey'in, biri Ardo'nun)",
          str([b.key for b in tree.BRANCHES]))
    for character in ("rey", "ardo"):
        keys = [b.key for b in tree.branches_for(character)]
        check(len(keys) == 3, f"{character}: uc dal goruyor", str(keys))
    check([b.key for b in tree.branches_for("rey")] == ["blade", "echo", "stone"],
          "Rey: KESKIN, YANKI, TAS")
    check([b.key for b in tree.branches_for("ardo")] == ["blade", "trace", "stone"],
          "Ardo: KESKIN, IZ, TAS - YANKI'nin yerinde IZ")
    for b in tree.BRANCHES:
        check(len(b.tiers) == SKILL_BRANCH_LEVELS, f"{b.key}: bes kademe",
              str(len(b.tiers)))
        sizes = [len(tier) for tier in b.tiers]
        check(sizes == [1, 1, 2, 1, 1], f"{b.key}: 3. kademe iki dugumlu SECIM",
              str(sizes))
        costs = [tier[0].cost for tier in b.tiers]
        check(costs == list(SKILL_COST_BY_LEVEL), f"{b.key}: bedel 1+1+2+2+3",
              str(costs))
        check(all(n.cost == b.tiers[2][0].cost for n in b.tiers[2]),
              f"{b.key}: secimin iki yolu ayni bedel")
        check(b.cost == 9, f"{b.key}: dal 9 puan", str(b.cost))
    check(len(tree.NODES) == 24, "yirmi dort dugum, hepsi benzersiz",
          str(len(tree.NODES)))
    check(tree.TOTAL_COST == 27, "bir karakterin agaci 27 puan",
          str(tree.TOTAL_COST))

    # Eski on iki anahtar AYNEN yasiyor - eski kayitlar yeteneklerini
    # kaybetmesin.
    legacy = ("blade_edge", "blade_flow", "blade_momentum", "blade_finisher",
              "echo_reach", "echo_ward", "echo_grip", "echo_mend",
              "stone_hide", "stone_guard", "stone_roll", "stone_will")
    check(all(key in tree.NODES for key in legacy),
          "eski 12 anahtarin hepsi agacta")

    # Her dal en az iki yeni HAREKET veriyor - Arda'nin istegi.
    for b in tree.BRANCHES:
        moves = [n.key for n in b.nodes if n.is_move]
        check(len(moves) >= 2, f"{b.key}: en az iki yeni hareket", str(moves))
    for b in tree.BRANCHES:
        check(b.tiers[4][0].is_move, f"{b.key}: dalin sonu bir hareket",
              b.tiers[4][0].key)


def check_budget() -> None:
    print("\n--- butce: bolume yayilmis puan, tamamlanamayan agac ---")
    check(len(SKILL_POINT_CHAPTERS) == 9, "dokuz bolum sonu puan veriyor",
          str(SKILL_POINT_CHAPTERS))
    check(tree.GUARANTEED_POINTS == 10, "garanti puan 10 (9 bolum + B4 kampi)",
          str(tree.GUARANTEED_POINTS))
    spread = sorted(SKILL_POINT_CHAPTERS)
    gaps = [b - a for a, b in zip(spread, spread[1:])]
    check(max(gaps) <= 3, "puansiz bolum araligi en fazla 2 bolum",
          str(gaps))
    best = tree.GUARANTEED_POINTS + 1         # + B15 hayalet
    check(best < tree.TOTAL_COST, "butce agaci ASLA tamamlamaya yetmiyor",
          f"{best} < {tree.TOTAL_COST}")
    check(best >= 9 + 2, "bir dal dibe + bir dalin ilk iki kademesi sigiyor",
          str(best))


def check_prerequisites() -> None:
    print("\n--- onkosul: kademe atlanamaz ---")
    save = fresh(points=99)
    check(tree.can_unlock(save, tree.BLADE_EDGE), "kademe 1 puan varken alinabilir")
    check(not tree.can_unlock(save, tree.BLADE_FLOW), "kademe 2 alinamaz - 1 kapali")
    check(not tree.unlock(save, tree.BLADE_DASH), "onkosulsuz unlock reddediliyor")
    check(save.skill_points == 99 and not save.skills,
          "reddedilen unlock hicbir sey degistirmedi")
    tree.unlock(save, tree.BLADE_EDGE)
    tree.unlock(save, tree.BLADE_FLOW)
    check(tree.can_unlock(save, tree.BLADE_DASH)
          and tree.can_unlock(save, tree.BLADE_HOVER),
          "kademe 2 acilinca secimin iki yolu da alinabilir")
    check(not tree.can_unlock(save, tree.BLADE_MOMENTUM),
          "kademe 4 secim yapilmadan alinamaz")

    print("\n--- secim: biri alininca oteki kilitlenir ---")
    check(tree.rival(tree.BLADE_DASH).key == tree.BLADE_HOVER,
          "Hamle'nin rakibi Havada Asili")
    check(tree.rival(tree.BLADE_EDGE) is None, "tek dugumlu kademede rakip yok")
    check(tree.unlock(save, tree.BLADE_HOVER), "Havada Asili alindi")
    check(tree.rival_taken(save, tree.BLADE_DASH), "Hamle artik secilmedi")
    check(not tree.can_unlock(save, tree.BLADE_DASH)
          and not tree.unlock(save, tree.BLADE_DASH),
          "puan bol olsa da Hamle ALINAMIYOR")
    check(tree.can_unlock(save, tree.BLADE_MOMENTUM),
          "secimin HANGI yolu alinmissa 4. kademe onun ustune acilir")
    other = fresh(points=99)
    for key in (tree.BLADE_EDGE, tree.BLADE_FLOW, tree.BLADE_DASH):
        tree.unlock(other, key)
    check(tree.can_unlock(other, tree.BLADE_MOMENTUM),
          "oteki yoldan da 4. kademeye iniliyor")
    tree.unlock(save, tree.BLADE_MOMENTUM)
    check(tree.unlock(save, tree.BLADE_FINISHER), "dalin sonuna inildi")
    check(tree.unlocked_nodes(save)[-1].key == tree.BLADE_FINISHER,
          "unlocked_nodes agac sirasinda")
    check(not tree.can_unlock(save, tree.STONE_GUARD),
          "bir daldaki ilerleme digerinin onkosulunu saymiyor")


def check_characters() -> None:
    print("\n--- karakter: dallar kime ait ---")
    rey = fresh(points=20, character="rey")
    ardo = fresh(points=20, character="ardo")
    check(tree.branch_usable(rey, tree.BRANCH_ECHO)
          and not tree.branch_usable(rey, tree.BRANCH_TRACE),
          "Rey YANKI'yi goruyor, IZ'i gormuyor")
    check(tree.branch_usable(ardo, tree.BRANCH_TRACE)
          and not tree.branch_usable(ardo, tree.BRANCH_ECHO),
          "Ardo IZ'i goruyor, YANKI'yi gormuyor")
    check(not tree.can_unlock(ardo, tree.ECHO_REACH)
          and not tree.unlock(ardo, tree.ECHO_REACH),
          "Ardo YANKI dugumu ACAMIYOR (puani bosa gitmesin)")
    check(not tree.can_unlock(rey, tree.TRACE_EYE), "Rey IZ dugumu acamiyor")
    check(tree.unlock(ardo, tree.TRACE_EYE), "Ardo IZ'in ilk kademesini aciyor")
    for key in (tree.BRANCH_BLADE, tree.BRANCH_STONE):
        check(tree.branch_usable(rey, key) and tree.branch_usable(ardo, key),
              f"{key} dali iki karakterde de")


def check_accounting() -> None:
    print("\n--- puan muhasebesi ---")
    save = fresh(points=1)
    check(tree.unlock(save, tree.STONE_HIDE), "1 puanla kademe 1")
    check(tree.available_points(save) == 0 and tree.spent_points(save) == 1,
          "puan dustu, harcanan 1")
    check(not tree.unlock(save, tree.STONE_GUARD), "puansiz unlock reddedildi")
    check(save.skills == [tree.STONE_HIDE], "reddedilen unlock kaydi kirletmedi")
    tree.grant_points(save, 2)
    tree.unlock(save, tree.STONE_GUARD)
    check(not tree.can_unlock(save, tree.STONE_RALLY),
          "1 puan 2 puanlik secim dugumune yetmiyor")
    tree.grant_points(save, 1)
    check(tree.unlock(save, tree.STONE_RALLY), "2 puan yeter")
    check(tree.spent_points(save) == 4 and tree.available_points(save) == 0,
          "muhasebe tutuyor", str(tree.spent_points(save)))


def check_awards() -> None:
    print("\n--- puan kaynaklari: her biri BIR kez ---")
    save = fresh()
    check(tree.award(save, "deneme") == 1 and save.skill_points == 1,
          "ilk kez puan veriyor")
    check(tree.award(save, "deneme") == 0 and save.skill_points == 1,
          "ayni kaynak ikinci kez vermiyor (bolumu yeniden oynamak)")
    check(tree.award_chapter(save, 3) == 1, "B3 sonu puan veriyor")
    check(tree.award_chapter(save, 3) == 0, "B3 ikinci kez vermiyor")
    check(tree.award_chapter(save, 5) == 0, "B5 listede degil - puan yok")
    check(tree.award_chapter(save, 0) == 0, "bolum numarasi yoksa puan yok")
    total = sum(tree.award_chapter(fresh(), c) for c in range(1, 19))
    check(total == len(SKILL_POINT_CHAPTERS), "bolum sonlari toplam 9 puan",
          str(total))

    print("\n--- eski kayda geri doldurma ---")
    old = fresh(chapter=7)
    got = tree.backfill(old)
    check(got == 3, "B7'deki eski kayit: B3 + B6 + B4 kampi", str(got))
    check(tree.backfill(old) == 0, "ikinci cagri hicbir sey vermiyor")
    check(tree.award_chapter(old, 6) == 0,
          "geri doldurulan bolumun sonu tekrar puan vermiyor")

    rested = fresh(chapter=7)
    rested.flags["ch04_rested"] = True
    rested.skill_points = 1                    # eski kod kampta verdi
    got = tree.backfill(rested)
    check(got == 2 and rested.skill_points == 3,
          "kampta dinlenmis kayit o puani ZATEN aldi - yalniz B3 + B6",
          f"{got} / {rested.skill_points}")
    check(tree.award(rested, tree.SOURCE_B4_CAMP) == 0,
          "B4 kampi bir daha vermiyor")

    check(tree.backfill(fresh(chapter=1)) == 0, "yeni oyun: geri doldurma yok")
    check(tree.backfill(fresh(chapter=4)) == 1, "B4'e gelen kayit: yalniz B3")
    late = fresh(chapter=18)
    late.flags["ch04_rested"] = True
    late.flags["ch15_ghost"] = True
    check(tree.backfill(late) == 10,
          "B18: dokuz bolum sonu + hayalet (kamp zaten alinmis)",
          str(late.skill_points))
    scene_ahead = fresh(chapter=3)
    check(tree.backfill(scene_ahead, current_chapter=7) == 3,
          "sahnenin bolumu kayittan ilerideyse o sayiliyor")


def check_effects() -> None:
    print("\n--- etkiler: carpanlar ---")
    idle = FakePlayer()
    check(near(tree.damage_scale([], idle), 1.0), "bos liste notr")
    check(near(tree.damage_scale(["yok_boyle"], idle), 1.0),
          "bilinmeyen anahtar yok sayiliyor")
    check(near(tree.damage_scale([tree.BLADE_EDGE], idle), 1.12), "BILEME %12")
    low = FakePlayer(combo=COMBO_THRESHOLD_MID - 1)
    high = FakePlayer(combo=COMBO_THRESHOLD_MID)
    check(near(tree.damage_scale([tree.BLADE_MOMENTUM], low), 1.0),
          "IVME esigin altinda notr")
    check(near(tree.damage_scale([tree.BLADE_MOMENTUM], high), 1.20),
          "IVME 10+ combo'da %20")
    both = tree.damage_scale([tree.BLADE_EDGE, tree.BLADE_MOMENTUM], high)
    check(near(both, 1.12 * 1.20), "carpanlar CARPILARAK birlesiyor",
          f"{both:.4f}")
    check(near(tree.damage_scale([tree.BLADE_FINISHER, tree.BLADE_DASH], high),
               1.0), "hareket dugumleri hasar carpani DEGIL - hareket")

    tracking_on = FakePlayer(tracking=FakeSense(True))
    tracking_off = FakePlayer(tracking=FakeSense(False))
    check(near(tree.damage_scale([tree.TRACE_READ], tracking_on), 1.15)
          and near(tree.damage_scale([tree.TRACE_READ], tracking_off), 1.0),
          "IZ OKUMA yalniz Iz acikken %15")
    check(near(tree.defence_scale([tree.TRACE_PATIENCE], tracking_on), 0.88)
          and near(tree.defence_scale([tree.TRACE_PATIENCE], idle), 1.0),
          "AVCI SABRI yalniz Iz acikken %12 koruma")
    check(near(tree.trace_range_scale([tree.TRACE_EYE]), 1.25)
          and near(tree.trace_range_scale([]), 1.0), "KESKIN GOZ iz menzili %25")

    print("\n--- etkiler: savunma ---")
    check(near(tree.defence_scale([tree.STONE_GUARD], idle), 0.92), "KORUMA %8")
    check(near(tree.defence_scale([tree.STONE_WILL], idle), 0.92), "IRADE %8")
    check(tree.defence_scale([tree.STONE_GUARD, tree.STONE_WILL,
                              tree.ECHO_WARD],
                             FakePlayer(echo=FakeSense(True))) > 0.7,
          "yigilma dokunulmazliga gitmiyor")
    check(near(tree.defence_scale([tree.ECHO_WARD], idle), 1.0)
          and near(tree.defence_scale([tree.ECHO_WARD],
                                      FakePlayer(echo=FakeSense(False))), 1.0)
          and near(tree.defence_scale([tree.ECHO_WARD],
                                      FakePlayer(echo=FakeSense(True))), 0.88),
          "SIPER yalniz Yanki acikken %12")
    seer = FakePlayer(echo=FakeSense())
    check(near(tree.echo_sight_scale([tree.ECHO_REACH, tree.ECHO_GRIP], seer),
               1.25 * 1.30)
          and near(tree.echo_sight_scale([tree.ECHO_REACH], idle), 1.0),
          "ERIM + KAVRAYIS carpiliyor; Yanki'siz notr")

    print("\n--- etkiler: duz bonuslar ---")
    check(tree.max_health_bonus([tree.STONE_HIDE, tree.STONE_WILL]) == 20,
          "POST + IRADE = +20 can")
    check(tree.chain_window_bonus([tree.BLADE_FLOW]) == 2, "AKIS +2 kare")
    check(tree.dodge_charge_bonus([tree.STONE_ROLL]) == 1, "YUVARLANMA +1 sarj")
    check(COMBO_TO_RESTORE - tree.restore_combo_reduction([tree.ECHO_MEND])
          == 14, "ONARIM: Yanki 20 yerine 14 combo'da")

    print("\n--- taban degerler yerinde (CLAUDE.md 7) ---")
    check(CHAIN_WINDOW_FRAMES == 12, "zincir penceresi tabani 12 kare")
    check(REY_CHAIN_WINDOW == 14 and ARDO_CHAIN_WINDOW == 10,
          "Rey 14 / Ardo 10 - AKIS bunlari yeniden yazmiyor")
    check(DODGE_IFRAMES == 6 and DODGE_TOTAL_FRAMES == 18, "kacinma 6/18 kare")
    check(REY_MAX_HEALTH == 80 and REY_DODGE_CHARGES == 2,
          "Rey'in taban can/sarj degerleri yerinde")
    check(all(n.chain_window >= 0 and n.max_health >= 0 and n.dodge_charges >= 0
              for n in tree.NODES.values()),
          "hicbir yetenek taban degeri DUSURMUYOR")


def check_save() -> None:
    print("\n--- kayit ---")
    save = fresh(points=3)
    tree.unlock(save, tree.BLADE_EDGE)
    tree.unlock(save, tree.BLADE_FLOW)
    tree.award(save, "deneme")
    back = SaveData.from_dict(json.loads(json.dumps(save.to_dict())))
    check(back.skills == save.skills and back.skill_points == save.skill_points,
          "JSON gidip donuyor")
    check(tree.award(back, "deneme") == 0,
          "kaynak bayragi diske yaziliyor - yukleyince ikinci puan yok")
    legacy = {
        "version": 1, "chapter": 3, "chapter_name": "chapter.torch_crypt",
        "character": "rey", "gold": 210, "max_health": 80, "health": 62,
        "abilities": ["sword", "dodge"], "charms": ["bloody_whet"],
        "weapon": "sword", "echo_tier": 2, "best_combo": 17,
    }
    old = SaveData.from_dict(legacy)
    check(old.skill_points == 0 and old.skills == [],
          "eski kayit aciliyor - yeni alanlar varsayilana dusuyor")
    ghost = SaveData.from_dict({**legacy, "skills": ["kaldirilmis"],
                                "skill_points": 2})
    check(tree.spent_points(ghost) == 0 and tree.available_points(ghost) == 2,
          "tanimadigimiz anahtar sayilmiyor, etkileri bozmuyor")
    veteran = SaveData.from_dict({**legacy, "skills": ["blade_edge"]})
    check(tree.unlocked(veteran, tree.BLADE_EDGE)
          and near(tree.damage_scale(veteran.skills, FakePlayer()), 1.12),
          "eski agacin anahtari yeni agacta calisiyor")


def main() -> int:
    check_shape()
    check_budget()
    check_prerequisites()
    check_characters()
    check_accounting()
    check_awards()
    check_effects()
    check_save()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Yetenek agaci belgedeki kurallara uyuyor.")
    return 0


raise SystemExit(main())
