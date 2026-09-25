"""Oyuncu: hareket, ziplama, uclu zincir, kacinma, karsi vurus.

Rey ve Ardo ayni sinifi paylasir; sayisal farklar `character_stats.py`'de
(docs/dovus-sistemi.md 8). Rey bilgiyle ve akisla kazanir, Ardo zamanlamayla
ve dayaniklilikla.

Cizim uc kipte calisir (F4): sprite, siluet ve kutu. Kutu kipi "kutularla
eglenceli mi?" sorusunu sprite'lari atmadan sormaya yarar.
"""
from __future__ import annotations

import math

import pygame

from src.combat.combo import (
    AttackPhase, ChainState, ComboCounter, DodgeState, counter_damage,
)
from src.combat.hitbox import DamageResult, Hitbox, Team, melee_rect
from src.config import (
    LAND_FRAMES_HARD, LAND_FRAMES_SOFT, TURN_FRAMES,
    TURN_PIVOT_MIN_SPEED, HARD_LAND_AIR_FRAMES,
    APEX_GRAVITY_SCALE, APEX_SPEED_THRESHOLD, COYOTE_FRAMES, DODGE_SPEED,
     JUMP_CUT_MULTIPLIER, LAST_CHANCE_HEALTH_RATIO, PLAYER_AIR_ACCEL,
    PLAYER_AIR_FRICTION, PLAYER_GROUND_ACCEL, PLAYER_GROUND_FRICTION,
    PLAYER_JUMP_SPEED, PLAYER_RUN_SPEED, PLAYER_SNEAK_RATIO,
    SHIELD_IFRAMES, SHIELD_KNOCKBACK_SCALE, SKILL_DASH_COOLDOWN,
    SKILL_DASH_DAMAGE_SCALE, SKILL_DASH_LUNGE, SKILL_DASH_MIN_SPEED,
    SKILL_DASH_REACH, SKILL_HOVER_FALL_SPEED, SKILL_HOVER_FRAMES,
    SKILL_HOVER_LIFT, SKILL_POISE_MAX_DAMAGE, SKILL_QUIET_NOISE_SCALE,
    SKILL_QUIET_SIGHT_SCALE, SKILL_QUIET_SNEAK_RATIO,
    SKILL_RALLY_FRAMES, SKILL_RALLY_HEAL_RATIO, SKILL_RALLY_POOL_RATIO,
    SKILL_WAVE_DAMAGE_RATIO, SKILL_WAVE_LIFE, SKILL_WAVE_SPEED,
    STEP_DISTANCE_PX,
)
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.art.trail import WeaponTrail
from src.core.input import NEUTRAL_INPUT, Action
from src.entities.actor import Actor
from src.entities.character_stats import CharacterStats, REY
from src.combat import weapons
from src.entities.player_anim import attack_progress, update_animation
from src.entities.player_render import draw_player
from src.systems import abilities, charms, consumables, skilltree

ATTACK_REACH = 22
ATTACK_HEIGHT = 18
FINISHER_REACH = 28
FINISHER_HEIGHT = 22
# Saldiri sirasinda one atilma - saldiri hem hareket hem hasardir.
LUNGE_BY_INDEX = (0.9, 1.1, 2.0)
PLAYER_IFRAMES_ON_HIT = 45
HURT_ANIMATION_FRAMES = 14
# Fren (tam hizda kosarken durmak): kisa gecis pozu. Yalnizca bu hizin
# ustunden durulunca - yavas yuruyusten durmak fren gerektirmiyor.
BRAKE_FRAMES = 9
BRAKE_MIN_SPEED_RATIO = 0.75


