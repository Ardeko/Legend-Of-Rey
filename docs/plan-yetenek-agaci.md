# PLAN — Yetenek ağacı: oyuna yayılan bir gelişim

**Ardeko Studios · 25.09.2026 · ONAY BEKLİYOR**

Arda: *"Yetenek ağacı bir işe yaramıyor gibi, sadece 1 kere geliştirme var. Burayı uzunca planla ve oyuna yay bence."*

> Bu belge bir **plan**. Kod yazılmadı. Onaylanınca aşamalar sırayla uygulanır (§9). Açık sorular §10'da; cevapları plana işlenmeden uygulamaya geçilmez. Sayılar `src/config.py`'ye girecek **öneriler**. Bağlayıcı dövüş değerlerine (`CLAUDE.md` §7) dokunulmuyor: her düğüm tabanın **üstüne** biniyor.

---

## 1. Teşhis — ölçüldü, tahmin değil

| # | Bulgu | Kanıt |
|---|---|---|
| 1 | Oyunun tamamında **tek** yetenek puanı veriliyor | `src/scenes/chapter04.py:273` `skilltree.grant_points(..., REST_SKILL_POINTS)` ve `REST_SKILL_POINTS = 1`. Başka `grant_points` çağrısı yok |
| 2 | Ağaç ekranı **yalnızca B4'te** açılıyor | `SkillTreeScene` yalnız `chapter04.open_skill_tree()`'den açılıyor. Puan olsa bile başka yerde harcanamıyor |
| 3 | Ağacın tamamı 18 puan; oyuncu 1 düğüm görüyor | `SKILL_COST_BY_LEVEL = (1, 1, 2, 2)` × 3 dal. Ağacın %94'ü hiç açılmıyor |
| 4 | Etkiler hissedilmiyor | +%6 hasar (`SKILL_EDGE_DAMAGE_BONUS`), +%25 görüş menzili, +5 can. Oyuncu açtığı düğümün farkını oyunda göremiyor |
| 5 | Ardo'da bir dal ölü | YANKI dalı `requires_echo=True`: Ardo'nun ağacı fiilen iki dal |
| 6 | Ekonomi belgesi puanları **satın alınabilir** yazıyor, kodda yok | `docs/ekonomi-uretim.md` "Yetenek puanı 150, 250, 400, 600... artan maliyet"; hiçbir tezgâh puan satmıyor |
| 7 | Hiçbir düğüm yeni bir **fiil** vermiyor | 12 düğümün 12'si sayı: hasar, menzil, can, pencere. Oyun biçimi değişmiyor |

Sonuç: sistem teknik olarak sağlam (mantık `skilltree.py`, ekran `skill_tree.py`, kayıt `SaveData.skills`, testler var) ama **oyuncunun deneyiminde yok**. Eksik olan altyapı değil; puanın kaynağı, ağaca erişim ve düğümlerin ağırlığı.

## 2. Hedefler

1. **Her 1–2 bölümde bir karar.** Oyun boyunca 10–12 puan, 18 bölüme yayılmış.
2. **Her düğüm hissedilsin.** Ya yeni bir fiil (hamle, havada zincir, sendelememe), ya da gözle görülür bir sayı (hasar %6 değil %12, ve vuruş kıvılcımı büyüsün).
3. **İki karakter, iki tam ağaç.** Rey'de YANKI dalı, Ardo'da **İZ** dalı. Aynı iskelet, zıt bilgi: oyunun her yerdeki ilkesi (`EchoState` / `TrackingState`).
4. **Puan dünyada kazanılsın.** Kamp ateşi, boss, gizli oda, B15'in hayalet ödülü. Altınla alınabilen puan yalnızca **ek** (gold sink), temel akış değil.
5. **Ağaç her dinlenme yerinde açılsın**, yalnız B4'te değil.
6. **Tamamlanamasın.** `skilltree.py`'nin kendi ilkesi korunuyor: *"her bölümde bir şey alabilmeli, ama her şeyi alamamalı"*. İki dal dibe, üçüncüsü yarıya.

## 3. Puan ekonomisi — nereden, kaç

### 3.1 Dünyada kazanılan (garanti: 10)

