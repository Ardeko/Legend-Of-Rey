"""Yetenek agaci - karakter basina uc dal, bes kademe, 3. kademe bir SECIM.

Arda (25.09.2026): *"Yetenek agacini bolume yayilmis puanlar olarak
tekrar yap. Yeni hareketler versin."* Plan: `docs/plan-yetenek-agaci.md`.

Bu dosya agacin **mantigi**: ne var, neyin onkosulu ne, kim neyi alabilir,
puan nereden geliyor ve acilanlarin toplam etkisi ne. Cizim
`src/ui/skill_tree.py`'de; modul durumsuz, durum kayitta
(`SaveData.skills` + `SaveData.skill_points` + `flags["skillpt_*"]`).
Ayni ayrim `charms.py` ve `abilities.py`'de de var.

## Eski agac neden yeniden yazildi

Oyunun tamaminda **tek** puan veriliyordu (B4 kampi) ve ekran yalnizca
B4'te aciliyordu: agacin %94'u hic acilmiyordu. On iki dugumun on ikisi
de bir sayiydi (hasar %6, can +5) - oyun bicimi hic degismiyordu.

## Dallar

    KESKIN   kilic         iki karakter
    TAS      ayakta kalmak iki karakter
    YANKI    ses           yalniz Rey  (Ardo Yanki'yi duymuyor)
    IZ       av            yalniz Ardo (Rey'in YANKI dalinin karsiligi)

Her karakter uc dal goruyor; oteki karakterin dali ekranda **hic yok**
(soluk bir dal "alamayacagin bir sey" diye bagiriyordu).

## Bes kademe, bedel 1+1+2+2+3

3. kademede iki dugum yan yana: **biri alinir, oteki kilitlenir.** Ayni
dali iki oyuncu farkli oynasin. 4. kademe ikisinden hangisi alinmissa
onun ustune acilir.

Dal 9 puan, agac 27. Oyun ~11 puan veriyor (`SKILL_POINT_CHAPTERS` +
B4 kampi + B15'in hayalet odulu): bir dal dibe, bir baskasi yariya.
*"Her bolumde bir sey alabilmeli, ama her seyi alamamali."*

## Yeni hareketler (`is_move`)

    Hamle          kosarken saldiri -> ileri atilan guclu vurus
    Havada Asili   havada vururken asili kalmak, hava zinciri
    Kilic Dalgasi  bitirici ileri ucan bir kesik firlatiyor
    Toparlanma     yenen darbenin bir kismi karsilik vurarak geri alinir
    Sarsilmaz      saldirirken hafif vuruslar zinciri bozmuyor
    Yalan Sezgisi  Yanki yalan soyleyince kolye urperiyor
    Yanki Darbesi  Yanki'yi acmak cevreyi itiyor ve sendeletiyor
    Pusu           arkadan / fark etmemis dusmana x1.5
    Sessiz Adim    daha hizli sessiz yuruyus, dusmanlar gec fark ediyor
    Ayi Kukremesi  Iz'i acmak cevreyi itiyor (Yanki Darbesi'nin ikizi)

Hareketlerin kendisi `player.py`/`play.py`/`enemy.py`de; burada yalnizca
"acik mi" sorusunun cevabi ve sayilar var.

## Etkiler carpan/bonus - taban degerlere DOKUNULMAZ

`docs/dovus-sistemi.md`'deki kare degerleri baglayici (CLAUDE.md 7).
Yetenekler onlarin **ustune** biner: zincir penceresi 12/14/10 oldugu gibi
kalir, "Akis" uzerine +2 kare ekler. Hicbir yetenek bir taban sayiyi
yeniden yazmiyor. Carpanlar **carpilarak** birlesir (dogal azalan getiri),
duz bonuslar toplanarak - `charms.py` deseni.

## Anahtarlar kalici

Kayda **bu dizeler** yaziliyor: yeni dugum eklemek serbest, var olani
yeniden adlandirmak eski kayitlarin yeteneklerini yok eder. Eski on iki
anahtarin hepsi korundu; `blade_finisher` artik "Kilic Dalgasi" ama ayni
anahtar - eski agacta bitiriciyi guclendiriyordu, yenisinde de oyle.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Iterable

from src.config import (
    COMBO_THRESHOLD_MID, GHOST_SKILL_POINTS, REST_SKILL_POINTS,
    SKILL_COST_BY_LEVEL, SKILL_EDGE_DAMAGE_BONUS, SKILL_FLOW_CHAIN_FRAMES,
    SKILL_GRIP_SIGHT_BONUS, SKILL_GUARD_DEFENCE_RELIEF,
    SKILL_HIDE_HEALTH_BONUS, SKILL_MEND_COMBO_RELIEF,
    SKILL_MOMENTUM_DAMAGE_BONUS, SKILL_POINT_CHAPTERS,
    SKILL_REACH_SIGHT_BONUS, SKILL_ROLL_DODGE_CHARGES,
    SKILL_TRACE_PATIENCE_RELIEF, SKILL_TRACE_RANGE_BONUS,
    SKILL_TRACE_READ_BONUS, SKILL_WARD_DEFENCE_RELIEF,
    SKILL_WILL_DEFENCE_RELIEF, SKILL_WILL_HEALTH_BONUS,
)

if TYPE_CHECKING:                      # yalnizca tip icin - dongusel import yok
    from src.systems.save import SaveData


# --- Dugum anahtarlari ------------------------------------------------------
BLADE_EDGE = "blade_edge"
BLADE_FLOW = "blade_flow"
BLADE_DASH = "blade_dash"            # yeni hareket: Hamle
BLADE_HOVER = "blade_hover"          # yeni hareket: Havada Asili
BLADE_MOMENTUM = "blade_momentum"
BLADE_FINISHER = "blade_finisher"    # yeni hareket: Kilic Dalgasi

ECHO_REACH = "echo_reach"
ECHO_WARD = "echo_ward"
ECHO_GRIP = "echo_grip"
ECHO_LIE = "echo_lie"                # Yalan Sezgisi
ECHO_MEND = "echo_mend"
ECHO_BURST = "echo_burst"            # yeni hareket: Yanki Darbesi

TRACE_EYE = "trace_eye"
TRACE_PATIENCE = "trace_patience"
TRACE_AMBUSH = "trace_ambush"        # Pusu
TRACE_QUIET = "trace_quiet"          # Sessiz Adim
TRACE_READ = "trace_read"
TRACE_ROAR = "trace_roar"            # yeni hareket: Ayi Kukremesi

STONE_HIDE = "stone_hide"
STONE_GUARD = "stone_guard"
STONE_ROLL = "stone_roll"
STONE_RALLY = "stone_rally"          # Toparlanma
STONE_WILL = "stone_will"
STONE_POISE = "stone_poise"          # Sarsilmaz

BRANCH_BLADE = "blade"
BRANCH_ECHO = "echo"
BRANCH_TRACE = "trace"
BRANCH_STONE = "stone"

# Puan kaynaklarinin kayittaki bayrak oneki. Her kaynak bir kez puan
# veriyor: tekrar oynanan bolum ikinci puani vermiyor (B4 kampinin eski
# kurali, simdi her kaynakta).
POINT_FLAG_PREFIX = "skillpt_"
SOURCE_B4_CAMP = "b4_camp"
SOURCE_GHOST = "ch15_ghost"


def _neutral(player: object) -> float:
    """Carpan kanallarinin varsayilani. Hicbir sey yapmaz."""
    return 1.0


@dataclass(frozen=True)
class Node:
    """Agactaki tek bir dugum.

    `label_key` / `desc_key` dil anahtari tutar, hazir metin degil - kayit
    ve arayuz dilden bagimsiz kalsin (charms.py ile ayni kural).

    Carpan alanlari oyuncunun **o andaki** durumuna bakar: "10+ combo'da
    hasar" gibi kosullu bir yetenek her karede yeniden karar verir. Duz
    bonus alanlari duruma bakmaz - acildigi anda sabittir.
    """

    key: str
    label_key: str
    desc_key: str
    cost: int

    # Carpan kanallari (durumsal)
    damage_scale: Callable[[object], float] = _neutral
    defence_scale: Callable[[object], float] = _neutral      # ALINAN hasar
    echo_sight_scale: Callable[[object], float] = _neutral

    # Duz bonuslar (sabit) - hepsi baglayici taban degerin USTUNE eklenir
    max_health: int = 0
    chain_window: int = 0        # kare
    dodge_charges: int = 0
    restore_combo: int = 0       # COMBO_TO_RESTORE'dan dusulecek vurus sayisi
    trace_range: float = 0.0     # Iz menzili orani (+0.25 = %25 uzak)

    # Yeni bir FIIL mi veriyor? Ekran bu dugumlere "yeni hareket" rozeti
    # koyuyor - oyuncu sayi ile hareket arasindaki farki gormeli.
    is_move: bool = False


@dataclass(frozen=True)
class Branch:
    """Bir dal: bes kademe, yukaridan asagi. Bir kademe 1 ya da 2 dugum.

    Iki dugumlu kademe bir SECIM: biri alininca oteki kilitlenir.
    """

    key: str
    label_key: str
    desc_key: str
    tiers: tuple[tuple[Node, ...], ...]
    # "" = iki karakter de; "rey" / "ardo" = yalniz o karakter.
    character: str = ""

    @property
    def nodes(self) -> tuple[Node, ...]:
        """Butun dugumler, kademe sirasiyla (secimde soldaki once)."""
        return tuple(node for tier in self.tiers for node in tier)

    @property
    def cost(self) -> int:
        """Dalin dibine inmenin bedeli - secim kademesinden tek dugum."""
        return sum(tier[0].cost for tier in self.tiers)


# --- Kosullu etkiler --------------------------------------------------------
# Hepsi `charms.py`'deki desenle ayni: oyuncudan `getattr` ile okur, eksik
# alanda notr doner. Test cift yonlu (kosul saglaninca / saglanmayinca)
# dogruluyor.
def _edge_damage(player: object) -> float:
    """Kosulsuz keskinlik. Dalin girisi - her oynayis bicimine calisir."""
    return 1.0 + SKILL_EDGE_DAMAGE_BONUS


def _momentum_damage(player: object) -> float:
    """10+ combo'da hasar. Saldirgan oynayani odullendirir, cekingeni degil."""
    combo = getattr(player, "combo", None)
    count = getattr(combo, "count", 0)
    return (1.0 + SKILL_MOMENTUM_DAMAGE_BONUS if count >= COMBO_THRESHOLD_MID
            else 1.0)


