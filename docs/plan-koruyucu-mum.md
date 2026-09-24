# PLAN — Koruyucu Mum: bir vuruşu senin yerine karşılayan tek kullanımlık

**Ardeko Studios · 25.09.2026 · ONAY BEKLİYOR**

Arda: *"Mum Bekçisi 1 hit'i engelleyebilecek harcanabilir tek kullanımlık bir şey satabilir, öyle bir mekanik ekleyelim. Ama bunun tasarımı çok önemli."*

> Bu belge bir **plan**. Kod yazılmadı. Sayılar `src/config.py`'ye girecek önerilerdir. Açık sorular §9'da.

---

## 1. Keşifte çıkan hata — bugün 320 altın boşa gidiyor

B3'teki Bekçi tezgâhı üç şey satıyor (`src/scenes/chapter03.py:73-74`). İkisinin **hiçbir etkisi yok**:

| Ürün | Fiyat | Belgedeki amaç (`docs/bolum-03.md` 115-116) | Koddaki durum |
|---|---|---|---|
| Meşale | 40 | yeni meşale | çalışıyor |
| Sönmez Fitil | 120 | "meşale artık kendi kendine sönmüyor" | **etkisiz.** B3'te meşaleler zaten hiç sönmüyor (`src/world/torch.py`'de ömür yok) |
| Koruyucu Mum | 200 | "öldüğün yerde yanar, altınını korur" | **etkisiz.** Ölünce altın kaybı da yok: `DEATH_GOLD_LOSS_RATIO` tanımlı ama hiçbir yerde kullanılmıyor |

`merchant.buy` iki ürünü "alındı" diye işaretliyor, altını düşüyor ve bitiriyor. Oyuncu 320 altın öder, hiçbir şey olmaz.

**Öneri:** İstenen mekanik için yeni bir ürün uydurmak yerine **Koruyucu Mum**'u o yapmak. Adı da, Bekçi'nin kendisi de zaten bunu anlatıyor: bekçinin mumları azalıyor (B3'te beş, B16'da iki, epilogda bir). Her mum bir can. Sana birini veriyor; vuruş geldiğinde o mum senin yerine sönüyor.

## 2. Tek cümle

**Koruyucu Mum, üzerindeyken seni vuracak ilk darbeyi karşılayıp söner.** Tuşu yok, seçimi yok. Onu almak bir karar; harcamak kendiliğinden oluyor.

## 3. Kurallar — ve her birinin nedeni

