"""Oyundaki butun diyaloglari duzenlenebilir bir dosyaya doker.

Arda (30.08.2026): *"Butun diyaloglari at guncelliyim."*

Ciktinin isi tek: metin yazari **anahtar aramadan** okuyup duzeltebilsin.
Bu yuzden JSON degil duz metin, ve konusmaci adlari cozulmus halde.

    python tools/dialogue_dump.py            # docs/diyaloglar.md yazar
    python tools/dialogue_dump.py --geri     # duzenlenmis dosyayi geri okur

## Neden geri okuma da var

Elle JSON duzenlemek iki dosyayi (tr/en) senkron tutmayi gerektiriyor ve
bir virgul hatasi butun oyunu aciyor. Doker-duzenle-geri oku dongusu o
riski aradan cikariyor: yazar yalnizca **metni** goruyor, anahtarlar ve
JSON bicimi arac tarafinda kaliyor.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG = ROOT / "src" / "ui" / "lang"
TARGET = ROOT / "docs" / "diyaloglar.md"

# Konusmaci anahtarlari (`ui/dialogue.py` SPEAKER_KEYS ile ayni sozluk).
#
# **Ikisi eksikti** (08.09.2026): Jet (B1'de kilici veren arkadas) ve
# Kalachev (B18'de tek repligi var). Eksik konusmaci sessizce "?" olarak
# dokuluyordu - metin yazari kimin konustugunu goremiyordu.
SPEAKERS = {"rey": "REY", "ardo": "ARDO", "cemo": "CEMO", "echo": "YANKI",
            "jet": "JET", "kalachev": "KALACHEV"}

# Anahtar onekine gore gruplama. Sira = oyundaki sira.
#
# **Liste B6'da duruyordu** (08.09.2026 bulundu). Sonucu sessiz ve kotu:
# B7-B18'in 232 repligi "DIGER" basligi altinda alfabetik bir yigina
# dusuyordu - yani belgenin butun isi (metin yazari anahtar aramadan
# okuyup duzeltebilsin) tam olarak calismiyordu. 337 repligin 78'i
# okunabilir haldeydi.
#
# Bolum adlari `docs/yapi.md`nin akisindan; kod tarafinda karsiligi
# `chapter.*` dil anahtarlari.
GROUPS = (
    ("prologue_", "PROLOG - acilis (src/scenes/prologue.py)"),
    ("ch01_", "BOLUM 1 - Koy"),
    ("ch02_", "BOLUM 2 - Ilk Inis"),
    ("ch03_", "BOLUM 3 - Mesale Mahzeni"),
    ("ch04_", "BOLUM 4 - Kayit Odasi"),
    ("ch05_", "BOLUM 5 - Sular"),
    ("ch06_", "BOLUM 6 - ARDO"),
    ("ch07_", "BOLUM 7 - Dar Gecit"),
    ("ch08_", "BOLUM 8 - Ates Basi"),
    ("ch09_", "BOLUM 9 - Can Kulesi"),
    ("ch10_", "BOLUM 10 - Ayrilik"),
    ("ch11_", "BOLUM 11 - Ayna Salonu"),
    ("ch12_", "BOLUM 12 - Mektup"),
    ("ch13_", "BOLUM 13 - Cemo"),
    ("ch14_", "BOLUM 14 - Yanki'nin Kaynagi"),
    ("ch15_", "BOLUM 15 - Sessizlik"),
    ("ch16_", "BOLUM 16 - Sirt Sirta"),
    ("ch17_", "BOLUM 17 - Ikili Kule"),
    ("ch18_", "BOLUM 18 - Son"),
)

# Hicbir bolume ait olmayan, ama gercekten metin olan anahtarlar.
# Ayri tutuluyorlar ki asagidaki "DIGER" basligi bir **alarm** olarak
# kalabilsin: orada bir sey cikarsa `GROUPS` eksik demektir.
LOOSE = ("echo_alone_voice", "kalachev_name")

HEADER = """# DİYALOGLAR

Bu dosya `tools/dialogue_dump.py` ile üretildi. **Elle düzenlenebilir** —
sadece tırnak içindeki metni değiştir, sonra:

    python tools/dialogue_dump.py --geri

komutuyla dile geri yazılır. Anahtarlara (`ch01_echo_wake` gibi) dokunma;
onlar kodun içinde geçiyor.

Konuşmacı adı satırın başında: **YANKI** kafanın içindeki ses (mor,
çerçevesiz), diğerleri odada konuşan kişiler.