def _scene_attr(player: object, name: str) -> object:
    return getattr(getattr(player, "scene", None), name, None)


def _has_echo(player: object) -> bool:
    """Sahnedeki Yanki durumu. Ardo'da `scene.echo` None (scenes/play.py)."""
    return _scene_attr(player, "echo") is not None


def _sense_active(player: object, name: str) -> bool:
    sense = _scene_attr(player, name)
    return sense is not None and bool(getattr(sense, "active", False))


def _reach_sight(player: object) -> float:
    return 1.0 + SKILL_REACH_SIGHT_BONUS if _has_echo(player) else 1.0


def _grip_sight(player: object) -> float:
    return 1.0 + SKILL_GRIP_SIGHT_BONUS if _has_echo(player) else 1.0


def _ward_defence(player: object) -> float:
    """Yanki ACIKKEN alinan hasari azaltir - bedeli hafifletir, silmez.

    Sifirlasaydi mekanigin kalbi olurdu: Yanki'nin yardimi bedelsiz kalinca
    "acik tut, unut" haline gelirdi (systems/echo.py "Bedel").
    """
    if not _sense_active(player, "echo"):
        return 1.0
    return 1.0 - SKILL_WARD_DEFENCE_RELIEF


def _patience_defence(player: object) -> float:
    """Avci Sabri: Iz ACIKKEN alinan hasar azalir - Yanki Kalkani'nin ikizi."""
    if not _sense_active(player, "tracking"):
        return 1.0
    return 1.0 - SKILL_TRACE_PATIENCE_RELIEF


