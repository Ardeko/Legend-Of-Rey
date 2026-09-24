"""Gezgin Mum Bekcisi - ok ve bombayi bolum bolum yeniden alabilmek.

Arda, 23.09.2026: *"Firlatilabilir itemler olunce sifirlanacak mi?
Sifirlancaksa olduktan sonra bir daha nasil alabilecek? Adaletsiz olur
eger dukkan olmazsa. Daha fazla dukkan olmali."*

## Sorun olculdu

Oyunun tek saticisi B3'teki Mum Bekcisi'ydi. B3'ten sonra oku biten
oyuncu **on bes bolum** boyunca yeniden alamiyordu - ve altin birikmeye
devam ediyordu, harcanacak yeri yoktu.

## Neden yeni bir karakter degil

Bekci zaten "konusmayan, savasmayan, ticaret yapan varlik"
(`candle_keeper.py`). Onun B6, B9, B12 ve B15'te **yeniden** belirmesi
bir dukkan zincirinden fazlasi: oyuncu uc bolum asagida ayni kukuletali
sekli goruyor ve "bu nasil buraya indi?" diye soruyor. Korku katmaninin
istedigi tekinsizlik (`docs/korku.md` - "dusman olmayan varliklar
yalnizligi derinlestirir") bedavaya geliyor.

Tabagi kucuk: yalnizca sarf malzemeleri. Tekil esyalar (Sonmez Fitil,
Olum Mumu) B3'e ait kaliyor - her dukkanda ayni seyleri satmak B3'un
kararini sulandirirdi.

## Sahneye nasil baglanir

`PlayScene` bolumun iki sinif ozelligine bakiyor, ikisi de `None` ise
bekci yok:

    merchant_tile     (sutun, satir) - acik yer. Girisi bir dovus ya da
                      sinematik olan bolumler icin (B6: kurtaris).
    merchant_offset   oyuncunun dogdugu noktadan piksel uzaklik.

Iki durumda da zemine oturtuluyor; zemin bulunamazsa bekci konmuyor.
"""
from __future__ import annotations

import pygame

from src.config import (CANDLE_KEEPER_PRICE_ARROWS, CANDLE_KEEPER_PRICE_BOMB,
                        TILE_SIZE)
from src.core.input import Action
from src.entities.candle_keeper import DEFAULT_CANDLES, CandleKeeper
from src.systems import consumables, economy
from src.systems.economy import TradeOffer
from src.ui import shop
from src.ui.i18n import t

# Gezgin tabagi - B3'un sarf teklifleriyle **ayni anahtar ve fiyat**.
# Fiyat farkli olsaydi oyuncu B3'te "ucuzmus" diye stok yapmayi ogrenirdi.
TRAVEL_OFFERS: tuple[TradeOffer, ...] = (
    TradeOffer("buy_arrows", CANDLE_KEEPER_PRICE_ARROWS, "trade.arrows",
               repeatable=True, item=consumables.ARROW, amount=3),
    TradeOffer("buy_bomb", CANDLE_KEEPER_PRICE_BOMB, "trade.bomb",
               repeatable=True, item=consumables.BOMB, amount=1),
)

# Oyuncu bu kadar yakinsa tus gostergesi cikiyor ve INTERACT tabagi aciyor.
REACH_X = 20
REACH_Y = 24
# Bu mesafede uyanik bir dusman varken tezgah ACILMIYOR, aciksa kapaniyor.
# Tezgah acikken oyuncu komut almiyor (`PlayScene._update_player`);
# dovusun ortasinda acilabilseydi alisveris bir tuzak olurdu.
THREAT_RANGE = 150.0


# --- Satin alma (B3 ve gezgin ortak) -----------------------------------------
def buy(scene, offer: TradeOffer) -> bool:
    """Tek satin alma kurali. Basarili olursa `True`.

    Siralama onemli: once "alabilir mi" sorulari, SONRA altin dusuyor.
    Dolu cantaya satis eskiden altini alip hicbir sey vermiyordu
    (`consumables.add` `MAX_CARRY`de kirpiyordu).
    """
    data = scene.save_data
    if economy.already_bought(data, offer):
        scene.show_toast(t("chapter03.already_bought"))
        scene.game.play_sound("ui_deny")
        return False
    if (offer.repeatable and offer.item
            and consumables.count(data, offer.item) >= consumables.MAX_CARRY):
        scene.show_toast(t("shop.full_toast"))
        scene.game.play_sound("ui_deny")
        return False
    if not economy.spend(data, offer.cost):
        scene.show_toast(t("chapter03.not_enough_gold"))
        scene.game.play_sound("ui_deny")
        return False
    if offer.repeatable:
        total = consumables.add(data, offer.item, offer.amount)
        if total == offer.amount:
            # Ilk kez alindi - firlatma tusunu ogret.
            scene.hint_once("hint_throw", "hint.throw", Action.THROW,
                            icon="throw")
        scene.show_toast(t("chapter03.bought_item",
                           name=t(offer.label_key), count=total), frames=160)
    else:
        economy.mark_bought(data, offer)
        scene.show_toast(t(offer.label_key), frames=160)
    scene.game.play_sound("chest_open")
    return True


