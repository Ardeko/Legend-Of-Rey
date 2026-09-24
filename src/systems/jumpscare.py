"""Jumpscare - oyunun tek sok ani (`docs/korku.md` 6.1).

Arda, 08.09.2026: *"mutlaka bir yerde jumpscare olsun."*

## Ucuz olmamasinin tek yolu: on bolumluk bir kurulumun karsiligi

Izleyen'in kurali uc bolum boyunca ogretiliyor:

    B5   ilk gorulur   yaklasirsan geri cekilir
    B11  ikinci kez    yine geri cekilir
    B13  ucuncu kez    Cemo ona bakar, yine geri cekilir
    B14  ...

Oyuncu tek bir sey ogrendi: **bu sey sana yaklasmaz.** Sonra B14'te,
Rey'in Yanki'nin ne oldugunu anladigi karede, Izleyen tam onunde
beliriyor.

Korkutucu olan ani hareket degil, **kuralin bozuldugunun anlasilmasi.**

## Sok SESIN GELMESIYLE degil, GELMEMESIYLE kuruluyor

Kare tablosu (`docs/korku.md` 6.1'den birebir):

    0       muzik ve butun ortam sesi kesilir
    1-44    hicbir sey. ~0,75 saniye tam sessizlik. Oyuncu OYNAYABILIR
    45      Izleyen ekranin ortasinda, oyuncunun iki tile onunde,
            ekranin %70'ini kaplayacak olcekte. Tek kare parlama,
            tek sert ses
    46-51   alti kare durur. Gozler oyuncuda
    52      yok olur. **Ses geri gelmez** - B14'un kalani sessiz oynanir

`player.control_locked = 20` yalnizca 45-65 arasi: Rey donuyor
(irkilme), oyun donmuyor. Yirmi kare bir kacinmadan kisa.

## 25.09.2026 - daha korkunc (Arda)

*"Jumpscare'li bolum daha korkunc olsun."* Eski hali olculup bakildi:
Izleyen **alti kare** (0,1 sn) ekrandaydi - goz onu korku degil bir
aksaklik olarak okuyordu. Goruntu 32 piksellik govdenin 6x buyutulmus
haliydi: koyu zemin ustunde koyu bir sutun, yuz yok. Sessizlik 0,75
saniyeydi; gerilimin birikmesine yetmiyordu.

Yeni tablo (kural ayni: **sesin gelmemesiyle kuruluyor**):

    0         muzik ve ortam kesilir
    1-109     ~1,8 sn tam sessizlik. 50'den sonra kenarlar YAVASCA
              karariyor - bir sey yaklasiyor ama ne oldugu yok
    110-114   Izleyen'in YUZU kameraya dogru atiliyor (bes boyut,
              `src/art/horror_face.py`), tek kare parlama, tek sert ses,
              radyal sarsinti. Rey irkiliyor (20 kare kilit)
    115-127   yuz ekrani dolduruyor, titriyor. Gozler oyuncuda
    128-135   KESME: tam karanlik
    136-177   karanlikta iki goz kaliyor ve soner. Kalp carpiyor
    180       bitti. Ses geri gelmiyor - B14'un kalani sessiz

Ihanet bildirimi (`chapter14.betrayed`) sokun SONUNA alindi:
sessizlik sirasinda ekranda yazi durursa gerilim dagiliyor.

## Kurallara uyum

  * **Oynanisi durdurmuyor**: kamera alinmiyor, ara sahne acilmiyor,
    oyuncu ekranda kaliyor.
  * **Ayni numara iki kez yok**: oyunda bir tane var, ve `done`
    bayragi ikinciyi imkansiz kiliyor.
  * **Fotosensitivite**: `flash_allowed` kapaliysa parlama atlaniyor,
    olay atlanmiyor - erisilebilirlik icerigi kaldirmaz, sunumu
    degistirir.
"""
from __future__ import annotations

from src.config import TILE_SIZE
from src.systems import horror

# Kare tablosu - `docs/korku.md` 6.1 ile birebir (25.09.2026 guncel).
HUSH_AT = 0
# Karartma kenardan iceri sizmaya bundan sonra basliyor.
CREEP_FROM = 50
APPEAR_AT = 110
# Hamle: yuz bu kadar karede tam boya ulasiyor.
LUNGE_FRAMES = 5
VANISH_AT = 128
# Kesme: yuz gidince tam karanlik.
BLACKOUT_UNTIL = 136
# Karanlikta kalan gozler bu kareye kadar sonuyor.
EYES_UNTIL = 178
UNLOCK_AT = 180
# Kalp: kesmeden hemen sonra ve bir kez daha.
HEARTBEAT_AT = (136, 160)
# Hamle boyunca yuzun boylari (piksel). Son boy ekranin ~%86'si.
FACE_HEIGHTS = (70, 110, 150, 190, 232)