def _read_damage(player: object) -> float:
    """Iz Okuma: Iz acikken dusmanin nereye basacagini okuyorsun."""
    if not _sense_active(player, "tracking"):
        return 1.0
    return 1.0 + SKILL_TRACE_READ_BONUS


def _guard_defence(player: object) -> float:
    return 1.0 - SKILL_GUARD_DEFENCE_RELIEF


def _will_defence(player: object) -> float:
    return 1.0 - SKILL_WILL_DEFENCE_RELIEF


def _node(key: str, level: int, **effects: object) -> Node:
    """Dugum kurucu. Dil anahtarlari **acikca** asagida yazili.

    f-string ile kurulan anahtari `tests/test_lang.py` kaynak taramasinda
    goremiyor ve "olu anahtar" sayiyor - o yuzden `label_key`/`desc_key`
    her dugumde elle geciliyor.
    """
    return Node(key=key, cost=SKILL_COST_BY_LEVEL[level - 1], **effects)


# --- Agac -------------------------------------------------------------------
BRANCHES: tuple[Branch, ...] = (
    Branch(
        key=BRANCH_BLADE,
        label_key="skill.blade",
        desc_key="skill.blade_desc",
        tiers=(
            (_node(BLADE_EDGE, 1, label_key="skill.blade_edge",
                   desc_key="skill.blade_edge_desc",
                   damage_scale=_edge_damage),),
            (_node(BLADE_FLOW, 2, label_key="skill.blade_flow",
                   desc_key="skill.blade_flow_desc",
                   chain_window=SKILL_FLOW_CHAIN_FRAMES),),
            (_node(BLADE_DASH, 3, label_key="skill.blade_dash",
                   desc_key="skill.blade_dash_desc", is_move=True),
             _node(BLADE_HOVER, 3, label_key="skill.blade_hover",
                   desc_key="skill.blade_hover_desc", is_move=True)),
            (_node(BLADE_MOMENTUM, 4, label_key="skill.blade_momentum",
                   desc_key="skill.blade_momentum_desc",
                   damage_scale=_momentum_damage),),
            (_node(BLADE_FINISHER, 5, label_key="skill.blade_finisher",
                   desc_key="skill.blade_finisher_desc", is_move=True),),
        ),
    ),
    Branch(
        key=BRANCH_ECHO,
        label_key="skill.echo",
        desc_key="skill.echo_desc",
        character="rey",
        tiers=(
            (_node(ECHO_REACH, 1, label_key="skill.echo_reach",
                   desc_key="skill.echo_reach_desc",
                   echo_sight_scale=_reach_sight),),
            (_node(ECHO_WARD, 2, label_key="skill.echo_ward",
                   desc_key="skill.echo_ward_desc",
                   defence_scale=_ward_defence),),
            (_node(ECHO_GRIP, 3, label_key="skill.echo_grip",
                   desc_key="skill.echo_grip_desc",
                   echo_sight_scale=_grip_sight),
             _node(ECHO_LIE, 3, label_key="skill.echo_lie",
                   desc_key="skill.echo_lie_desc", is_move=True)),
            (_node(ECHO_MEND, 4, label_key="skill.echo_mend",
                   desc_key="skill.echo_mend_desc",
                   restore_combo=SKILL_MEND_COMBO_RELIEF),),
            (_node(ECHO_BURST, 5, label_key="skill.echo_burst",
                   desc_key="skill.echo_burst_desc", is_move=True),),
        ),
    ),
    Branch(
        key=BRANCH_TRACE,
        label_key="skill.trace",
        desc_key="skill.trace_desc",
        character="ardo",
        tiers=(
            (_node(TRACE_EYE, 1, label_key="skill.trace_eye",
                   desc_key="skill.trace_eye_desc",
                   trace_range=SKILL_TRACE_RANGE_BONUS),),
            (_node(TRACE_PATIENCE, 2, label_key="skill.trace_patience",
                   desc_key="skill.trace_patience_desc",
                   defence_scale=_patience_defence),),
            (_node(TRACE_AMBUSH, 3, label_key="skill.trace_ambush",
                   desc_key="skill.trace_ambush_desc", is_move=True),
             _node(TRACE_QUIET, 3, label_key="skill.trace_quiet",
                   desc_key="skill.trace_quiet_desc", is_move=True)),
            (_node(TRACE_READ, 4, label_key="skill.trace_read",
                   desc_key="skill.trace_read_desc",
                   damage_scale=_read_damage),),
            (_node(TRACE_ROAR, 5, label_key="skill.trace_roar",
                   desc_key="skill.trace_roar_desc", is_move=True),),
        ),
    ),
    Branch(
        key=BRANCH_STONE,
        label_key="skill.stone",
        desc_key="skill.stone_desc",
        tiers=(
            (_node(STONE_HIDE, 1, label_key="skill.stone_hide",
                   desc_key="skill.stone_hide_desc",
                   max_health=SKILL_HIDE_HEALTH_BONUS),),
            (_node(STONE_GUARD, 2, label_key="skill.stone_guard",
                   desc_key="skill.stone_guard_desc",
                   defence_scale=_guard_defence),),
            (_node(STONE_ROLL, 3, label_key="skill.stone_roll",
                   desc_key="skill.stone_roll_desc",
                   dodge_charges=SKILL_ROLL_DODGE_CHARGES),
             _node(STONE_RALLY, 3, label_key="skill.stone_rally",
                   desc_key="skill.stone_rally_desc", is_move=True)),
            (_node(STONE_WILL, 4, label_key="skill.stone_will",
                   desc_key="skill.stone_will_desc",
                   max_health=SKILL_WILL_HEALTH_BONUS,
                   defence_scale=_will_defence),),
            (_node(STONE_POISE, 5, label_key="skill.stone_poise",
                   desc_key="skill.stone_poise_desc", is_move=True),),
        ),
    ),
)

