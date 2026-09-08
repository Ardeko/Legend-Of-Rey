---
name: lore-dev
description: LORE - Legend of Rey oyununu calistir, test et ve gorsel olarak dogrula. Oynanis, sprite, bolum, dovus ya da fizik degisikliklerinden sonra kullan. "oyunu calistir", "test et", "sprite'lara bak", "bolum ekle", "hissi ayarla" gibi isteklerde devreye girer.
---

# LORE gelistirme dongusu

> **08.09.2026'da bastan yazildi.** Onceki surum terk edilmis
> `_prototype/` (v2.x) surumunu anlatiyordu: `run.py`,
> `tools/smoke_test.py`, `tools/combat_test.py`, `tools/make_levels.py`,
> `docs/ROADMAP.md`, "Essence dusmesi", `App.__init__`, `dt == 0` -
> **altisi da bu depoda yok**, ve `dt` tabanli fizik `CLAUDE.md` §12'de
> acikca yasak. Beceri "oyunu calistir" dendiginde yukleniyor, yani
> her oturumu var olmayan araclara yonlendiriyordu.

Bu depo `pygame-ce` ile yazilmis, yandan gorunumlu bir aksiyon-RPG.
Once **`CLAUDE.md`** (baglayici kurallar), sonra **`DEVIR.md`** (durum)
okunur. Degisiklikleri **gormeden** tamamlanmis sayma: oyun bassiz
calisip ekran goruntusu uretebiliyor.

## Python

Sanal ortam depo kokunde: `.venv/`. Sistem Python'u kullanma.

```
Windows : .venv/Scripts/python.exe
Diger   : .venv/bin/python
```

Kurulum: `python -m venv .venv` sonra
`.venv/Scripts/python.exe -m pip install pygame-ce numpy`.

## Dogrulama sirasi

Oynanisa dokunan her degisiklikten sonra, bu sirayla:

**1. Testler.** 48 paket var, hepsi tek dosya ve `raise SystemExit`
ile biter - `pytest` kullanmiyor.

```bash
for f in tests/test_*.py; do .venv/Scripts/python.exe "$f" || echo "KIRIK: $f"; done
```

Tek bir bolume dokunduysan yalnizca onu ve `test_lang.py`'yi
calistirmak yeter; **paketin tamami ~4 dakika.**

**2. Ekran goruntusu — bak, "calisiyor" deme.**

```bash
.venv/Scripts/python.exe tools/shot.py --scene src.scenes.chapter03:Chapter03Scene \
    --frames 120 --out build/testshots/b3.png
```

Sonra dosyayi **Read ile ac ve gercekten bak.** Cokme olmadan da
gorsel bozulmus olabilir; bu projede en az bes hata (uyuyan dusmanin
dik durmasi, kapanis jeneriginin gorunmemesi, B16'nin simsiyah
sinematigi) yalnizca bakinca cikti.

**3. Bolum degistiyse - gecilebilirlik.**

```bash
.venv/Scripts/python.exe tools/reachability.py --ayrinti
```

BFS her odayi geziyor. **Bolum 5 haric** (BFS suyu bilmiyor; su yolu
`tests/test_chapter05.py` icinde gercek fizikle oynatiliyor).

**4. Sprite'a dokunulduysa.**

```bash
.venv/Scripts/python.exe tools/sprite_sheet.py     # kontakt sayfasi
.venv/Scripts/python.exe tools/roster.py           # kadro + siluet testi
.venv/Scripts/python.exe tools/silhouette.py       # yalniz siluet
```

Silahin hucre disina tasip **kirpilmadigini** kontrol et.

**5. Asset ya da ses eklendiyse - kayit uretilir, elle yazilmaz.**

```bash
.venv/Scripts/python.exe tools/registry.py         # assets/REGISTRY.md
.venv/Scripts/python.exe tools/dialogue_dump.py    # docs/diyaloglar.md
```

## Gercek pencerede calistirma

```bash
.venv/Scripts/python.exe main.py            # bastan
.venv/Scripts/python.exe main.py bolum13    # dogrudan bir bolum
.venv/Scripts/python.exe main.py dovus      # dovus test odasi
```

Gecerli sahne adlari `main.py` icindeki `SCENES` sozlugunde; yanlis ad
yazilinca liste basiliyor. **Kullanici oynayacaksa bunu oner** - pencere
acan bir surec oturumu bloke eder, kendi dogrulamani `tools/shot.py`
ile yap.

## Sik karsilasilan tuzaklar

- **`dt` yok.** Fizik ve dovus **sabit 60 FPS'te kare** sayiyor
  (`CLAUDE.md` §4, §12). `dt` tabanli bir hesap yazma.
- **Palet disi renk `PaletteError` firlatir.** 37 renk,
  `tools/palette.json`. `palette.color()` golge ZINCIRI adlarini
  (`"blood"` degil, `"brass"`/`"soot"` gibi) reddeder - bu tuzaga iki
  kez dusuldu.
- **Dil anahtarlari DUZ DIZE yazilir.** `f"line.ch{n}_x"` gibi
  hesaplanmis bir anahtari `tests/test_lang.py` goremiyor ve "olu
  anahtar" diye kirilir. Dorduncu kez dusuldu.
- **`smoothscale` yasak** piksel art icin; yalnizca isik/aura
  katmaninda serbest.
- **Her yuzeyde `.convert()` / `.convert_alpha()`** - unutulursa oyun
  3-5 kat yavaslar.
- **Yoldasi (`companion`) sahne kendi guncelliyor ve ciziyor.**
  `PlayScene` yalnizca `allies` listesini gezer. B16'da bu satir
  unutuldu ve yoldas havada donmus kaldi.
- **Iki cikis yolu olan seyde tek govde olmali.** `Companion._stand`
  ve `Caller._kneel` ayni dersin izi: `die()` ile `take_damage`
  ayri yazilinca biri kancayi cagirmayi unuttu ve bolum
  bitirilemez oldu.
- **Kayitli olmayan ses adi uydurma.** `tests/test_audio.py`:
  *"listeden cikmayan bir ses, yazilmamis bir ozelliktir."*
- **Testler oyuncunun kaydina dokunmaz.** Her paket basinda
  `LORE_SAVE_DIR` gecici bir klasore alinir - yeni test yazarken bu
  bloku kopyala. Bir kez atlandi ve Arda'nin gercek ilerlemesi silindi.

## Mimari

`CLAUDE.md` (kurallar) · `DEVIR.md` (durum, acik isler, ogrenilen
dersler) · `docs/` (11 tasarim belgesi, hepsi baglayici).

`_prototype/` terk edilmis v2.x denemesidir - **referans, asla import
edilmez.** Oradaki adlar (Aethelmoor, Cael, Echobrand, Essence) artik
gecerli degil.