# Oyuncunun kac tile onunde.
AHEAD_TILES = 2
# Rey'in donma suresi. Bir kacinma 18 kare; bu ondan biraz uzun ama
# oyunu durdurmuyor.
CONTROL_LOCK = 20


class Jumpscare:
    """Tek seferlik sok. `arm()` ile kuruluyor, `update()` sayiyor."""

    __slots__ = ("frames", "armed", "done", "x", "feet_y", "facing")

    def __init__(self) -> None:
        self.frames = -1
        self.armed = False
        self.done = False
        self.x = 0.0
        self.feet_y = 0.0
        self.facing = 1

    # --- Durum --------------------------------------------------------------
    @property
    def running(self) -> bool:
        return self.armed and not self.done

    @property
    def visible(self) -> bool:
        """Izleyen'in yuzu su an ekranda mi."""
        return self.armed and APPEAR_AT <= self.frames < VANISH_AT

    @property
    def height(self) -> int:
        """Yuzun tam boyu - hamlenin sonu."""
        return FACE_HEIGHTS[-1]

    @property
    def face_height(self) -> int:
        """Bu karedeki yuz boyu: hamle bes boydan geciyor."""
        step = max(0, self.frames - APPEAR_AT)
        return FACE_HEIGHTS[min(len(FACE_HEIGHTS) - 1, step)]

    @property
    def lunge(self) -> float:
        """Hamlenin ilerlemesi 0..1."""
        if self.frames < APPEAR_AT:
            return 0.0
        return min(1.0, (self.frames - APPEAR_AT) / LUNGE_FRAMES)

    @property
    def creep(self) -> float:
        """Sessizlikte kenardan iceri sizan karartma 0..1."""
        if not self.armed or self.frames < CREEP_FROM:
            return 0.0
        if self.frames >= APPEAR_AT:
            return 0.0
        return (self.frames - CREEP_FROM) / (APPEAR_AT - CREEP_FROM)

    @property
    def blackout(self) -> bool:
        """Kesme: yuz gitti, ekran tam karanlik."""
        return self.armed and VANISH_AT <= self.frames < BLACKOUT_UNTIL

    @property
    def afterglow(self) -> float:
        """Karanlikta kalan gozlerin parlakligi 1..0."""
        if not self.armed or not BLACKOUT_UNTIL <= self.frames < EYES_UNTIL:
            return 0.0
        return 1.0 - (self.frames - BLACKOUT_UNTIL) / (EYES_UNTIL
                                                       - BLACKOUT_UNTIL)

    # --- Akis ---------------------------------------------------------------
    def arm(self, player) -> bool:
        """Sayaci baslatir. Bir kez - ikincisi reddediliyor."""
        if self.armed or self.done:
            return False
        self.armed = True
        self.frames = -1
        body = player.body
        self.facing = getattr(player, "facing", 1)
        self.x = body.center_x + self.facing * AHEAD_TILES * TILE_SIZE
        self.feet_y = body.feet[1]
        return True

    def update(self, game, player) -> None:
        """Bir kare ilerlet ve tablodaki isleri yap."""
        if not self.running:
            return
        self.frames += 1
        frame = self.frames

        if frame == HUSH_AT:
            # **Ses kesiliyor ve geri gelmiyor.** Sokun kurulumu bu.
            game.music_hush = 1.0

        elif frame == APPEAR_AT:
            game.play_sound("watcher_strike")
            game.play_sound("breath_sharp")
            # Rey irkiliyor - OYUN donmuyor.
            player.control_locked = max(getattr(player, "control_locked", 0),
                                        CONTROL_LOCK)

        elif frame in HEARTBEAT_AT:
            game.play_sound("heartbeat")

        elif frame >= UNLOCK_AT:
            # Bitti. `music_hush` **bilerek** geri alinmiyor: belge
            # "ses geri gelmez, B14'un kalani sessiz oynanir" diyor.
            self.armed = False
            self.done = True

    def flash(self, settings) -> float:
        """Beliris karesinde tek kare parlama - 0 ise cizilmiyor.

        `flash_limit` acikken sifir donuyor ama olay yine oluyor.
        """
        if self.frames != APPEAR_AT:
            return 0.0
        if not horror.flash_allowed(settings):
            return 0.0
        return 1.0


def allowed(settings) -> bool:
    """Katman 3 acik mi (`docs/korku.md` 8)."""
    return horror.shock(settings)