# Duz aramalar - agac sabit oldugu icin bir kez kuruluyor.
NODES: dict[str, Node] = {
    node.key: node for branch in BRANCHES for node in branch.nodes
}
_BRANCH_OF: dict[str, Branch] = {
    node.key: branch for branch in BRANCHES for node in branch.nodes
}
_LEVEL_OF: dict[str, int] = {
    node.key: level
    for branch in BRANCHES
    for level, tier in enumerate(branch.tiers, start=1)
    for node in tier
}


def branches_for(character: str) -> tuple[Branch, ...]:
    """Bu karakterin gordugu dallar, ekrandaki sirayla."""
    return tuple(b for b in BRANCHES if b.character in ("", character))


# Bir karakterin agacinin tamami (Rey ile Ardo esit: 3 x 9). Oyunun
# verdigi puanla kiyaslanabilsin diye adlandirildi - denge tartismasi
# sayiyi tahmin ederek yapilmasin.
TOTAL_COST: int = sum(b.cost for b in branches_for("rey"))
# Garanti puan: bolum sonlari + B4 kampi. Hayalet odulu bunun ustunde.
GUARANTEED_POINTS: int = len(SKILL_POINT_CHAPTERS) + REST_SKILL_POINTS


# --- Sorgular ---------------------------------------------------------------
def get(node_key: str) -> Node | None:
    return NODES.get(node_key)