| # | Kural | Neden |
|---|---|---|
| 1 | **Pasif, kendiliğinden.** Hasar alacağın ilk vuruşta tetiklenir | Bir tuş olsaydı kaçınmayla yarışırdı. Bu bir sigorta, beceri değil |
| 2 | **En fazla 1 taşınır.** Doluyken satılmaz | İki mum boss dövüşlerini "iki hata hakkı"na çevirirdi. Bir mum = bir hata, o kadar |
| 3 | **Vuruşun hasarını tamamen siler.** Geri itme yarıya iner, hitstop normal (3 kare) | Oyuncu neyin olduğunu **hissetmeli**. Hasar yok ama darbe var |
| 4 | Söndükten sonra **30 kare dokunulmazlık** | Çok vuruşlu saldırıda (Zindancı'nın zinciri, sürü) mum ilk vuruşu karşılar, ikincisi hemen gelirse satın alma boşa gider |
| 5 | Kaçınmayla atlatılan vuruşta **tetiklenmez** | Dokunulmazlık zaten koruyor; mumu yakmak cezaya dönerdi |
| 6 | **"Son şans"tan önce** gelir (`CLAUDE.md` §8) | Mum oyuncunun bilinçli aldığı şey; af sessiz yedek. Önce bilinen harcansın |
| 7 | **Her hasar kaynağını** karşılar: düşman, boss, mermi, tuzak, lav. **Dünyanın dışına düşmeyi** karşılamaz | Düşüş zaten yeniden doğuruyor, can almıyor. Onu "karşılamak" anlamsız |
| 8 | Yalnız **oyuncu karakteri**. Yoldaş korunmaz | Mum senin |
| 9 | B17'de iki karakter: **ilk vurulan** korunur (çanta ortak) | Kayıtta tek sayaç; karakter başına ayrı bir envanter karmaşa |

## 4. Görünür ve duyulur olmalı — `CLAUDE.md` §9: diegetik tercih

- **Taşırken:** Oyuncunun omzunun üstünde küçük bir mum alevi süzülüyor. Bekçi'nin gözleriyle aynı alev (`candle_keeper._draw_eyes`, aynı titreme). HUD çubuğu **yok**: alevin kendisi göstergedir.
- **Tetiklenince:**
  - Alev bir anda büyüyor ve mor-altın bir halka olarak dağılıyor (Bekçi'nin cüppesi mor, alevi altın): 12 parçacık, `violet` ve `spark` yolları.
  - Yeni tek atımlık ses `ward_break`: yumuşak bir üfleme ve cam gibi bir çınlama. Oyuncu bir şeyin **kırıldığını** değil **söndüğünü** duymalı.
  - Oyuncu 30 kare boyunca bir kademe açık tonda (dokunulmazlık okunmalı). Parlama **yok**: fotosensitivite, `flash_limit`.
- **Renk körlüğü:** Alev + şekil (halka) birlikte. Tek başına renk değil (`CLAUDE.md` §10).

## 5. Sayılar (öneri)

| Sabit | Değer | Gerekçe |
|---|---|---|
| `WARD_PRICE` | **60** altın | Bir bölümün geliri ~250 (`docs/ekonomi-uretim.md`). Mum bir bölüm gelirinin dörtte biri: anlamlı ama kıskanç değil. Bugünkü 200, altın koruma içindi |
| `WARD_MAX_CARRY` | 1 | Kural 2 |
| `WARD_IFRAMES` | 30 kare | Kural 4. Bir kaçınmanın toplamından (18) uzun, ikisinin toplamından kısa |
| `WARD_KNOCKBACK_SCALE` | 0.5 | Kural 3 |
| Hitstop | 3 (normal) | Bağlayıcı değer (`CLAUDE.md` §7). Yeni sayı yok |

**Kaç tane:** Bekçi dört kez görünüyor (B3, B7, B12, B16) ve en fazla 1 taşınıyor. Her ziyarette elindeki mum yanmış olursa oyun boyunca **en fazla 4 mum**. Dört saatlik oyunda dört hata hakkı: boss dövüşlerinde (B6, B13, B14, B18) anlamlı, dengeyi bozacak kadar değil.

## 6. Hikâye

- Bekçi hiç konuşmuyor; mumunu uzatıyor, o kadar.
- Ağaç ile bağ: epilogda Bekçi'nin **son** mumu söndüğünde oyuncu kaç mumunu satın aldığını biliyor. (İstenirse: satın alınan mum sayısı jeneriğin "senin yolun" satırına girebilir: *"Bekçi'nin mumlarından üçü seni korudu."* §9/5)
- `docs/bolum-03.md`'nin cümlesi korunuyor: *"Bekçi sana yardım eder ama seninle ilgilenmez."*

## 7. Kod planı

| Dosya | İş |
|---|---|
| `src/systems/consumables.py` | `WARD = "ward"` sarf kalemi, `MAX_CARRY` kalem başına (ward: 1) |
| `src/systems/merchant.py` | `TRAVEL_OFFERS`'a `buy_ward`. `merchant.buy` taşıma sınırını zaten soruyor |
| `src/scenes/chapter03.py` | `death_candle` teklifi `buy_ward`'a dönüşüyor |
| `src/entities/player.py` | `take_damage` başında: mum varsa hasarı sil, geri itmeyi yarıla, 30 kare dokunulmazlık, `scene.on_ward_spent()` |
| `src/scenes/play.py` | `on_ward_spent`: parçacık, ses, kayıttan düş. Omuz alevinin çizimi |
| `src/audio/sfx_*.py` | `ward_break` (`_register`) |
| `src/ui/shop.py` | ikon: `candle` zaten var |
| Kayıt göçü | Eski kayıtta `death_candle` "alındı" ise **bir mum** ve 140 altın iade (200 ödedi, mum 60) |

## 8. Testler

- Mum varken ilk vuruş **0 hasar**; mum düşüyor; 30 kare dokunulmazlık.
- Kaçınmanın dokunulmazlığında vuruş gelirse mum **harcanmıyor**.
- "Son şans"tan önce tetikleniyor: can %10'dayken öldürücü vuruş → mum söner, af hâlâ duruyor.
- Doluyken ikinci mum satılmıyor, altın düşmüyor (`merchant.buy` sırası).
- Dünyanın dışına düşme mumu harcamıyor.
- Eski kayıt göçü: `death_candle` alınmışsa bir mum ve 140 altın, **bir kez**.
- Görünürlük: taşırken alev çiziliyor, `flash_limit` açıkken beyaz parlama yok.

## 9. Arda'ya sorular

1. **Fiyat 60** uygun mu? (Önerim 60; 40 çok ucuz, meşaleyle aynı.)
2. **En fazla 1** mi, yoksa 2 mi? (Önerim 1.)
3. **Tuzak ve lav** da karşılansın mı (önerim evet, kural 7)?
4. **Sönmez Fitil** ne olsun?
   - (a) Tezgâhtan kalksın, eski kayıtlara 120 iade *(önerim: en temizi)*
   - (b) B3'e meşale ömrü eklensin ki fitil anlam kazansın. B3'ün tasarımını değiştirir, oynanmadan önerilmez
   - (c) Başka bir kalıcı etkiye dönüşsün: meşalenin ışık yarıçapı +%30
5. Jeneriğe *"Bekçi'nin mumlarından N'i seni korudu"* satırı eklensin mi?
