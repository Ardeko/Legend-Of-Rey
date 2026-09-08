# LORE — Asset Planı v2 (Revize)

> **⚠ 02.09.2026 DÜZELTME.** Bu belge 21.08.2026'da yazıldı ve tasarım
> içeriği hâlâ geçerli. Ama üç *olgusal* iddiası bayatladı — aşağıda
> düzeltildi, gerekçeler `CLAUDE.md` §6 ve `DEVIR.md` §7'de:
>
> | Eskiden | Şimdi |
> |---|---|
> | Palet **32 renk** | **37 renk** — Arda 23.08.2026'da beş yeşil onayladı |
> | "Türkçe karakter eksik" | **Tam set var** (`src/ui/font_data.py`) |
> | "Yüz: 2 piksel göz, ağız yok" | Arda 29.08.2026'da genişletti: sprite'ta göz + kaş + çene gölgesi; gerçek yüz **portrede** (`src/art/portrait.py`) |
>
> Oyunun tamamı yazıldı (18/18 bölüm). Bu belge artık bir **plan**
> değil, bir **kayıt**.

**GDD Ek C-2** · Mevcut prototip görüldükten sonra güncellendi

---

## DEĞİŞEN VARSAYIM

Prototipteki sprite kalitesi (okunabilir 32px karakter, dinamik kılıç pozu, vuruş flaşı + parçacık, meşale ışığı, parallax katmanı, konuşma balonu) **üretim kalitesinde**. Önceki plandaki "sanatçı bul / hazır paket al" önerisi geçersiz.

**Yeni varsayım:** Görsel asset'lerin ~%80'i Claude Code ile üretilebilir. Darboğaz sanat değil, **zaman ve tutarlılık**.

---

## 1. ÜRETİM YÖNTEMİNE GÖRE SINIFLANDIRMA

### ✅ A Sınıfı — Claude Code rahatça üretir
Prototipte kanıtlanmış.

| Kalem | Miktar | Not |
|---|---|---|
| Karakter animasyonları (Rey, Ardo) | ~117 kare | Kılıç pozu zaten çalışıyor |
| Düşman sprite'ları (10 tip) | ~240 kare | Prototipteki yaratık seviyesi yeterli |
| Tileset (3 katman) | ~240 tile | Duvar dokusu + zemin zaten var |
| Hikâye dekorları | ~23 | Basit siluetler |
| Efektler (parçacık sistemi) | ~75 | Kod, sprite değil |
| UI tamamı | ~65 | Kalp/elmas/balon zaten var |
| Işıklandırma | — | Meşale ışığı zaten çalışıyor |
| Parallax katmanları | ~12 | 4. görselde çalışıyor |

### ⚠️ B Sınıfı — Üretilebilir ama dikkat ister

| Kalem | Miktar | Risk |
|---|---|---|
| Boss'lar (64–96px) | ~210 kare | Büyük sprite'ta detay zorlaşır. Siluet + ışıkla çöz |
| Cemo (duygusal karakter) | ~14 kare | Az kare ama ifade taşımalı |
| Ses efektleri | ~65 | Kod sentezi retro durur; ücretsiz kütüphane karıştır |

### ❌ C Sınıfı — Harici kaynak gerekir

| Kalem | Miktar | Çözüm |
|---|---|---|
| Ara sahne panelleri | ~40 | Aşağıdaki "panel stratejisi" |
| Müzik | 9 parça | Ücretsiz kütüphane / AI müzik aracı |
| Türkçe piksel font | 1 | Mevcut font'a 6 karakter ekle: ğ ü ş ı ö ç |

---

## 2. ARA SAHNE PANEL STRATEJİSİ (kritik çözüm)

40 illüstrasyon çizmek yerine **üç katmanlı ucuz yöntem**:

