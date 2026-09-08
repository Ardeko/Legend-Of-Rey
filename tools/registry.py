"""assets/REGISTRY.md dosyasini koddan uretir.

`CLAUDE.md` 6 uretilen her asset'in kaydedilmesini istiyor. Elle tutulan bir
liste kaciniLmaz olarak eskir - kimse spec degistirdiginde belgeyi
guncellemeyi hatirlamaz. Bu yuzden tablo koddan turetiliyor.

Kullanim:
    python tools/registry.py            # yazar
    python tools/registry.py --kontrol  # guncel mi diye bakar, yazmaz
                                        # (guncel degilse 1 doner)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets" / "REGISTRY.md"

ROLES = {
    "rey": "Oynanabilir - Yankisoyleyen",
    "rey_armed": "Rey, kilic kusanmis (Bolum 1 sonrasi)",
    "rey_dagger": "Rey + Hancer (Bolum 2 mini-boss odulu)",
    "rey_axe": "Rey + Balta (Bolum 2 mini-boss odulu)",
    "ardo": "Oynanabilir - yabanci",
    "ardo_dagger": "Ardo + Hancer (Bolum 2 mini-boss odulu)",
    "ardo_axe": "Ardo + Balta (Bolum 2 mini-boss odulu)",
    "cemo": "Rey'in kucuk kardesi - menu 5. asama",
    "villager": "Bolum 1 koylusu - olay patlayinca evine kaciyor",
    # Katman 1 - Curuyenler (B1-B6): combo KURMAYI ogretiyor
    "shambler": "Katman 1 - Suruklenen",
    "climber": "Katman 1 - Tirmanan",
    "bloated": "Katman 1 - Sismek",
    # Katman 2 - Lanetli Muhafizlar (B7-B13): combo KIRMAYI ogretiyor.
    # **Onun da AI'i yazildi** (30.08.2026); `tests/test_enemies.py`
    # her birinin `docs/gdd.md` 7'deki cumlesini gercekten yaptigini
    # olcuyor.
    "shieldbearer": "Katman 2 - Kalkanli (B5'te tanitiliyor)",
    "spearman": "Katman 2 - Mizrakli (B10)",
    "archer": "Katman 2 - Okcu (B13)",
    "commander": "Katman 2 - Komutan (B13)",
    # Katman 3 - Yanki'nin Cocuklari (B14-B18): yardimcinin ihaneti
    "silent": "Katman 3 - Sessiz - Yanki onu gostermez (B14)",
    "echoing": "Katman 3 - Yankilayan - sahte ipucu verir (B14)",
    "splitter": "Katman 3 - Bolunen - vurunca ikiye ayrilir (B14)",
    # Boss'lar - dordu de kendi arenasinda (docs/gdd.md 8)
    "rotted_one": "BOSS 1 - Curumus Olan (B6), Ardo'yla ilk beraber dovus",
    "gaoler": "BOSS 2 - Zindanci (B13), zaman kapilari",
    "source": "BOSS 3 - Kaynak (B14), twist'in kendisi",
    # Anlati varliklari - dusman degil
    "jet": "B1'de kilici veren arkadas",
    "kalachev": "Onceki maceraci (docs/kalachev.md) - B4/B5/B6/B10/"
                "B12/B13/B15, B18'de olur",
    "watcher": "Izleyen (docs/korku.md 5.2) - saldirmaz, bakar. "
               "B5/B11/B14",
}


def _sound_count() -> int:
    """Kayitli efekt sayisi. Sayiyi elle yazmak eskitiyordu."""
    from src.audio.sfx import SFX
    return len(SFX)



# Ikonun nerede kullanildigi - kayit "hangi dosya" degil "ne ise
# yariyor" sorusunu cevapliyor.
ICON_ROLES = {
    "question": "B6 - Ardo'yla ilk karsilasma",
    "alert": "Genel uyari",
    "heart": "B16 kapanisi ve B18 son paneli",
    "necklace": "B1 Cemo'nun kolyesi, B18 geri takilmasi",
    "echo": "Yanki isareti",
    "hand": "Jest secimi - elini uzat (B16, B18)",
    "nod": "Jest secimi - basini salla (B16, B18)",
    "back": "Jest secimi - geri cekil (B16, B18)",
}

MUSIC_ROLES = {
    "menu": "Ana menu",
    "explore": "Kesif - B5 ve B12 gibi sulu/sakin bolumler",
    "combat": "Dovus",
    "miniboss": "Mini-boss",
    "boss": "Buyuk boss - B6, B13, B14, B18",
    "echo": "Yanki kisimlari",
    "companion": "Oteki karakterin girisi",
    "sad": "Uzucu kisimlar - B10, B15, B17",
    "emotional": "Cok nadir duygusal anlar - yalnizca B18 kapanisi",
}


def _music_rows() -> list[str]:
    from src.audio import music
    rows = []
    for context, filename in music.TRACKS.items():
        where = MUSIC_ROLES.get(context, "-")
        rows.append(f"| `{context}` | {filename} | {where} |")
    return rows


def _icon_rows() -> list[str]:
    from src.ui import balloon
    rows = []
    for name in balloon.ICONS:
        rows.append(f"| `{name}` | {ICON_ROLES.get(name, '-')} |")
    return rows


def build() -> str:
    pygame.init()
    pygame.display.set_mode((64, 64))
    from src.art.animation import ANIMATIONS, CHARACTERS
    from src.art import palette

    total_frames = sum(count for _, count, _ in ANIMATIONS.values())
    anims = " · ".join(f"{k} ({c})"
                       for k, (_, c, _) in sorted(ANIMATIONS.items()))

    lines = [
        "# ASSET KAYDI",
        "",
        "`CLAUDE.md` 6: uretilen her asset buraya kaydedilir.",
        "",
        "**Bu projede sprite'lar PNG degil.** Hepsi `src/art/spritegen.py`",
        "icindeki `draw_humanoid()` ile **calisma zamaninda** uretiliyor;",
        "disk uzerinde sprite dosyasi yok. Bu yuzden kayit \"hangi dosya\"",
        "degil, **hangi spec** sorusunu cevapliyor.",
        "",
        "> Bu dosya `tools/registry.py` tarafindan uretilir. **Elle",
        "> duzenleme** - spec degisince araci yeniden calistir.",
        "",
        "## Karakterler",
        "",
        "Uretici: `src/art/spritegen.py :: draw_humanoid(spec, pose)`  ",
        "Spec'ler: `src/art/animation.py :: CHARACTERS`",
        "",
        "| Ad | Hucre | Taban (foot_y) | Kare | Rol |",
        "|---|---|---|---|---|",
    ]
    for name, spec in CHARACTERS.items():
        lines.append(
            f"| `{name}` | {spec.cell_width}x{spec.cell_height} | "
            f"{spec.foot_y} | {total_frames} | {ROLES.get(name, '-')} |")

    lines += [
        "",
        f"**Animasyon durumlari (kare sayisi):** {anims}",
        "",
        "Her karakter bu durumlarin tamamini uretir; toplam kare sayisi bu",
        "yuzden kadroda ayni.",
        "",
        "## Portreler",
        "",
        "Uretici: `src/art/portrait.py :: draw_portrait(spec)`  ",
        "Spec'ler: `src/art/portrait.py :: PORTRAITS`",
        "",
        "| Ad | Boyut | Rol |",
        "|---|---|---|",
        "| `rey` | 64x96 | Diyalog + karakter secimi |",
        "| `ardo` | 64x96 | Diyalog + karakter secimi |",
        "| `cemo` | 64x96 | Diyalog |",
        "",
        "**Neden ayri bir varlik sinifi:** oyun ici sprite'ta kafa ~7 "
        "piksel ve ",
        "goz kapagi/iris/highlight/burun kumesi/dudak oraya sigmiyor. "
        "Sprite'i ",
        "buyutmek de mumkun degil - oyunun en dar gecidi 2 tile = 32 "
        "piksel ",
        "(olculdu, `tests/test_sprites.py` koruyor). Portrede kafa 40 "
        "piksel ve ",
        "istenen her sey gercekten ciziliyor.",
        "",
        "Yanki'nin portresi **yok**: kafanin icindeki sesin yuzu olmaz "
        "(ayni ",
        "gerekce onun diyalog kutusunu da kaldirmisti).",
        "",
        "## Palet",
        "",
        f"Tek kaynak: `tools/palette.json` - **{len(palette.COLORS)} renk**, ",
        "degistirilemez. `src/art/palette.py` okur ve palet disi her rengi ",
        "`PaletteError` ile reddeder. Golge zincirleri "
        f"({len(palette.SHADE_CHAINS)} adet) rampalar arasi gecerek renk ",
        "sinirini asmadan tonlama saglar.",
        "",
        "## Font",
        "",
        "`src/ui/font_data.py` - 5x11 bitmap, tam Turkce seti. Eksik glif ",
        "sessizce dusmez, konsola rapor edilir.",
        "",
        "## Dil",
        "",
        "`src/ui/lang/tr.json` (kanonik) ve `en.json`. Anahtar paritesi ",
        "`tests/test_lang.py` ile korunuyor.",
        "",
        "## Ses",
        "",
        f"`src/audio/sfx.py :: SFX` - **{_sound_count()} efekt**, hepsi "
        "calisma zamaninda ",
        "sentezleniyor (numpy). Sprite'lar gibi: diskte dosya yok, kaynak "
        "koddur. ",
        "Her tekrarli ses +-%8 rastgele perdeyle calinir "
        "(`CLAUDE.md` 7).",
        "",
        "Donguli/surekli **efektler** bilerek kaldirildi (Arda: "
        "*\"cizirti gibi, ",
        "rahatsiz edici\"*); altyapi (`play_loop`/`stop_loop`) duruyor.",
        "",
        "## Muzik",
        "",
        "`src/audio/music.py :: TRACKS` - **gercek kayit**, sentez degil. ",
        "Diskteki tek asset kategorisi bu.",
        "",
        "| Baglam | Parca | Nerede |",
        "|---|---|---|",
        *_music_rows(),
        "",
        "Parcalar `assets/audio/music/` altinda ve **akitilarak** "
        "calmiyor: ",
        "`Fade.mp3` (479 sn) cozuldugunde ~80 MB tutar, dokuzu birden "
        "bellege ",
        "alinamaz. `music.py` tek seferde tek parca tutuyor.",
        "",
        "## Balon ikonlari",
        "",
        "`src/ui/balloon.py :: ICONS` - **7x7 piksel deseni**, font glifi ",
        "degil. Oyunda hicbir replik yok (`docs/gdd.md` 2); duygu ve niyet ",
        "bu ikonlarla tasiniyor.",
        "",
        "| Ikon | Nerede |",
        "|---|---|",
        *_icon_rows(),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    content = build()
    check_only = "--kontrol" in sys.argv

    current = TARGET.read_text(encoding="utf-8") if TARGET.is_file() else ""
    if current == content:
        print("REGISTRY.md guncel.")
        return 0

    if check_only:
        print("!! REGISTRY.md guncel degil - `python tools/registry.py` calistir.")
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(content, encoding="utf-8", newline="\n")
    print(f"yazildi: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
