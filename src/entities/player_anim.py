"""Oyuncu animasyon durumu - oynanistan turer, tersi degil.

**Saldirilar ilerlemeyle surulur.** Kare, saldirinin kendi kare
butcesindeki konumdan seciliyor; boylece animasyon dovus zamanlamasini asla
kaydiramaz. Ters kurulsaydi (animasyon karesi hitbox'i acsaydi) bir sanat
degisikligi sessizce combo penceresini bozardi.

`player.py`'den ayrildi: dosya 400 satiri asmisti (CLAUDE.md 11) ve bu blok
zaten ayri bir sorumluluk - **hangi animasyon**, **hangi karede**.
"""
from __future__ import annotations

from src.art.animation import CHARACTERS, pose_table
from src.art.spritegen import weapon_tip
from src.combat.combo import AttackPhase
from src.config import (
    DODGE_TOTAL_FRAMES, PLAYER_JUMP_SPEED, PLAYER_RUN_SPEED,
    SNEAK_ANIM_HOLD_SCALE, SNEAK_CROUCH,
)

# Yere serilen oyuncunun (anlatimin kontrolu aldigi an, B1) hasar pozu:
# savrulmanin en geri noktasi. Ilerleme toparlanmaya kaysaydi yerde yatan
# karakter ayakta gibi gorunurdu.
KNOCKED_DOWN_PROGRESS = 0.3


def update_animation(player) -> None:
    """Animasyon durumu oynanistan turer, tersi degil.

    Saldirilar **ilerlemeyle** surulur: kare, saldirinin kendi kare
    butcesindeki konumdan secilir. Boylece animasyon dovus zamanlamasini
    asla kaydiramaz.
    """
    _update_sway(player)

    # Sessiz yuruyus: kosu dongusu yavas akiyor, govde hafifce comeliyor.
    # Yeni kare yok - bekleme carpani ve squash (`CLAUDE.md` 7).
    sneaking = getattr(player, "sneaking", False)
    player.animator.hold_scale = SNEAK_ANIM_HOLD_SCALE if sneaking else 1.0
    if sneaking and player.land_frames <= 0:
        player.squash.trigger(SNEAK_CROUCH, 2)

    if player.dead:
        player.animator.play("death")
        player.animator.update()
        return

    if player.chain.busy:
        state = f"attack{min(player.chain.index + 1, 3)}"
        player.animator.play(state)
        progress = attack_progress(player)
        player.animator.set_progress(progress)
        _feed_trail(player, state, progress)
        return
    player.trail.clear()

    # Hizli eylemler ILERLEMEYLE: poz, eylemin kendi suresindeki konumdan.
    # Poz sayisi artsa da (8 FPS kurali gevsedi, 25.09.2026) zamanlama
    # eylemin kendisinde - animasyon onu kaydiramaz.
    if player.hurt_frames > 0:
        player.animator.play("hurt")
        if getattr(player, "control_locked", 0) > 0:
            progress = KNOCKED_DOWN_PROGRESS
        else:
            total = max(1, getattr(player, "hurt_animation_frames", 14))
            progress = 1.0 - player.hurt_frames / total
        player.animator.set_progress(progress)
        return
    if player.dodge.active:
        player.animator.play("dodge")
        player.animator.set_progress(
            1.0 - player.dodge.frames_left / max(1, DODGE_TOTAL_FRAMES))
        return
    if not player.body.grounded and player.body.vy < -0.3:
        # Ziplama dikey hizla suruluyor: kalkista gerilme, tepede toplanma.
        player.animator.play("jump")
        player.animator.set_progress(
            1.0 + player.body.vy / max(0.1, PLAYER_JUMP_SPEED))
        return
    if not player.body.grounded:
        player.animator.play("fall")
    # Gecis kareleri kosu/duruştan ONCE bakiliyor: ikisi de kisa surer ve
    # bittiginde normal duruma kendiliginden donulur. Sonra bakilsaydi
    # kosan bir karakter inis/pivot karesini hic gostermezdi.
    elif player.land_frames > 0:
        player.animator.play("land")
    elif player.turn_frames > 0:
        player.animator.play("turn")
    elif getattr(player, "brake_frames", 0) > 0:
        # Fren suresiyle suruluyor: once kayis, sonra toparlanma.
        player.animator.play("brake")
        total = max(1, getattr(player, "brake_animation_frames", 14))
        player.animator.set_progress(1.0 - player.brake_frames / total)
        return
    elif abs(player.body.vx) > 0.25:
        player.animator.play("run")
    else:
        player.animator.play("idle")
    player.animator.update()

