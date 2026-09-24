"""Eve donus - kapanisin ve epilogun ortak bilgisi.

`DawnCinematic`'ten jenerige kadar dort sahne ayni seyi biliyor:
oyuncu kimdi, B15'te kimseyi uyandirmadan mi gecti, B16'da hangi jesti
yapti, Kalachev oldu mu, kac kez dustu. Her sahne bunu kayittan ayri
ayri okusaydi dort ayri okuma dort ayri hata firsati olurdu (ayni
ders `play.py`'de `sense_betrayed` icin yazili). Burada bir kez
okunuyor ve sahneden sahneye **nesne olarak** tasiniyor.

Kaynak her zaman kayit (`from_save`). Testler ve dogrudan sahne
acilislari nesneyi elle kurabiliyor - kayit yoksa hepsi varsayilan
ve hicbiri bir sahneyi KILITLEMIYOR (`DEVIR.md`: dort bayrak kapanisi
sekillendiriyor, kilitlemiyor).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# `src.entities.kalachev.DEATH_FLAG` ile ayni dize. Import edilmiyor:
# o modul dovus sistemini cekiyor, bu modul saf veri kalmali.
KALACHEV_DEATH_FLAG = "kalachev_dead"
# Epilog bitince yazilir - DEVAM ET bitmis oyunu koye goturuyor.
EPILOGUE_FLAG = "epilogue_seen"
FINISHED_FLAG = "finished"
HOMECOMING_CHAPTER_NAME = "chapter.homecoming"


@dataclass(frozen=True)
class Homecoming:
    """Oyuncunun yolculugundan kapanisa kalanlar."""

    character: str = "rey"
    ghost: bool = False          # B15: kimseyi uyandirmadan gecti
    lifted: bool = False         # B16: yoldasi kaldirdi
    gesture: str = "nod"         # B16: reach / nod / withdraw
    tidy: bool = False           # B17: az gecisle cozdu
    clean: bool = False          # B18: sesi erken birakti
    kalachev: bool = False       # B18: Kalachev faz 2'de oldu
    deaths: int = 0              # oyun boyunca kac kez dustu

    @property
    def ally(self) -> str:
        """Yoldas - oynanmayan karakter."""
        return "rey" if self.character == "ardo" else "ardo"

    @property
    def ardo(self) -> bool:
        return self.character == "ardo"

    @classmethod
    def from_save(cls, data: Any, character: str = "") -> Homecoming:
        """Kayittan kur. `data` None ise varsayilanlar (dogrudan acilis)."""
        if data is None:
            return cls(character=character or "rey")
        flags = getattr(data, "flags", {}) or {}
        return cls(
            character=character or getattr(data, "character", "rey"),
            ghost=bool(flags.get("ch15_ghost")),
            lifted=bool(flags.get("ch16_lifted")),
            gesture=str(flags.get("ch16_gesture") or "nod"),
            tidy=bool(flags.get("ch17_tidy")),
            clean=bool(flags.get("ch18_clean")),
            kalachev=bool(flags.get(KALACHEV_DEATH_FLAG)),
            deaths=max(0, int(getattr(data, "deaths", 0) or 0)),
        )


def finished(data: Any) -> bool:
    """Bu kayit oyunu bitirmis mi? (Menu ve DEVAM ET buna bakiyor.)"""
    if data is None:
        return False
    flags = getattr(data, "flags", {}) or {}
    return bool(getattr(data, "finished", False) or flags.get(FINISHED_FLAG))