| Bölüm | Kaynak | Puan | Neden orası |
|---|---|---|---|
| B3 | Sönmüş Olan (mini-boss) yenilince | 1 | İlk gerçek zafer; ağaç B4'te zaten açılıyor |
| B4 | Kamp dinlenmesi (**var**) | 1 | Değişmiyor |
| B6 | Çürümüş Olan (BOSS 1) | 1 | Katman 1'in finali |
| B8 | Ateş başı (dinlenme) | 1 | Nefes bölümü, dinlenme anı |
| B10 | Bölüm sonu — yalnız kalıp çıkmak | 1 | Ayrılığın bedeli bir kazanç |
| B12 | Mektup — dinlenme | 1 | Nefes bölümü |
| B13 | Zindancı (BOSS 2) | 1 | |
| B14 | Kaynak (BOSS 3) | 1 | |
| B16 | Sırt Sırta — kamp | 1 | Yeniden birleşme |
| B17 | İkili Kule sonu | 1 | Son büyük hazırlık |

### 3.2 İsteğe bağlı (en fazla +4)

| Kaynak | Puan | Not |
|---|---|---|
| B15 hayalet geçiş (kimseyi uyandırmadan) | +1 | Görünür ödül zaten var; puan onu ağırlaştırıyor |
| Gizli odalar: her bölümün gizli alanında bir **Yankı Taşı** parçası; **3 parça = 1 puan** | +2 civarı | Keşfe ödül. Ardo'da aynı taş "İz Taşı" adıyla |
| Mum Bekçisi: altınla **en fazla 1 puan** / görünüş (B7, B12, B16) | +3'e kadar | Ekonomi belgesinin 150/250/400 artan fiyatı. Oyunun temel akışı değil, altın fazlası olana seçenek |

**Toplam:** 10 garanti + 2–7 isteğe bağlı → **12–17**. Yeni ağacın tamamı 27 puan (§4). İyi oynayan bile ağacın yarısını biraz geçer.

### 3.3 Kazanma anı

- Puan kazanıldığında HUD'da tek bildirim: kolyenin yanında küçük bir parıltı ve "Yetenek puanı +1". Ağaç ekranı kendiliğinden **açılmaz**; oyunun akışını kesmez.
- Harcanmamış puan varken bir sonraki dinlenme yerinde ekran "harcanacak puanın var" diye nazikçe hatırlatır.

## 4. Yeni ağaç — üç dal, beş kademe

Her dalda **5 kademe**, bedel `(1, 1, 2, 2, 3)` → dal başına 9, ağaç 27 puan. **3. kademe bir seçim:** iki düğümden biri alınır, öteki kilitlenir. Aynı dalı iki oyuncu farklı oynasın.

Düğüm adlarında İngilizce anahtar (kayıt uyumu), metinler dil tablosundan. Mevcut 12 anahtar **korunuyor**; eski kayıtlar bozulmuyor (§7).

### 4.1 KESKİN — kılıç (iki karakter)

| K | Düğüm | Etki | Neden hissedilir |
|---|---|---|---|
| 1 | Keskin Kenar *(var: `blade_edge`)* | Hasar +%12 (bugün +%6) | Vuruş kıvılcımı bir kademe büyür |
| 2 | Akış *(var: `blade_flow`)* | Zincir penceresi +2 kare | Zincir daha affedici; UI'da pencere çubuğu hafif uzar |
| 3a | **Hamle** *(yeni)* | Koşarken saldırı → kısa ileri atılışla vuruş (1 şarj, 45 kare) | **Yeni fiil:** mesafe kapatma |
| 3b | **Havada Zincir** *(yeni)* | Havada 2. vuruş açılır | **Yeni fiil:** hava kombosu |
| 4 | Momentum *(var: `blade_momentum`)* | 10+ combo'da hasar +%20 ve saldırı toparlanması −2 kare | Combo sayacı kıvılcımla parlıyor |
| 5 | **Bitirici Dalgası** *(`blade_finisher` genişliyor)* | Bitirici +%25 hasar **ve** kısa bir şok dalgası: arkadaki düşmanı da vurur | Kalabalığa karşı karar anı |

