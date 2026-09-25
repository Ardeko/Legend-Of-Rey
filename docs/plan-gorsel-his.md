# PLAN — Görsel gerçekçilik, akıcı animasyon, vuruş hissi

**Ardeko Studios · 25.09.2026 · §3 KARARI VERİLDİ, AŞAMA 3 UYGULANDI**

Arda: *"Hazır el atmışken görüntüleri de iyileştir ve daha gerçekçi yap. Animasyonlar da daha akıcı, vuruş hissiyatı daha iyi ve tatmin edici olsun. Tahrik edici yap."*

> Bu belge bir **plan**. §3'teki kararı Arda verdi: *"8 fps kuralını oyunu bozmadan dikkatlice geçebilirsin, akıcı ve güzel gözüken animasyonlar yap."* Aşama 3 (akıcı animasyon) uygulandı (§5). Aşama 1, 2, 4 ve 5 hâlâ öneri.

---

## 1. Bugün ne var — tekrar yazılmasın diye

### 1.1 Envanter

| Katman | Var olan | Nerede |
|---|---|---|
| Hitstop | normal 3 / bitirici 7 / boss 9 / öldürücü 12 kare (bağlayıcı) | `src/core/juice.py`, `config.py` |
| Sarsıntı | yönlü, üstel sönümlü, orta ve büyükte rotasyon | `juice.ScreenShake` |
| Hedef parlaması | 2 kare tam beyaz | `HIT_FLASH_FRAMES` |
| Squash & stretch | zıplama 0.85/1.15, iniş 1.2/0.8, vuruş 1.3/0.7 | `juice.Squash` |
| Parçacık | renk yolları: `blood`, `spark`, `dust`, `echo`, `violet`, `soot`; üst sınır 200 | `src/art/particles.py` |
| Silah izi | vuruş yayı boyunca iz | `src/art/trail.py` |
| Kalıcılık | kan/moloz izleri bölüm boyunca | `decals` |
| Işık | ışıma, sis, kenar ışığı, renk derecelendirme | `bloom.py`, `rimlight.py`, `postfx.py` |
| Kumaş | Rey/Ardo pelerin ve saç sallanması | `animator.SWAY_CHARACTERS` |
| Ses | tekrarlanan efektlerde ±%8 perde | `juice.pitch_variation` |

### 1.2 Bu oturumda yapılan

1. **Kol titreşimi bağlandı.** Ayar ve `InputManager.rumble` vardı ama **hiçbir yer çağırmıyordu**. Artık `Juice.on_hit`'te, hitstop ve sarsıntıyla aynı karede, darbe ağırlığına göre (`RUMBLE_*`). Ayar kapalıysa sessiz. Test: `tests/test_combat.py`.
2. **Köylü kıyafet varyantları.** Altı kıyafet (yaşlı, başörtülü, işçi, keten, kırmızı elbiseli, tunik) aynı iskeletten; epilogda rolüne göre, B1'de tohuma göre.

## 2. Ölçüm — "daha akıcı"nın sayısı

Animasyon kare sayıları (`src/art/animation.py`, `ANIMATIONS`):

| Durum | Kare | Bekleme | Etkin FPS | Gözlem |
|---|---|---|---|---|
| idle | 6 | 9 | 6.7 | yavaş nefes, doğru |
| run | 8 | 5 | 12 | iyi |
| **dodge** | **2** | ilerlemeyle | — | **en kaba geçiş**: kaçınma iki pozla okunuyor |
| **jump** | **1** | — | — | kalkışın ve tepe noktasının pozu yok |
| fall | 4 | 6 | 10 | |
| **hurt** | **2** | 7 | 8.6 | vuruş almanın ağırlığı yok |
| land / turn | 3 | 3 | 20 | iyi, kısa geçiş |
| attack1-3 | 5 | ilerlemeyle | — | hazırlık ve takip pozu belirsiz |
| death | 6 | 8 | 7.5 | |

