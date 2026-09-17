"""Bolum 1 dogrulamasi - Ardo'nun Rey'e ozel ogretileri almadigi.

`docs/gdd.md`: Ardo egitimli bir yabanci, Rey'in ogrenme yayini tekrar
oynamiyor. Ama Bolum 1'in Yanki Gorusu ogretisi (`on_echo_tutorial`)
karakter kontrolu olmadan yazilmisti: Ardo da (Yanki'si olmadigi halde)
"Yanki Gorusu kazandin" bildirimini goruyordu - hicbir mekanik karsiligi
olmayan bir gucu acmasi isteniyordu (Arda'nin bildirdigi hata).

Calistir:
    python tests/test_chapter01.py
"""
from __future__ import annotations

import os
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

import pygame  # noqa: E402

# `pygame.init()` DEGIL. O, joystick alt sistemini de acar ve bu
# makinede 40 SANIYE surer (olculdu 30.08.2026 - bir surucu sorunu,
# kodla ilgisi yok). 21 test paketi bunu ayri ayri odedigi icin butun
# paket 14 dakikayi asiyordu.
#
# `src/core/game.py` de tam olarak bu yolu izliyor; test oyunla ayni
# sekilde acilsin. Ses gerekirse `synth.init_mixer()` cagrilir.
pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.core.game import Game  # noqa: E402
from src.scenes.chapter01 import Chapter01Scene  # noqa: E402
from src.systems import abilities  # noqa: E402
from src.world.rooms.chapter01 import ECHO_TUTORIAL_TILE, PROLOGUE  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def fresh(game: Game, character: str = "rey") -> Chapter01Scene:
    """Sahneyi bastan kurar - Game'i YENIDEN YARATMADAN.

    `Game.shutdown()` `pygame.quit()` cagiriyor ve bu makinede bir
    sonraki `pygame.init()` 40 saniye suruyor (olculdu 23.08.2026; kodla
    ilgisi yok, SDL yeniden baslatma maliyeti). Yedi ayri Game yaratmak
    testi 284 saniyeye cikariyordu. Sahne durumu zaten `set_root` ile
    sifirlaniyor - Game'i tazelemeye gerek yok.
    """
    game.scenes.set_root(Chapter01Scene, transition=False, character=character)
    game.scenes._flush()
    return game.scenes.current


def make_scene(game: Game, character: str) -> Chapter01Scene:
    game.scenes.set_root(Chapter01Scene, transition=False, character=character)
    game.scenes._flush()
    scene = game.scenes.current
    scene.beat_index = len(PROLOGUE)          # prologu atla, dogrudan oyna
    return scene


def confirm(game: Game, step: int, scene) -> None:
    """Okuyan bir oyuncuyu taklit eder - yazi bitince onaylar.

    31.08.2026'dan beri prolog replikleri oyuncuyu **bekliyor**
    (Arda: *"kullanici basana kadar yazilar gecmesin"*). Yani prologun
    icini test eden her dongu artik onaylamak zorunda; pasif bir
    dongu ilk replikte duruyor.

    KEYDOWN **ve** KEYUP birlikte gonderiliyor: `_activate` tus zaten
    basiliysa yeni bir "press" saymiyor (dogru davranis - klavye
    tekrari combo'yu bozardi), yani birakmadan ikinci kez basilamiyor.
    """
    if not (scene.dialogue.active and scene.dialogue.complete):
        return
    if step % 24:
        return
    game.input.handle_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    game.input.handle_event(
        pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))


def idle(game: Game, scene, frames: int) -> None:
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        scene.update()