def branch_of(node_key: str) -> Branch | None:
    return _BRANCH_OF.get(node_key)


def level_of(node_key: str) -> int:
    """Dugumun dalindaki kademesi (1..5). Bilinmeyen dugum 0."""
    return _LEVEL_OF.get(node_key, 0)


def label_key(node_key: str) -> str:
    node = NODES.get(node_key)
    return node.label_key if node else "skill.unknown"


def desc_key(node_key: str) -> str:
    node = NODES.get(node_key)
    return node.desc_key if node else "skill.unknown"


def tier_of(node_key: str) -> tuple[Node, ...]:
    """Dugumun kademesindeki butun dugumler (kendisi dahil)."""
    branch = _BRANCH_OF.get(node_key)
    level = _LEVEL_OF.get(node_key, 0)
    if branch is None or level <= 0:
        return ()
    return branch.tiers[level - 1]


def prerequisites(node_key: str) -> tuple[Node, ...]:
    """Bir ust kademe. **Herhangi biri** acik olmali. Ilk kademede bos.

    Secim kademesinin altinda iki dugum de onkosul sayiliyor: Hamle'yi
    secen de Havada Asili'yi secen de 4. kademeye inebilmeli.
    """
    branch = _BRANCH_OF.get(node_key)
    level = _LEVEL_OF.get(node_key, 0)
    if branch is None or level <= 1:
        return ()
    return branch.tiers[level - 2]