**Yöntem 1 — Sahnelenmiş oyun görüntüsü (panellerin %60'ı)**
Ara sahneyi oyun motorunda oynat. Karakterleri özel pozlara sok, kamerayı yakınlaştır, kararma/vinyet ekle, zamanı yavaşlat. Yeni sprite gerekmez — mevcut animasyonların birer karesi. Dan the Man'in ucuz sahnelerinin çoğu bu.

**Yöntem 2 — Siluet paneli (%25)**
Duygusal anlar için: iki siluet, arkada ateş ışığı, detay yok. El tutma, ateş başı, sırt sırta — hepsi siluetle *daha güçlü* anlatılır, çünkü oyuncu yüzü hayal eder. Üretimi neredeyse bedava, sanatsal etkisi yüksek.
→ B7 (el tutma), B8 (ateş başı), B12 (mektup), B16 (sırt sırta), B18 (son panel)

**Yöntem 3 — Gerçek illüstrasyon (%15, ~6 panel)**
Sadece en kritik anlar: açılış (Cemo'nun düşüşü), Ardo'nun ilk girişi, twist anı, final. Bunlara zaman ayır. 6 panel yönetilebilir.

**Sonuç: 40 panelin gerçek maliyeti ~6 illüstrasyon.**

---

## 3. TUTARLILIK PROTOKOLÜ (asıl risk burada)

Claude Code her seferinde sprite üretebilir — ama **her seferinde biraz farklı üretir**. 240 düşman karesi ayrı oturumlarda üretilirse oyun dağınık görünür. Çözüm:

**a) Palet dosyası — ilk iş**
`palette.py` içinde **37 renk** sabit. Her sprite üretiminde bu dosya referans verilir. Palet dışı renk yasak.

**b) Sprite üretici modülü**
Sprite'lar elle çizilmiş PNG değil, **kod fonksiyonu** olarak üretilsin:
```
draw_humanoid(surface, palette, pose, outfit)
```
Böylece Rey, Ardo, Muhafızlar aynı iskeletten çıkar. Tutarlılık garanti, varyasyon ucuz.