### 4.2 TAŞ — dayanıklılık (iki karakter)

| K | Düğüm | Etki | Neden hissedilir |
|---|---|---|---|
| 1 | Taş Deri *(var: `stone_hide`)* | Azami can +10 (bugün +5) | Can çubuğu görünür biçimde uzar |
| 2 | Duruş *(var: `stone_guard`)* | Alınan hasar −%8 | |
| 3a | Çift Kaçınma *(var: `stone_roll`)* | +1 kaçınma şarjı | |
| 3b | **Son Nefes** *(yeni)* | "Son şans" (`CLAUDE.md` §8) bölüm başına **iki** kez | Oyuncu affının görünür uzantısı |
| 4 | İrade *(var: `stone_will`)* | Azami can +10, alınan hasar −%8 | |
| 5 | **Sarsılmaz** *(yeni)* | Hafif vuruşlarda sendelememe (`poise`) | **Yeni fiil:** vuruş alırken zinciri bitirme |

### 4.3 YANKI — yalnızca Rey

| K | Düğüm | Etki |
|---|---|---|
| 1 | Menzil *(var: `echo_reach`)* | Görüş menzili +%25 |
| 2 | Yankı Kalkanı *(var: `echo_ward`)* | Yankı açıkken alınan hasar −%12 |
| 3a | Kavrayış *(var: `echo_grip`)* | Görüş +%30 |
| 3b | **Yalan Sezgisi** *(yeni)* | Yankı'nın yalanı ekranda kısa bir titremeyle belli olur (`docs/korku.md` 4.1'in ödülü) |
| 4 | Onarım *(var: `echo_mend`)* | Kademe onarımı 6 vuruş daha kısa |
| 5 | **Rezonans Genişler** *(yeni)* | Rezonans darbesinin yarıçapı +%40 (B8/B9/B15 bulmacalarına ikinci yol) |