# --- Gezgin ------------------------------------------------------------------
class TravellingMerchant:
    """Bir bolumde oturan bekci ve tabagi."""

    def __init__(self, x: float, feet_y: float, candles: int = 4) -> None:
        self.keeper = CandleKeeper(x, feet_y, candles=candles)
        self.open = False
        self.index = 0

    def near(self, player) -> bool:
        return (abs(self.keeper.x - player.body.center_x) < REACH_X
                and abs(self.keeper.feet_y - player.body.feet[1]) < REACH_Y)

    def update(self, scene) -> None:
        """Kare isi. **Once** acik tabak, sonra acma - ayni E basisi hem
        acip hem satin almasin (`CONFIRM` E'yi de iceriyor)."""
        self.keeper.update()
        inp = scene.game.input
        threatened = _threatened(scene)
        if self.open and threatened:
            self.open = False
            scene.game.play_sound("ui_deny")
            return
        if self.open:
            self.index = shop.step_index(inp, self.index, len(TRAVEL_OFFERS))
            if inp.pressed(Action.UP) or inp.pressed(Action.DOWN):
                scene.game.play_sound("ui_tick")
            if shop.wants_close(inp) or not self.near(scene.player):
                self.open = False
            elif shop.wants_buy(inp):
                buy(scene, TRAVEL_OFFERS[self.index])
            return
        if scene.player.dead or threatened or not self.near(scene.player):
            return
        scene.prompts.offer("merchant", self.keeper.x, self.keeper.feet_y - 24,
                            verb_key="prompt.trade")
        if inp.pressed(Action.INTERACT):
            self.open = True
            self.index = 0
            scene.game.play_sound("ui_confirm", bus="volume_sfx")

    def draw_world(self, surface: pygame.Surface, offset) -> None:
        self.keeper.draw(surface, offset)

    def draw_panel(self, surface: pygame.Surface, scene) -> None:
        if self.open:
            shop.draw(surface, TRAVEL_OFFERS, self.index, scene.save_data,
                      "shop.title_travel", scene.game.input, scene.game.frame)


def _threatened(scene) -> bool:
    """Oyuncunun yakininda uyanik, diri bir dusman var mi?"""
    player = scene.player.body
    for enemy in getattr(scene, "enemies", ()):
        if getattr(enemy, "dead", False) or not getattr(enemy, "aware", False):
            continue
        if (abs(enemy.body.center_x - player.center_x) < THREAT_RANGE
                and abs(enemy.body.center_y - player.center_y) < THREAT_RANGE):
            return True
    return False


def place(scene, offset: float) -> TravellingMerchant | None:
    """Oyuncunun dogdugu yerden `offset` piksel otede."""
    return _grounded(scene, scene.player.body.center_x + offset,
                     scene.player.body.feet[1])


def place_at_tile(scene, tile_x: int, tile_y: int) -> TravellingMerchant | None:
    """Acik bir karonun ortasinda; `tile_y` bekcinin durdugu satir."""
    return _grounded(scene, tile_x * TILE_SIZE + TILE_SIZE * 0.5,
                     (tile_y + 1) * TILE_SIZE)


def _grounded(scene, x: float, feet_hint: float) -> TravellingMerchant | None:
    """Zemine oturtulmus bir bekci - ya da hic.

    Zemin asagi dogru araniyor; bulunamazsa ya da nokta duvarin
    icindeyse bekci **hic konmuyor** - havada asili bir satici, hic
    olmamasindan kotu.
    """
    feet = scene.tilemap.floor_below(x, feet_hint, 12, 20)
    if feet is None:
        return None
    return TravellingMerchant(x, feet, candles_for(scene))


def candles_for(scene) -> int:
    """*"Her seferinde biraz daha az mumla"* (`docs/bolum-03.md` 122).

    B3'te bes; B7'de dort, B12'de uc, B16'da iki. Bolum numarasindan
    turuyor - her bolume elle bir sayi yazmak birinin unutulmasiydi.
    """
    chapter = getattr(scene, "chapter_number", 0) or 0
    return max(1, DEFAULT_CANDLES - max(0, chapter - 3) // 4)
