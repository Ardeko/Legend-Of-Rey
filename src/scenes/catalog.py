"""Bolum numarasi -> oynanabilir sahne.

DEVAM ET bunu kullanir. Bir donem `VerticalJourneyScene.on_finished`
her zaman Bolum 1'i aciyordu: yorum "ileri bolumler geldikce burasi
bolum numarasina bakacak" diyordu, 18 bolum yazildiktan sonra satir
unutuldu. Kayit karti dogru bolumu gosteriyor, kamera inisi de o
numaraya gore uzuyor, ama varis her zaman koydu - oyuncu "yeni oyundan
basliyor" okuyor.
"""
from __future__ import annotations

import importlib

CHAPTER_COUNT = 18

# (modul, sinif). Anahtarlar duz sayi: hesaplanmis import yolu
# `tests/test_lang.py`'nin isi degil, ama bir tablo yine tek kaynak.
_CHAPTER_SCENES: dict[int, tuple[str, str]] = {
    1: ("src.scenes.chapter01", "Chapter01Scene"),
    2: ("src.scenes.chapter02", "Chapter02Scene"),
    3: ("src.scenes.chapter03", "Chapter03Scene"),
    4: ("src.scenes.chapter04", "Chapter04Scene"),
    5: ("src.scenes.chapter05", "Chapter05Scene"),
    6: ("src.scenes.chapter06", "Chapter06Scene"),
    7: ("src.scenes.chapter07", "Chapter07Scene"),
    8: ("src.scenes.chapter08", "Chapter08Scene"),
    9: ("src.scenes.chapter09", "Chapter09Scene"),
    10: ("src.scenes.chapter10", "Chapter10Scene"),
    11: ("src.scenes.chapter11", "Chapter11Scene"),
    12: ("src.scenes.chapter12", "Chapter12Scene"),
    13: ("src.scenes.chapter13", "Chapter13Scene"),
    14: ("src.scenes.chapter14", "Chapter14Scene"),
    15: ("src.scenes.chapter15", "Chapter15Scene"),
    16: ("src.scenes.chapter16", "Chapter16Scene"),
    17: ("src.scenes.chapter17", "Chapter17Scene"),
    18: ("src.scenes.chapter18", "Chapter18Scene"),
}

assert len(_CHAPTER_SCENES) == CHAPTER_COUNT, "katalog 18 bolumu kapsamali"


def clamp_chapter(chapter: int) -> int:
    """Bozuk bir kayit numarasi oyunu durdurmaz - 1..18'e kirpar."""
    try:
        number = int(chapter)
    except (TypeError, ValueError):
        return 1
    return max(1, min(CHAPTER_COUNT, number))


def chapter_scene_class(chapter: int) -> type:
    """Kayitli bolumun oynanabilir sahne sinifi. Ara sahne DEGIL."""
    number = clamp_chapter(chapter)
    module_name, class_name = _CHAPTER_SCENES[number]
    return getattr(importlib.import_module(module_name), class_name)


def chapter_name_key(chapter: int) -> str:
    """Menu kartinin dil anahtari - sahne sinifindaki tek kaynaktan."""
    key = getattr(chapter_scene_class(chapter), "chapter_name_key", "")
    return str(key or "chapter.village")
