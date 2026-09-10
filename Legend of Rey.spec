# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller paket tanimi - tester surumu.

## Bu dosya bir kez SESSIZCE bozuldu

Onceki surum yalnizca `assets` klasorunu paketliyordu. Ama oyun uc yerden
daha diskten okuyor ve ikisi `assets` altinda **degil**:

    tools/palette.json     37 rengin tek kaynagi (`src/art/palette.py`)
    src/ui/lang/*.json     Turkce/Ingilizce metinler (`src/ui/i18n.py`)

Ikisi de eksik oldugu icin paketlenen oyun **acilir acilmaz cokerdi** -
ve bu, calistirilana kadar gorunmezdi. `tests/test_build.py` artik
kaynaktaki her disk yolunu tarayip burada bildirildigini dogruluyor;
yeni bir varlik klasoru eklenip buraya yazilmazsa test kiriliyor.

## Neyin paketlenmedigi de bilincli

    assets/portraits/kaynak/   yuksek cozunurluklu asillar (5.7 MB) -
                               yalnizca yeniden uretim icin, oyun
                               64x96 olanlari okuyor
    assets/*.md                belgeler
    docs/, tools/, tests/      gelistirme

## console=False - yayin surumu (Arda, 10.09.2026)

Tester surumunde `True`'ydu: cokme **gorunur** olsun, tester ekran
goruntusu alabilsin diye. Oyun bitti ve dagitilacak surumde oyunla
birlikte acilan siyah pencere yersiz duruyordu - kapatildi.

**Bedeli bilinerek kabul edildi:** bu surumde bir cokme iz birakmadan
kapanir. Kodda konsola dogrudan yazan satir yok (`print` stdout `None`
iken sessizce hicbir sey yapmiyor), yani konsolun kapanmasi kendi basina
bir cokme uretmiyor - paketlenmis exe 40 sn olculdu.
"""

from pathlib import Path as _Path

# Elle cizilmis portreler. **Tek tek sayilmiyor** - klasordeki her PNG
# aliniyor.
#
# ## Bu satir bir kez daha sessizce bozuldu (09.09.2026)
#
# Liste elle yaziliydi ve uzerinde `rey`, `ardo`, `cemo` vardi. Sonradan
# `jet.png` ve `kalachev.png` cizildi, ikisi de oyunda kullaniliyor
# (`chapter01_cinematics.py` Jet'in yakin cekimi,
# `chapter04_render.py` B4'un Kalachev paneli) ama listeye
# eklenmemisti.
#
# Sonucu **hicbir hata vermiyordu**, en kotu turden bir hata:
#
#   Jet       `staging._draw_closeup` prosedurel portreye duserdi -
#             yani cizim kaybolur, sahne oynamaya devam ederdi
#   Kalachev  prosedurel bir spec'i YOK (`portrait.PORTRAITS` ucu
#             tutuyor), yani `portrait()` None doner ve
#             `chapter04_render` panelin tamamini cizmeden geri doner -
#             B4'un Kalachev acigi paketlenmis oyunda HIC gorunmezdi
#
# "Her yeni portre bir satir eklesin" bir hatanin sekli; bu projede
# ayni ders `summon_kalachev`in yara bayraginda da yazildi. Glob
# ozyinelemeli DEGIL, yani `kaynak/` (5.7 MB asillar) yine disarida
# kaliyor - o bilincli bir dislama.
_PORTRAITS = [(str(f).replace("\\", "/"), 'assets/portraits')
              for f in sorted(_Path('assets/portraits').glob('*.png'))]

DATAS = [
    # Palet - `src/art/palette.py` acilista okuyor. Olmazsa oyun baslamaz.
    ('tools/palette.json', 'tools'),
    # Diller - `src/ui/i18n.py`. Olmazsa her metin anahtar adi olarak cikar.
    ('src/ui/lang', 'src/ui/lang'),
    # Muzik (53 MB) ve logo.
    ('assets/audio', 'assets/audio'),
    ('assets/logo', 'assets/logo'),
] + _PORTRAITS

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=DATAS,
    hiddenimports=[
        # Bolumler ve sahneler `importlib` ile **ada gore** yukleniyor
        # (`main.py` SCENES, `chapter*.py` ENEMY_CLASSES). PyInstaller
        # statik analizle bunlari goremiyor - tek tek bildirilmezse
        # paketlenen oyun "modul yok" diye coker.
        # **Duz dize, uretilmis degil.** Ilk surum
        # `f'src.scenes.chapter{n:02d}'` yaziyordu; PyInstaller onu
        # dogru cozerdi ama `tests/test_build.py` goremezdi - ve
        # bu projede tam olarak o tuzak dort kez patladi (dil
        # anahtarlari, ses adlari, panel onekleri, bu).
        # Denetlenemeyen bir liste, olmayan bir listedir.
        'src.scenes.chapter01',
        'src.scenes.chapter02',
        'src.scenes.chapter03',
        'src.scenes.chapter04',
        'src.scenes.chapter05',
        'src.scenes.chapter06',
        'src.scenes.chapter07',
        'src.scenes.chapter08',
        'src.scenes.chapter09',
        'src.scenes.chapter10',
        'src.scenes.chapter11',
        'src.scenes.chapter12',
        'src.scenes.chapter13',
        'src.scenes.chapter14',
        'src.scenes.chapter15',
        'src.scenes.chapter16',
        'src.scenes.chapter17',
        'src.scenes.chapter18',
        'src.world.rooms.chapter01',
        'src.world.rooms.chapter02',
        'src.world.rooms.chapter03',
        'src.world.rooms.chapter04',
        'src.world.rooms.chapter05',
        'src.world.rooms.chapter06',
        'src.world.rooms.chapter07',
        'src.world.rooms.chapter08',
        'src.world.rooms.chapter09',
        'src.world.rooms.chapter10',
        'src.world.rooms.chapter11',
        'src.world.rooms.chapter12',
        'src.world.rooms.chapter13',
        'src.world.rooms.chapter14',
        'src.world.rooms.chapter15',
        'src.world.rooms.chapter16',
        'src.world.rooms.chapter17',
        'src.world.rooms.chapter18',
        'src.scenes.intro',
        'src.scenes.prologue',
        'src.scenes.combat_room',
        'src.scenes.foundation_check',
        'src.ui.menu',
        'src.scenes.chapter02_cinematics',
        'src.scenes.chapter03_cinematics',
        'src.scenes.chapter06_cinematics',
        'src.scenes.chapter07_cinematics',
        'src.scenes.chapter08_cinematics',
        'src.scenes.chapter09_cinematics',
        'src.scenes.chapter10_cinematics',
        'src.scenes.chapter12_cinematics',
        'src.scenes.chapter13_cinematics',
        'src.scenes.chapter14_cinematics',
        'src.scenes.chapter15_cinematics',
        'src.scenes.chapter16_cinematics',
        'src.scenes.chapter17_cinematics',
        'src.scenes.chapter18_cinematics',
        'src.scenes.ending',
        'src.entities.bosses.caller',
        'src.entities.enemies.shambler',
        'src.entities.enemies.climber',
        'src.entities.enemies.bloated',
        'src.entities.enemies.bloated_one',
        'src.entities.enemies.shieldbearer',
        'src.entities.enemies.spearman',
        'src.entities.enemies.archer',
        'src.entities.enemies.commander',
        'src.entities.enemies.silent',
        'src.entities.enemies.echoing',
        'src.entities.enemies.splitter',
        'src.entities.enemies.shadow_shambler',
        'src.entities.enemies.extinguished_one',
        'src.entities.bosses.rotted_one',
        'src.entities.bosses.gaoler',
        'src.entities.bosses.source',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Legend of Rey',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Yayin surumu: konsol penceresi yok. Gerekce dosya basliginda.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