En büyük kazanç **dodge, jump, hurt ve saldırıların hazırlık/takip** pozlarında.

## 3. Bağlayıcı kurallarla çakışan öneriler — KARAR GEREKİYOR

| Kural | Öneri | Neden | Karar |
|---|---|---|---|
| `CLAUDE.md` §6: **"Animasyon hissi 8 FPS"** | Hızlı eylemlerde (dodge, saldırı, hurt) **ilerlemeyle sürülen ara pozlar**. Idle/run/fall 8 FPS kalır | Saldırı ve kaçınma zaten kareye değil **dövüş zamanlamasına** bağlı (`attack_progress`). Aynı süreye daha çok poz koymak zamanlamayı değiştirmez, yalnızca akıcılaştırır | ✅ **Arda onayladı (25.09.2026)**, `CLAUDE.md` §6'ya işlendi |
| `CLAUDE.md` §7: hitstop 3/7/12 | **Değişmiyor.** Hissi hitstop'u uzatmadan artırıyoruz (§4) | Değerler bağlayıcı |

## 4. Vuruş hissi — öneriler (çoğu kural dışı, onaysız da yapılabilir)

| # | Öneri | Ne değişir | Maliyet |
|---|---|---|---|
| V1 | **Yönlü vuruş kıvılcımı**: temas noktasında, silahın yayı yönünde 3 karelik hilal (`spark` yolu) | Vuruşun **nereye** indiği okunur | Düşük |
| V2 | **Düşman tepki eğrisi**: geri itme önce kısa bir "asılı kalma" (2 kare), sonra sönümlü kayma | Darbenin kütlesi hissedilir | Düşük |
| V3 | **Bitirici yumruğu**: bitiricide kamera darbe yönünde 3 px itilip geri döner (tam sayı) | Bitirici ayrı bir olay gibi okunur | Düşük |
| V4 | **Katmanlı ses**: vuruş = gövde + metal + hava. Bitiricide alçak bir "bas" katmanı | "Tahrik edici" asıl kulaktan geliyor | Orta: `sfx_*` sentezi |
| V5 | **Öldürme anı**: öldürücü vuruşta düşman silueti 1 kare tehlike renginde, sonra dağılma | Kill cancel'ın anlamı görülür | Düşük |
| V6 | **Oyuncunun vurulması**: ekran kenarında 6 karelik kan kırmızısı nabız (`blood_dark`), yönlü | Hasar yönü okunur (erişilebilirlik: renk + yön) | Düşük |
| V7 | Kol titreşimi ✅ yapıldı | | |

## 5. Akıcı animasyon — öneriler (§3 kararına bağlı)

| # | Öneri | Kare | Durum |
|---|---|---|---|
| A1 | **Dodge**: 2 → 8 poz (itiş, atılış, toparlanma) | ilerlemeyle | ✅ |
| A2 | **Jump**: 1 → 4 poz (kalkış, yükseliş, tepe); **dikey hızla** sürülüyor | ilerlemeyle | ✅ |
| A3 | **Hurt**: 2 → 5 poz (darbe, savrulma, toparlanma) | hasar süresiyle | ✅ |
| A4 | **Saldırı**: 5 → 8 poz, zamanlama aynı | ilerlemeyle | ✅ |
| A5 | **Durma**: tam hızdan fren — 5 poz, 14 kareye yayılı (önce kayış, sonra toparlanma), kayarken ayakta toz, zeminde kalıcı sürtünme izi. **Fizik değişmedi** (Arda: *"1 olsun"* — yalnız görsel) | fren süresiyle | ✅ durma · ⬜ koşuya başlama |
| A6 | Pelerin/saç sallanmasını Jet ve Kalachev'e de ver (`SWAY_CHARACTERS`) | bellek: karakter başına ×3 sprite | ⬜ |

