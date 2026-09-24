"""Epilog - "Eve Donus". Iki oda: kuyunun dibi ve sabah koyu.

Arda (24.09.2026): *"koye hep beraber donduklari bir sinematik. belki
oraya da bir kisa oynanis veya oyuncuyu odullendirecek bir sahne."*
Tasarim ve gerekceler: `docs/yapi.md` Epilog, `DEVIR.md` ayni tarih.

## Neden bu iki oda

**Kuyunun dibi.** Jet B4'te *"doğu yolu beni buraya indirdi, bir ip
bağladım"*, B15'te *"adımı söylemen yeter; burada olacağım"* dedi.
Zindandan cikis o ip - baska bir kapi uydurmak oyunun kendi sozunu
yok saymak olurdu.

**Sabah koyu.** B1'in koyu, **ayni evler**, ama safakta ve tersinden:
B1 batida (Rey'in evi) basliyor doguya gidiyordu; epilog doguda (ipin
ucu) basliyor, batiya - eve - donuyor. Platformlar, kilic, yaratiklar
ve kirilabilir duvar yok: burasi bir ogreti odasi degil, bir koy.
"""
from __future__ import annotations

from src.world.level import parse
from src.world.rooms.chapter01 import SCENERY as B1_SCENERY

# --- 1. Kuyunun dibi ---------------------------------------------------------
#   R oyuncu   C Cemo   ! ipin sarktigi yer
# Tavanda uc sutunluk bosluk (21-23): kuyunun agzi, isik oradan iniyor.
SHAFT_ROWS: list[str] = [
    "#####################...########",
    "#####################...########",
    "#####################...########",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#.CR..................!........#",
    "################################",
    "################################",
    "################################",
]
SHAFT_LEVEL = parse("epilog-kuyu", SHAFT_ROWS)
# Ipin kuyunun agzindan sarktigi sutun.
ROPE_COLUMN = 22
# Kuyu agzi sutunlari - isik huzmesi bunlarin genisliginde.
SHAFT_MOUTH = (21, 24)

# --- 2. Sabah koyu -----------------------------------------------------------
# B1'in koyu, ev yerlesimi ayni (`B1_SCENERY`) - ama batida **fazladan
# bir yol parcasi** var. B1'de ev sahnenin en solundaydi ve kamera oraya
# yapisiyordu; epilogun bitisi o evin duvarinda (Cemo'nun resmi) ve
# resim ekranin kenarinda, portrenin altinda kaliyordu. Yol, kameranin
# evi ortalamasina yer aciyor; oyun sonrasinda koyden cikis da oradan.
WEST_MARGIN = 10
#   R oyuncu (doguda, ipin yaninda)   ! Rey'lerin evi (bitis)
VILLAGE_ROWS: list[str] = (
    ["." * (64 + WEST_MARGIN)] * 11
    + ["." * WEST_MARGIN
       + "....!.....................................................R....."]
    + ["#" * (64 + WEST_MARGIN)] * 2
)
VILLAGE_LEVEL = parse("epilog-koy", VILLAGE_ROWS)

# Rey'lerin evi - B1'in basladigi ev. Cemo'nun cizimi bu evin duvarina
# yapiliyor, bitis burada.
HOME_INDEX = 0
# Hana cevrilen ev: B1'in en buyuk evi (16, 11, 6, 5).
INN_INDEX = 2

# Koy cani - dogu girisinde, son evle cit arasindaki acik alanda.
BELL_FRAME = (WEST_MARGIN + 41, 11, 3, 4)
BELL_TILE = (WEST_MARGIN + 42, 8)

# Kapanan yarigin izi - Cemo'nun cekildigi yer, Rey'lerin evinin onu.
SCAR_TILES = (WEST_MARGIN + 7, 3)            # (baslangic, genislik)

# Jet'in ipi: dogu ucundaki kuyunun agzi ve ipin bagli oldugu kazik.
ROPE_POST_TILE = WEST_MARGIN + 60
HOLE_TILES = (WEST_MARGIN + 61, 2)
JET_TILE = WEST_MARGIN + 55

# Bati yolu: evin bahce citi. B1'de burasi sahnenin disiydi.
WEST_SCENERY = ((WEST_MARGIN - 7, 11, 4, 1, "fence"),)

# Koyluler: (ev indeksi, rol, kapidan uzaklik px). Rol, sahnede
# repliege donusuyor (`epilogue_village.py`). Rey'lerin evinden kimse
# cikmiyor - o ev bos, sahipleri disarida.
VILLAGERS: tuple[tuple[int, str, float], ...] = (
    (1, "elder", -14.0),
    (1, "falls", 16.0),
    (INN_INDEX, "inn", 12.0),
    (3, "seven", -12.0),
    (3, "rooster", 14.0),
    (4, "door", 12.0),
)


def _epilogue_scenery() -> tuple:
    """B1'in dekoru (bati yolu kadar kaydirilmis) + han + can iskelesi.

    B1'in listesi degismiyor; kopya kaydiriliyor.
    """
    scenery = []
    for index, (tx, ty, tw, th, kind) in enumerate(B1_SCENERY):
        if index == INN_INDEX and kind == "house":
            kind = "inn"
        scenery.append((tx + WEST_MARGIN, ty, tw, th, kind))
    scenery.extend(WEST_SCENERY)
    scenery.append((*BELL_FRAME, "bellframe"))
    return tuple(scenery)


EPILOGUE_SCENERY = _epilogue_scenery()
HOUSES = tuple(item for item in EPILOGUE_SCENERY
               if item[4] in ("house", "inn"))
