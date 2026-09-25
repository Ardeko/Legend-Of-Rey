# Yetenek ağacı: bölümlere yayılan puanlar, yeni hareketler

**Ardeko Studios · 25.09.2026 · UYGULANDI**

Arda'nın iki isteği:

1. *"Yetenek ağacı bir işe yaramıyor gibi, sadece 1 kere geliştirme var. Burayı uzunca planla ve oyuna yay bence."*
2. *"Yetenek ağacını bölüme yayılmış puanlar olarak tekrar yap. Yeni hareketler versin."*

Bu belge önce plandı. İkinci istekle kararlar verildi ve uygulandı.

- **Mantık:** `src/systems/skilltree.py`
- **Ekran:** `src/ui/skill_tree.py`
- **Hareketler:** `src/entities/player.py`, `src/scenes/play.py`, `src/entities/enemy.py`
- **Sayılar:** `src/config.py` → YETENEK AGACI.

---

## 1. Neden yeniden yazıldı (ölçüldü)

| # | Bulgu | Kanıt |
|---|---|---|
| 1 | Oyunun tamamında **tek** puan veriliyordu | `grant_points` yalnızca B4 kampında çağrılıyordu, `REST_SKILL_POINTS = 1` |
| 2 | Ağaç ekranı yalnızca B4'te açılıyordu | `SkillTreeScene` yalnızca `chapter04.open_skill_tree()`'den |
| 3 | Ağacın %94'ü hiç açılmıyordu | 18 puanlık ağaca karşılık 1 puan |
| 4 | Hiçbir düğüm yeni bir **fiil** vermiyordu | 12 düğümün 12'si bir sayıydı (hasar %6, can +5) |
| 5 | Ardo'da bir dal ölüydü | YANKI dalı Ardo'da etkisizdi |
| 6 | Silah değişince "Akış"ın +2 karesi kayboluyordu | `equip_weapon` zinciri `stats.chain_window` ile yeniden kuruyordu |

## 2. Puan: bölümlere yayılmış

| Kaynak | Puan | Nerede |
|---|---|---|
| Bölüm sonu: B3, B6, B8, B10, B12, B13, B14, B16, B17 | 1'er, **9** | `ChapterEndScene` açılışta veriyor. Özette "Yetenek puanı +1" satırı altın renginde |
| B4 kampında dinlenmek | 1 | `chapter04._rest` |
| B15'i kimseyi uyandırmadan geçmek | +1 | `chapter15._end_chapter`, özet ekranında aynı satır |

- **Garanti 10, en fazla 11.** Bir karakterin ağacı 27 puan (3 dal × 9). İyi oynayan bir dalı dibine kadar açıp bir başkasının ilk iki kademesini alabilir. Ağaç tamamlanamaz.
- **Puansız en uzun ara iki bölüm.** B3 ile B6 arasındaki boşluğu B4'ün kampı dolduruyor.
- **Her kaynak bir kez.** Kaynak başına bir `flags["skillpt_*"]` bayrağı var. Bölümü yeniden oynamak ya da ölüp dirilmek ikinci puanı vermez.
- **Eski kayıtlar** (`skilltree.backfill`, `PlayScene._migrate_save`):
  - Kayıt geçilmiş kaynakların puanını bir kez alır, ekranda bir bildirim görünür.
  - B4 kampında dinlenmiş (`ch04_rested`) kayıt o puanı zaten almıştı; yalnızca işaretlenir.
- **Harcamak her yerden:** duraklat menüsünde **YETENEKLER** var. Harcanmamış puan varsa menünün altında altın renkli bir satır çıkar. B4'ün kampı ağacı yine kendiliğinden açar.
- **Etki hemen görülür:** duraklat menüsünden açılan düğüm oyuncuya o anda biner (`PlayScene.learn_skill`).

## 3. Ağaç: karakter başına üç dal, beş kademe

- Bedeller `(1, 1, 2, 2, 3)`.
- **3. kademe bir seçimdir.** İki düğümden biri alınır, öteki kalıcı olarak kilitlenir.
  - Ekranda ilk basış uyarır: *"Tekrar bas: X kalıcı olarak kilitlenir"*. İkinci basış onaylar (`CLAUDE.md` §9: geri alınamayan eylemde varsayılan İPTAL).
  - 4. kademe, hangi yol seçildiyse onun üstünde açılır.
- ◆ = **yeni hareket.** Ekranda düğümün yanında küçük bir elmas, ayrıntıda *"YENİ HAREKET"* yazısı var.

### KESKİN (iki karakter)

