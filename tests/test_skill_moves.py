"""Yetenek agacinin HAREKETLERI - gercek oyun dongusunde olculuyor.

Arda (25.09.2026): *"Yeni hareketler versin."* `test_skilltree.py` agacin
mantigini (kim neyi alabilir) olcuyor; burasi acilan dugumun oyunda
gercekten bir sey DEGISTIRDIGINI:

    Hamle          kosarken saldiri daha uzaga, daha agir gidiyor
    Havada Asili   havada vururken dusus yavasliyor
    Kilic Dalgasi  bitirici ucan bir kesik firlatiyor
    Sarsilmaz      hafif darbe zinciri bozmuyor, agir darbe bozuyor
    Toparlanma     yenen darbenin bir kismi karsilik vurunca geri geliyor
    Pusu           arkadan vurus x1.5, yuzune degil
    Sessiz Adim    sessiz yuruyus hizlaniyor, dusman gec fark ediyor
    Yanki Darbesi  Yanki'yi acmak iten bir halka birakiyor (bekleme var)
    Ayi Kukremesi  Ardo'da ayni hareket Iz ile
    Yalan Sezgisi  Yanki yalan soyleyince kolye urperiyor

Ayrica oyuncu affi ve yeni esya:

    Eski Kalkan    ilk darbeyi karsilayip kiriliyor; kacinmada harcanmiyor
    Son sans       %15 altinda oldurucu darbe 1 can birakiyor, bolumde bir kez
    Oyun ortasi    duraklat menusunden acilan dugum HEMEN biniyor

Calistir:
    python tests/test_skill_moves.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# **Oyuncunun kaydina DOKUNMA** - bkz. test_combat.py.
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.systems.save import SaveData, write_save  # noqa: E402

write_save(SaveData())

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.combat.combo import AttackPhase  # noqa: E402
from src.combat.hitbox import Hitbox, Team  # noqa: E402
from src.config import (  # noqa: E402
    ENEMY_SIGHT_RANGE, PLAYER_SNEAK_RATIO, SHIELD_IFRAMES,
    SKILL_AMBUSH_SCALE, SKILL_BURST_COOLDOWN, SKILL_BURST_SIZE,
    SKILL_DASH_COOLDOWN, SKILL_DASH_LUNGE, SKILL_HOVER_FALL_SPEED,
    SKILL_QUIET_SIGHT_SCALE, SKILL_QUIET_SNEAK_RATIO, SKILL_RALLY_FRAMES,
    SKILL_RALLY_POOL_RATIO,
)
from src.core.game import Game  # noqa: E402
from src.entities.enemies.shambler import Shambler  # noqa: E402
from src.scenes.combat_room import CombatRoomScene  # noqa: E402
from src.systems import abilities, consumables, skilltree  # noqa: E402
from src.systems.echo import Answer  # noqa: E402

KEY_ATTACK = pygame.K_j
KEY_JUMP = pygame.K_SPACE
KEY_RIGHT = pygame.K_RIGHT
KEY_LEFT = pygame.K_LEFT
KEY_SNEAK = pygame.K_LCTRL
KEY_ECHO = pygame.K_q

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


class Harness:
    """Kare kare kontrol edilen dovus odasi. Dusmanlar temizleniyor."""

    def __init__(self, character: str = "rey") -> None:
        self.game = Game()
        self.sounds: list[str] = []
        original = self.game.play_sound

        def record(name, *args, **kwargs):
            self.sounds.append(name)
            return original(name, *args, **kwargs)

        self.game.play_sound = record
        self.game.scenes.set_root(CombatRoomScene, transition=False,
                                  character=character)
        self.game.scenes._flush()
        self.scene = self.game.scenes.current
        self.scene.enemies = []
        self.player = self.scene.player
        self.player.grant(abilities.SWORD)
        self.player.grant(abilities.DODGE)
        self.held: set[int] = set()

    def learn(self, *keys: str) -> None:
        self.player.apply_skills(set(self.player.skills) | set(keys))
        self.scene.refresh_skills()

    def step(self, press: tuple[int, ...] = (), release: tuple[int, ...] = (),
             count: int = 1) -> None:
        for index in range(count):
            self.game.input.begin_frame()
            if index == 0:
                for key in press:
                    self.game.input.handle_event(
                        pygame.event.Event(pygame.KEYDOWN, key=key))
                for key in release:
                    self.game.input.handle_event(
                        pygame.event.Event(pygame.KEYUP, key=key))
            self.game.input.end_frame()
            self.scene.update()

    def tap(self, key: int) -> None:
        self.step(press=(key,))
        self.step(release=(key,))

    def settle(self, frames: int = 30) -> None:
        self.step(count=frames)

    def enemy_box(self, damage: int, knockback: float = 2.0) -> Hitbox:
        body = self.player.body
        return Hitbox(rect=body.rect.inflate(4, 4), damage=damage, owner=None,
                      targets=Team.PLAYER, knockback=knockback,
                      knockback_up=0.8, active_frames=1)

    def hit_player(self, damage: int, knockback: float = 2.0):
        """Gercek hasar hattindan (HitboxManager) bir dusman darbesi."""
        self.scene.hitboxes.spawn(self.enemy_box(damage, knockback))
        self.step()


def run_distance(h: Harness, dash: bool) -> tuple[float, bool]:
    """Kosup saldirir; saldiridan sonraki 24 karede alinan yol."""
    h.step(press=(KEY_RIGHT,), count=24)          # tam hiza cik
    start = h.player.body.center_x
    h.step(press=(KEY_ATTACK,))
    dashed = h.player.dashing
    h.step(release=(KEY_ATTACK, KEY_RIGHT), count=24)
    return h.player.body.center_x - start, dashed


def check_dash() -> None:
    print("--- Hamle (KESKIN 3a) ---")
    plain = Harness()
    plain.settle(4)
    normal, dashed = run_distance(plain, dash=False)
    check(not dashed, "yetenek yokken kosarak saldiri hamle degil")

    h = Harness()
    h.learn(skilltree.BLADE_DASH)
    h.settle(4)
    h.step(press=(KEY_RIGHT,), count=24)
    h.step(press=(KEY_ATTACK,))
    check(h.player.dashing, "kosarken saldiri HAMLE oluyor")
    check(abs(h.player.body.vx - SKILL_DASH_LUNGE) < 0.01,
          "atilis hizi SKILL_DASH_LUNGE", f"{h.player.body.vx:.2f}")
    check(h.player.dash_cooldown >= SKILL_DASH_COOLDOWN - 2,
          "hamle bekleme suresi basladi", str(h.player.dash_cooldown))
    boxes = []
    for _ in range(8):
        h.step()
        boxes.extend(b for b in h.scene.hitboxes.boxes
                     if b.owner is h.player and b not in boxes)
    check(any(b.follow is h.player for b in boxes),
          "hamlenin kutusu govdeyle birlikte ilerliyor")
    h.step(release=(KEY_ATTACK, KEY_RIGHT), count=20)

    h2 = Harness()
    h2.learn(skilltree.BLADE_DASH)
    h2.settle(4)
    far, dashed2 = run_distance(h2, dash=True)
    check(dashed2 and far > normal + 15,
          "hamle normal kosu-saldirisindan belirgin uzaga gidiyor",
          f"{far:.0f} px vs {normal:.0f} px")

    slow = Harness()
    slow.learn(skilltree.BLADE_DASH)
    slow.settle(4)
    slow.step(press=(KEY_RIGHT, KEY_SNEAK), count=24)
    slow.step(press=(KEY_ATTACK,))
    check(not slow.player.dashing, "sessiz yururken hamle YOK (yalniz kosarken)")


def air_fall(h: Harness) -> float:
    """Ziplayip tepede saldirir; saldiri boyunca dusulen yol."""
    h.step(press=(KEY_JUMP,))
    for _ in range(60):
        h.step()
        if h.player.body.vy >= 0:
            break
    start = h.player.body.y
    h.step(press=(KEY_ATTACK,), release=(KEY_JUMP,))
    peak_vy = 0.0
    for _ in range(14):
        h.step()
        peak_vy = max(peak_vy, h.player.body.vy)
    return h.player.body.y - start, peak_vy


def check_hover() -> None:
    print("\n--- Havada Asili (KESKIN 3b) ---")
    plain = Harness()
    plain.settle(10)
    normal_fall, normal_vy = air_fall(plain)
    h = Harness()
    h.learn(skilltree.BLADE_HOVER)
    h.settle(10)
    hover_fall, hover_vy = air_fall(h)
    check(hover_vy <= SKILL_HOVER_FALL_SPEED + 1e-6,
          "havada vururken dusus hizi tavanda", f"{hover_vy:.2f}")
    check(hover_fall < normal_fall - 6,
          "ayni surede belirgin az dusuyor",
          f"{hover_fall:.0f} px vs {normal_fall:.0f} px")
    h.settle(90)
    check(h.player.body.grounded and h.player.hover_frames > 0,
          "yere basinca asili kalma butcesi doluyor")


def check_wave() -> None:
    print("\n--- Kilic Dalgasi (KESKIN 5) ---")
    for known in (False, True):
        h = Harness()
        if known:
            h.learn(skilltree.BLADE_FINISHER)
        h.settle(4)
        waves = 0
        for _ in range(3):
            h.tap(KEY_ATTACK)
            for _ in range(10):
                h.step()
                waves = max(waves, sum(1 for b in h.scene.hitboxes.boxes
                                       if b.visual == "blade_wave"))
        for _ in range(30):
            h.step()
            waves = max(waves, sum(1 for b in h.scene.hitboxes.boxes
                                   if b.visual == "blade_wave"))
        if known:
            check(waves == 1, "bitirici tek bir ucan kesik firlatiyor",
                  str(waves))
        else:
            check(waves == 0, "yetenek yokken dalga yok")


def check_poise() -> None:
    print("\n--- Sarsilmaz (TAS 5) ---")
    h = Harness()
    h.learn(skilltree.STONE_POISE)
    h.settle(4)
    h.step(press=(KEY_ATTACK,))
    h.step(release=(KEY_ATTACK,))
    before = h.player.health
    h.hit_player(8)
    check(h.player.health < before, "hafif darbe yine can goturuyor")
    check(h.player.chain.busy and h.player.hurt_frames == 0,
          "hafif darbe zinciri BOZMADI")
    h.settle(60)
    h.step(press=(KEY_ATTACK,))
    h.step(release=(KEY_ATTACK,))
    h.hit_player(20)
    check(not h.player.chain.busy, "agir darbe zinciri bozuyor")

    plain = Harness()
    plain.settle(4)
    plain.step(press=(KEY_ATTACK,))
    plain.step(release=(KEY_ATTACK,))
    plain.hit_player(8)
    check(not plain.player.chain.busy, "yetenek yokken hafif darbe de bozuyor")


def check_rally() -> None:
    print("\n--- Toparlanma (TAS 3b) ---")
    h = Harness()
    h.learn(skilltree.STONE_RALLY)
    h.settle(4)
    full = h.player.health
    h.hit_player(20)
    lost = full - h.player.health
    check(h.player.rally_pool == round(lost * SKILL_RALLY_POOL_RATIO),
          "yenen darbenin bir kismi geri alinabilir", str(h.player.rally_pool))
    healed = h.player.on_dealt_damage(10)
    check(healed == 5 and h.player.health == full - lost + 5,
          "karsilik vurunca can donuyor", f"+{healed}")
    h.settle(SKILL_RALLY_FRAMES + 2)
    check(h.player.rally_pool == 0, "geri cekilen havuzu kaybediyor")
    check(h.player.on_dealt_damage(10) == 0, "havuz bosken iyilesme yok")

    plain = Harness()
    plain.hit_player(20)
    check(plain.player.rally_pool == 0, "yetenek yokken havuz yok")


def check_ambush() -> None:
    print("\n--- Pusu (IZ 3a, Ardo) ---")
    h = Harness(character="ardo")
    h.learn(skilltree.TRACE_AMBUSH)
    body = h.player.body
    enemy = Shambler(h.scene, body.center_x + 12, body.bottom)
    enemy.aware = True

    def strike(facing: int) -> int:
        enemy.health = enemy.max_health
        enemy.facing = facing
        box = Hitbox(rect=enemy.body.rect.copy(), damage=10, owner=h.player,
                     targets=Team.ENEMY)
        result = enemy.take_damage(box, (1.0, 0.0))
        return result.amount

    face = strike(-1)                  # oyuncuya donuk (oyuncu solda)
    back = strike(1)                   # sirti donuk
    check(face == 10, "yuzune vurus normal", str(face))
    check(back == round(10 * SKILL_AMBUSH_SCALE), "SIRTINA vurus x1.5",
          str(back))
    enemy.aware = False
    check(strike(-1) == round(10 * SKILL_AMBUSH_SCALE),
          "fark etmemis dusmana vurus da pusu")

    rey = Harness(character="rey")
    foe = Shambler(rey.scene, rey.player.body.center_x + 12,
                   rey.player.body.bottom)
    foe.aware, foe.facing = True, 1
    box = Hitbox(rect=foe.body.rect.copy(), damage=10, owner=rey.player,
                 targets=Team.ENEMY)
    check(foe.take_damage(box, (1.0, 0.0)).amount == 10,
          "yetenegi olmayan sirttan vurunca da normal")


def check_quiet() -> None:
    print("\n--- Sessiz Adim (IZ 3b, Ardo) ---")
    h = Harness(character="ardo")
    check(abs(h.player.sneak_ratio - PLAYER_SNEAK_RATIO) < 1e-6
          and h.player.noise_scale == 1.0, "yeteneksiz: taban degerler")
    h.learn(skilltree.TRACE_QUIET)
    check(abs(h.player.sneak_ratio - SKILL_QUIET_SNEAK_RATIO) < 1e-6,
          "sessiz yuruyus hizlaniyor")
    check(h.player.noise_scale < 1.0, "adim sesi kisiliyor")
    enemy = Shambler(h.scene, h.player.body.center_x
                     + ENEMY_SIGHT_RANGE * SKILL_QUIET_SIGHT_SCALE + 20,
                     h.player.body.bottom)
    h.scene.enemies = [enemy]
    enemy._update_awareness()
    check(not enemy.aware, "gorus menzilinin icinde ama seni FARK ETMIYOR")


def check_burst() -> None:
    print("\n--- Yanki Darbesi (YANKI 5) / Ayi Kukremesi (IZ 5) ---")
    for character, key in (("rey", skilltree.ECHO_BURST),
                           ("ardo", skilltree.TRACE_ROAR)):
        h = Harness(character=character)
        h.learn(key)
        h.settle(4)
        h.step(press=(KEY_ECHO,))
        burst = [b for b in h.scene.hitboxes.boxes
                 if b.owner is h.player and b.rect.size == SKILL_BURST_SIZE]
        h.step(count=6)
        check(bool(burst) or h.scene._burst_cooldown > 0,
              f"{character}: duyuyu acmak iten halkayi birakiyor")
        check(h.scene._burst_cooldown > SKILL_BURST_COOLDOWN - 20,
              f"{character}: bekleme basladi", str(h.scene._burst_cooldown))
        h.step(release=(KEY_ECHO,), count=40)
        before = h.scene._burst_cooldown
        h.step(press=(KEY_ECHO,))
        check(h.scene._burst_cooldown < before,
              f"{character}: bekleme bitmeden ikinci halka YOK")
        h.step(release=(KEY_ECHO,))

    plain = Harness()
    plain.step(press=(KEY_ECHO,))
    check(plain.scene._burst_cooldown == 0, "yetenek yokken halka yok")


def check_lie_sense() -> None:
    print("\n--- Yalan Sezgisi (YANKI 3b) ---")
    for known in (False, True):
        h = Harness()
        if known:
            h.learn(skilltree.ECHO_LIE)
        h.scene.echo.ask = lambda: Answer.LIE
        h.sounds.clear()
        h.scene.on_echo_ask()
        urged = "necklace_conflict" in h.sounds
        if known:
            check(urged, "yalan soylenince kolye urperiyor (ses)")
        else:
            check(not urged, "yetenek yokken yalan sessiz kaliyor")


def check_shield() -> None:
    print("\n--- Eski Kalkan ---")
    h = Harness()
    consumables.add(h.scene.save_data, consumables.SHIELD, 5)
    check(consumables.count(h.scene.save_data, consumables.SHIELD) == 1,
          "en fazla BIR kalkan tasiniyor")
    h.settle(4)
    full = h.player.health
    h.sounds.clear()
    h.hit_player(25, knockback=3.0)
    check(h.player.health == full, "ilk darbe hic can goturmedi")
    check(consumables.count(h.scene.save_data, consumables.SHIELD) == 0,
          "kalkan kirildi")
    check(h.player.iframes >= SHIELD_IFRAMES - 2,
          "kirildiktan sonra kisa dokunulmazlik", str(h.player.iframes))
    check("shield_break" in h.sounds, "kirilma duyuluyor")
    h.settle(SHIELD_IFRAMES + 2)
    h.hit_player(25)
    check(h.player.health == full - 25, "ikinci darbe normal isliyor")

    dodge = Harness()
    consumables.add(dodge.scene.save_data, consumables.SHIELD, 1)
    dodge.settle(4)
    dodge.step(press=(pygame.K_LSHIFT,))
    dodge.hit_player(25)
    check(consumables.count(dodge.scene.save_data, consumables.SHIELD) == 1,
          "kacinmanin dokunulmazliginda kalkan HARCANMIYOR")


def check_last_chance() -> None:
    print("\n--- Son sans (CLAUDE.md 8) ---")
    h = Harness()
    h.settle(4)
    h.player.health = 10                       # 80'in %15'i = 12
    h.hit_player(40)
    check(not h.player.dead and h.player.health == 1,
          "%15 altinda oldurucu darbe 1 can birakiyor", str(h.player.health))
    check(h.scene.last_chance_left == 0, "bolumdeki tek hak harcandi")
    h.settle(60)
    h.hit_player(40)
    check(h.player.dead, "ikinci oldurucu darbe olduruyor")

    high = Harness()
    high.settle(4)
    high.player.health = 30
    high.hit_player(40)
    check(high.player.dead, "%15 USTUNDEYKEN af yok (kural boyle yazili)")

    shielded = Harness()
    consumables.add(shielded.scene.save_data, consumables.SHIELD, 1)
    shielded.settle(4)
    shielded.player.health = 10
    shielded.hit_player(40)
    check(shielded.player.health == 10 and shielded.scene.last_chance_left == 1,
          "once kalkan harcaniyor - sessiz af yedekte kaliyor")

    restart = Harness()
    restart.scene.last_chance_left = 0
    restart.scene.restart()
    check(restart.scene.last_chance_left == 0,
          "olup yeniden dogmak hakki TAZELEMIYOR (bolum basina bir)")


def check_learning() -> None:
    print("\n--- oyun ortasinda ogrenmek ---")
    h = Harness()
    base_health = h.player.max_health
    base_window = h.player.chain.window_frames
    h.scene.learn_skill(skilltree.STONE_HIDE)
    check(h.player.max_health == base_health + 10
          and h.player.health == h.player.max_health,
          "POST aninda: azami can +10 ve bolme dolu")
    h.scene.learn_skill(skilltree.STONE_HIDE)
    check(h.player.max_health == base_health + 10,
          "ayni dugum iki kez uygulanmiyor")
    h.scene.learn_skill(skilltree.BLADE_FLOW)
    check(h.player.chain.window_frames == base_window + 2,
          "AKIS aninda zincire biniyor")
    h.player.equip_weapon(h.player.weapon)
    check(h.player.chain.window_frames == base_window + 2,
          "silah degisince AKIS kaybolmuyor (eski hata)")

    ardo = Harness(character="ardo")
    base_range = ardo.scene.tracking.range_scale
    ardo.scene.learn_skill(skilltree.TRACE_EYE)
    check(ardo.scene.tracking.range_scale > base_range,
          "KESKIN GOZ iz menzilini aninda uzatiyor",
          f"{ardo.scene.tracking.range_scale:.2f}")


def main() -> int:
    check_dash()
    check_hover()
    check_wave()
    check_poise()
    check_rally()
    check_ambush()
    check_quiet()
    check_burst()
    check_lie_sense()
    check_shield()
    check_last_chance()
    check_learning()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Yetenek hareketleri, kalkan ve son sans oyunda calisiyor.")
    return 0


raise SystemExit(main())
