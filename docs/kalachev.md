# KALACHEV
**Tasarım önerisi · Ardeko Studios · 08.09.2026**

> Bu belge bir **öneridir**. Arda onaylayana kadar hiçbir satırı
> uygulanmaz. Onaylanan bölümler `docs/gdd.md` ile aynı statüye geçer.

---

## 1. TEK CÜMLE

**Efe Kalachev**, Ardo'nun eski dostu ve serseri bir maceracı — Rey'in
yapayalnız olduğu altı bölüm boyunca beliren, önüne geleni parçalayan ve
yardım edip gitmeden önce hiç durup açıklama yapmayan adam.

---

## 2. YERİ ZATEN BOŞTU

Bu karakteri yerleştirecek bir yer aramadım; **oyunda hazır duruyordu.**

| Bölüm | Yanında kim var |
|---|---|
| B1–B5 | kimse |
| **B6–B9** | **Ardo** |
| **B10–B15** | **kimse — altı bölüm** |
| B16–B18 | Ardo |

`docs/yapi.md` B10'u *"Ayrılık. Yol ikiye ayrılır. Yalnız devam"* diye
tanımlıyor ve o yalnızlık bilinçli: B11 aynalar, B12 Ardo'nun izleri,
B14 twist. Ama **altı bölüm** uzun bir sessizlik ve orta oyunun tempo
sorunu tam olarak orada.

Kalachev o boşluğu dolduruyor — ama **yoldaş olarak değil.**

> ### Kalachev bir `Companion` DEĞİL
>
> `src/entities/companion.py` yanında sürekli duran, emir alan, ölmeyen
> bir sistem. Kalachev'i ona bağlamak onu ikinci bir Ardo yapardı ve
> B10–B15'in yalnızlığını iptal ederdi.
>
> Kalachev **belirir, keser, gider.** Emir veremezsin. Bekleyemez.
> Bir sonraki odada yoktur. Güvenilebilecek bir yardım değil — bir
> **olay**.

---

## 3. ARDO'NUN DOSTU, REY'İN YABANCISI

Arda'nın koyduğu kısıt (08.09.2026): *"Kalachev Rey'in çok yakın dostu
falan değil. Sadece oralarda takılan bir maceracı. Ardo'nun dostu."*

Bu kısıt oyunun **iki oynanabilir karakter** yapısını bedavaya
kullanıyor. Aynı adam, iki bambaşka ilişki:

| | **Rey oynarken** | **Ardo oynarken** |
|---|---|---|
| İlk görüş | Tehdit. Karanlıktan çıkan, bağırmadan öldüren biri | Tanıdık. "Sen hâlâ buralarda mısın?" |
| Konuşma | Kısa, kesik. Rey soru sorar, Kalachev cevap vermez | Şakalaşma, yarım cümleler, ortak geçmiş |
| Güven | Yavaş kazanılır ve hiç tamamlanmaz | Baştan tam |
| Ölümü | Bir yabancının ölümü — üzücü ama uzak | **Ardo'nun kaybı** |
| Yankı ne der | *"Bu adam senin için gelmedi."* | (Ardo'nun Yankı'sı yok — İz Sürme okur) |

**Rey'in hattı bir tanışma hikâyesi, Ardo'nunki bir veda hikâyesi.**
İkisi aynı sahneleri paylaşıyor, farklı şey yaşıyor.

Kritik: Rey oynarken Kalachev'i **Ardo tanıtıyor**. B6'da Ardo düşer,
üç yaratığı biçer, ve Kalachev de oradadır — Rey ikisinin birbirini
tanıdığını görür. Rey'in ona güvenmesi Ardo'ya güvenmesinden geçer.

---

## 4. NEDEN AGRESİF

Arda: *"Rey ve Ardo'ya göre çok daha agresif olsa, direkt düşmanlara
saldıran cinsten."*

Bu bir kişilik seçimi değil, bir **bilgi**: Kalachev bu zindanda tek
başına hayatta kalmış tek insan ve yanındaki adamı kaybetmiş. Bir tek
şey öğrenmiş — beklersen ölürsün.

Mekanik karşılığı, üç karakterin aynı sistemde ayrışması:

| | tell okur mu | mesafe | kaçınma | poise |
|---|---|---|---|---|
| **Rey** | öğrenir | orta | 3 şarj | düşük |
| **Ardo** | okur, bekler | uzak durur | 2 şarj | yüksek |
| **Kalachev** | **okumaz** | **kapanır** | **yok** | **çok yüksek** |

Kalachev tell beklemiyor, doğrudan giriyor ve **yediği hasarı umursamıyor**
— çünkü sendelemiyor. Oyuncu onu izlerken "bu adam böyle devam ederse
ölecek" diye düşünmeli. **Sonra ölüyor.** Ölümü sürpriz değil, önceden
gösterilmiş bir sonuç — ve iyi ölüm sahnesi tam olarak budur.

---

## 5. NEREDE GÖRÜNÜYOR

Arda: *"gelebileceği en erken bölümde gelmesi ve tanışmamız, ara ara
bölümlerde dahil olması ve finalde ölmesi."*

| B | Ne | Süre |
|---|---|---|
| **B4** Kayıt Odası | **Kampı.** İskelet onun değil — **yoldaşının**. Günlük zaten kafatası ve *sönmüş* alevle bitiyor: "arkadaşım öldü", "ben öldüm" değil. Bir ölü kendi ölümünü çizemez | dövüşsüz |
| **B5** Sular | **İlk görüş.** Uzakta, bir sürünün ortasına dalıyor, hepsini kesiyor, suya atlayıp kayboluyor. Tek kelime yok | ~15 sn |
| **B6** Ardo | **Tanışma.** Ardo düşer, üçünü biçer — ve Kalachev de oradadır. İkisi birbirini tanır | sahne |
| **B10** Ayrılık | Rey yalnız kaldıktan sonra ilk kez tek başına belirir. Tuzağı o kırar | ~40 sn |
| **B12** Mektup | Ardo'nun izlerini sürerken **Kalachev'in izleri de var** — ikisi burada birlikte yürümüş | dövüşsüz |
| **B13** Cemo | Zindancı dövüşüne dalar. Yaralanır ve bu **görünür kalır** | boss |
| **B15** Sessizlik | Uyuyan sürünün arasında. Konuşmuyor — konuşamaz, çünkü ses sürüyü uyandırır. İlk kez **sessiz** ve bu onu yanlış gösteriyor | ~30 sn |
| **B18** Son | Faz 1'de dördü birlikte. **Faz 2'de ölür** | final |

B7, B8, B9, B11, B14, B16, B17 **kasıtlı olarak boş**: her bölümde
görünen bir karakter bir olay değil, bir dekor olur.

### 5.1 Uygulama durumu (08.09.2026)

Sekiz maddenin **yedisi ekranda**; kalan tek madde **B18**.

| B | Nerede | Anahtar |
|---|---|---|
| B4 | `src/scenes/chapter04*.py` | panel "kampın sahibi" der, iskelet yoldaşınındır |
| B5 | `chapter05.py` `_update_sighting()` | `SIGHTING_*` — çıkıntıda, oyuncu 13 tile içindeyken |
| B6 | `chapter06.py` `_rescue()` | kurtarma anında belirir |
| B10 | `chapter10.py` `_break_trap()` | tuzağı o kırar, oyuncu düşmez |
| B12 | `world/rooms/chapter12.py` | yedinci iz, `kind="pair"`, ayrı renk |
| B13 | `chapter13.py` `_seal_arena()` + `on_boss_phase()` | mühür inerken girer, faz 1'de yaralanır |
| B15 | `chapter15.py` `_update_kalachev()` | sürünün arasında, `silent=True` |
| B18 | `chapter18.py` `_summon_kalachev()` + `_update_taken()` | üç faz; faz 2'de ölür |
| Kapanış | `ending.py` `"bakis"` paneli | Ardo dönüp bakar, kimse yoktur |

**Sekizi de yazıldı (08.09.2026).** Üç mekanik karaktere ait,
bölüme değil — B18 üçünü de hiçbir şey yazmadan devraldı:

* **Yara** (`wounded`) — `_blit_wound()` sprite'a 7 piksel işliyor,
  yön değişince aynalanıyor. Kalıcılığı `SaveData.flags`'te
  (`kalachev.WOUND_FLAG`), okunduğu tek yer
  `PlayScene.summon_kalachev`. "Her bölüm bir satır eklesin" bir
  hatanın şekli: bir bölüm unutulur ve yara sessizce kaybolur.
* **Sessizlik** (`silent`) — durur, bakar, vurmaz, süre saati işlemez.
  Sürü uyanınca kendiliğinden biter. B18 faz 2'de aynı kip başka bir
  anlam taşıyor: çocuğun sesi gelince **durup dinliyor.**
* **Ölüm** (`perish`, `chase`) — `leave()` ile aynı şey değil ve
  bilerek ayrı: çekilme geçici bir yokluk, ölüm kalıcı. Gövde yerde
  kalıyor (`gone` False), yani "gitti mi, öldü mü" sorusu hiç
  sorulmuyor.

### 6.1 Finalin uygulaması (08.09.2026)

    faz 1   arena mühürlenirken üçü de içeride (yoldaş da içeri alınır)
    faz 2   ilk diz çöküşte başlar — 392 karelik senaryolu bir an
    faz 3   `PHASE_ALONE`; susturma tam burada açılır

Faz 2 bir **ara sahne değil**: oyuncunun arenasında, oyuncunun
kamerasıyla, kontrolü kilitli olarak geçiyor. Kesip başka bir yüzeye
gitseydik olay oyuncunun başına değil ekranın başına gelirdi.

Cetvel ölçüldü, tahmin edilmedi: yem 47. tile'da (51'de denendi —
125 değil 60 piksellik bir "koşu" çıkıyordu ve gövde oyuncunun dibine
düşüyordu), yemin ömrü koşudan uzun (150 karelik varsayılan ömür
koşunun ortasında sönüyordu), yaratık cetvel boyunca diz çökük
tutuluyor (`CALLER_RISE_FRAMES` 96, cetvel 392 — uzatılmasaydı
kontrolü kilitli oyuncuyu dövmeye başlardı).

**Susturma faz 2'nin sonunda açılıyor**, ilk diz çöküşte değil.
`docs/yapi.md`'nin "yardımsız savaşır" cümlesi böylece bir varsayım
olmaktan çıkıp bir sonuç oluyor.

---

## 6. FİNAL — ÜÇ FAZ

`docs/yapi.md` B18'in doruğu bağlayıcı: *"Rey sesi susturmayı seçer —
sessizlikte, yardımsız savaşır."*

Dörtlü sahne bu doruğu silmemeli, **kurmalı**:

| Faz | Kim savaşıyor | Ne olur |
|---|---|---|
| **1** | Rey · Ardo · Kalachev | Çağıran dirilir. Dördünüz birlikte. Cemo sahnede — kafeste, savaşmıyor |
| **2** | — | Yaratık **Cemo'nun sesiyle** konuşur. Kalachev o sese doğru koşar. **Ölür.** Ardo onu çekmeye giderken kapı iner — geride kalır |
| **3** | Rey · yalnız | Rey sesi susturur. Sessizlikte bitirir |

**Ölümü, Rey'i yalnız bırakan şeyin ta kendisi oluyor.** "Yardımsız"
artık bir karar değil bir **sonuç** — ve doruğun anlamı keyfi olmaktan
çıkıp kazanılmış oluyor.

Kalachev neden o sese koşuyor: çünkü **o da bir çocuk sesi duyuyor** ve
bu zindanda kaybettiği adamın sesi. Yaratık herkese kaybettiğini
gösteriyor. Rey direniyor, Kalachev direnmiyor — çünkü Kalachev
beklemeyi hiç öğrenmedi (§4).

---

## 7. HAYALET SORUSU

Arda: *"Efe'nin final savaşından sonra hayalet olarak dirilme ihtimali
çok mu kötü?"*

**Dirilme kötü. Görünme değil.** Aradaki fark her şey.

Ölümü işe yarıyorsa geri gelmemeli — geri gelen bir ölüm, ölüm değil bir
gecikme olur ve faz 2'nin bütün ağırlığını geri alır.

