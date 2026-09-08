"""Nefes - `docs/korku.md` 5.1.

Kaynakta tek satiri yoktu ve belge onu "en ucuz kazanc" diye
isaretliyor. Nefes bir efekt degil: oyuncunun Rey ile **ayni bedende**
oldugunu hatirlatan sey.

## Nefes SUREKLI degil

En onemli karar bu. Nefes hep duyulsaydi arka plan gurultusune
donusurdu ve iki hafta sonra kimse duymazdi. Uc durumda calisiyor,
digerlerinde **tamamen susuyor**:

    can %25 altinda        yaralisin
    Yanki acik             bedelin duyulabilir hali
    karanlikta hareketsiz  <-- asil olan

Nefesin *baslamasi* sinyalin kendisi. Sessizken sessiz, baslayinca fark
ediliyor.

## Ucuncusu neden asil olan

Oyuncu durup dusunmek istedigi anda oyun ona durmanin da bir maliyeti
oldugunu hissettiriyor. Hicbir sayi dusmuyor, hicbir uyari cikmiyor,
hicbir mekanik ceza yok - sadece nefes hizlaniyor. Baski **tamamen**
sesle kuruluyor.

## Alis ve verisi ayri sesler

Tek ses dongude calinsa mekanik bir tekrar olurdu. `sfx_horror.py`
ikisini asimetrik uretiyor (alis kisa/keskin, verisi uzun/dagilan) ve
burasi sirayla caliyor.

## Kalp atisi ayri esik

Can %12'nin altina inince nefese kalp atisi ekleniyor. Bu, can barina
bakmadan "olmek uzeresin" diyen ikinci kanal - `CLAUDE.md` 9'un
diegetik gostergeler ilkesi.
"""
from __future__ import annotations

from src.systems import horror

# Kare cinsinden nefes araliklari. Kucuk = hizli.
PERIOD_HURT = 74            # Can %25 altinda
PERIOD_ECHO = 96            # Yanki acik
PERIOD_STILL_DARK = 62      # Karanlikta hareketsiz - en hizlisi

HURT_RATIO = 0.25
HEARTBEAT_RATIO = 0.12
HEARTBEAT_PERIOD = 108

# Karanlikta bu kadar kare hareketsiz durulunca nefes basliyor. Kisa
# tutulursa her duraklamada tetikleniyor ve numara yipraniyor; 1.5
# saniye "durdu ve dinliyor" demek.
STILL_FRAMES = 90
STILL_SPEED = 0.12          # Bunun altindaki hiz "hareketsiz" sayiliyor


class Breath:
    """Oyuncunun nefesi. Sahne her karede `update()` cagirir."""

    __slots__ = ("timer", "heart_timer", "still_frames", "exhale", "active")

    def __init__(self) -> None:
        self.timer = 0
        self.heart_timer = 0
        self.still_frames = 0
        self.exhale = False      # Sirada verme mi var?
        self.active = False      # Su an nefes duyuluyor mu (hata ayiklama)

    def reset(self) -> None:
        self.timer = 0
        self.heart_timer = 0
        self.still_frames = 0
        self.exhale = False
        self.active = False

    # --- Karar --------------------------------------------------------------
    def _period(self, scene) -> int:
        """Bu karede nefes araligi kac kare? 0 = nefes yok.

        Birden fazla kosul saglaniyorsa **en hizlisi** kazaniyor: can
        dusukken karanlikta durmak, ikisinin ortalamasi kadar degil en
        az ikisi kadar korkutucu olmali.
        """
        player = getattr(scene, "player", None)
        if player is None or getattr(player, "dead", False):
            return 0

        periods: list[int] = []

        max_health = max(1, getattr(player, "max_health", 1))
        ratio = getattr(player, "health", max_health) / max_health
        if ratio <= HURT_RATIO:
            periods.append(PERIOD_HURT)

        echo = getattr(scene, "echo", None)
        if echo is not None and getattr(echo, "active", False):
            periods.append(PERIOD_ECHO)

        if self.still_frames >= STILL_FRAMES and _in_darkness(scene):
            periods.append(PERIOD_STILL_DARK)

        return min(periods) if periods else 0

    def _track_stillness(self, scene) -> None:
        player = getattr(scene, "player", None)
        if player is None:
            self.still_frames = 0
            return
        body = getattr(player, "body", None)
        moving = (body is not None
                  and (abs(getattr(body, "vx", 0.0)) > STILL_SPEED
                       or abs(getattr(body, "vy", 0.0)) > STILL_SPEED))
        busy = getattr(player, "busy", False)
        if moving or busy:
            self.still_frames = 0
        else:
            self.still_frames += 1

    # --- Dongu --------------------------------------------------------------
    def update(self, game, scene) -> None:
        self._track_stillness(scene)

        # Katman 2 kapaliysa nefes hic calismaz - ama sayaclar yine de
        # ilerliyor ki ayar oyun ortasinda acilinca durum tutarli olsun.
        if not horror.atmosphere(game.settings):
            self.active = False
            return

        period = self._period(scene)
        self.active = period > 0
        if not self.active:
            # Sayaci sifirlamiyoruz **bilerek**: tehlikeden cikip tekrar
            # girince nefes bastan baslamiyor, kaldigi yerden suruyor.
            # Bu, nefesin bir sayac degil bir durum olmasini sagliyor.
            return

        self.timer += 1
        if self.timer >= period:
            self.timer = 0
            game.play_sound("breath_out" if self.exhale else "breath_in",
                            bus="volume_sfx",
                            volume=horror.loudness(game.settings))
            self.exhale = not self.exhale

        self._update_heartbeat(game, scene)

    def _update_heartbeat(self, game, scene) -> None:
        player = getattr(scene, "player", None)
        if player is None:
            return
        max_health = max(1, getattr(player, "max_health", 1))
        if getattr(player, "health", max_health) / max_health > HEARTBEAT_RATIO:
            self.heart_timer = 0
            return
        self.heart_timer += 1
        if self.heart_timer >= HEARTBEAT_PERIOD:
            self.heart_timer = 0
            game.play_sound("heartbeat", bus="volume_sfx",
                            volume=horror.loudness(game.settings) * 0.8)

    def debug_line(self) -> str:
        return (f"nefes {'acik' if self.active else 'kapali'}  "
                f"hareketsiz {self.still_frames}")


def _in_darkness(scene) -> bool:
    """Oyuncu karanlikta mi?

    `LightState` yalnizca Bolum 3'te var (mesale ekonomisi). Diger
    bolumlerde isik sistemi yok, o yuzden sahne kendi cevabini
    verebiliyor: `dark_ambient = True` diyen bir bolum, oyuncu
    hareketsiz kalinca nefesi duyurur.

    Ikisi de yoksa cevap `False` - yani nefes yalnizca can ve Yanki
    kosullarindan gelir. Sessizce yanlis calismaktansa hic calismasin.
    """
    light = getattr(scene, "light", None)
    if light is not None:
        player = getattr(scene, "player", None)
        if player is None:
            return False
        return not light.in_light(player.body.center_x, player.body.center_y)
    return bool(getattr(scene, "dark_ambient", False))