**c) Stil sözleşmesi (CLAUDE.md'ye yazılacak)**
- Kontur: koyu ama siyah değil (paletin en koyu 2. rengi)
- Işık kaynağı: her zaman sol üst
- Karakter yüzü: göz + kaş + çene gölgesi (29.08.2026'da genişletildi; gerçek yüz detayı portrede)
- Gölge: karakterin altında 1 elips
- Animasyon: 8 FPS hissi (her kare 7-8 oyun karesi)

**d) Asset kayıt defteri**
`assets/REGISTRY.md` — üretilen her sprite'ın adı, boyutu, kare sayısı, hangi paletten. Yeni üretimde referans.

---

## 4. PROTOTİPTEN GELEN DÜZELTMELER

| Sorun | Çözüm |
|---|---|
| ~~Türkçe karakter eksik~~ | **Kapandı** — tam set `src/ui/font_data.py` içinde |
| Ekran çok karanlık | Platform kenarı yeşil şeridi güçlendir; meşale yarıçapını %30 artır |
| Platform okunabilirliği | Kenar şeridine 1px açık kontur ekle |
| Arka plan duvar dokusu tekdüze | 3-4 varyant tile + rastgele dağıtım |
| Düşman siluetleri zayıf | Düşmanlara belirgin siluet ver — oyuncu 1 karede tanımalı |

**Siluet testi:** Her sprite'ı tek renk siyaha çevir. Hâlâ ne olduğu anlaşılıyorsa iyi tasarım. Anlaşılmıyorsa yeniden çiz. Bu test 10 saniye sürer, kaliteyi devasa artırır.

---

## 5. DİKEY DİLİM ASSET LİSTESİ (Bölüm 2)

Prototipte zaten var olanlar **[✓]** ile işaretli:

**Görsel**
- [✓] Rey temel animasyonlar (boşta, yürüme, zıplama, saldırı)
- [ ] Rey: 3'lü zincir (saldırı 2 ve 3), kaçınma, havaya kaldırma, havada saldırı, Yankı aktif pozu
- [✓] Bir düşman tipi (yeşil yaratık → **Sürüklenen** olarak yeniden adlandır)
- [ ] Tırmanan, Şişkin
- [ ] Mini-boss (büyütülmüş Sürüklenen + 1 saldırı)
- [✓] Katman 1 tileset temeli (duvar, zemin, platform)
- [ ] Tileset varyantları + 9-slice tamamlama
- [ ] Hikâye dekoru: tırmık izi, iskelet, sönmüş meşale
- [✓] Vuruş flaşı + parçacık
- [ ] Slash yayı, kaçınma izi, toz, sandık açılma
- [✓] Can barı, para göstergesi, konuşma balonu
- [ ] Yankı göstergesi (3 kademe), combo sayacı, ekipman ikonu ×3

**Ses**
- [ ] Vuruş 4, düşman 8, ayak 6, UI 3, sandık 2, Yankı fısıltı 3
- [ ] Katman 1 ambient + dövüş müziği (2 parça)

**Font**
- [x] Türkçe karakterler

**Kalan gerçek iş: ~35 sprite/animasyon + ~26 ses + font.** Prototipin üstüne inşa edildiğinde makul.

---

## 6. ÜRETİM SIRASI

1. **Palet + stil sözleşmesi + font** (yarım gün, her şeyi etkiler)
2. **Sprite üretici modülü** (iskeletten karakter üretimi)
3. **Rey'in eksik animasyonları** (dövüş sistemi buna bağlı)
4. **2 yeni düşman + mini-boss**
5. **Tileset tamamlama + dekorlar**
6. **Efektler (parçacık kodu)**
7. **UI eksikleri**
8. **Ses** (en son — oynanış oturmadan ses yapma)

---

## 7. GÜNCEL RİSK DEĞERLENDİRMESİ

| Risk | Eski | Yeni |
|---|---|---|
| Sanat üretimi | 🔴 Yüksek | 🟡 Orta |
| Tutarlılık | 🟡 | 🔴 **Yüksek** ← yeni ana risk |
| Ara sahneler | 🔴 | 🟢 Düşük (siluet stratejisi) |
| Müzik | 🟡 | 🟡 Orta |
| Kapsam (18 bölüm) | 🔴 | 🟡 Orta |

**Ana risk artık sanat üretimi değil, üretilen sanatın tutarlılığı.** Palet dosyası ve sprite üretici modülü bu riski büyük ölçüde kapatır — ikisi de ilk hafta yapılmalı.

---

## Z. GERÇEKLEŞEN — ölçülmüş sayılar (08.09.2026)

Yukarısı 21.08.2026'da yazılmış bir **plan**. Aşağısı oyun bitince
kodun kendisinden sayıldı: `docs` ile depo arasındaki fark bir daha
tahmin edilmesin diye.

| Kalem | Plan | Gerçek | Not |
|---|---|---|---|
| Palet | 32 renk | **37** | beş yeşil eklendi (`DEVIR.md` §7) |
| Karakter/varlık sprite'ı | Rey + Ardo + 10 düşman | **25 `CharSpec`** | `src/art/animation.py` |
| Karakter başına animasyon | ~18 klip | **12 klip / 36 sanat karesi** | `ANIMATIONS` |
| Toplam sprite karesi | ~581 | **~900 (25 × 36)** | hiçbiri PNG değil — **kod** |
| Portre | listede yok | **3** (Rey, Ardo, Cemo) | 64×96, 29.08'de eklendi |
| Ses efekti | ~65 | **80** | `sfx_*.py` içinde `@_register` |
| Müzik | 8–10 parça | **9** | `music.py :: TRACKS` |
| Ara sahne paneli | ~40 statik illüstrasyon | **186 `Panel`, 18 sahne** | illüstrasyon YOK |

### Planın en isabetli tahmini

K bölümündeki 6. madde: *"Ara sahne panellerini oyun sprite'ından
üret. Ayrı illüstrasyon çizme — büyütülmüş sprite + özel poz yeter."*

Tam olarak bu oldu. 40 elle çizilmiş panel hiç üretilmedi; yerine
`src/scenes/staging.py` geldi: aktörleri sahneye koyan, poz/bakış
veren, ışık ve zerre ekleyen bir **sahneleme katmanı**. 18 ara sahne
onu kullanıyor ve hepsi oyunun kendi sprite'larından çıkıyor. En
pahalı görsel kalem böylece sıfıra indi ve tutarlılık bedava geldi.

### Planın yanıldığı yer

*"Yankı ses işlemi: önceden işlenmiş ikinci set (~20 dosya)."*
Dosya üretilmedi — sesler zaten kod (`numpy` dalga tabloları), o
yüzden boğuk sürüm **çalışma zamanında** aynı tablodan türetiliyor
(`src/audio/sfx.py`, "boğulmuş set"). İkinci bir set tutmak, tek
kaynağı ikiye bölmek olurdu.

### Sayılar nasıl tekrar ölçülür

```
python -c "from src.art.animation import CHARACTERS, ANIMATIONS; \
           print(len(CHARACTERS), len(ANIMATIONS))"
grep -c "@_register(" src/audio/sfx_*.py
python -c "from src.audio import music; print(len(music.TRACKS))"
grep -rho "Panel(" src/scenes/*.py | wc -l
```

`tests/test_pipeline.py` ve `tests/test_audio.py` bunların bir kısmını
zaten bağlayıcı olarak ölçüyor.