def rival(node_key: str) -> Node | None:
    """Secim kademesindeki OTEKI dugum. Tek dugumlu kademede None."""
    for node in tier_of(node_key):
        if node.key != node_key:
            return node
    return None


def branch_usable(save: "SaveData", branch_key: str) -> bool:
    """Bu kayittaki karakter bu dali gorebiliyor mu?"""
    branch = next((b for b in BRANCHES if b.key == branch_key), None)
    if branch is None:
        return False
    return branch.character in ("", _character(save))


def _character(save: "SaveData") -> str:
    return "ardo" if getattr(save, "character", "rey") == "ardo" else "rey"


# --- Puan muhasebesi --------------------------------------------------------
def unlocked(save: "SaveData", node_key: str) -> bool:
    return node_key in (getattr(save, "skills", None) or ())


def rival_taken(save: "SaveData", node_key: str) -> bool:
    """Secim kademesinde oteki dugum alinmis mi? (Ekran "secilmedi" der.)"""
    other = rival(node_key)
    return other is not None and unlocked(save, other.key)


def spent_points(save: "SaveData") -> int:
    """Acilmis dugumlere yatirilan toplam puan.

    Kayitta tanimadigimiz bir anahtar varsa (eski surumden kalma, ya da
    kaldirilmis bir dugum) sayilmaz - bilmedigimiz bir seyin bedelini
    uydurmaktansa gormezden gelmek dogru.
    """
    total = 0
    for key in (getattr(save, "skills", None) or ()):
        node = NODES.get(key)
        if node is not None:
            total += node.cost
    return total


def available_points(save: "SaveData") -> int:
    """Harcanabilir puan. `skill_points` **kalan** havuzdur, kazanilan degil."""
    return max(0, int(getattr(save, "skill_points", 0) or 0))


def grant_points(save: "SaveData", count: int = 1) -> int:
    """Puan ekler. Yeni toplami doner. Bayraksiz - `award` tercih edilir."""
    save.skill_points = available_points(save) + max(0, count)
    return save.skill_points


def can_unlock(save: "SaveData", node_key: str) -> bool:
    """Dugum su an alinabilir mi?

    Dort sart, hepsi birden:
      * dal bu karakterin  - Ardo YANKI'yi, Rey IZ'i alamaz
      * secim kademesinde oteki alinmamis
      * bir ust kademeden biri acik (kademe atlanamaz)
      * puan yetiyor
    """
    node = NODES.get(node_key)
    if node is None or unlocked(save, node_key):
        return False
    branch = _BRANCH_OF[node_key]
    if branch.character not in ("", _character(save)):
        return False
    if rival_taken(save, node_key):
        return False
    above = prerequisites(node_key)
    if above and not any(unlocked(save, n.key) for n in above):
        return False
    return available_points(save) >= node.cost


def unlock(save: "SaveData", node_key: str) -> bool:
    """Dugumu acar ve puani duser. Acilamazsa hicbir sey degistirmeden False.

    Kismi degisiklik birakmiyor: once kosul, sonra iki yazma. Puan dusup
    dugum eklenmeseydi oyuncu sessizce puan kaybederdi.
    """
    if not can_unlock(save, node_key):
        return False
    node = NODES[node_key]
    if getattr(save, "skills", None) is None:
        save.skills = []
    save.skill_points = available_points(save) - node.cost
    save.skills.append(node_key)
    return True


def unlocked_nodes(save: "SaveData") -> tuple[Node, ...]:
    """Acilmis dugumler, agactaki siralariyla (kayit sirasiyla degil)."""
    return tuple(node for node in NODES.values() if unlocked(save, node.key))


# --- Puan kaynaklari --------------------------------------------------------
# Arda: *"bolume yayilmis puanlar"*. Kaynak basina bir bayrak: ayni kaynak
# ikinci kez puan vermiyor (bolumu yeniden oynamak, olup yeniden dogmak).
def point_flag(source: str) -> str:
    return POINT_FLAG_PREFIX + source


def chapter_source(chapter: int) -> str:
    return f"ch{int(chapter)}"


def award(save: "SaveData", source: str, count: int = 1) -> int:
    """Kaynak daha once puan vermediyse `count` puan verir. Verileni doner."""
    if save is None or count <= 0:
        return 0
    flags = getattr(save, "flags", None)
    if flags is None:
        return 0
    flag = point_flag(source)
    if flags.get(flag):
        return 0
    flags[flag] = True
    grant_points(save, count)
    return count


