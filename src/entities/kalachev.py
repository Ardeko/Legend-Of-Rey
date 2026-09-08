"""Kalachev - `docs/kalachev.md`. **Yoldas DEGIL.**

Ardo'nun eski dostu, serseri bir maceraci. Belirir, onune geleni
parcalar, gider. Emir veremezsin, bekleyemez, sonraki odada yoktur.

## Neden `Companion`'dan turemiyor

`Companion` yaninda **duran** bir sey: tasmasi var (`COMPANION_LEASH`),
oyuncuyu takip ediyor, "burada bekle" emri aliyor, olmuyor - diz
cokuyor ve kalkiyor. Hepsi dogru, ve hepsi Kalachev'in tersi.

Ondan turetseydik `hold()`, `release()`, `assist()` ve tasma mantigi
miras kalirdi; biri gun gelir kullanirdi ve Kalachev ikinci bir Ardo
olurdu. Belgenin en onemli karari buydu (`docs/kalachev.md` 2):
B10-B15'in yalnizligi onun yuzunden iptal olmamali.

Ortak olan tek sey `Actor` - ikisi de bir govde ve bir animator.

## Davranisi bir kisilik degil bir BILGI

`docs/kalachev.md` 4: bu zindanda tek basina hayatta kalmis ve
yanindaki adami kaybetmis. Tek bir sey ogrenmis - **beklersen
olursun.**

    Rey       tell ogrenir, kacinir, mesafe ayarlar
    Ardo      tell okur, BEKLER, uzak durur
    Kalachev  tell OKUMAZ, mesafe KAPATIR, kacinmasi YOK

Oyuncu onu izlerken "bu adam boyle giderse olecek" demeli. Sonra
oluyor (B18 faz 2). Olum surpriz degil, **onceden gosterilmis** bir
sonuc - ve iyi olum sahnesi tam olarak budur.

## Hasari umursamamasi mekanikte

`poise` cok yuksek: sendelemiyor, yani vurus yiyince saldirisi
kesilmiyor. Ekranda su goruluyor - Kalachev vuruluyor ve **durmuyor.**
Bu bir guc gosterisi degil bir uyari.

## Kalici olarak olmuyor

Buradaki `health` yalnizca "ne kadar hirpalandi" gostergesi. Sifira
inince cekiliyor (`leave()`), olmuyor: olumu senaryolu ve B18'e ait.
Bir yan karakterin rastgele bir Suruklenen tarafindan oldurulmesi
finalin butun agirligini caldirirdi.
"""
from __future__ import annotations

import math

import pygame

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Hitbox, Team
from src.entities.actor import Actor

# --- Dovus degerleri ---------------------------------------------------------
# Ardo'dan (COMPANION_DAMAGE) daha sert ve daha hizli: balta agir ve
# Kalachev geri cekilmiyor. Ama oyuncudan **zayif** - bolumu onun
# temizlemesi oyuncunun isini calardi.
DAMAGE = 16
ATTACK_RANGE = 30.0
ATTACK_COOLDOWN = 34
# **Tell YOK.** Ardo savururken duruyor ve bekliyor; Kalachev
# dogrudan vuruyor. Belgenin karakter tanimi bu.
SWING_ACTIVE = 5

SPEED = 1.15                # Ardo'dan hizli - mesafe kapatiyor
MAX_HEALTH = 90
POISE = 40                  # Cok yuksek: vurulunca DURMUYOR

# Bu kadar uzaktaki dusmani bile kovaliyor. `Companion`in tasmasi
# (oyuncuya baglilik) burada YOK - Kalachev oyuncunun yaninda kalmak
# zorunda degil, isi dusmanlarla.
SIGHT = 260.0

# Sahnede bu kadar kare kaldiktan sonra kendiliginden cekiliyor.
# Kalici olsaydi bir yoldas olurdu.
DEFAULT_STAY = 60 * 22
FADE_FRAMES = 40