def main() -> int:
    game = Game()

    # --- Ardo: Yanki yok, ogreti tetiklenmemeli ------------------------------
    print("--- Ardo: Yanki Gorusu ogretisi ---")
    ardo = make_scene(game, "ardo")
    check(ardo.echo is None, "Ardo'nun Yanki'si yok")
    check(not ardo.player.has(abilities.ECHO_SIGHT),
          "Ardo basta Yanki Gorusu'ne sahip degil (zaten olmamali)")

    ardo.player.body.set_feet(ECHO_TUTORIAL_TILE.x, ECHO_TUTORIAL_TILE.feet_y)
    ardo.player.body.vx = ardo.player.body.vy = 0.0
    # Bildirim alanini **once temizle**. Olculmek istenen sey ogretinin
    # ne urettigi; sahnenin daha once gosterdigi baska bir sey degil.
    # Envanter ipucu (`hint.inventory`) eklendiginde bu kontrol kirildi
    # ve hakli degildi: ipucu dogru calisiyordu, olcum yanlis yerdeydi.
    ardo.toast = ""
    ardo.toast_frames = 0
    idle(game, ardo, 5)
    check(not ardo.player.has(abilities.ECHO_SIGHT),
          "ogreti tetiklenince de Ardo Yanki Gorusu KAZANMIYOR")
    check(ardo.toast == "", "ogreti hicbir bildirim URETMEDI",
          repr(ardo.toast))
    check(ardo.echo_taught,
          "tetikleyici yine de 'ogretildi' isaretleniyor - tekrar denenmiyor")

    # --- Rey: ayni ogreti hala calismali (fix asiri kisitlamiyor) -----------
    print("\n--- Rey: Yanki Gorusu ogretisi hala calisiyor ---")
    rey = make_scene(game, "rey")
    check(rey.echo is not None, "Rey'in Yankisi var")
    rey.player.body.set_feet(ECHO_TUTORIAL_TILE.x, ECHO_TUTORIAL_TILE.feet_y)
    rey.player.body.vx = rey.player.body.vy = 0.0
    idle(game, rey, 5)
    check(rey.player.has(abilities.ECHO_SIGHT),
          "Rey ogretiyle Yanki Gorusu'nu kazaniyor")

    # --- Ikisi de silahsiz basliyor; kilici Jet veriyor ---------------------
    print("\n--- ikisi de silahsiz; Jet kilici veriyor ---")
    from src.scenes.chapter01_cinematics import SwordCinematic
    for who in ("rey", "ardo"):
        scene = make_scene(game, who)
        check(not scene.player.has(abilities.SWORD),
              f"{who} basta kilica sahip degil")
        check(scene.sword_pos is not None,
              f"{who} icin Jet'in kilici sahneye konmus")
        sx, sy = scene.sword_pos
        scene.player.body.set_feet(sx, sy + 11)
        idle(game, scene, 5)
        game.scenes._flush()
        check(scene.player.has(abilities.SWORD),
              f"{who} Jet'ten kilici aldi")
        check(scene.player.animator.character == f"{who}_armed",
              f"{who} kilic kusaninca armed sprite'a gecti",
              scene.player.animator.character)
        check(isinstance(game.scenes.current, SwordCinematic),
              f"{who} kilic sohbeti acildi")
        if who == "ardo":
            cur = scene.dialogue.current
            check(cur is None or cur.speaker != "echo",
                  "Ardo kilic alinca Yanki konusmuyor")
            check(scene.player.has(abilities.DODGE),
                  "Ardo kacinmayla basliyor (egitimli yabanci)")

    # --- Prolog: replikler OYUNCUYU BEKLIYOR --------------------------------
    # Arda, canli oynanis (31.08.2026): *"ilk sahnede koyde Rey ile Cemo
    # konusurken cok hizli geciyor, kullanici basana kadar yazilar
    # gecmesin."*
    #
    # Bu bolumun garantisi 31.08.2026'da **degisti**. Eskiden replikler
    # `auto_advance=True` ile aciliyordu ve test "pasif oyuncu hicbir
    # repligi kaybetmesin" diye yaziliydi. Artik beat zamanlayicisi
    # replige tabi: pasif oyuncu **ilerlemiyor**, ve bu bir hata degil
    # istenen davranis.
    #
    # Iki sey birden korunmali:
    #   1. Onaylamayan oyuncu ilk repligin uzerinde DURUYOR.
    #   2. Onaylayan oyuncu bes repligin hepsini SIRAYLA goruyor -
    #      hicbiri bir sonraki beat tarafindan sessizce ezilmiyor
    #      (Arda'nin "bunlar cok anlamsiz cumleler" hatasi buydu).
    print("\n--- prolog: replikler oyuncuyu bekliyor ---")
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    idle_scene = game.scenes.current
    for _ in range(sum(frames for frames, _ in PROLOGUE) + 300):
        game.input.begin_frame()
        game.input.end_frame()
        idle_scene.update()
    current = idle_scene.dialogue.current
    check(current is not None and current.key == "line.ch01_echo_first",
          "onaylamayan oyuncu ILK replikte duruyor",
          current.key if current else "replik yok")
    check(idle_scene.beat_index <= 1,
          "prolog ilerlemedi - beat zamanlayicisi replige tabi",
          f"beat {idle_scene.beat_index}")

    print("\n--- prolog: onaylayan oyuncu hepsini goruyor ---")
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    prolog_scene = game.scenes.current
    seen_keys: list[str] = []
    last_key = None
    for step in range(sum(frames for frames, _ in PROLOGUE) + 900):
        game.input.begin_frame()
        confirm(game, step, prolog_scene)
        game.input.end_frame()
        prolog_scene.update()
        cur = prolog_scene.dialogue.current
        key = cur.key if cur else None
        if key is not None and key != last_key:
            seen_keys.append(key)
        last_key = key
    for expected_key in ("line.ch01_echo_first", "line.ch01_cemo_gift",
                         "line.ch01_rey_thanks", "line.ch01_echo_rift",
                         "line.ch01_echo_alone"):
        check(expected_key in seen_keys,
              f"onaylayan oyuncu '{expected_key}' repligini goruyor",
              ", ".join(seen_keys))

    # --- Kolye gercekten EL DEGISTIRIYOR ------------------------------------
    # Eskiden `necklace` "alone" adiminda sessizce True oluyordu: oyunun
    # butun hikayesi o kolyeye asili ama oyuncu onun kendisine gectigi ani
    # hic gormuyordu. Artik Cemo'dan firlayip bir yay cizerek geliyor ve
    # VARDIGI karede aliniyor.
    # `make_scene()` prologu ATLIYOR (beat_index = len(PROLOGUE)) - hediye
    # prologun icinde oldugu icin onunla test edilemez. Pasif oyuncu
    # testindeki gibi sahneyi dogrudan kuruyoruz.
    print("\n--- kolye ucusu: Cemo'dan oyuncuya ---")
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    gift = game.scenes.current
    check(not gift.necklace, "baslangicta kolye YOK")
    check(gift.gift_frames < 0, "baslangicta kolye havada degil")

    saw_flight = False
    flight_positions: list[tuple[float, float]] = []
    got_at = None
    for frame in range(sum(f for f, _ in PROLOGUE) + 900):
        game.input.begin_frame()
        confirm(game, frame, gift)
        game.input.end_frame()
        gift.update()
        if gift.gift_flying:
            saw_flight = True
            flight_positions.append(gift.gift_position())
        if gift.necklace and got_at is None:
            got_at = frame

    check(saw_flight, "kolye havada bir sure gorunuyor (ucus var)")
    check(got_at is not None, "kolye sonunda oyuncuya geciyor", str(got_at))
    check(len(flight_positions) > 1, "ucus birden fazla kare suruyor",
          f"{len(flight_positions)} kare")
    if len(flight_positions) > 2:
        # Yay: orta noktanin yuksekligi iki ucun ortalamasindan YUKARIDA
        # olmali (ekran koordinatinda kucuk y = yukari). Duz gitseydi
        # "isinlandi" gibi okunurdu.
        first_y = flight_positions[0][1]
        last_y = flight_positions[-1][1]
        mid_y = flight_positions[len(flight_positions) // 2][1]
        check(mid_y < (first_y + last_y) * 0.5,
              "ucus DUZ degil, yay ciziyor (firlatilmis nesne gibi)",
              f"orta {mid_y:.1f} < ortalama {(first_y + last_y) * 0.5:.1f}")

    # --- Koyluler: gezinir, yarik acilinca evlerine kacar -------------------
    # Arda'nin istegi: "ilk basta etrafta koyluler dolasabilir. Olaylar
    # patlak verdiginde koyluler evlerine kacsin." Prologun anlatimi
    # "sakin koy -> yarik -> kayip" uzerine kurulu; koy yasamiyorsa
    # kaybedilen sey de soyut kaliyor.
    print("\n--- koyluler: gezinme ve kacis ---")
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    village = game.scenes.current

    check(len(village.villagers) >= 3, "koyde birden fazla koylu var",
          str(len(village.villagers)))
    start_positions = [v.x for v in village.villagers]

    # Yarik acilmadan once: gezinirler, hicbiri kacmaz.
    for _ in range(120):
        game.input.begin_frame(); game.input.end_frame()
        village.update()
    check(not village.villagers_fled, "yarik acilmadan kimse kacmiyor")
    moved = sum(1 for v, x0 in zip(village.villagers, start_positions)
                if abs(v.x - x0) > 1.0)
    check(moved > 0, "koyluler gercekten geziniyor (yerlerinde durmuyorlar)",
          str(moved) + " koylu hareket etti")
    check(all(v.state == "wander" for v in village.villagers),
          "hepsi hala gezinme durumunda")

    # Prologun geri kalanini oynat: yarik acilir, koyluler kacar.
    for frame in range(sum(f for f, _ in PROLOGUE) + 900):
        game.input.begin_frame()
        confirm(game, frame, village)
        game.input.end_frame()
        village.update()
    check(village.villagers_fled, "yarik acilinca kacis tetiklendi")
    check(not village.villagers,
          "butun koyluler evlerine girdi (listeden dustuler)",
          str(len(village.villagers)) + " kaldi")

    # --- Yanki Rey'in laneti: Ardo onu DUYMAZ ------------------------------
    # Olculdu (24.08.2026): prolog replikleri karakterden bagimsiz
    # oynuyordu. Ardo da mor sesi duyuyordu - ona yol gostermeyi teklif
    # eden bir ses duyup sonra o yetenegi hic almiyordu. Ayrica tesekkur
    # repligi sabit "rey" konusmaciyla yaziliydi: Ardo oynarken ekranda
    # "REY" etiketi cikiyordu.
    print("\n--- Yanki Rey'e ozel, replikler oynanan karaktere ait ---")

    def prologue_lines(character: str):
        game.scenes.set_root(Chapter01Scene, transition=False,
                             character=character)
        game.scenes._flush()
        scene = game.scenes.current
        seen, last = [], None
        for frame in range(sum(f for f, _ in PROLOGUE) + 900):
            game.input.begin_frame()
            confirm(game, frame, scene)
            game.input.end_frame()
            scene.update()
            cur = scene.dialogue.current
            key = (cur.speaker, cur.key) if cur else None
            if key is not None and key != last:
                seen.append(key)
            last = key
        return seen

    rey_lines = prologue_lines("rey")
    ardo_lines = prologue_lines("ardo")

    check(any(sp == "echo" for sp, _ in rey_lines),
          "Rey Yanki'yi duyuyor",
          str(sum(1 for sp, _ in rey_lines if sp == "echo")) + " replik")
    check(not any(sp == "echo" for sp, _ in ardo_lines),
          "Ardo Yanki'yi DUYMUYOR (Yanki Rey'in laneti)",
          ", ".join(sp for sp, _ in ardo_lines))
    check(not any(sp == "rey" for sp, _ in ardo_lines),
          "Ardo oynarken hicbir replik REY etiketiyle cikmiyor",
          ", ".join(sp for sp, _ in ardo_lines))
    check(any(sp == "ardo" for sp, _ in ardo_lines),
          "Ardo kendi sesiyle konusuyor (motivasyonu yaziliyor)",
          str(sum(1 for sp, _ in ardo_lines if sp == "ardo")) + " replik")

    game.shutdown()

    test_ardo_jet_talks_like_rey()
    test_sword_handoff()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 1 karakter-ozel ogreti kurallarina uyuyor.")
    return 0


def test_ardo_jet_talks_like_rey() -> None:
    """Kilici verirken Ardo da isim sohbetini yasar - kisa selam degil."""
    print("\n--- Ardo-Jet kilic sohbeti ---")
    from src.scenes.chapter01_cinematics import SwordCinematic

    game = Game()
    try:
        game.scenes.set_root(Chapter01Scene, transition=False, character="ardo")
        game.scenes._flush()
        game.scenes.push(SwordCinematic, character="ardo")
        game.scenes._flush()
        top = game.scenes.current
        check(isinstance(top, SwordCinematic), "Ardo kilic sinematigi acildi")
        if not isinstance(top, SwordCinematic):
            return
        isim = next(p for p in top.panels if p.name == "isim")
        keys = [line.key for line in isim.dialogue_lines]
        check("line.ch01_ardo_emre" in keys,
              "Ardo Emre adini kendisi soyluyor", str(keys))
        check("line.ch01_jet_name2_ardo" in keys,
              "Ardo da adi seven soyler vurusunu duyuyor", str(keys))
        check(len(isim.dialogue_lines) >= 5,
              "isim paneli kisa selam degil",
              str(len(isim.dialogue_lines)))
        uzatma = next(p for p in top.panels if p.name == "uzatma")
        check(len(uzatma.dialogue_lines) >= 5,
              "uzatma sohbet, iki satirlilik selam degil",
              str(len(uzatma.dialogue_lines)))
        ayrilik = next(p for p in top.panels if p.name == "ayrilik")
        leave = [line.key for line in ayrilik.dialogue_lines]
        check("line.ch01_ardo_leave" in leave,
              "Ardo veda ediyor", str(leave))
    finally:
        game.shutdown()


def step_game(game: Game, frames: int = 1) -> None:
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        game.scenes.update()
        game.frame += 1


def press_confirm(game: Game) -> None:
    game.input.begin_frame()
    game.input.handle_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    game.input.handle_event(
        pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
    game.input.end_frame()
    game.scenes.update()
    game.frame += 1


def wait_line_ready(game: Game, scene, limit: int = 240) -> None:
    for _ in range(limit):
        if (scene.dialogue.active and scene.dialogue.complete
                and scene.dialogue.lock <= 0):
            return
        step_game(game)


def save_canvas(game: Game, name: str) -> Path:
    game.canvas.fill((0, 0, 0, 255))
    game.scenes.draw(game.canvas)
    path = ROOT / "build" / "testshots" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    scaled = pygame.transform.scale(
        game.canvas, (game.canvas.get_width() * 2, game.canvas.get_height() * 2))
    pygame.image.save(scaled, str(path))
    return path


def _save_brightness_variants(game: Game, stem: str) -> None:
    """Ayni kare 0.75 / 1.0 / 1.25 - kaydiricinin oyunu da actigini gosterir."""
    from src.art import brightness
    from src.config import BRIGHTNESS_DEFAULT, BRIGHTNESS_MAX, BRIGHTNESS_MIN

    base = game.canvas.copy()
    for value, suffix in (
        (BRIGHTNESS_MIN, "dim"),
        (BRIGHTNESS_DEFAULT, "default"),
        (BRIGHTNESS_MAX, "lift"),
    ):
        frame = base.copy()
        brightness.apply(frame, value)
        path = ROOT / "build" / "testshots" / f"{stem}_{suffix}.png"
        scaled = pygame.transform.scale(
            frame, (frame.get_width() * 2, frame.get_height() * 2))
        pygame.image.save(scaled, str(path))


def test_sword_handoff() -> None:
    """Jet kilici elinde tutar; ilk onayda teslim, sonra oyuncu kusaniyor."""
    print("\n--- Jet kilic teslimi ---")
    from src.art import palette
    from src.config import HITSTOP_FINISHER
    from src.scenes.chapter01_cinematics import (
        APPROACH_FRAMES, SWORD_REACH, SWORD_SCALE, SwordCinematic,
    )
    from src.scenes.chapter01_render import blit_sword

    blade = pygame.Surface((48, 48), pygame.SRCALPHA)
    blit_sword(blade, 16, 4, scale=SWORD_SCALE)
    stone = palette.color("stone_light")
    # Uç kemik rengi; namluyu ortasından say.
    mid_y = 4 + 8
    width = sum(1 for x in range(48) if blade.get_at((x, mid_y))[:3] == stone)
    check(width == SWORD_SCALE, "sinematik kilic 2px namlu, 1px cizgi degil",
          str(width))

    game = Game()
    try:
        game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
        game.scenes._flush()
        game.scenes.push(SwordCinematic, character="rey")
        game.scenes._flush()
        cin = game.scenes.current
        assert isinstance(cin, SwordCinematic)

        step_game(game, APPROACH_FRAMES + 2)
        check(cin.panel is not None and cin.panel.name == "uzatma",
              "uzatma panosuna ulasildi",
              cin.panel.name if cin.panel else "yok")
        player = cin.actor("player")
        jet = cin.actor("jet")
        check(player is not None and player.animator.character == "rey",
              "uzatmada oyuncu hâlâ silahsiz",
              player.animator.character if player else "yok")
        check(jet is not None and jet.animator.character == "jet_unarmed",
              "uzatmada Jet bel kilici tasimiyor",
              jet.animator.character if jet else "yok")
        from src.art.animation import CHARACTERS
        from src.art.animator import Animator as _Animator
        check(CHARACTERS["jet_unarmed"].weapon == "none",
              "jet_unarmed spec silahsiz")
        check(CHARACTERS["jet"].weapon == "sword",
              "varsayilan jet silueti silahli kalir")
        armed = _Animator("jet")
        armed.play("idle")
        bare = _Animator("jet_unarmed")
        bare.play("idle")
        assert armed.image is not None and bare.image is not None
        armed_px = pygame.mask.from_surface(armed.image).count()
        bare_px = pygame.mask.from_surface(bare.image).count()
        check(armed_px > bare_px,
              "silahsiz Jet'te bel namlusu yok (daha az piksel)",
              f"jet {armed_px} unarmed {bare_px}")
        check(cin.actor("jet") is jet,
              "cue adi hâlâ jet - yakin plan portreyi bulur")
        pos = cin.sword_screen_pos()
        check(pos is not None, "kilic Jet'in elinde gorunuyor")
        if pos is not None:
            jet_x = int(round(cin.JET_X)) - SWORD_REACH
            mid_x = int(round((cin.JET_X + cin.PLAYER_X) * 0.5))
            check(abs(pos[0] - jet_x) <= 1,
                  "kilic iki govdenin ortasinda degil, Jet'te",
                  f"x={pos[0]} jet={jet_x} mid={mid_x}")
            check(abs(pos[0] - mid_x) > 8,
                  "eski 1px orta-cizgi konumundan uzak")
        wait_line_ready(game, cin)
        save_canvas(game, "jet_sword_offer.png")
        _save_brightness_variants(game, "jet_sword_offer")

        press_confirm(game)
        check(cin._passing and not cin._handed,
              "ilk onay teslimi baslatti",
              f"passing={cin._passing} handed={cin._handed}")
        check(cin.freeze_frames > 0,
              "teslim hitstop (bitirici 7 kare)",
              str(cin.freeze_frames))
        pass_pos = cin.sword_screen_pos()
        check(pass_pos is not None, "freeze karesinde kilic havada")
        if pos is not None and pass_pos is not None:
            check(pass_pos[0] < pos[0],
                  "kilic Jet'ten oyuncuya dogru kaydi",
                  f"{pos[0]} -> {pass_pos[0]}")
        check(player is not None and player.animator.character == "rey",
              "freeze bitmeden armed sprite yok",
              player.animator.character if player else "yok")
        save_canvas(game, "jet_sword_pass.png")

        step_game(game, HITSTOP_FINISHER + 1)
        check(cin._handed and not cin._passing,
              "freeze bitince teslim tamam",
              f"handed={cin._handed} passing={cin._passing}")
        check(player is not None and player.animator.character == "rey_armed",
              "oyuncu kusanmis sprite'a gecti",
              player.animator.character if player else "yok")
        check(jet is not None and jet.animator.character == "jet_unarmed",
              "teslimden sonra Jet silahsiz kalir",
              jet.animator.character if jet else "yok")
        check(cin.sword_screen_pos() is None,
              "sahte kilic kayboldu (cift namlu yok)")
        step_game(game, 24)
        save_canvas(game, "jet_sword_armed.png")

        # Fotosensitivite: olay olur, beyaz kare cizilmez.
        game.settings.set("flash_limit", True)
        game.scenes.pop()
        game.scenes._flush()
        game.scenes.push(SwordCinematic, character="ardo")
        game.scenes._flush()
        cin2 = game.scenes.current
        assert isinstance(cin2, SwordCinematic)
        step_game(game, APPROACH_FRAMES + 2)
        wait_line_ready(game, cin2)
        press_confirm(game)
        check(cin2._passing, "flash_limit teslimi iptal etmez")
        check(cin2.flash_strength <= 0.01,
              "flash_limit acikken parlama yok",
              str(cin2.flash_strength))
        ardo = cin2.actor("player")
        step_game(game, HITSTOP_FINISHER + 1)
        check(ardo is not None and ardo.animator.character == "ardo_armed",
              "Ardo da teslimde armed sprite'a gecer",
              ardo.animator.character if ardo else "yok")
        jet2 = cin2.actor("jet")
        check(jet2 is not None and jet2.animator.character == "jet_unarmed",
              "Ardo sahnesinde de Jet silahsiz",
              jet2.animator.character if jet2 else "yok")
    finally:
        game.shutdown()


raise SystemExit(main())