| K | Düğüm | Etki |
|---|---|---|
| 1 | Bileme `blade_edge` | Hasar +%12 |
| 2 | Akış `blade_flow` | Zincir penceresi +2 kare, tabanın üstüne |
| 3a | ◆ **Hamle** `blade_dash` | Koşarken saldırı ileri atılır, ~45 px. Vuruşun menzili +10, hasarı ×1.3; sendeletir, deler. Bekleme süresi 45 kare |
| 3b | ◆ **Havada Asılı** `blade_hover` | Havada vururken düşüş tavanı 0.5 px/kare, her vuruşta hafif kalkış. Butçe 40 kare; yere basınca dolar |
| 4 | İvme `blade_momentum` | 10+ combo'da hasar +%20 |
| 5 | ◆ **Kılıç Dalgası** `blade_finisher` | Bitirici, ileri uçan çelik bir kesik fırlatır (bitiricinin hasarının %60'ı). Fısıltı'da ikinci bir dalga çıkmaz; kendi dalgası ağırlaşır |

### TAŞ (iki karakter)

| K | Düğüm | Etki |
|---|---|---|
| 1 | Post `stone_hide` | Azami can +10 |
| 2 | Koruma `stone_guard` | Alınan hasar −%8 |
| 3a | Yuvarlanma `stone_roll` | +1 kaçınma şarjı |
| 3b | ◆ **Toparlanma** `stone_rally` | Yenen darbenin %60'ı 3 sn boyunca "geri alınabilir" kalır. Karşılık vurdukça vuruş hasarının yarısı kadar can döner. HUD'da çubuğun yanında altın, çizgili bir bant var |
| 4 | İrade `stone_will` | Azami can +10, alınan hasar −%8 |
| 5 | ◆ **Sarsılmaz** `stone_poise` | Saldırırken 12 ve altı darbeler zinciri bozmaz, geri itmez. Can yine gider |

### YANKI (yalnızca Rey)

| K | Düğüm | Etki |
|---|---|---|
| 1 | Erim `echo_reach` | Yankı görüşü +%25 |
| 2 | Siper `echo_ward` | Yankı açıkken alınan hasar −%12 |
| 3a | Kavrayış `echo_grip` | Görüş +%30 daha |
| 3b | ◆ **Yalan Sezgisi** `echo_lie` | Yankı yalan söylediğinde kolye ürperir: ses (`necklace_conflict`) ve boyundan dökülen is. Yazı yok; yalan yine söylenir ve deftere geçer (`docs/korku.md` 4.1) |
| 4 | Onarım `echo_mend` | Yankı 20 yerine 14 combo'da iyileşir |
| 5 | ◆ **Yankı Darbesi** `echo_burst` | Yankı'yı açtığın an çevredekiler savrulur ve sendeler (72×36, poise 3). Bekleme süresi 5 sn. Bedel Yankı'nın bedeli |

### İZ (yalnızca Ardo, yeni dal)

| K | Düğüm | Etki |
|---|---|---|
| 1 | Keskin Göz `trace_eye` | İz menzili +%25 (`TrackingState.range_scale`) |
| 2 | Avcı Sabrı `trace_patience` | İz açıkken alınan hasar −%12. Yankı Kalkanı'nın ikizi |
| 3a | ◆ **Pusu** `trace_ambush` | Arkasından ya da fark etmemiş düşmana vuruş ×1.5. "Arka" bakış yönünden okunur. Düşman saldırırken dönmez, yani kaçınmayla içinden geçip sırtına vurmak bir hareket. Kıvılcım ve ağır ses |
| 3b | ◆ **Sessiz Adım** `trace_quiet` | Sessiz yürüyüş %40 yerine %50 hızda. Adım ve iniş sesi yarıya iner (B15). Düşmanlar seni 170 yerine ~110 px'ten fark eder |
| 4 | İz Okuma `trace_read` | İz açıkken hasar +%15 |
| 5 | ◆ **Ayı Kükremesi** `trace_roar` | İz'i açtığın an kükrersin. Yankı Darbesi'nin ikizi: toz halkası, `bear_roar` sesi |

**Anahtarlar kalıcı.** Eski 12 anahtarın hepsi korundu (`blade_finisher` artık Kılıç Dalgası). Tanınmayan anahtar sayılmaz ve etkileri bozmaz.

## 4. Bağlayıcı değerler

Hiçbir düğüm bir taban değeri yeniden yazmıyor (`CLAUDE.md` §7):

- Zincir 12/14/10, kaçınma 6/18, hitstop 3/7/12, tell ≥14 aynı.
- Yetenekler çarpan ya da bonus olarak tabanın üstüne biniyor.
- Hamle'nin atılışı saldırının kendi kare bütçesinde (4+3+8) oluyor; zincir kareleri değişmiyor.

## 5. Testler

| Dosya | Ne |
|---|---|
| `tests/test_skilltree.py` | Şekil, bütçe, önkoşul, seçim kilidi, karakter dalları, puan kaynakları (bir kez), eski kayda geri doldurma, çarpanlar, taban değerler, kayıt |
| `tests/test_skill_moves.py` | Gerçek oyun döngüsünde her hareket: Hamle (44 px ve 7 px), Havada Asılı (5 px ve 22 px düşüş), Kılıç Dalgası, Sarsılmaz, Toparlanma, Pusu, Sessiz Adım, Yankı Darbesi / Ayı Kükremesi, Yalan Sezgisi. Ayrıca Eski Kalkan, son şans ve oyun ortasında öğrenmek |
| `tests/test_skill_tree_ui.py` | Bölüm sonu satırı, YETENEKLER menüsü, ekran gezintisi, iki basışlı seçim, karakterin dalları |

## 6. Açık kalanlar (öneri)

- **Önizleme:** düğümün yanında "Hasar 18 → 20" gibi sayı. Plan §6/2'deydi, yapılmadı.
- **İsteğe bağlı kaynaklar:** gizli odalarda Yankı Taşı, Bekçi'den altınla puan, ağacı sıfırlama. Plan §3.2 ve §5'teydi; oynanış testinden sonra karar verilmeli.
- **Denge:** sayılar oynanmadan seçildi. Özellikle Hamle'nin 45 karelik beklemesi ve Pusu'nun ×1.5'i ilk oyun testinde ölçülmeli.