class Kalachev(Actor):
    """Belirir, keser, gider. Emir alinmaz."""

    team = Team.PLAYER
    body_width = 13
    body_height = 23
    max_health = MAX_HEALTH
    poise = POISE

    def __init__(self, scene, x: float, y: float,
                 stay: int = DEFAULT_STAY) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator("kalachev")
        self.sprite_foot_y = CHARACTERS["kalachev"].foot_y
        self.attack_frames = 0
        self.swing_frames = 0
        self.stay_frames = stay
        self.fade = 0
        self.leaving = False
        self.kills = 0
        self._target = None

    # --- Durum --------------------------------------------------------------
    @property
    def gone(self) -> bool:
        return self.leaving and self.fade <= 0

    @property
    def alpha(self) -> float:
        if not self.leaving:
            return 1.0
        return max(0.0, self.fade / FADE_FRAMES)

    def leave(self) -> None:
        """Cekilme. **Olmuyor** - olumu senaryolu ve B18'e ait."""
        if self.leaving:
            return
        self.leaving = True
        self.fade = FADE_FRAMES

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, box, direction):
        """Hasar aliyor ama **olmuyor** - cani bitince cekiliyor.

        Hasar **once** kirpiliyor, sonradan can geri verilmiyor:
        `Actor.take_damage` can sifira inince `dead` bayragini koyuyor
        ve o bayragi sonradan silmek bir dizi yan etkiyi (olum
        animasyonu, temizlenme, sayaclar) yarim birakirdi. Test
        yakaladi.

        Ayni desen `Player.take_damage`de de var (Yanki carpani):
        kutunun hasari gecici olarak degistiriliyor, `finally` ile geri
        konuyor - hitbox baska hedeflere de degiyor olabilir.
        """
        original = box.damage
        if box.damage >= self.health:
            box.damage = max(0, self.health - 1)
        try:
            result = super().take_damage(box, direction)
        finally:
            box.damage = original
        # Bir yan karakterin rastgele bir Suruklenen tarafindan
        # oldurulmesi finalin butun agirligini caldirirdi
        # (`docs/kalachev.md` 6: olumu senaryolu ve B18'e ait).
        if result.hit and self.health <= 1:
            self.leave()
        return result

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        if self.leaving:
            self.fade -= 1
            self.body.approach_vx(0.0, 0.4)
            self.body.move(self.scene.tilemap)
            self.animator.update()
            return

        self.stay_frames -= 1
        if self.stay_frames <= 0:
            self.leave()
            return

        if self.attack_frames > 0:
            self.attack_frames -= 1
        if self.swing_frames > 0:
            self.swing_frames -= 1

        self._think()
        self.body.move(self.scene.tilemap)
        self._animate()

    def _think(self) -> None:
        target = self._pick_target()
        self._target = target
        if target is None:
            # Dusman yoksa **bekliyor değil, ilerliyor**: kendi isi var.
            self.body.approach_vx(self.facing * SPEED * 0.6, 0.2)
            return

        delta = target.body.center_x - self.body.center_x
        if abs(delta) > 2.0:
            self.facing = 1 if delta > 0 else -1

        if abs(delta) <= ATTACK_RANGE:
            # **Durmadan vuruyor.** Tell yok, geri cekilme yok.
            self.body.approach_vx(0.0, 0.5)
            if self.attack_frames <= 0:
                self._swing()
            return
        # **Mesafe kapatiyor** - Ardo uzak durur, Kalachev girer.
        self.body.approach_vx(self.facing * SPEED, 0.3)

    def _pick_target(self):
        """En yakin diri dusman. **Tasma yok** - oyuncuya bagli degil."""
        best, best_distance = None, SIGHT
        for enemy in getattr(self.scene, "enemies", ()):
            if getattr(enemy, "dead", False):
                continue
            distance = math.hypot(enemy.body.center_x - self.body.center_x,
                                  enemy.body.center_y - self.body.center_y)
            if distance < best_distance:
                best, best_distance = enemy, distance
        return best

    def _swing(self) -> None:
        from src.combat.hitbox import melee_rect
        rect = melee_rect(self.body, self.facing, ATTACK_RANGE, 20)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.ENEMY,
            damage=DAMAGE, active_frames=SWING_ACTIVE,
            knockback=2.6, knockback_up=0.8, poise_damage=3,
        ))
        self.attack_frames = ATTACK_COOLDOWN
        self.swing_frames = SWING_ACTIVE + 6
        self.scene.game.play_sound("swing_heavy")
        hook = getattr(self.scene, "on_kalachev_swing", None)
        if hook:
            hook(self)

    # --- Cizim --------------------------------------------------------------
    def _animate(self) -> None:
        if self.swing_frames > 0:
            self.animator.play("attack1")
        elif abs(self.body.vx) > 0.1:
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        image = self.animator.render(self.facing, flash=self.flash.active)
        if image is None:
            return
        ox, oy = offset
        alpha = self.alpha
        if alpha < 1.0:
            image = image.copy()
            image.set_alpha(int(255 * alpha))
        surface.blit(image, (int(self.body.center_x - image.get_width() * 0.5) - ox,
                             int(self.body.bottom - self.sprite_foot_y) - oy))

    def debug_lines(self) -> list[str]:
        return [f"kalachev can {self.health}/{self.max_health}  "
                f"kalan {self.stay_frames}  "
                f"{'cekiliyor' if self.leaving else 'dovusuyor'}"]
