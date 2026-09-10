"""Paketlenmis surum calisir mi - **calistirmadan** once.

## Neden var

`Legend of Rey.spec` bir kez sessizce bozuldu: yalnizca `assets`
klasorunu paketliyordu, ama oyun iki yerden daha diskten okuyor ve
ikisi de `assets` altinda degil:

    tools/palette.json     37 rengin tek kaynagi
    src/ui/lang/*.json     Turkce/Ingilizce metinler

Paketlenen oyun **acilir acilmaz cokerdi** ve bu ancak exe
calistirilinca gorulurdu - yani tester'in elinde. Kaynak tarafta
hicbir sey yanlis gorunmuyordu.

Ayni sinif hata bu projede uc kez yasandi (dil anahtarlari, ses
adlari, `draw_extra`): **sessizce basarisiz olan sey testle
yakalanir**, dikkatle degil.

Bu test iki sey soruyor:

  1. Kaynakta diskten okunan her klasor spec'te bildirilmis mi?
  2. `importlib` ile ada gore yuklenen her modul `hiddenimports`ta mi?

Ikincisi de gercek: bolumler ve dusmanlar dize yollarla yukleniyor
(`main.py` SCENES, `ENEMY_CLASSES`), PyInstaller statik analizle
bunlari goremiyor.

Calistir:
    python tests/test_build.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA.** (08.09.2026)
#
# Sahneler `read_save()` ile kaydi yukluyor ve `_sync_abilities()` gibi
# yerler `write_save()` ile geri yaziyor - yani bu paketi calistirmak
# Arda'nin gercek ilerlemesini siliyordu. 55 altin ve secilmis balta
# boyle kayboldu; yedek dosyasi da ustune yazildigi icin
# kurtarilamadi.
#
# Bir test, oyuncunun verisine asla dokunmamali. Kayit dizini her
# calistirmada gecici bir klasore aliniyor.
import tempfile  # noqa: E402

os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

# Klasore **varsayilan bir kayit** tohumlaniyor. Bos birakilsaydi
# `read_save()` None donerdi ve sahnelerin `save_data`si None olurdu -
# oysa testler gercek bir kaydin varligina gore yazilmis (bayrak
# okuyor, bolum numarasi yaziyor). Amac oyuncunun dosyasindan
# kurtulmak, testlerin davranisini degistirmek degil.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.systems.save import SaveData as _SaveData  # noqa: E402
from src.systems.save import write_save as _write_save  # noqa: E402

_write_save(_SaveData())

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SPEC = ROOT / "Legend of Rey.spec"

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def spec_text() -> str:
    return SPEC.read_text(encoding="utf-8")


# --- 1. Diskten okunan yollar spec'te mi -------------------------------------
def test_data_paths() -> None:
    """`Path(__file__)...` ile kurulan her veri yolu paketlenmeli.

    Desen: `parents[N] / "klasor" / ...`. Kaynak agacinin disina cikan
    her yol bir veri dosyasidir ve donmus surumde `sys._MEIPASS`
    altinda **ayni goreli konumda** bulunmali.
    """
    print("\n--- diskten okunan yollar ---")
    spec = spec_text()
    pattern = re.compile(
        r'Path\(__file__\)\.resolve\(\)\.parents?\[?\d*\]?'
        r'((?:\s*/\s*"[^"]+")+)')
    found: dict[str, str] = {}
    for path in (ROOT / "src").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for match in pattern.finditer(source):
            parts = re.findall(r'"([^"]+)"', match.group(1))
            if not parts:
                continue
            found.setdefault(parts[0], str(path.relative_to(ROOT)))

    # `parent / "lang"` gibi **kardes** klasorler de veri: modulun
    # yanindaki json PyInstaller'a otomatik girmiyor.
    sibling = re.compile(r'Path\(__file__\)\.resolve\(\)\.parent\s*/\s*"([^"]+)"')
    for path in (ROOT / "src").rglob("*.py"):
        for match in sibling.finditer(path.read_text(encoding="utf-8")):
            rel = path.relative_to(ROOT).parent / match.group(1)
            found.setdefault(str(rel).replace("\\", "/"),
                             str(path.relative_to(ROOT)))

    check(bool(found), "kaynakta veri yolu bulundu", f"{len(found)} tane")
    for folder, owner in sorted(found.items()):
        needle = folder.replace("\\", "/")
        check(needle in spec.replace("\\", "/"),
              f"'{needle}' spec'te bildirilmis", f"kullanan: {owner}")


# --- 2. Ada gore yuklenen moduller hiddenimports'ta mi ----------------------
def test_dynamic_imports() -> None:
    """`"modul:Sinif"` ve `("modul", "Sinif")` ile yuklenen her sey.

    PyInstaller bunlari **goremiyor**: statik analiz `importlib` ile
    calisan bir dize yolunu takip etmiyor. Bildirilmezse paketlenen
    oyun o bolume girildiginde coker - yani ilk uc bolum calisir,
    dorduncusu patlar.
    """
    print("\n--- dinamik import'lar ---")
    spec = spec_text()
    modules: set[str] = set()

    colon = re.compile(r'"(src\.[\w.]+):(\w+)"')
    tuple_form = re.compile(r'\(\s*"(src\.[\w.]+)"\s*,\s*"(\w+)"\s*\)')
    for path in list((ROOT / "src").rglob("*.py")) + [ROOT / "main.py"]:
        source = path.read_text(encoding="utf-8")
        for match in colon.finditer(source):
            modules.add(match.group(1))
        for match in tuple_form.finditer(source):
            modules.add(match.group(1))

    check(bool(modules), "dinamik yuklenen modul bulundu",
          f"{len(modules)} tane")
    missing = sorted(m for m in modules if f"'{m}'" not in spec)
    check(not missing, "hepsi hiddenimports'ta",
          ", ".join(missing) if missing else f"{len(modules)} modul")


# --- 3. Paketlenmemesi gerekenler --------------------------------------------
def test_excluded() -> None:
    """Yuksek cozunurluklu asillar ve belgeler pakete girmemeli."""
    print("\n--- disarida kalmasi gerekenler ---")
    # **Yalnizca DATAS listesine bak.** Modul basligindaki aciklama
    # `assets/portraits/kaynak` klasorunden bahsediyor ve ilk surum onu
    # "paketlenmis" sandi. Bir yorumda gecmek paketlenmek degildir.
    raw = spec_text()
    start = raw.find("DATAS = [")
    spec = raw[start:raw.find("]", start)].replace("\\", "/")
    check("assets/portraits/kaynak" not in spec,
          "yuksek cozunurluklu asillar paketlenmiyor (5.7 MB)")
    check("('assets', 'assets')" not in spec,
          "assets TOPTAN paketlenmiyor - kaynak klasoru de girerdi")


# --- 4. Spec'in kendisi tutarli mi -------------------------------------------
def test_spec_sane() -> None:
    print("\n--- spec ---")
    check(SPEC.exists(), "spec dosyasi var")
    spec = spec_text()
    # Yayin surumu (Arda, 10.09.2026): konsol penceresi YOK. Tester
    # surumunde True'ydu - geri acilirsa oyunla birlikte siyah bir
    # pencere acilir ve bu test onu yakalar.
    check("console=False" in spec,
          "yayin surumu: konsol penceresi kapali")
    check((ROOT / "icon.ico").exists(), "icon.ico yerinde")
    check((ROOT / "tools" / "palette.json").exists(), "palette.json yerinde")
    check((ROOT / "src" / "ui" / "lang" / "tr.json").exists(),
          "dil dosyalari yerinde")


def test_every_portrait_is_packaged() -> None:
    """Cizilmis her portre pakete giriyor mu - ve istenen her ad var mi.

    09.09.2026'da bulundu: spec portreleri **tek tek sayiyordu** ve
    listede yalnizca rey/ardo/cemo vardi. Sonradan cizilen `jet.png`
    ile `kalachev.png` eksikti, ikisi de kullaniliyordu.

    Hicbir hata cikmiyordu, en kotu turden:

      Jet       `staging._draw_closeup` prosedurele duser - Arda'nin
                cizimi kaybolur, sahne oynamaya devam eder
      Kalachev  prosedurel spec'i YOK (`PORTRAITS` ucu tutuyor),
                `portrait()` None doner ve `chapter04_render` paneli
                hic cizmeden geri doner - B4'un Kalachev acigi
                paketlenmis oyunda GORUNMEZDI

    Iki sey olculuyor:

      1. `assets/portraits/*.png` icindeki her dosya pakete giriyor mu.
         Asil hata buydu: cizilen sey diskte kaliyordu.
      2. Kodun ADIYLA istedigi (`portrait("x")`) her portrenin ya bir
         spec'i ya bir PNG'si var mi.

    `closeup="x"` **kasitli olarak taranmiyor**: oradaki ad bir portre
    degil bir sahne aktoru kimligi (`ActorSpec("player", character,
    ...)`), ve `staging` onu once aktorun gercek karakterine ceviriyor.
    "player" diye bir portre aramak yanlis alarm olurdu.
    """
    print("\n--- portreler ---")
    from src.art.portrait import PORTRAITS

    spec = spec_text().replace("\\", "/")
    # Glob kullanildiginda adlar spec metninde GECMEZ; o zaman olcut
    # "klasorde duruyor mu" oluyor.
    globbed = "assets/portraits').glob('*.png'" in spec
    drawn = sorted(f.stem
                   for f in (ROOT / "assets" / "portraits").glob("*.png"))
    check(bool(drawn), "elle cizilmis portre var", ", ".join(drawn))

    if globbed:
        check(True, "portreler glob ile aliniyor - liste bayatlayamaz")
    else:
        outside = [n for n in drawn
                   if f"assets/portraits/{n}.png" not in spec]
        check(not outside, "cizilmis her portre pakete giriyor",
              "DISARIDA: " + ", ".join(outside) if outside else "")

    wanted: set[str] = set()
    for path in sorted((ROOT / "src").rglob("*.py")):
        wanted |= set(re.findall(r'portrait\(\s*"([a-z_]+)"',
                                 path.read_text(encoding="utf-8")))
    check(bool(wanted), "kaynakta adiyla istenen portre bulundu",
          ", ".join(sorted(wanted)))

    missing = [name for name in sorted(wanted)
               if name not in PORTRAITS and name not in drawn]
    check(not missing,
          "istenen her portrenin ya spec'i ya PNG'si var",
          "EKSIK: " + ", ".join(missing) if missing else "")


def main() -> int:
    test_spec_sane()
    test_every_portrait_is_packaged()
    test_data_paths()
    test_dynamic_imports()
    test_excluded()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        print("\nPaketlenen surum calismayabilir. Spec'i duzelt.")
        return 1
    print("Paket tanimi tutarli - her veri yolu ve dinamik modul bildirilmis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