Ama `docs/korku.md` 5.3'ün hayalet sistemi zaten yazıldı ve **yalnızca
Yankı açıkken** görünüyor. Bu, çok daha iyi bir kapanış veriyor:

> **Kapanışta, gün ışığında, Rey arkasına bakar. Hiçbir şey yoktur —
> çünkü Yankı artık susmuştur.**
>
> Ama **Ardo** arkasına bakar ve bir an durur.
>
> Oyuncu Kalachev'i göremez. Ardo görür mü, o da belli değildir.

Rey Yankı'yı susturarak Cemo'yu kurtardı ve aynı hareketle ölüleri görme
yeteneğini de kaybetti. **Sessizliğin bedeli bu.** Kalachev geri gelmiyor;
Rey'in onu göremiyor olması onun gerçekten gittiğinin kanıtı oluyor.

### Ama iskeleti savaşabilir

Arda'nın *"hayaleti veya iskeletinin savaşması"* fikri ayrı bir yere
oturuyor ve orada iyi çalışır: **B18 faz 1'de Kalachev'in yanında
savaşan şey zaten canlı değil olabilir mi?** Hayır — bu belge onu
**gerçekten canlı** tutuyor, çünkü ölümünün işe yaraması için oyuncunun
onu canlı sanması değil, canlı **olması** gerekiyor. Sahte bir Kalachev
faz 2'yi bir numaraya çevirirdi.

---

## 8. NE YAPMAYACAĞIZ

- ❌ **`Companion` olmayacak.** İkinci bir Ardo, B10–B15'in yalnızlığını
  iptal eder (§2).
- ❌ **Emir alamayacak.** "Burada bekle" diyebildiğin an bir araç olur.
- ❌ **Her bölümde görünmeyecek.** Yedi bölüm kasıtlı olarak boş (§5).
- ❌ **Ölümü geri alınmayacak.** Görünmesi başka, dirilmesi başka (§7).
- ❌ **Cemo final dövüşünde savaşmayacak.** Kaçırılmış bir çocuğun
  kurtarılma hikâyesini, onu dövüştürerek zayıflatmayız. Sahnede olacak,
  savaşmayacak.
- ❌ **Rey'le duygusal bir yakınlık kurulmayacak.** Arda'nın kısıtı
  (§3): tanıdık değil, Ardo'nun dostu.

---

## 9. MALİYET

| Sıra | İş | Maliyet |
|---|---|---|
| 1 | Sprite (`kalachev` CharSpec) — ağır, yaralı, silahı belirgin | Küçük |
| 2 | `entities/kalachev.py` — agresif AI, `Companion` değil | Orta |
| 3 | B5 ilk görüş + B10 belirme (kısa sahneler) | Orta |
| 4 | Diyaloglar: Rey hattı ve Ardo hattı **ayrı** | Orta |
| 5 | B18 üç fazlı final + ölüm sahnesi | Büyük |
| 6 | B4 kampın anlamı düzeltiliyor (iskelet = yoldaşı) | Küçük |
| 7 | Kapanışta Ardo'nun dönüp bakması | Küçük |

**Öneri: 1, 2, 6 ile başlayıp B5+B10'u oynayalım.** Karakterin
agresifliği ekranda doğru hissettirmiyorsa geri kalanı yazmanın anlamı
yok — bu belge onun ölümüne yatırım yapıyor ve o yatırım ancak oyuncu
onu izlemekten hoşlanırsa geri döner.

---

## 10. AÇIK KALAN

1. **Portresi var, sprite'ı yok.** Oyun içi 32 piksellik gövdesi
   üretilecek (§9.1). Portre `assets/portraits/kalachev.png` hazır.
2. **B2'nin gizli odasındaki iskelet kim?** Şu an "biri gelmiş" diyor.
   Kalachev'in yoldaşı mı, üçüncü biri mi? Üçüncü biri olması zindanın
   daha çok insan yuttuğunu söyler ve bence daha iyi.
3. **Ardo oynarken B18 nasıl bitiyor?** Rey'in doruğu "sesi susturmak".
   Ardo'nun Yankı'sı yok — onun son fazı ne? Bu belgenin dışında ve
   zaten açık bir soruydu.