def award_chapter(save: "SaveData", chapter: int) -> int:
    """Bolum sonu puani - yalniz `SKILL_POINT_CHAPTERS`teki bolumlerde."""
    if int(chapter or 0) not in SKILL_POINT_CHAPTERS:
        return 0
    return award(save, chapter_source(chapter))


def backfill(save: "SaveData", current_chapter: int = 0) -> int:
    """ESKI KAYIT: gecilmis kaynaklarin puanini bir kez verir.

    Yeni sistemden once B7'ye gelmis bir oyuncu B3 ve B6'nin puanini hic
    almadi - yeni agaci kaybettigi puanlarla karsilamamali. Kaynak
    bayraklari yuzunden iki kez calismak zararsiz; yeni oyunda da hicbir
    sey vermiyor (gecilmis bolum yok).

    **B4 kampi**: eski kod puani bayraksiz veriyordu. Kampta dinlenmis
    (`ch04_rested`) bir kayit o puani ZATEN aldi - yalnizca isaretleniyor.
    """
    if save is None or getattr(save, "flags", None) is None:
        return 0
    chapter = max(int(getattr(save, "chapter", 1) or 1), int(current_chapter or 0))
    flags = save.flags
    granted = 0
    camp = point_flag(SOURCE_B4_CAMP)
    if flags.get("ch04_rested"):
        flags.setdefault(camp, True)
    elif chapter > 4:
        granted += award(save, SOURCE_B4_CAMP, REST_SKILL_POINTS)
    for number in SKILL_POINT_CHAPTERS:
        if number < chapter:
            granted += award_chapter(save, number)
    if flags.get("ch15_ghost"):
        granted += award(save, SOURCE_GHOST, GHOST_SKILL_POINTS)
    return granted


# --- Etki toplayicilari -----------------------------------------------------
def _product(keys: Iterable[str], player: object, channel: str) -> float:
    total = 1.0
    for key in keys:
        node = NODES.get(key)
        if node is not None:
            total *= getattr(node, channel)(player)
    return total


def damage_scale(keys: Iterable[str], player: object) -> float:
    """Acik yeteneklerin **verilen** hasar carpani."""
    return _product(keys, player, "damage_scale")


def defence_scale(keys: Iterable[str], player: object) -> float:
    """Acik yeteneklerin **alinan** hasar carpani. 1.0'in altinda = koruma."""
    return _product(keys, player, "defence_scale")


def echo_sight_scale(keys: Iterable[str], player: object) -> float:
    """Yanki gorus menzili carpani (systems/echo.py `sight_range`)."""
    return _product(keys, player, "echo_sight_scale")


def trace_range_scale(keys: Iterable[str]) -> float:
    """Iz menzili carpani (`TrackingState.range_scale`). Carpilarak."""
    total = 1.0
    for key in keys:
        node = NODES.get(key)
        if node is not None and node.trace_range:
            total *= 1.0 + node.trace_range
    return total


def _flat(keys: Iterable[str], field_name: str) -> int:
    """Duz bonuslar toplanir - carpanlarin aksine durumdan bagimsiz."""
    total = 0
    for key in keys:
        node = NODES.get(key)
        if node is not None:
            total += getattr(node, field_name)
    return total


def max_health_bonus(keys: Iterable[str]) -> int:
    """REY_MAX_HEALTH / ARDO_MAX_HEALTH uzerine EKLENIR."""
    return _flat(keys, "max_health")


def chain_window_bonus(keys: Iterable[str]) -> int:
    """Zincir penceresine eklenen kare. Taban (14/10) degismez."""
    return _flat(keys, "chain_window")


def dodge_charge_bonus(keys: Iterable[str]) -> int:
    """Kacinma sarji. 6/18 karelik baglayici zamanlama degismez."""
    return _flat(keys, "dodge_charges")


def restore_combo_reduction(keys: Iterable[str]) -> int:
    """COMBO_TO_RESTORE'dan dusulecek vurus sayisi (20 -> 14)."""
    return _flat(keys, "restore_combo")