def attack_progress(player) -> float:
    """Su anki saldirinin 0..1 arasi ilerlemesi."""
    spec = player.chain.spec
    total = spec.total
    if total <= 0:
        return 1.0
    if player.chain.phase is AttackPhase.WINDUP:
        done = spec.windup - player.chain.phase_frames_left
    elif player.chain.phase is AttackPhase.ACTIVE:
        done = spec.windup + (spec.active - player.chain.phase_frames_left)
    else:
        done = (spec.windup + spec.active
                + (spec.recovery - player.chain.phase_frames_left))
    return max(0.0, min(1.0, done / total))

# --- Hareket ------------------------------------------------------------


def _feed_trail(player, state: str, progress: float) -> None:
    """Silahin ucunu izin uzerine ekler (src/art/trail.py).

    Uc, sprite'i cizen **ayni** poz fonksiyonundan hesaplaniyor
    (`spritegen.weapon_tip`) - yaklasik bir noktadan degil. Poz degisirse
    iz de kendiliginden dogru kalir.

    Hucre -> dunya donusumu `player_render.draw_player` ile ayni:
    yatayda merkez, dikeyde sprite'in TABAN CIZGISI govdenin altina
    hizali. Sola bakarken sprite aynalandigi icin `tip_x` de aynalanmali;
    unutulursa iz karakterin arkasindan cikar.
    """
    spec = CHARACTERS.get(player.animator.character)
    if spec is None:
        return
    pose_fn, count, looping = pose_table(spec.name).get(state, (None, 1, False))
    if pose_fn is None:
        return
    tip = weapon_tip(spec, pose_fn(max(0.0, min(1.0, progress))))
    if tip is None:
        return                      # Silahsiz (yumruk) - iz yok
    # Bitirici izi ALTIN, normal vurus celik beyazi. Zincirin ucuncu
    # vurusu docs/dovus-sistemi.md'de ayri bir agirliga sahip (7 kare
    # hitstop, iptal edilemez) - o agirlik gorsel olarak da okunmali.
    player.trail.chain = "brass" if player.chain.is_finisher else "bone_pale"
    tip_x, tip_y = tip
    if player.facing < 0:
        tip_x = spec.cell_width - tip_x
    world_x = player.body.center_x - spec.cell_width * 0.5 + tip_x
    world_y = player.body.bottom - player.sprite_foot_y + tip_y
    player.trail.add(world_x, world_y)


def _update_sway(player) -> None:
    """Pelerin/sac/etegin ikincil hareketini besler.

    Hedef, karakterin **kendi yonundeki** hizi: ileri kosarken kumas
    arkaya savrulur, geri geri giderken one. Sprite her zaman saga bakar
    halde uretiliyor ve sola bakarken aynalaniyor - bu yuzden `facing`
    ile carpmak iki yonde de dogru sonucu veriyor.

    Havadayken dusus hizi da katiliyor: serbest dususte kumas yukari
    savrulmali, yoksa karakter havada donmus gibi gorunuyor.
    """
    forward = player.body.vx * player.facing / max(0.1, PLAYER_RUN_SPEED)
    if not player.body.grounded:
        forward += abs(player.body.vy) * 0.16
    player.animator.update_sway(forward)