> **B14'ten sonra.** Yankı ihanet ediyor (`sense_betrayed`). Bu dalın düğümleri **silinmiyor**; açıkken Yankı'nın bedeli yine işliyor. Kendi dalının sana ihanet etmesi, oyunun tezinin mekanikteki karşılığı. (Arda'ya soru §10/3.)

### 4.4 İZ — yalnızca Ardo *(yeni dal)*

Ardo'nun duyusu İz Sürme (`src/systems/tracking.py`). Aynı iskelet, zıt bilgi:

| K | Düğüm | Etki |
|---|---|---|
| 1 | Keskin Göz | İz menzili +%25 |
| 2 | Avcı Sabrı | İz açıkken alınan hasar −%12 (Yankı Kalkanı'nın karşılığı) |
| 3a | Taze İz | İzler düşmanın **bir sonraki** saldırı yönünü gösterir (tell +4 kare okunur) |
| 3b | Tuzak Sezgisi | Tuzaklar ve çürük zemin iz açıkken belirir (B10'un tuzağına Ardo için ikinci yol) |
| 4 | İz Okuma | İzlenen düşmana hasar +%15 |
| 5 | **Av Dersi** | Bir düşmanı öldürmek, iz açıkken yakındaki düşmanları 2 sn işaretler |

Böylece Ardo'nun ağacı da üç dal. `Branch.requires_echo` yerine `Branch.character` (`"rey"` / `"ardo"` / `""`).

## 5. Ağaca erişim — dinlenme yerleri

- Ağaç **her dinlenme yerinde** açılır: B4 kampı (var), B8 ateş başı, B12, B16 kampı ve her bölümün **checkpoint'i** (`PlayScene.restart()`'ın odası).
- Duraklat menüsüne salt okunur bir "Yetenekler" sekmesi: ne açık, ne kadar puan var. **Harcamak dinlenme yerinde** (seçim bir mola kararı olsun, dövüşün ortasında değil).
- Tek sefer **sıfırlama** Mum Bekçisi'nde, altınla (bedel: harcanan puan × 60). Ağaç bir deney alanı olsun ama bedava değil. (§10/4)

## 6. Arayüz

`src/ui/skill_tree.py` var ve çalışıyor. Değişecekler:

1. **Beş kademe**, 3. kademede iki düğüm yan yana ve aralarında "ya o ya bu" işareti.
2. Düğümün yanında **önizleme**: "Hasar 18 → 20", "Zincir penceresi 14 → 16 kare". Sayı gösterilince oyuncu farkı biliyor.
3. Yeni fiil düğümlerinde kısa, döngüsel bir önizleme animasyonu (sprite `pose_table`'dan, yeni sanat yok).
4. Açılış anı: düğüm parlıyor, `necklace_warm` sesi, kısa bir yazı.
5. Ardo'da YANKI dalının yerinde İZ dalı. Soluk bir dal hiç görünmüyor.

## 7. Kayıt uyumu

- `SaveData.skills` düğüm anahtarlarını tutuyor. **12 eski anahtar aynen kalıyor**; yeni düğümler yeni anahtar.
- Eski kayıtlar: B4'ten sonraki bölümlerdeyse, geçtikleri kaynakların puanı **bir kez** veriliyor (`skills_backfilled` bayrağı). Oyuncu yeni sistemi kaybettiği puanlarla karşılamasın.
- `skill_points` "kalan havuz" anlamını koruyor.

## 8. Testler

- Her kaynak **bir kez** puan veriyor (tekrar oynanan bölüm ikinci puanı vermiyor, B4 deseni).
- Toplam garanti puan = 10; isteğe bağlılar ayrı ölçülüyor.
- 3. kademe seçimi: biri alınınca öteki kilitli.
- Ardo'da İZ dalı açık, YANKI dalı yok; Rey'de tersi.
- Bağlayıcı değerler (`CLAUDE.md` §7) **taban** olarak değişmiyor, yalnızca bonus üstüne biniyor. Bugünkü `test_skilltree.py` bunu zaten ölçüyor; yeni düğümlerle genişletilecek.
- Geri doldurma: eski kayıt B10'daysa B3/B4/B6/B8'in puanları bir kez veriliyor.
- Yeni fiiller (Hamle, Havada Zincir, Sarsılmaz) için oynanarak ölçülen testler (`test_combat.py` deseni).

## 9. Aşamalar

| Aşama | İş | Etki | Risk |
|---|---|---|---|
| **A** | Puan kaynakları (§3.1) ve her dinlenme yerinde ağaç (§5) | Sistem oyunda ilk kez **var** oluyor | Düşük: altyapı hazır |
| **B** | Mevcut 12 düğümün sayılarını hissedilir yap (§4) | Açılan her düğüm fark ediliyor | Düşük: sabitler |
| **C** | Beş kademe ve 3. kademe seçimi | Karar anı | Orta: ekran değişiyor |
| **D** | Ardo'nun İZ dalı | İki karakter eşit | Orta: `tracking.py`'ye kanca |
| **E** | Yeni fiiller: Hamle, Havada Zincir, Sarsılmaz, Bitirici Dalgası | Oyun biçimi değişiyor | Yüksek: dövüş testleri, denge |
| **F** | İsteğe bağlı kaynaklar: taş parçaları, Bekçi'den puan, sıfırlama | Keşif ve altın bağlanıyor | Düşük |

**Önerilen başlangıç:** A + B aynı oturumda. İkisi tek başına "sadece 1 geliştirme var" sorununu çözüyor; C–F onaylanınca.

## 10. Arda'ya sorular

1. **Puanın ana kaynağı** dünya mı (§3.1, önerim) yoksa ekonomi belgesindeki gibi altın mı? İkisi birden mi?
2. **3. kademe seçimi** geri alınamaz mı, yoksa Bekçi'de sıfırlanabilir mi (§5)?
3. **YANKI dalı B14'ten sonra** aynen mi çalışsın (önerim: evet, ama Yankı'nın ihanet bedeli sürsün), yoksa dal "kararsın" mı?
4. **Yeni fiiller** (Hamle, Havada Zincir) oyunun ilk yarısında da işe yarasın diye 3. kademede. Bu kadar erken yeni bir fiil vermek B2–B6 dengesini bozar mı? (Önerim: Hamle'nin şarjı 45 kare, B6'dan önce açılamayacak kadar pahalı değil.)
5. Ardo'nun **İZ dalı** isimleri ve etkileri uygun mu?
