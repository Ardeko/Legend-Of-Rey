"""Yalan defteri - `docs/korku.md` 4.1.

## Duzeltilen sey bir eksiklik degil, TERS calisan bir tasarimdi

`LIE_CHANCE` oyunun basindan beri calisiyor: bulanik kademede %35,
sessizde %100 ihtimalle Yanki yalan soyluyor. Ama oyun bunu
**hatirlamiyordu**, dolayisiyla oyuncu asla ogrenemiyordu. Zar atiliyor,
cevap bozuluyor, oyuncu yanlis yere gidiyor ve *"ben yanlis anladim"*
diyordu.

Yani Yanki'nin yalani, **oyuncunun kendi hatasi gibi okunuyordu.** Bir
mekanigin tam tersine calismasi bundan ibarettir.

## Yakalanmak yalanin kendisinden onemli

Bu modul yalan uretmiyor - `echo.ask()` zaten uretiyor. Bu modul yalanin
**yakalanmasini** mumkun kiliyor: her yalan kayda geciyor ve oyuncu onu
curuten seyi buldugunda (kolye tersini gosteriyor, gosterilen "gizli
oda" duz duvar cikiyor, isaretlenen dusman zaten olu) sistem fark
ediyor.

Sonra Yanki **susuyor**. Uc saniye. Ne aciklama, ne ozur.

## Neden ozur yok

Ozur dileyen bir ses **karakter** olur; konuyu degistiren bir ses
**tehdit** kalir (`docs/korku.md` kural 5). Uc saniyelik bosluk,
soylenebilecek her cumleden daha cok sey soyluyor.

## Sayac gorunmuyor

Oyuncuya "2 yalan yakaladin" diye bir arayuz cizilmiyor. Ilk seferde
"tuhaf" der, ikincide durur, ucuncude sormaya korkar. Sayilirsa bir
mekanik olur; sayilmazsa bir his kalir.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Yalan yakalandiginda Yanki bu kadar kare susar. 180 kare = 3 saniye.
# Kisa tutuldugunda fark edilmiyor, uzun tutuldugunda oyuncu oyunun
# bozuldugunu saniyor - olculdu ve 3 saniyede karar kilindi.
SILENCE_FRAMES = 180

# Bir yalan bu kadar kare sonra "unutuluyor". Oyuncu on dakika sonra
# alakasiz bir duvara carpip eski bir yalani yakalamis sayilmamali.
STALE_FRAMES = 60 * 60 * 3


@dataclass
class Lie:
    """Soylenmis tek bir yalan.

    `where` piksel cinsinden oyuncunun konumu - yalanin nerede
    soylendigi, curutuldugu yerle karsilastirilabilsin diye.
    """

    frame: int
    where: tuple[float, float]
    direction: int = 0          # Yanki'nin gosterdigi yon (-1/0/1)
    caught: bool = False


@dataclass
class LieLedger:
    """Bir bolumdeki yalanlar. Sahne tutar, kayda YAZILMAZ.

    Kalicilik bilincli olarak yok: yalanlarin hafizasi oyuncunun
    kafasinda olmali, kayit dosyasinda degil. Bolum bitince defter
    kapaniyor, his kaliyor.
    """

    entries: list[Lie] = field(default_factory=list)
    silence_frames: int = 0
    caught_count: int = 0
    _frame: int = 0

    # --- Kayit --------------------------------------------------------------
    def record(self, where: tuple[float, float], direction: int = 0) -> Lie:
        """Yanki yalan soyledi. Deftere yaz."""
        entry = Lie(frame=self._frame, where=where, direction=direction)
        self.entries.append(entry)
        return entry

    @property
    def pending(self) -> list[Lie]:
        """Henuz yakalanmamis ve **hala taze** yalanlar."""
        return [e for e in self.entries
                if not e.caught and self._frame - e.frame <= STALE_FRAMES]

    # --- Yakalama -----------------------------------------------------------
    def catch(self) -> bool:
        """Bekleyen en eski yalan curutuldu.

        `True` donerse sahne sessizligi baslatmali. Bekleyen yalan yoksa
        `False` - yani "yanlis bir sey buldum" demek her zaman
        "yalan yakaladim" demek degil.
        """
        waiting = self.pending
        if not waiting:
            return False
        waiting[0].caught = True
        self.caught_count += 1
        self.silence_frames = SILENCE_FRAMES
        return True

    @property
    def silenced(self) -> bool:
        """Yanki su an susuyor mu? Sahne buna bakip repligi yutuyor."""
        return self.silence_frames > 0

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        self._frame += 1
        if self.silence_frames > 0:
            self.silence_frames -= 1

    def debug_line(self) -> str:
        return (f"yalan {len(self.entries)} soylendi / {self.caught_count} "
                f"yakalandi  sus {self.silence_frames}")