"""


def _speaker_of(key: str, table: dict[str, str] | None = None) -> str:
    """Anahtardan konusmaciyi cozer.

    Anahtarlarin cogu `ch05_echo_valve` / `prologue_rey_3` gibi
    konusmaciyi ICINDE tasiyor. Ama 46 replik tasimiyordu ve "?" olarak
    dokuluyordu (olculdu 08.09.2026) - metin yazari o repliklerde kimin
    konustugunu goremiyordu, ki belgenin butun isi bu.

    Kalan uc kalibi **koddan okuyarak** cozuyoruz, elle tablo tutmadan;
    tutulsaydi kod ile tablo bir gun ayrisirdi:

    `_trace_`     Ardo'nun iz surmesi (`src/systems/tracking.py`).
                  Rey ayni beat'te Yanki'yi duyar (`_echo_`), Ardo izi
                  okur - ayni sahne, iki karakter, iki bilgi.
    `_lie_..._react`  yalana tepki: oynanan karakter
                  (`Line(self.character, react)`).
    `_lie_...`    yalanin kendisi: Yanki soyluyor.
    `X` + `X_ardo`  `say_player(X, X_ardo)` kalibi - taban anahtar
                  Rey'in repligi, `_ardo`li Ardo'nunki.
    """
    for token, label in SPEAKERS.items():
        if re.search(rf"(^|_){token}(_|\d|$)", key):
            return label
    if "_trace_" in key:
        return "ARDO"
    if "_lie_" in key:
        return "OYUNCU" if key.endswith("_react") else "YANKI"
    if key.endswith("_after") and "_ally_" in key:
        return "YOLDAS"
    if table is not None and f"{key}_ardo" in table:
        return "REY"
    return "?"


def dump() -> str:
    tr = json.loads((LANG / "tr.json").read_text(encoding="utf-8"))["line"]
    en = json.loads((LANG / "en.json").read_text(encoding="utf-8"))["line"]

    used: set[str] = set()
    parts = [HEADER]
    for prefix, title in GROUPS:
        keys = sorted(k for k in tr if k.startswith(prefix))
        if not keys:
            continue
        used.update(keys)
        parts.append(f"\n## {title}\n")
        for key in keys:
            parts.append(f"\n### {key}\n")
            parts.append(f"**{_speaker_of(key, tr)}**\n")
            parts.append(f'- tr: "{tr[key]}"\n')
            parts.append(f'- en: "{en.get(key, "")}"\n')

    loose = [k for k in LOOSE if k in tr]
    if loose:
        used.update(loose)
        parts.append("\n## BOLUM DISI\n")
        for key in loose:
            parts.append(f"\n### {key}\n")
            parts.append(f"**{_speaker_of(key, tr)}**\n")
            parts.append(f'- tr: "{tr[key]}"\n')
            parts.append(f'- en: "{en.get(key, "")}"\n')

    # **DIGER dolu ise bir uyaridir.** Bir bolum eklenip `GROUPS`a
    # yazilmazsa replikleri buraya duser ve metin yazari onlari
    # bulamaz - belgenin B6'da donmasi tam olarak boyle oldu.
    rest = sorted(k for k in tr if k not in used)
    if rest:
        parts.append("\n## DIGER - gruplanmamis\n")
        parts.append("\n> Bu basligin altinda bir sey varsa "
                     "`tools/dialogue_dump.py` icindeki `GROUPS`\n"
                     "> listesi eksik demektir.\n")
        for key in rest:
            parts.append(f"\n### {key}\n")
            parts.append(f"**{_speaker_of(key, tr)}**\n")
            parts.append(f'- tr: "{tr[key]}"\n')
            parts.append(f'- en: "{en.get(key, "")}"\n')
    return "".join(parts)


def restore() -> int:
    """Duzenlenmis dosyayi dil tablolarina geri yazar."""
    if not TARGET.is_file():
        print(f"!! {TARGET} yok - once dokum al")
        return 1
    body = TARGET.read_text(encoding="utf-8")

    current_key = ""
    updates: dict[str, dict[str, str]] = {"tr": {}, "en": {}}
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("### "):
            current_key = line[4:].strip()
            continue
        match = re.match(r'^-\s*(tr|en)\s*:\s*"(.*)"\s*$', line)
        if match and current_key:
            updates[match.group(1)][current_key] = match.group(2)

    changed = 0
    for lang in ("tr", "en"):
        path = LANG / f"{lang}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, value in updates[lang].items():
            if key in data["line"] and data["line"][key] != value:
                data["line"][key] = value
                changed += 1
            elif key not in data["line"]:
                # **Yeni anahtar EKLENMIYOR.** Kodda kullanilmayan bir
                # anahtar `tests/test_lang.py`'de "olu anahtar" olarak
                # kirilir; yeni replik once kodda yerini bulmali.
                print(f"   atlandi (kodda yok): {lang}/{key}")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"{changed} replik guncellendi")
    return 0


def main() -> int:
    if "--geri" in sys.argv:
        return restore()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(dump(), encoding="utf-8", newline="\n")
    count = dump().count("\n### ")
    print(f"yazildi: {TARGET}  ({count} replik)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
