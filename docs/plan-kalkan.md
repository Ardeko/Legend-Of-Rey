# Eski Kalkan: bir vuruşu senin yerine karşılayan tek kullanımlık

**Ardeko Studios · 25.09.2026 · UYGULANDI**

Arda'nın iki isteği:

1. *"Mum Bekçisi 1 hit'i engelleyebilecek harcanabilir tek kullanımlık bir şey satabilir, öyle bir mekanik ekleyelim. Ama bunun tasarımı çok önemli."*
2. *"Sönmez fitil ve koruyucu mum'u kaldır ve zırh alalım. Koruyucu mum olmasın, kalkan veya zırh olsun."*

Bu belge önce "Koruyucu Mum" planıydı (eski adı `plan-koruyucu-mum.md`). İkinci istekle eşya bir **kalkan** oldu ve uygulandı.

## 1. Tezgâhtan kalkan iki ürün

B3'teki Bekçi tezgâhı iki **etkisiz** ürün satıyordu:

| Ürün | Fiyat | Neden etkisizdi |
|---|---|---|
| Sönmez Fitil | 120 | Meşaleler zaten hiç sönmüyordu (`src/world/torch.py`'de ömür yok) |
| Koruyucu Mum | 200 | Ölünce altın kaybı yoktu (`DEATH_GOLD_LOSS_RATIO` hiç kullanılmıyor) |

- **İkisi de tezgâhtan kalktı.** B3 artık meşale, ok, bomba ve Eski Kalkan satıyor.
- **Eski kayıtlara iade:** bu ürünleri almış kayda paraları bir kez geri veriliyor (120 + 200). Oyuncu bildirimi görüyor: *"Bekçi eski mallarını geri aldı: +320 altın"*.
- İade `merchant.refund_legacy` ile, `shop_refund_v1` bayrağıyla bir kez yapılıyor.

## 2. Tek cümle

**Eski Kalkan, sırtındayken seni vuracak ilk darbeyi karşılayıp kırılır.** Tuşu yok, seçimi yok. Onu almak bir karar; harcamak kendiliğinden oluyor.

**Neden kalkan:** Arda mum istemedi. Zırh da tek kullanımlık bir eşya olarak zor okunuyor, oysa kırılan bir tahta kalkan anında anlaşılıyor. Adı **Eski**: Bekçi aşağıda kalanların eşyasını satıyor.

## 3. Kurallar ve nedenleri

| # | Kural | Neden |
|---|---|---|
| 1 | **Pasif, kendiliğinden.** Hasar alacağın ilk vuruşta tetiklenir | Bir tuş olsaydı kaçınmayla yarışırdı. Bu bir sigorta, beceri değil |
| 2 | **En fazla 1 taşınır** (`SHIELD_MAX_CARRY`). Doluyken satılmaz, altın da gitmez | İki kalkan boss dövüşlerini "iki hata hakkı"na çevirirdi |
| 3 | **Vuruşun hasarını tamamen siler.** Geri itme yarıya iner, hitstop normal (3 kare) | Oyuncu neyin olduğunu **hissetmeli**. Hasar yok ama darbe var |
| 4 | Kırıldıktan sonra **30 kare dokunulmazlık** | Çok vuruşlu saldırıda (Zindancı'nın zinciri, sürü) kalkan ilk vuruşu karşılar; ikincisi hemen gelirse satın alma boşa giderdi |
| 5 | Kaçınmanın dokunulmazlığında **tetiklenmez** | `HitboxManager` dokunulmaz oyuncuyu hiç vurmuyor |
| 6 | **"Son şans"tan önce** gelir (`CLAUDE.md` §8) | Kalkan oyuncunun bilerek aldığı şey; af sessiz yedek. Önce bilinen harcanır |
| 7 | Her hasar kutusunu karşılar: düşman, boss, mermi, tuzak. Dünyanın dışına düşmeyi karşılamaz | Düşüş zaten yeniden doğuruyor, can almıyor |
| 8 | Yalnızca oyuncu korunur, yoldaş korunmaz. B17'de ilk vurulan korunur | Çanta ortak |
| 9 | **Ölümde geri gelir** | Aynı çantada, ok ve bombayla aynı kural (`PlayScene._restore_bag`). Odayı yeniden oynamak zaten bedel; kalkanı da almak çift ceza olurdu |

## 4. Görünür ve duyulur

- **Taşırken:**
  - Oyuncunun sırtında, omuz hizasında küçük bir tahta kalkan görünüyor: 7×7, demir göbek, ışık sol üstten.
  - HUD çubuğu yok; kalkanın kendisi gösterge (`CLAUDE.md` §9, diegetik).
  - İlk sürüm kalkanı gövdenin arkasına çiziyordu. Ekran görüntüsünde tamamen kayboluyordu, bu yüzden sprite'ın üstüne alındı.
- **Tetiklenince:**
  - Tek `on_hit` geçidiyle hitstop, sarsıntı ve talaş parçacıkları. Yeni `splinter` renk yolu: `flesh_light → earth → earth_dark`.
  - Yerde talaş lekesi kalıyor.
  - Yeni ses `shield_break`: tahtanın çatırtısı, tok bir darbe ve kısa bir demir tınısı.
  - *"KALKAN KIRILDI"* bildirimi.
- **Satın alınca:** *"Eski Kalkan sırtında: ilk darbeyi karşılar, sonra kırılır."*
- Tezgâh satırında yuvarlak kalkan ikonu ve `0/1` sayacı var.

## 5. Sayılar

| Sabit | Değer | Gerekçe |
|---|---|---|
| `SHIELD_PRICE` | **60** | Bir bölümün geliri ~250 (`docs/ekonomi-uretim.md`). Kalkan bunun dörtte biri: anlamlı, ama kıskanılacak kadar pahalı değil |
| `SHIELD_MAX_CARRY` | 1 | Kural 2 |
| `SHIELD_IFRAMES` | 30 kare | Kural 4. Bir kaçınmanın toplamından (18) uzun |
| `SHIELD_KNOCKBACK_SCALE` | 0.5 | Kural 3 |

**Nerede:**

- B3 tezgâhı ve gezgin Bekçi (B7, B12, B16).
- Bekçi dört kez görünüyor ve en fazla bir kalkan taşınıyor: dört saatlik oyunda en fazla dört hata hakkı.

## 6. Kod

| Dosya | İş |
|---|---|
| `src/systems/consumables.py` | `SHIELD`, `PASSIVE`: fırlatılmıyor, seçim döngüsünde yok. Eşyaya özel sınır: `max_carry`, `full` |
| `src/systems/merchant.py` | `SHIELD_OFFER` iki tezgâhta ortak, `refund_legacy`, kalkan bildirimi |
| `src/entities/player.py` | `_shield_absorbs` (`take_damage`'in başında), `_spare_last_chance` |
| `src/scenes/play.py` | `on_shield_broken`, `_migrate_save` |
| `src/entities/player_render.py` | Sırttaki kalkan |
| `src/ui/shop.py` | Kalkan ikonu; fitil ve mum ikonları kalktı |

## 7. Son şans da bağlandı (`CLAUDE.md` §8)

- Kural yazılıydı ama **hiçbir yerde uygulanmıyordu**. Artık `Player._spare_last_chance` uyguluyor.
- Can %15'in altındayken gelen öldürücü darbe 1 can bırakıyor.
- Bölüm başına bir kez. Sayaç sahnede ve `restart()` onu taşıyor: ölüp dirilmek hakkı tazelemiyor.
- Oyuncuya **hiçbir şey söylenmiyor**.

## 8. Testler

- `tests/test_skill_moves.py`:
  - İlk darbe 0 hasar veriyor, kalkan kırılıyor, 30 kare dokunulmazlık başlıyor, ses çalıyor, ikinci darbe normal işliyor.
  - Kaçınmada kalkan harcanmıyor, en fazla bir tane taşınıyor.
  - Son şans: %15'in altında 1 can kalıyor, üstünde af yok, önce kalkan harcanıyor, ölüm hakkı tazelemiyor.
- `tests/test_merchant.py`: kalkan iki tezgâhta; ikincisi satılmıyor ve altın gitmiyor; iade bir kez yapılıyor.
- `tests/test_consumables.py`: tezgâhta ok, bomba ve kalkan var; kalkan fırlatma seçiminde yok.
