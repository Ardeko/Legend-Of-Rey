"""Mekanik ipuclari - oyuncu yeni bir seyi OGRENIYOR mu?

Arda, canli oynanis (08.09.2026):

  * *"can kulesi bolumunde kullanici ne yapmasi gerektigini asla
    anlamiyor"*
  * *"karakter degistirebildigimiz bolumde de hint yok"*
  * *"yeni mekanik acilan her bolum icin guzel grafiklerle ve belirgin
    ux ui ile ipuclari versin oyun"*

Bir tus varsa ama kimse bilmiyorsa **yok** demektir.

Korunan kurallar:

  * Her yeni mekanigin bir ipucu var ve o ipucu bir KART (bildirim
    degil). Bildirim, "14 COMBO" ile ayni yerde ve ayni bicimde
    cikiyordu - oyunun "bu senin yeni yetenegin" demesiyle bir combo
    sayaci gorsel olarak ayni seydi.
  * Kart oynanisi **durdurmuyor** (`CLAUDE.md` 9).
  * Tus adi atama tablosundan okunuyor - sabit "G" yazsaydik tusu
    degistiren oyuncuya yalan soylerdik.
  * Metin karta **sigiyor**. Ilk surum tasiyordu ve ancak ekran
    goruntusune bakinca goruldu.
  * Anahtarlar duz dize - f-string ile kurulani `test_lang.py`
    goremiyor ve "olu anahtar" sayiyor (bu tuzaga bes kez dusuldu).

Calistir:
    python tests/test_hints.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# **Oyuncunun kaydina DOKUNMA.** Gerekcesi oteki paketlerde yazili.
import tempfile  # noqa: E402

os.environ["LORE_SAVE_DIR"] = tempfile.mkdtemp(prefix="lore_test_")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.systems.save import SaveData as _SaveData  # noqa: E402
from src.systems.save import write_save as _write_save  # noqa: E402

_write_save(_SaveData())

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.ui import i18n  # noqa: E402
from src.ui import mechanic_card as card_mod  # noqa: E402
from src.ui.mechanic_card import (  # noqa: E402
    BODY_COLUMNS, HEIGHT, TITLES, TOTAL, WIDTH, MechanicCard, title_for,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def main() -> int:
    i18n.set_language("tr")
    game = Game()
    game.settings.save = lambda *a, **k: None    # type: ignore[method-assign]

    # --- 1. Her baslik anahtari cozuluyor ----------------------------------
    print("--- anahtarlar ---")
    for body_key, title_key in TITLES.items():
        for lang in ("tr", "en"):
            i18n.set_language(lang)
            for key in (body_key, title_key):
                resolved = i18n.t(key, key="G")
                check(resolved != f"[{key}]", f"{lang}: {key} cozuluyor",
                      resolved if resolved != f"[{key}]" else "")
    i18n.set_language("tr")

    check(title_for("hint.bell") == "hint.bell_title",
          "govde anahtarindan baslik anahtari bulunuyor")
    check(title_for("hint.olmayan") == "hint.olmayan",
          "bilinmeyen anahtar kartı BOZMUYOR - govde iki kez cikar, "
          "oyun calisir")

    # --- 2. Metin karta SIGIYOR --------------------------------------------
    # Ilk surum tek satir ciziyordu ve Turkce metin sag kenardan
    # tasiyordu ("G ile sesini gonder - ça|"). Olcum degil GOZ yakaladi;
    # artik olcum de yakaliyor.
    print("\n--- metin karta sigiyor ---")
    from src.ui.dialogue import _wrap
    for lang in ("tr", "en"):
        i18n.set_language(lang)
        for body_key in TITLES:
            body = i18n.t(body_key, key="Tab")
            rows = _wrap(body, BODY_COLUMNS)
            check(len(rows) <= card_mod.BODY_LINES,
                  f"{lang}: {body_key} en fazla {card_mod.BODY_LINES} satir",
                  f"{len(rows)} satir: {body}")
            check(all(len(r) <= BODY_COLUMNS for r in rows),
                  f"{lang}: {body_key} satirlari genisligi asmiyor",
                  str([len(r) for r in rows]))
        # Basliklar tek satir ve karta sigmali.
        for title_key in TITLES.values():
            title = i18n.t(title_key)
            check(len(title) <= BODY_COLUMNS + 2,
                  f"{lang}: {title_key} basligi sigiyor",
                  f"{len(title)} karakter: {title}")
    i18n.set_language("tr")

    # --- 3. Kart ciziliyor ve SONUYOR --------------------------------------
    print("\n--- kart yasam dongusu ---")
    import numpy as np
    canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

    def pixels(card_obj) -> int:
        canvas.fill((0, 0, 0))
        card_obj.draw(canvas)
        return int(np.count_nonzero(pygame.surfarray.array3d(canvas)))

    card = MechanicCard("hint.bell_title", "hint.bell", "resonance", "G")
    check(pixels(card) == 0, "ilk karede henuz gorunmuyor")
    for _ in range(90):
        card.update()
    drawn = pixels(card)
    check(drawn > 0, "kart ciziliyor", f"{drawn} piksel")
    check(not card.done, "hala ekranda")

    for _ in range(TOTAL):
        card.update()
    check(card.done, "kendiliginden kapaniyor - oyuncu bir sey yapmiyor")
    check(pixels(card) == 0, "kapaninca hicbir sey cizmiyor")

    # --- 4. Her ikonun cizicisi var ----------------------------------------
    # Bilinmeyen ikon adi kartI bozmamali; ama bilinen adlarin GERCEKTEN
    # farkli cizmesi lazim, yoksa ikon fikri anlamsiz.
    print("\n--- ikonlar ---")
    seen: dict[str, int] = {}
    for icon in ("resonance", "boost", "switch", "companion", "inventory"):
        one = MechanicCard("hint.bell_title", "hint.bell", icon, "G")
        for _ in range(90):
            one.update()
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        one._draw_icon(surface)
        seen[icon] = int(np.count_nonzero(
            pygame.surfarray.array3d(surface)))
        check(seen[icon] > 0, f"{icon} ikonu cizim uretiyor",
              f"{seen[icon]} piksel")
    check(len(set(seen.values())) > 1,
          "ikonlar birbirinden FARKLI - hepsi ayni cizseydi ikon fikri "
          "anlamsiz olurdu", str(seen))

    unknown = MechanicCard("hint.bell_title", "hint.bell", "olmayan", "G")
    for _ in range(90):
        unknown.update()
    check(pixels(unknown) > 0,
          "bilinmeyen ikon adi kartI BOZMUYOR - genel isaret ciziliyor")

    # --- 5. B9'un can ipucu GERCEKTEN cikiyor ------------------------------
    # Bu, Arda'nin "can kulesinde ne yapacagimi anlamiyorum" sikayetinin
    # dogrudan karsiligi: bu bolumde rezonans icin HICBIR ipucu yoktu.
    print("\n--- B9: can ipucu ---")
    from src.scenes.chapter09 import BELL_HINT_RANGE, Chapter09Scene

    game.scenes.set_root(Chapter09Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current
    if scene.save_data is None:
        scene.save_data = _SaveData()
    scene.save_data.flags.pop("hint_bell", None)
    scene.mechanic_card = None

    check(bool(scene.bells), "bolumde can var", str(len(scene.bells)))
    bell = scene.bells[0]
    far = bell.rect.centerx + BELL_HINT_RANGE * 3
    scene.player.body.set_feet(far, scene.player.body.feet[1])
    scene._update_bell_hint()
    check(scene.mechanic_card is None, "uzaktayken ipucu YOK")

    scene.player.body.set_feet(float(bell.rect.centerx),
                               float(bell.rect.centery + 8))
    scene._update_bell_hint()
    check(scene.mechanic_card is not None,
          "cana yaklasinca ipucu KARTI aciliyor")
    if scene.mechanic_card is not None:
        check(scene.mechanic_card.icon == "resonance",
              "rezonans ikonu", scene.mechanic_card.icon)
        check(scene.mechanic_card.key_label,
              "tus etiketi atama tablosundan geldi",
              scene.mechanic_card.key_label)

    scene.mechanic_card = None
    scene._update_bell_hint()
    check(scene.mechanic_card is None,
          "BIR KEZ - her cana yaklasmada tekrarlanmiyor")

    # --- 6. Kart oynanisi DURDURMUYOR --------------------------------------
    print("\n--- kart oynanisi durdurmuyor ---")
    scene.save_data.flags.pop("hint_bell", None)
    scene._update_bell_hint()
    before = scene.player.body.center_x
    for _ in range(30):
        game.input.begin_frame()
        game.input.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        game.input.end_frame()
        scene.update()
    check(scene.player.body.center_x != before,
          "kart acikken oyuncu YURUYEBILIYOR",
          f"{before:.0f} -> {scene.player.body.center_x:.0f}")

    # --- 7. Her gercek mekanigin ipucu var ---------------------------------
    # Kaynak taramasi: `icon=` verilen her `hint_once` cagrisi bir kart
    # aciyor. Sayi dusarse bir mekanik sessizce ipucusuz kalmis demektir.
    print("\n--- her mekanigin ipucu var ---")
    import re
    calls: list[str] = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        body = path.read_text(encoding="utf-8")
        calls += re.findall(r'hint_once\(\s*"([a-z_]+)"', body)
    check(len(calls) >= 11, "ipucu cagrisi sayisi", f"{len(calls)} cagri")
    for needed in ("hint_bell", "hint_resonance", "hint_boost",
                   "hint_switch", "hint_inventory", "hint_companion"):
        check(needed in calls, f"{needed} bir yerden cagriliyor")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Her yeni mekanik ogretiliyor - kartla, tusuyla, bir kez.")
    return 0


raise SystemExit(main())
