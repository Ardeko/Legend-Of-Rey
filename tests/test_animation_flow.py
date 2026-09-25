"""Akici animasyon - 8 FPS kurali gevsedi, zamanlama bozulmadi.

Arda (25.09.2026): *"8 fps kuralini oyunu bozmadan dikkatlice
gecebilirsin, akici ve guzel gozuken animasyonlar yap."* Iki soz var ve
ikisi de burada olculuyor:

  1. **Oyun bozulmadi.** Zamanla surulen her durumun TOPLAM suresi
     eskisiyle ayni (`animator.DURATIONS`): dusmanlar saldiri/hasari
     zamanla oynatiyor, poz sayisi artip sure uzasaydi savurus vurustan
     geri kalirdi. Dovus kare degerleri (`CLAUDE.md` 7) zaten zincirde;
     animasyon onlari okumuyor, onlar animasyonu suruyor.
  2. **Daha akici.** Hizli eylemler (kacinma, ziplama, hasar, saldiri)
     ilerlemeyle suruluyor ve eylem boyunca GERCEKTEN birden cok poz
     gosteriyor.

Calistir:
    python tests/test_animation_flow.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.systems.save import SaveData, write_save  # noqa: E402

write_save(SaveData())

import pygame  # noqa: E402

pygame.display.init()
pygame.display.set_mode((64, 64))

from src.art.animation import ANIMATIONS  # noqa: E402
from src.art.animator import DURATIONS, Animator, hold_for  # noqa: E402
from src.config import DODGE_TOTAL_FRAMES  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.combat_room import CombatRoomScene  # noqa: E402
from src.systems import abilities  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


# Eski (poz sayisi, bekleme) - 25.09.2026 oncesi. Sure = carpim.
BEFORE = {"idle": (6, 9), "run": (8, 5), "attack1": (5, 7), "attack2": (5, 7),
          "attack3": (5, 7), "hurt": (2, 7), "dodge": (2, 7)}


def frames_to_finish(name: str, state: str) -> int:
    """Zamanla surulen tek seferlik bir durum kac karede son poza variyor."""
    animator = Animator(name)
    animator.play(state)
    last = len(animator.frames[state]) - 1
    for frame in range(1, 400):
        animator.update()
        if animator.index >= last:
            return frame
    return -1


def frames_per_loop(name: str, state: str) -> int:
    """Dongunun bir turu kac kare: son pozdan ilk poza SARDIGI an."""
    animator = Animator(name)
    animator.play(state)
    previous = animator.index
    for frame in range(1, 400):
        animator.update()
        if animator.index < previous:
            return frame
        previous = animator.index
    return -1


def check_durations() -> None:
    print("--- toplam sure eskisiyle ayni ---")
    for state, (count, hold) in BEFORE.items():
        check(DURATIONS.get(state) == count * hold,
              f"{state}: sure {count}x{hold}={count * hold} kare korunuyor",
              str(DURATIONS.get(state)))
    for state in ("attack1", "attack3", "hurt"):
        n = len(Animator("shambler").frames[state])
        old_count, old_hold = BEFORE[state]
        # Eski sistemde son poza (count-1) x hold karede variliyordu.
        want = DURATIONS[state] - round(hold_for(state, n))
        got = frames_to_finish("shambler", state)
        check(abs(got - want) <= 1,
              f"dusman {state}: son poza ayni zamanda variyor",
              f"{got} kare (beklenen ~{want}, eskiden "
              f"{(old_count - 1) * old_hold})")
    for state in ("idle", "run"):
        got = frames_per_loop("rey_armed", state)
        check(abs(got - DURATIONS[state]) <= 1,
              f"{state} dongusunun temposu ayni", f"{got} kare")


def check_pose_counts() -> None:
    print("\n--- hizli eylemlerde daha cok poz ---")
    for state, minimum in (("dodge", 6), ("jump", 3), ("hurt", 4),
                           ("attack1", 7), ("attack2", 7), ("attack3", 7)):
        count = ANIMATIONS[state][1]
        check(count >= minimum, f"{state}: en az {minimum} poz", str(count))
    check("brake" in ANIMATIONS and not ANIMATIONS["brake"][2],
          "fren (kosudan durus) gecis pozu var, dongusel degil")


def check_player_flow() -> None:
    print("\n--- oyuncu: eylem boyunca pozlar akiyor ---")
    game = Game()
    game.scenes.set_root(CombatRoomScene, transition=False)
    game.scenes._flush()
    scene = game.scenes.current
    scene.enemies = []
    player = scene.player
    player.grant(abilities.SWORD)
    player.grant(abilities.DODGE)

    def step(press=(), release=(), count=1):
        for index in range(count):
            game.input.begin_frame()
            if index == 0:
                for key in press:
                    game.input.handle_event(
                        pygame.event.Event(pygame.KEYDOWN, key=key))
                for key in release:
                    game.input.handle_event(
                        pygame.event.Event(pygame.KEYUP, key=key))
            game.input.end_frame()
            scene.update()

    step(count=10)
    seen: list[int] = []
    step(press=(pygame.K_LSHIFT,))
    for _ in range(DODGE_TOTAL_FRAMES):
        if player.animator.state == "dodge":
            seen.append(player.animator.index)
        step(release=(pygame.K_LSHIFT,))
    check(len(set(seen)) >= 6, "kacinma boyunca en az 6 farkli poz",
          str(sorted(set(seen))))
    check(seen == sorted(seen), "kacinma pozlari geri sarmiyor (ilerlemeyle)")

    step(count=30)
    step(press=(pygame.K_SPACE,))
    jump: list[int] = []
    for _ in range(40):
        if player.animator.state == "jump":
            jump.append(player.animator.index)
        step()
    check(len(set(jump)) >= 3, "ziplama kalkistan tepeye birden cok poz",
          str(sorted(set(jump))))
    step(release=(pygame.K_SPACE,), count=60)

    from src.combat.hitbox import Hitbox, Team
    scene.hitboxes.spawn(Hitbox(rect=player.body.rect.inflate(4, 4),
                                damage=5, owner=None, targets=Team.PLAYER,
                                active_frames=1))
    hurt: list[int] = []
    for _ in range(16):
        step()
        if player.animator.state == "hurt":
            hurt.append(player.animator.index)
    check(len(set(hurt)) >= 4, "hasar: darbe, savrulma, toparlanma",
          str(sorted(set(hurt))))

    step(count=60)
    step(press=(pygame.K_RIGHT,), count=30)
    step(release=(pygame.K_RIGHT,))
    braked = player.brake_frames > 0 or player.animator.state == "brake"
    step(count=2)
    check(braked and player.animator.state in ("brake", "idle", "run"),
          "tam hizdan durunca fren pozu", player.animator.state)
    step(count=30)
    step(press=(pygame.K_RIGHT, pygame.K_LCTRL), count=20)
    step(release=(pygame.K_RIGHT,))
    check(player.brake_frames == 0, "yavas yuruyusten durmak fren degil")
    game.shutdown()


def main() -> int:
    check_durations()
    check_pose_counts()
    check_player_flow()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Animasyon akici, zamanlama eskisiyle ayni.")
    return 0


raise SystemExit(main())