**Bosta 6 → 8 poz, koşu 8 → 10 poz** da oldu. Bunlar zamanla sürülüyor ama
**toplam süreleri aynı** (`src/art/animator.py :: DURATIONS`): bosta 54,
koşu 40, düşman saldırısı 35, hasar 14 kare. Düşmanlar saldırı ve hasarı
zamanla oynatıyor. Poz sayısı artıp bekleme aynı kalsaydı düşmanın savuruşu
vuruşundan geri kalırdı. Bekleme artık kesirli (`hold_for`).

Ölçüm: `tests/test_animation_flow.py`.

- Süreler eskisiyle aynı.
- Kaçınma 8, zıplama 4, hasar 5 farklı poz gösteriyor.
- Fren yalnızca tam hızdan durunca çıkıyor.

Kontak sayfası: `python tools/sprite_sheet.py --karakter rey_armed,ardo_armed --durum dodge,jump,hurt,brake,attack1,attack3`.

Hepsi **prosedürel pozlarla** (`spritegen` / `pose_table`); yeni PNG yok. Her yeni poz siluet testinden geçer (`tools/silhouette.py`).

## 6. Görsel gerçekçilik — öneriler

| # | Öneri | Not |
|---|---|---|
| G1 | **Temas gölgesi**: karakter ve nesnelerin zeminle birleştiği yerde 1 px koyu şerit (ambient occlusion) | Bugün yalnız elips gölge var; nesneler "yapıştırılmış" gibi durabiliyor |
| G2 | **Noktasal ışık**: meşale, lav ve ateş karakterlerin **o yöne bakan** kenarını aydınlatsın | `rimlight.py` bugün ortam ışığı. Aynı tek karartma yüzeyiyle (`CLAUDE.md` §4) |
| G3 | **Islak taş**: B5 (Sular) zemininde ışığı yansıtan tek piksel parıltılar | `tileset` teması |
| G4 | **Toz ve iz**: koşarken ayak dibinde küçük toz, dönüşte savrulan çakıl | `dust` yolu var |
| G5 | **Nefes buharı**: soğuk/derin bölümlerde (B11+) idle'da ağızdan 1-2 piksel buhar | Karakteri canlı gösterir |
| G6 | Dört tonlu gövde rampası (bugün 3): elbiselerde bir ara ton | Palet içinden, `SHADE_CHAINS` |

## 7. Ölçüt — "daha iyi" nasıl anlaşılacak

1. **Önce/sonra kaydı**: aynı 20 saniyelik dövüş (B2 ilk oda) iki sürümde kare kare. Klip `build/testshots/feel/`.
2. **Siluet testi**: yeni her poz tek renk siyahta okunuyor.
3. **Kare bütçesi**: bugün ~2.9 ms / 16.7. Öneriler toplamı +1.5 ms'yi geçmemeli (ölçülür).
4. **Oynayan göz**: Arda'nın "tahrik edici" ölçütü ölçülemez. Her aşamadan sonra 5 dakikalık bir tester oturumu.

## 8. Aşamalar

| Aşama | İçerik | Onay |
|---|---|---|
| 1 | V1, V2, V3, V5, V6, G1, G4 | **gerekmiyor** (kural dışı, düşük maliyet) |
| 2 | V4 katmanlı ses | gerekmiyor, ama kulakla dinlenmeli (başsız testte ses dinlenemiyor) |
| 3 | A1–A5 akıcı animasyon | ✅ **uygulandı** (25.09.2026) |
| 4 | G2 noktasal ışık, G3, G5, G6 | gerekmiyor; performans ölçülerek |
| 5 | A6 sallanma genişletme | gerekmiyor; bellek ölçülerek |

## 9. Arda'ya sorular

1. ~~**8 FPS kuralı** hızlı eylemlerde gevşetilsin mi?~~ **Evet** (Arda, 25.09.2026). Uygulandı.
2. **Oyuncunun vurulma nabzı** (V6) korku katmanının "azaltılmış" ayarında kapansın mı?
3. **Kol titreşimi varsayılan açık** kalsın mı? (Bugün ayar varsayılanı açık, kol desteği varsayılan kapalı.)