class Player(Actor):
    team = Team.PLAYER
    body_width = 10
    body_height = 22
    iframes_on_hit = PLAYER_IFRAMES_ON_HIT
    # Hasar pozu bu sureye yayiliyor (`player_anim`, ilerlemeyle).
    hurt_animation_frames = HURT_ANIMATION_FRAMES
    # Girdiyi bu oyuncu mu aliyor.
    #
    # On alti bolumde sahnede tek bir `Player` var ve hep True. Bolum
    # 17 "Ikili Kule" ikisini birden sahneye koyuyor
    # (`docs/yapi.md` 119: *"iki `Player` nesnesi, aktif olani
    # `active_player` isaretcisiyle degistir"*) ve pasif olani
    # `NEUTRAL_INPUT` ile suruyor.
    controlled = True

    def __init__(self, scene, x: float, y: float,
                 stats: CharacterStats = REY) -> None:
        self.stats = stats
        self.max_health = stats.max_health
        super().__init__(scene, x, y)

        # Yetenek kapisi **tek yerde**. Dagitilsaydi biri mutlaka bir yerde
        # unutulur ve oyuncu henuz almadigi bir seyi yapabilirdi.
        self.abilities: set[str] = abilities.starting_set(stats.name.lower())
        # Takili tilsimlar. Yetenekten ayri tutuluyor: yetenek "yapabilir
        # misin", tilsim "ne kadar iyi yapiyorsun" sorusunu cevapliyor.
        self.charms: set[str] = set()
        # Acilmis yetenek agaci dugumleri. `charms` ile ayni desen:
        # kume, ve etkiler `skilltree.py`'deki toplayicilardan
        # geliyor. `PlayScene` kayittan dolduruyor.
        self.skills: set[str] = set()
        # Govdenin ne kadari suyun altinda (0..1). Sahne her karede
        # yaziyor; animasyon ve ses buna bakiyor. Susuz bolumlerde
        # hep 0.0 kaliyor.
        self.water_ratio = 0.0

        # Silah: ikisi de yumrukla baslar, kilici Bolum 1'de Jet verir.
        # `self.animator`/`self.chain` bu silaha gore kuruluyor; ayri ayri
        # ilklendirilselerdi biri diger degisince unutulurdu.
        self.weapon = weapons.starting_weapon(stats.name.lower())
        self.chain = ChainState(window_frames=stats.chain_window,
                                chain_table=weapons.get(self.weapon).chain)
        self.trail = WeaponTrail()
        # Gecis kareleri (src/art/animation.py::_land/_turn):
        # kalan kare sayisi. 0 = gecis oynamayior.
        self.land_frames = 0
        self.turn_frames = 0
        self.brake_frames = 0
        self._last_facing = 1
        self._apply_weapon_sprite()
        self.dodge = DodgeState(charges=stats.dodge_charges,
                                max_charges=stats.dodge_charges)
        self.combo = ComboCounter()

        self.coyote_frames = 0
        self.jump_held = False
        self.air_frames = 0
        self.hurt_frames = 0        # Hasar animasyonu suresi
        # Anlatimin kontrolu kisa sureligine aldigi anlar (orn. Bolum 1'de
        # sarsintinin Rey'i yere sermesi). Girdi **yok sayilir**, fizik
        # surer - oyuncu dusup yuvarlanir, ekran donmaz.
        self.control_locked = 0
        # Sessiz yuruyor mu (`Action.SNEAK`) - bu kare. Animasyon ve
        # B15'in gurultusu okuyor.
        self.sneaking = False
        self.last_hit_was_counter = False
        # Adim sesi - kare sayisi degil, alinan **mesafeye** gore tetiklenir
        # (STEP_DISTANCE_PX): yavas yuruyus de hizli kosu da dogal sikilikta
        # ses uretir.
        self._step_distance = 0.0

        # --- Yetenek agacinin hareketleri (`skilltree.py`) ---------------
        # Hamle: kosarken saldiri. `dashing` yalnizca o vurus boyunca.
        self.dashing = False
        self.dash_cooldown = 0
        # Havada Asili: bir havada kalista harcanabilecek asili kare.
        self.hover_frames = SKILL_HOVER_FRAMES
        # Toparlanma: yenen darbenin geri alinabilir kismi ve suresi.
        self.rally_pool = 0
        self.rally_frames = 0
        # Sarsilmaz: son vurus zinciri bozmadan mi yendi (cizim/ses okur).
        self.poised_frames = 0

    # --- Durum sorgulari ----------------------------------------------------
    @property
    def invulnerable(self) -> bool:
        return self.iframes > 0 or self.dodge.invulnerable

    @property
    def busy(self) -> bool:
        return self.chain.busy or self.dodge.active or self.dead

    def knows(self, node_key: str) -> bool:
        """Yetenek agacindan bu dugum acik mi? (Hareketlerin tek kapisi.)"""
        return node_key in self.skills

    @property
    def sneak_ratio(self) -> float:
        """Sessiz yuruyus hizi. Sessiz Adim (IZ 3b) biraz hizlandiriyor."""
        if self.knows(skilltree.TRACE_QUIET):
            return SKILL_QUIET_SNEAK_RATIO
        return PLAYER_SNEAK_RATIO

    @property
    def noise_scale(self) -> float:
        """Adim/inis gurultusunun carpani (B15 okuyor). Sessiz Adim yariliyor."""
        return SKILL_QUIET_NOISE_SCALE if self.knows(skilltree.TRACE_QUIET) else 1.0

    @property
    def sight_scale(self) -> float:
        """Dusmanin seni fark etme menzili carpani (`Enemy._update_awareness`)."""
        return SKILL_QUIET_SIGHT_SCALE if self.knows(skilltree.TRACE_QUIET) else 1.0

    @property
    def state_name(self) -> str:
        if self.dead:
            return "olu"
        if self.dodge.active:
            return "kacinma"
        if self.chain.busy:
            return f"vurus{self.chain.index + 1}:{self.chain.phase.name.lower()}"
        if not self.body.grounded:
            return "havada"
        if abs(self.body.vx) > 0.2:
            return "kosu"
        return "bosta"

    # --- Ana guncelleme -----------------------------------------------------
    def update(self) -> None:
        if self.dead:
            self._update_dead()
            return

        # **Kontrol edilmeyen oyuncu komut almiyor** ama her seyi
        # yapmaya devam ediyor: yer cekimi, animasyon, dokunulmazlik,
        # ayak sesi. Bolum 17'de sahnede iki `Player` var ve girdiyi
        # yalnizca aktif olan aliyor (`docs/yapi.md` mekanik 10).
        #
        # Tek satir, cunku girdinin bu metoda tek bir girisi var.
        # `if self.controlled:` dallari serpistirmek ayni seyi bes
        # yerde tekrarlamak olurdu ve biri gunun birinde unutulurdu.
        inp = self.scene.game.input if self.controlled else NEUTRAL_INPUT
        if self.iframes > 0:
            self.iframes -= 1
        if self.hurt_frames > 0:
            self.hurt_frames -= 1
        self.flash.update()
        self.squash.update()
        self.trail.update()
        if self.land_frames > 0:
            self.land_frames -= 1
        if self.turn_frames > 0:
            self.turn_frames -= 1
        if self.brake_frames > 0:
            self.brake_frames -= 1
        # Kosarken yon degistirmek tek karede aynalanma degil, bir PIVOT.
        # Yavas yururken tetiklenmiyor: yerinde donen karakter surekli
        # pivot yapardi ve hareket "kaygan" gorunurdu.
        if (self.facing != self._last_facing and self.body.grounded
                and abs(self.body.vx) > TURN_PIVOT_MIN_SPEED):
            self.turn_frames = TURN_FRAMES
        self._last_facing = self.facing

        self.dodge.update(self.body.grounded)
        if self.combo.update():
            self.scene.on_combo_reset()
        self._tick_skill_moves()

        self.sneaking = False
        if self.control_locked > 0:
            self.control_locked -= 1
            self.hurt_frames = max(self.hurt_frames, 1)   # yerde
            self.body.approach_vx(0.0, 0.12)
        elif self.dodge.active:
            self._update_dodge()
        else:
            self._update_chain(inp)
            if not self.chain.busy or self.chain.phase is AttackPhase.RECOVERY:
                self._update_movement(inp)
            self._handle_actions(inp)

        self._apply_physics()
        self._update_ground_state()
        self._update_footsteps()
        self._update_animation()

    def _tick_skill_moves(self) -> None:
        """Yetenek hareketlerinin sayaclari. Hepsi kare cinsinden."""
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if not self.chain.busy:
            self.dashing = False
        if self.body.grounded:
            self.hover_frames = SKILL_HOVER_FRAMES
        if self.rally_frames > 0:
            self.rally_frames -= 1
            if self.rally_frames == 0:
                self.rally_pool = 0
        if self.poised_frames > 0:
            self.poised_frames -= 1

    def _update_footsteps(self) -> None:
        """Yerde ve saldirmiyorken alinan mesafeyi biriktirir.

        Esik asilinca `scene.on_player_step()` cagrilir - hangi ses
        calinacagina (yer tipine gore) sahne karar verir.
        """
        if not self.body.grounded or self.chain.busy:
            self._step_distance = 0.0
            return
        self._step_distance += abs(self.body.vx)
        if self._step_distance >= STEP_DISTANCE_PX:
            self._step_distance -= STEP_DISTANCE_PX
            on_step = getattr(self.scene, "on_player_step", None)
            if on_step:
                on_step(self)

    def _update_animation(self) -> None:
        update_animation(self)

    def _attack_progress(self) -> float:
        return attack_progress(self)

    def _update_movement(self, inp) -> None:
        move = inp.axis_x
        if abs(move) < 0.2:
            move = 0.0

        # Sessiz yuruyus: yon ayni, hiz kirpik. Havada degil - ziplamanin
        # yayini kisaltmak platformlari bozardi.
        self.sneaking = (move != 0.0 and self.body.grounded
                         and inp.held(Action.SNEAK))
        if self.sneaking:
            move = math.copysign(min(abs(move), self.sneak_ratio), move)

        # Saldiri sirasinda yon kontrolu kisitli - tamamen kilitlemek kotu
        # hissettirir, serbest birakmak vurusu anlamsizlastirir.
        authority = 1.0
        if self.chain.busy:
            authority = 0.45 if self.chain.phase is AttackPhase.RECOVERY else 0.0

        if move != 0.0 and authority > 0.0:
            self.facing = 1 if move > 0 else -1

        speed = PLAYER_RUN_SPEED * self.stats.move_multiplier
        accel = PLAYER_GROUND_ACCEL if self.body.grounded else PLAYER_AIR_ACCEL
        friction = (PLAYER_GROUND_FRICTION if self.body.grounded
                    else PLAYER_AIR_FRICTION)

        if move != 0.0 and authority > 0.0:
            self.body.approach_vx(move * speed * authority, accel)
            self.brake_frames = 0
        else:
            self._maybe_brake(speed)
            self.body.approach_vx(0.0, friction)

    def _maybe_brake(self, top_speed: float) -> None:
        """Tam hizdayken birakilan yon: ayak kayarak durur (gorsel gecis).

        Fizik degismiyor - surtunme ayni. Yalnizca poz ve bir tutam toz:
        durusun AGIRLIGI gorunsun.
        """
        if (self.brake_frames > 0 or self.chain.busy or not self.body.grounded
                or abs(self.body.vx) < top_speed * BRAKE_MIN_SPEED_RATIO):
            return
        self.brake_frames = BRAKE_FRAMES
        on_brake = getattr(self.scene, "on_player_brake", None)
        if on_brake:
            on_brake(self)

    def has(self, ability: str) -> bool:
        return ability in self.abilities

    def apply_skills(self, keys) -> None:
        """Kayittan gelen yetenekleri uygular.

        `PlayScene` sahne kurulurken cagiriyor. Duz bonuslar (can, zincir
        penceresi, kacinma sarji) **kurulus aninda** biniyor; carpanlar
        (hasar, savunma) her kullanimda toplayicilardan okunuyor.

        Duz bonuslar **tabandan** yeniden hesaplaniyor, ustune eklenmiyor:
        eski surum `+=` yapiyordu ve iki kez cagrilinca can iki kat
        artiyordu. Yetenek oyunun ortasinda da acilabildigi icin
        (`learn_skill`, duraklat menusu) bu artik gercek bir yol.
        """
        before = self.max_health
        self.skills = set(keys)
        self.max_health = (self.stats.max_health
                           + skilltree.max_health_bonus(self.skills))
        gained = self.max_health - before
        # Can bonusu gelince bos cubuk degil DOLU bolme ekleniyor: yeni
        # acilan "Tas Deri" hemen hissedilsin.
        self.health = max(1, min(self.max_health, self.health + max(0, gained)))
        # Taban pencere (`docs/dovus-sistemi.md`, BAGLAYICI) degismiyor;
        # yetenek onun USTUNE ekliyor.
        self.chain.window_frames = self._chain_window()
        if hasattr(self.dodge, "max_charges"):
            charges = (self.stats.dodge_charges
                       + skilltree.dodge_charge_bonus(self.skills))
            gained_charges = charges - self.dodge.max_charges
            self.dodge.max_charges = charges
            if gained_charges > 0:
                self.dodge.charges = min(charges,
                                         self.dodge.charges + gained_charges)

    def learn_skill(self, node_key: str) -> None:
        """Oyunun ORTASINDA acilan dugum (duraklat menusundeki agac).

        Kayit zaten `skilltree.unlock` ile guncellendi; burada yalnizca
        canli oyuncu yetisiyor - yoksa oyuncu bir sonraki bolume kadar
        acdigi seyi hissetmezdi.
        """
        self.apply_skills(self.skills | {node_key})

    def _chain_window(self) -> int:
        return self.stats.chain_window + skilltree.chain_window_bonus(self.skills)

    def equip(self, charm: str) -> bool:
        """Tilsim tak. Zaten takiliysa `False` doner."""
        if charm in self.charms:
            return False
        self.charms.add(charm)
        return True

    def grant(self, ability: str) -> bool:
        """Yetenek kazandirir. Zaten varsa False doner."""
        if ability in self.abilities:
            return False
        self.abilities.add(ability)
        if ability == abilities.SWORD:
            self.equip_weapon(weapons.SWORD)
        return True

    def equip_weapon(self, key: str) -> None:
        """Silah degistir - yumruktan kilica, ileride hancer/baltaya.

        Zincir tablosu tamamen degisir (`src/combat/weapons.py`); yarim
        kalmis bir vurusun ortasinda silah degismez cunku `grant()` bunu
        yalnizca ability kazanildigi anda cagirir, o an zaten `chain.busy`
        degildir (yetenek diyalog/sandik anlarinda verilir, dovus aninda
        degil). Sprite, ayni iskeletten cikan "_armed" varyanti varsa
        degisir - yumruk kendi "silahsiz" sprite'ini kullanmaya devam eder.
        """
        self.weapon = key
        weapon = weapons.get(key)
        # Pencere yetenek bonusuyla birlikte: `stats.chain_window` tek
        # basina yazilinca "Akis"in +2 karesi silah degisince kayboluyordu
        # (PlayScene yetenekleri silahtan ONCE uyguluyor).
        self.chain = ChainState(window_frames=self._chain_window(),
                                chain_table=weapon.chain)
        # Savurma izi silahin rengini tasiyor: Fisilti mor, orak celik.
        self.trail.chain = weapon.trail_chain
        self._apply_weapon_sprite()

    def _apply_weapon_sprite(self) -> None:
        suffix = weapons.get(self.weapon).sprite_suffix
        sprite_name = f"{self.stats.sprite_name}{suffix}"
        if sprite_name not in CHARACTERS:
            sprite_name = self.stats.sprite_name
        self.animator = Animator(sprite_name)
        # Sprite hucresi karakterden buyuk; ayak cizgisini govdenin altina
        # hizalamak icin gerekli. Bilinmezse karakter havada durur.
        self.sprite_foot_y = CHARACTERS[sprite_name].foot_y

    def _handle_actions(self, inp) -> None:
        # Kacinma once bakilir: saldiriyi iptal edebilir, akiciligin kalbi bu.
        if inp.buffered(Action.DODGE) and self._can_dodge():
            inp.consume(Action.DODGE)
            self._start_dodge(inp)
            return

        if inp.buffered(Action.JUMP) and self._can_jump():
            inp.consume(Action.JUMP)
            self._jump()

        # Degisken ziplama yuksekligi
        if not inp.held(Action.JUMP) and self.body.vy < 0.0 and self.jump_held:
            self.body.vy *= JUMP_CUT_MULTIPLIER
            self.jump_held = False

        # Yumruk bastan acik - silah yok sayisi degil, ilk silah. Kilic/hancer/
        # balta zaten `equip_weapon()` ile zincir tablosunu degistiriyor.
        if inp.buffered(Action.ATTACK):
            inp.consume(Action.ATTACK)
            self._request_attack()

    def _can_jump(self) -> bool:
        return (self.coyote_frames > 0 and not self.chain.busy
                and not self.dodge.active)

    def _can_dodge(self) -> bool:
        if not self.has(abilities.DODGE):
            return False
        if not self.dodge.can_dodge:
            return False
        # Vurus 1 ve 2'nin recovery'si iptal edilebilir; bitiricininki edilemez.
        if self.chain.busy and not self.chain.cancelable:
            return False
        return True

    def _jump(self) -> None:
        self.body.vy = -PLAYER_JUMP_SPEED
        self.coyote_frames = 0
        self.jump_held = True
        self.air_frames = 1
        self.squash.jump()
        self.scene.on_player_jump(self)

    def _update_ground_state(self) -> None:
        if self.body.grounded:
            self.coyote_frames = COYOTE_FRAMES
            if not self.body.was_grounded and self.air_frames > 10:
                self.squash.land()
                # Yuksekten inen daha uzun toparlanir - inisin bedeli
                # dususun boyuna bagli olmali.
                self.land_frames = (LAND_FRAMES_HARD
                                    if self.air_frames >= HARD_LAND_AIR_FRAMES
                                    else LAND_FRAMES_SOFT)
                self.scene.on_player_land(self, self.air_frames)
            self.air_frames = 0
        else:
            self.coyote_frames = max(0, self.coyote_frames - 1)
            self.air_frames += 1

    def _apply_physics(self) -> None:
        if not self.dodge.active:
            # Apex hafifligi: ziplamanin tepesinde yercekimi azalir, havadaki
            # kontrol suresi uzar.
            scale = (APEX_GRAVITY_SCALE
                     if abs(self.body.vy) < APEX_SPEED_THRESHOLD else 1.0)
            self.body.apply_gravity(scale)
            self._apply_hover()
        self.body.move(self.scene.tilemap)
        self.body.drop_through = False

    @property
    def hovering(self) -> bool:
        """Havada Asili (KESKIN 3b): havada vururken dusus yavasliyor."""
        return (self.chain.busy and not self.body.grounded
                and self.hover_frames > 0
                and self.knows(skilltree.BLADE_HOVER))

    def _apply_hover(self) -> None:
        """Yercekiminden SONRA: dusus tavani `SKILL_HOVER_FALL_SPEED`.

        Butce (`SKILL_HOVER_FRAMES`) yere basinca doluyor - sonsuz
        suzulme olmasin, ama her ziplamada bir hava zinciri sigsin.
        """
        if not self.hovering:
            return
        self.hover_frames -= 1
        if self.body.vy > SKILL_HOVER_FALL_SPEED:
            self.body.vy = SKILL_HOVER_FALL_SPEED

    # --- Kacinma ------------------------------------------------------------
    def _start_dodge(self, inp) -> None:
        direction = self.facing
        if abs(inp.axis_x) > 0.3:
            direction = 1 if inp.axis_x > 0 else -1
        self.facing = direction
        self.chain.cancel()
        self.dodge.start(direction)
        self.scene.on_player_dodge(self)

    def _update_dodge(self) -> None:
        # Kacinma boyunca yercekimi yok: mesafe tahmin edilebilir kalir.
        self.body.vx = self.dodge.direction * DODGE_SPEED
        self.body.vy = 0.0
        self.scene.on_dodge_trail(self)

    # --- Saldiri ------------------------------------------------------------
    def _request_attack(self) -> None:
        if self.chain.busy:
            self.chain.request_next()
            return
        self.dashing = self._can_dash()
        if self.dashing:
            self.dash_cooldown = SKILL_DASH_COOLDOWN
        self.chain.start(self.chain.next_index())
        self._apply_lunge()
        self._air_lift()
        if self.dashing:
            on_dash = getattr(self.scene, "on_player_dash", None)
            if on_dash:
                on_dash(self)
        self.scene.on_player_attack(self, self.chain.index)

    def _can_dash(self) -> bool:
        """Hamle (KESKIN 3a): yerde, KOSARKEN ve bakilan yone saldiri.

        Yavas yurumek ya da geri geri kacmak hamle yapmiyor - yoksa her
        ilk vurus bir atilisa donerdi ve kalabalikta kontrol kaybolurdu.
        """
        if not self.knows(skilltree.BLADE_DASH) or self.dash_cooldown > 0:
            return False
        if not self.body.grounded:
            return False
        top = PLAYER_RUN_SPEED * self.stats.move_multiplier
        return self.body.vx * self.facing >= top * SKILL_DASH_MIN_SPEED

    def _apply_lunge(self) -> None:
        if self.dashing:
            self.body.vx = self.facing * SKILL_DASH_LUNGE
            return
        lunge = LUNGE_BY_INDEX[min(self.chain.index, len(LUNGE_BY_INDEX) - 1)]
        if not self.body.grounded:
            lunge *= 0.55
        self.body.vx = self.facing * lunge

    def _air_lift(self) -> None:
        """Havada Asili: her hava vurusunun basinda dusus durup hafif kalkiyor.

        "Asili kalma" hissinin kendisi bu - tavan tek basina yalnizca
        yavaslatiyor, bu an ise vurusun havayi TUTTUGUNU gosteriyor.
        """
        if self.body.grounded or self.hover_frames <= 0:
            return
        if self.knows(skilltree.BLADE_HOVER):
            self.body.vy = min(self.body.vy, -SKILL_HOVER_LIFT)

    def _update_chain(self, inp) -> None:
        event = self.chain.update()
        if event == "spawn_hitbox":
            self._spawn_attack_hitbox()
        elif event == "chain":
            # Hamle yalniz zincirin ilk vurusu - devaminda normal atilis.
            self.dashing = False
            self._apply_lunge()
            self._air_lift()
            self.scene.on_player_attack(self, self.chain.index)
        if self.dashing and self.chain.phase is not AttackPhase.RECOVERY:
            on_trail = getattr(self.scene, "on_dash_trail", None)
            if on_trail:
                on_trail(self)

    def _spawn_attack_hitbox(self) -> None:
        spec = self.chain.spec
        finisher = self.chain.is_finisher
        weapon = weapons.get(self.weapon)
        # Silahin kendi menzili (`combat/weapons.py`): mizrak uzun ve dar,
        # orak biraz genis. Kilic/hancer/balta eski degerlerinde.
        reach = (FINISHER_REACH if finisher else ATTACK_REACH) + weapon.reach_bonus
        height = max(8, (FINISHER_HEIGHT if finisher else ATTACK_HEIGHT)
                     - weapon.height_trim)

        damage = spec.damage
        is_counter = self.dodge.consume_counter()
        if is_counter:
            damage = counter_damage(damage, self.stats.counter_bonus)
        # Tilsim carpani vurus **uretilirken** biniyor; sonradan duzeltmek
        # olum esigini kaydirirdi (src/systems/charms.py).
        if self.charms:
            scale = charms.damage_scale(self.charms, self)
            if scale != 1.0:
                damage = max(1, round(damage * scale))
        # Yetenek agaci carpani da AYNI YERDE biniyor - tilsimla ayni
        # gerekce, ve ikisi carpimsal birlesiyor (bir dugum + bir tilsim
        # ust uste gelirse ikisi de sayiliyor).
        if self.skills:
            skill_scale = skilltree.damage_scale(self.skills, self)
            if skill_scale != 1.0:
                damage = max(1, round(damage * skill_scale))
        knockback = spec.knockback
        poise = 2 if finisher else 1
        if self.dashing:
            # Hamle: uzun, agir ve SENDELETEN bir vurus - mesafeyi kapatan
            # vurus ilk temasta dusmani durdurabilmeli.
            reach += SKILL_DASH_REACH
            damage = max(1, round(damage * SKILL_DASH_DAMAGE_SCALE))
            knockback *= 1.5
            poise = 2
        self.last_hit_was_counter = is_counter

        box = Hitbox(
            rect=melee_rect(self.body, self.facing, reach, height),
            damage=damage,
            owner=self,
            targets=Team.ENEMY | Team.BREAKABLE,
            knockback=knockback,
            knockback_up=1.4 if finisher else 0.6,
            active_frames=spec.active,
            poise_damage=poise,
            is_finisher=finisher,
            is_counter=is_counter,
            pierce=finisher or self.dashing,
        )
        if self.dashing:
            # Govde hala atiliyor: kutu onunla birlikte ilerlesin, yoksa
            # oyuncu kendi vurusunun ONUNE gecerdi.
            box.follow = self
            box.offset = (2 + reach // 2, 0)
        self.scene.hitboxes.spawn(box)
        self.scene.on_attack_swing(self, box)
        if finisher and weapon.finisher:
            self._finisher_effect(weapon, box, height)
        if finisher and self.knows(skilltree.BLADE_FINISHER):
            self._blade_wave(weapon, box)

    def _blade_wave(self, weapon, box: Hitbox) -> None:
        """Kilic Dalgasi (KESKIN 5): bitirici ileri ucan bir kesik firlatiyor.

        Fisilti'nin bitiricisi zaten bir dalga - ikinci bir dalga ust uste
        binip gurultu olurdu. Orada yetenek dalganin kendisini
        guclendiriyor (`_finisher_effect`).
        """
        if weapon.finisher == weapons.FINISHER_WAVE:
            return
        rect = pygame.Rect(0, 0, 12, 20)
        rect.center = (int(self.body.center_x + self.facing * 16),
                       int(self.body.center_y))
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect,
            damage=max(1, round(box.damage * SKILL_WAVE_DAMAGE_RATIO)),
            owner=self, targets=Team.ENEMY | Team.BREAKABLE,
            knockback=2.4, knockback_up=0.8, active_frames=SKILL_WAVE_LIFE,
            poise_damage=1, pierce=True, stop_on_solid=True,
            velocity=(self.facing * SKILL_WAVE_SPEED, 0.0),
            visual="blade_wave",
        ))
        self.scene.game.play_sound("swing_heavy")

    def _finisher_effect(self, weapon, box: Hitbox, height: int) -> None:
        """Silaha ozel bitirici - zincirin sonu silahin imzasi.

        wave   Fisilti: ileri ucan, delici bir ses dalgasi (mor)
        lunge  Iz Mizragi: bitiricide one atilma - mesafeyi kapatiyor
        sweep  Zincir Orak: ayni vurus ARKAYA da - iki yandan gelene
        """
        from src.config import (SICKLE_BACK_REACH, SPEAR_LUNGE,
                                WHISPER_WAVE_DAMAGE, WHISPER_WAVE_LIFE,
                                WHISPER_WAVE_SPEED)
        if weapon.finisher == weapons.FINISHER_WAVE:
            rect = pygame.Rect(0, 0, 10, 16)
            rect.center = (int(self.body.center_x + self.facing * 14),
                           int(self.body.center_y))
            damage = WHISPER_WAVE_DAMAGE
            if self.knows(skilltree.BLADE_FINISHER):
                # Kilic Dalgasi Fisilti'da ikinci dalga degil, ayni dalga
                # daha agir (`_blade_wave`).
                damage += round(box.damage * SKILL_WAVE_DAMAGE_RATIO)
            self.scene.hitboxes.spawn(Hitbox(
                rect=rect, damage=damage, owner=self,
                targets=Team.ENEMY | Team.BREAKABLE, knockback=2.0,
                knockback_up=0.6, active_frames=WHISPER_WAVE_LIFE,
                poise_damage=1, pierce=True, stop_on_solid=True,
                velocity=(self.facing * WHISPER_WAVE_SPEED, 0.0),
                visual="echo_wave",
            ))
            self.scene.game.play_sound("echo_open")
        elif weapon.finisher == weapons.FINISHER_LUNGE:
            self.body.vx = self.facing * SPEAR_LUNGE
        elif weapon.finisher == weapons.FINISHER_SWEEP:
            self.scene.hitboxes.spawn(Hitbox(
                rect=melee_rect(self.body, -self.facing, SICKLE_BACK_REACH,
                                height),
                damage=box.damage, owner=self,
                targets=Team.ENEMY | Team.BREAKABLE,
                knockback=box.knockback, knockback_up=box.knockback_up,
                active_frames=box.active_frames, poise_damage=2,
                is_finisher=True, pierce=True,
            ))

    def notify_kill(self) -> None:
        """Bir dusman oldu: recovery iptal olur (kill cancel).

        Kalabalik dovusun "bicip gecme" hissi tek basina bundan gelir.
        """
        self.chain.kill_cancel()

    def register_hit(self) -> None:
        """Vurus degdi: combo sayacini ilerlet."""
        for threshold in self.combo.register_hit():
            self.scene.on_combo_threshold(self, threshold)

    def on_dealt_damage(self, amount: int) -> int:
        """Toparlanma (TAS 3b): karsilik vurdukca yenen canin bir kismi doner.

        Havuz yalniz son darbeden sonraki `SKILL_RALLY_FRAMES` boyunca
        acik: geri cekilen oyuncu havuzu kaybediyor, karsilik veren
        kazaniyor. Iyilesen miktari doner (HUD/ses icin).
        """
        if self.rally_pool <= 0 or self.rally_frames <= 0 or self.dead:
            return 0
        heal = min(self.rally_pool,
                   max(1, round(amount * SKILL_RALLY_HEAL_RATIO)),
                   self.max_health - self.health)
        if heal <= 0:
            return 0
        self.heal(heal)
        self.rally_pool -= heal
        return heal

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, box, direction):
        if self.dead or self.invulnerable:
            return DamageResult(hit=False)
        # 1. Kalkan - oyuncunun BILEREK aldigi sey, sessiz aftan once
        #    harcaniyor (docs/plan-kalkan.md kural 6).
        if self._shield_absorbs(box, direction):
            return DamageResult(hit=False, blocked=True)
        # Yanki acikken savunma duser - bedelin en somut parcasi.
        # Carpani hasar **uygulanmadan** once bindiriyoruz; sonradan
        # duzeltmek olum esigini kaydirirdi.
        echo = getattr(self.scene, "echo", None)
        original = box.damage
        if echo is not None and echo.active:
            box.damage = max(1, round(box.damage * echo.damage_multiplier))
        # Yetenek agacinin SAVUNMA carpani (TAS dali + Yanki SIPER'i).
        # `<1.0` koruma demek. Yanki cezasindan SONRA biniyor: siper
        # yeteneginin isi tam olarak o cezayi hafifletmek, o yuzden onun
        # ustune uygulanmali - once uygulansaydi ceza siperi yutardi.
        if self.skills:
            guard = skilltree.defence_scale(self.skills, self)
            if guard != 1.0:
                box.damage = max(1, round(box.damage * guard))
        # 2. Son sans (CLAUDE.md 8) - butun indirimlerden SONRA: olup
        #    olmedigine son hasar karar veriyor.
        self._spare_last_chance(box)
        poised = self._poised(box)
        velocity = (self.body.vx, self.body.vy)
        try:
            result = super().take_damage(box, direction)
        finally:
            box.damage = original
        if result.hit:
            if poised and not result.killed:
                # Sarsilmaz: darbe yendi ama zincir ve durus bozulmadi.
                self.body.vx, self.body.vy = velocity
                self.poised_frames = HURT_ANIMATION_FRAMES
                on_poised = getattr(self.scene, "on_player_poised", None)
                if on_poised:
                    on_poised(self)
            else:
                self.chain.cancel()
                self.hurt_frames = HURT_ANIMATION_FRAMES
            self.combo.reset()
            self._fill_rally(result.amount)
            self.scene.on_player_hurt(self, result)
        return result

    def _shield_absorbs(self, box, direction) -> bool:
        """Eski Kalkan (Mum Bekcisi, tek kullanimlik): ILK darbeyi karsilar.

        Hasar yok ama darbe var: geri itme yariya iniyor, oyuncu bir
        seyin oldugunu hissediyor. Ardindan kisa bir dokunulmazlik - cok
        vuruslu saldirida (zincir, suru) ikinci vurus satin almayi bosa
        cikarmasin. Kacinmanin dokunulmazliginda buraya hic gelinmiyor
        (`HitboxManager` dokunulmazi atliyor), yani kalkan bosa yanmiyor.
        """
        data = getattr(self.scene, "save_data", None)
        if box.damage <= 0 or not consumables.spend(data, consumables.SHIELD):
            return False
        length = max(1e-5, math.hypot(direction[0], direction[1]))
        push = box.knockback * SHIELD_KNOCKBACK_SCALE
        self.body.vx = direction[0] / length * push
        self.body.vy = -box.knockback_up * SHIELD_KNOCKBACK_SCALE
        self.iframes = SHIELD_IFRAMES
        self.chain.cancel()
        on_break = getattr(self.scene, "on_shield_broken", None)
        if on_break:
            on_break(self, box, direction)
        return True

    def _spare_last_chance(self, box) -> None:
        """Son sans (CLAUDE.md 8): %15'in altindayken oldurucu darbe 1 can birakir.

        **Oyuncuya asla soylenmez** - ne yazi ne ses. Bolum basina bir kez;
        sayac sahnede, cunku olup yeniden dogmak bolumu yeniden baslatmiyor.
        """
        if box.damage < self.health:
            return
        if self.health >= self.max_health * LAST_CHANCE_HEALTH_RATIO:
            return
        left = int(getattr(self.scene, "last_chance_left", 0) or 0)
        if left <= 0:
            return
        self.scene.last_chance_left = left - 1
        box.damage = max(0, self.health - 1)

    def _poised(self, box) -> bool:
        """Sarsilmaz (TAS 5): saldirirken hafif darbeler zinciri bozmuyor."""
        return (self.chain.busy and box.damage <= SKILL_POISE_MAX_DAMAGE
                and self.knows(skilltree.STONE_POISE))

    def _fill_rally(self, amount: int) -> None:
        """Toparlanma havuzu - yenen darbenin `SKILL_RALLY_POOL_RATIO`i."""
        if amount <= 0 or self.dead or not self.knows(skilltree.STONE_RALLY):
            return
        room = self.max_health - self.health
        self.rally_pool = min(room, self.rally_pool
                              + round(amount * SKILL_RALLY_POOL_RATIO))
        self.rally_frames = SKILL_RALLY_FRAMES

    def die(self) -> None:
        super().die()
        self.rally_pool = 0
        self.rally_frames = 0
        self.scene.on_player_died(self)

    def _update_dead(self) -> None:
        self.body.approach_vx(0.0, PLAYER_GROUND_FRICTION)
        self.body.apply_gravity()
        self.body.move(self.scene.tilemap)
        self.flash.update()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        draw_player(self, surface, offset)

    def debug_lines(self) -> list[str]:
        return [
            f"{self.stats.name}  {self.state_name}",
            f"can {self.health}/{self.max_health}  combo {self.combo.count}"
            f" (en iyi {self.combo.best})",
            f"kacinma sarj {self.dodge.charges}  "
            f"karsi {self.dodge.counter_window_left}  "
            f"coyote {self.coyote_frames}",
        ]
