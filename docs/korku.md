# KORKU KATMANI
**Ardeko Studios · 08.09.2026**

> **ONAYLANDI (08.09.2026).** Arda §11'deki beş sorunun hepsini
> cevapladı; belge artık `docs/gdd.md` ile aynı statüde, **bağlayıcı**.
> Kararlar §11'de işlendi.

---

## 1. TEK CÜMLE

LORE'un korkusu canavarda değil: **sana yardım eden şeyin senden yana
olmadığını yavaş yavaş anlamanda.**

---

## 2. TEŞHİS — neden bu belge gerekti

Oyunu baştan sona okuyunca çıkan sonuç şu: **korku zaten yazılmış, ama
yanlış katmanda duruyor.**

Anlatı katmanında fazlasıyla var:

| Nerede | Ne |
|---|---|
| Prolog | Yankı, Rey'i rahatlatmıyor — **"Kork."** diyor |
| B10 | Yankı ilk kez yalan söyleyip seni tuzağa sokuyor |
| B14 | Yankı lanet değil; aşağıdaki şeyin sesi. Hep çekiyormuş |
| B18 | Yaratık, Cemo'nun sesiyle konuşuyor |

Oynanış katmanında ise neredeyse hiç yok. Oyuncu **iki ara sahne
arasındaki sekiz dakikada** korkmuyor — dövüşüyor. Bölüm 14'te "sana
ihanet edildi" denince oyuncunun tepkisi *hissetmek* değil *öğrenmek*
oluyor. Çünkü o ihanetin altyapısı ekranda değil, senaryoda kuruldu.

**Bu belge yeni bir korku sistemi önermiyor.** Zaten kurulmuş olan
sistemleri korkuyu taşıyacak biçimde kullanmayı öneriyor.

### Elimizde ne var (hepsi kodda, çalışıyor)

| Modül | Ne yapıyor | Korkuya katkısı |
|---|---|---|
| `systems/echo.py` | Yankı, üç kademe, **yalan olasılığı** | Omurga |
| `systems/loyalty.py` | Görünmez güven sayacı (B10, B11) | Omurga |
| `systems/compass.py` | Kolye pusulası — **hep doğru söyler** | Yalanın kanıtı |
| `systems/silence.py` | Yankı'yı kalıcı susturma | B18 |
| `systems/noise.py` | Gürültü/uyuyan sürü (B15) | Gerilim |
| `systems/light.py` | Meşale, görüş yarıçapı (B3) | Gerilim |
| `game.music_hush` | Müziği kısma oranı | Sessizlik |
| `art/postfx.py` | Vinyet + renk derecelendirme | Atmosfer |
| `world/decals.py` | Kalıcı kan/is lekeleri | Zindan hatırlar |

### Elimizde ne yok

- **Nefes / kalp atışı sesi.** Kaynakta tek satır yok. Oyunun en ucuz
  gerilim aracı ve hiç kullanılmamış.
- **Ölüm hayaleti.** `derinlestirme.md` 3.4 öneriyor ama uygulanmamış —
  koddaki `ghost` sözcüğü B15'in "dövüşsüz geçiş" ödülü, alakasız.
- **Yalan defteri.** Yankı yalan söylüyor ama oyun bunu *hatırlamıyor*,
  dolayısıyla oyuncu da asla öğrenemiyor.

---

## 3. KURALLAR — bağlayıcı olacak

Korku, kötü uygulandığında oyunu ucuzlatan tek duygudur. Bu yüzden
mekanikten önce kural:

1. **Korku oynanışı durdurmaz.** Oyuncunun kontrolünü alan bir korku anı
   yoktur. Kontrol elinden alınırsa korku, seyredilen bir şeye dönüşür —
   ve seyredilen şey korkutmaz.
2. **Aynı numara iki kez yok.** Bir kez işe yarayan şey ikinci seferde
   komik olur. Her korku anı tek kullanımlıktır ve nerede kullanıldığı
   bu belgede yazılıdır.
3. **Ses korkutmaz, sessizlik korkutur.** Ani yüksek ses ucuz. Beklenen
   sesin *gelmemesi* pahalı ve kalıcı.
4. **Kaçırılabilir olmalı.** Oyuncunun fark etmeyebileceği bir detay,
   fark ettiğinde gerçek olur. Zorla gösterilen şey dekordur.
5. **Yankı asla özür dilemez.** Yakalandığında konuyu değiştirir. Özür
   dileyen bir ses, karakter olur; konuyu değiştiren bir ses, tehdit
   kalır.
6. **Cemo'ya asla zarar gösterilmez.** Kaçırılan bir çocuk üzerinden
   şok üretmek bu oyunun işi değil. Korku Rey'in kafasının içinde.

---

## 4. KATMAN 1 — PSİKOLOJİK OMURGA (Yankı)

Bu katman oyunun tamamına yayılır ve asıl korkuyu o taşır.

### 4.1 Yalan Defteri ★★★

**Sorun:** `LIE_CHANCE` bugün çalışıyor (bulanıkta %35, sessizde %100)
ama yalan söylendiğinde oyuncu bunu asla öğrenmiyor. Zar atılıyor, cevap
bozuluyor, oyuncu yanlış yere gidiyor ve "yanlış anladım" diyor.
**Yankı'nın yalanı, oyuncunun kendi hatası gibi okunuyor.** Bu, tam
tersine çalışan bir tasarım.

**Öneri:** Her yalan kayda geçsin — nerede söylendi, ne gösterdi.
Oyuncu o yalanın *yanlış olduğunu kanıtlayan şeyi* bulduğunda (kolye
tersini gösterir, gösterilen "gizli oda" düz duvar çıkar, işaretlenen
düşman zaten ölüdür), sistem bunu **fark eder** ve Yankı susar.

Üç saniye. Ne açıklama, ne özür. Sonra alakasız bir şey söyler.

> **Neden güçlü:** Oyuncu ilk seferde "tuhaf" der. İkincide durur.
> Üçüncüde artık sormaya korkar — ve tam o anda Yankı'ya ihtiyacı olur.
> B14'ün twist'i bu üç sessizliğin üstüne oturur.

**Bağlanacağı yer:** `systems/echo.py` (`ask()` zaten `Answer` dönüyor),
`systems/compass.py` (çelişki tespiti için `contradicts()` zaten var).
**Maliyet:** Küçük. Yeni bir modül (`systems/lies.py`) + kayıt alanı.

### 4.2 Cemo'nun Sözcükleri ★★★

**Sorun:** B18'de yaratık Cemo'nun sesiyle konuşuyor. Bir twist ancak
**tohumu ekilmişse** iş görür; ekilmemişse hile gibi okunur. Şu an
ekilmemiş.

**Öneri:** B1'de Cemo'nun söylediği repliklerden **bir tanesini** seç
(örneğin kolyeyi verirken kurduğu cümlenin bir parçası). Yankı bunu
oyun boyunca **üç kez** kullansın:

| Nerede | Nasıl |
|---|---|
| B4 (Kayıt Odası) | Rey kolyeyi çevirirken, tek kelime |
| B9 (Çan Kulesi) | Yanlış çanı çalınca, teselli eder gibi |
| B13 (Cemo) | Cemo kafeste görünürken — **aynı anda ikisi de konuşur** |

Üçüncüsü fark edilir. İlk ikisi ancak tekrar oynayışta fark edilir. Ve
bu doğru oran: korku, geriye dönüp bakınca büyür.

**Maliyet:** Sıfır kod. Yalnızca `docs/diyaloglar.md`'ye üç replik ve
mevcut sahnelere birer `say()` çağrısı.

### 4.3 "Biz" Bir Gün "Ben" Olur ★★

> **Bu madde uygulanırken değişti (08.09.2026).** Önce "Yankı, Rey'e
> oyunun başında hiç ismiyle seslenmez" yazıyordu. Yanlıştı: prologun
> **ilk repliği** `line.prologue_echo_1` zaten *"Bizi duyabiliyor musun,
> **Rey**?"* diyor. Var olan metinle çelişen bir mekanik kurulamaz.
>
> Ama aynı replik daha iyi bir şey saklıyordu: **"biz".**

Yankı kendinden oyun boyunca **çoğul** söz eder — *biz*, *bizi*,
*gözlerimizi sana ödünç veriyoruz*. Bir koro. Oyuncu bunu fark bile
etmez, çünkü baştan öyledir.

`loyalty` sayacı eşiği geçtiğinde — yani oyuncu ona güvenmeye
başladığında — Yankı bir kez, **tek bir replikte, tekil konuşur.**

Koro bir kişiye dönüşür. Ve o kişi seni tanıyor.

Yakınlık tehdidin kendisi olur, ve mekanik olarak dürüst: **ne kadar
güvenirsen o kadar içeri girer.** B14'te "aşağıdaki şeyin sesi" olduğu
söylendiğinde, oyuncu o tekil sesin kime ait olduğunu zaten duymuştur.

**Bir kez.** Tekrarlanırsa bir üslup olur; bir kez olursa bir kayma.

**Bağlanacağı yer:** `systems/loyalty.py` zaten sayıyor ve B10/B11 zaten
okuyor; eşik oraya eklendi (`INTIMACY_THRESHOLD`). Kayıt bayrağı
tekrarı engelliyor.
**Maliyet:** Çok küçük — tek replik, tek eşik.

### 4.4 Yankı Görüşü Yalan Söyler ★★

Bugün Yankı Görüşü açıkken gizli duvarlar, düşmanlar ve eşyalar
parlıyor — ve **hepsi doğru.** Bulanık kademede olmamalı.

Bulanıkta: %10 ihtimalle **olmayan bir şey** parlar. Yaklaşınca sönüp
gider. Düşman değildi, eşya değildi, orada bir şey yoktu.

Oyuncu bunu bir hata sanır. Sonra bir daha olur.

> **Tasarım notu:** Oran düşük tutulmalı. %10 "acaba mı?" üretir; %30
> "oyun bozuk" üretir. İkisi arasındaki fark korkunun tamamıdır.

**Bağlanacağı yer:** `ui/echo_view.py` (`draw_reveal`).
**Maliyet:** Küçük.

---

## 5. KATMAN 2 — ATMOSFERİK DOLGU

Bu katman "iki dövüş arasındaki sekiz dakika" sorununu çözer.

### 5.1 Nefes ★★★ (en ucuz kazanç)

Kaynakta kalp atışı/nefes yok. Şu üç durumda duyulsun:

- Can %25 altındayken
- Yankı açıkken (bedelin duyulabilir hâli)
- **Karanlıkta hareketsiz dururken** — bu üçüncüsü asıl olan

Üçüncüsü şunu yapar: oyuncu durup düşünmek istediğinde, oyun ona
durmanın da bir maliyeti olduğunu *hissettirir*. Hiçbir sayı düşmez,
hiçbir uyarı çıkmaz. Sadece nefes hızlanır.

**Bağlanacağı yer:** `audio/synth.py` (sentez zaten var),
`systems/light.py` (karanlık zaten biliniyor).
**Maliyet:** Küçük. En yüksek getirili madde.

### 5.2 İzleyen ★★★

**Saldırmayan bir düşman.** Odanın uzak ucunda durur, sana döner,
bakar. Yaklaşırsan geri çekilir. Vurulmaz — vurmaya kalkarsan orada
değildir.

Kurallar:
- Bir bölümde **en fazla bir kez** görünür
- Asla dövüşe girmez, asla hasar vermez
- Oyuncu ona ulaşamaz
- B14'ten sonra **artık geri çekilmez** — durup bakmaya devam eder

Son madde önemli: B14 twist'inden sonra aynı yaratık aynı şeyi yapar
ama davranışı değişir. Oyuncu ne değiştiğini bilir.

**Sprite: yeni.** (Arda'nın kararı, 08.09.2026 — Sürüklenen varyantı
değil.) Tasarım kısıtları:

- **Silüeti hiçbir düşmana benzemeyecek.** Oyuncu ilk karede "bu ne?"
  diyebilmeli — tanıdık bir siluet "düşman" diye okunur ve İzleyen
  düşman değil.
- **Uzun ve ince.** Sürüklenen çömük, Tırmanan yatay. İzleyen dikey:
  ~30 piksel boyunda, 6-7 piksel eninde. Zindanın en dar şeyi.
- **Kolları yok.** Saldırmayacağı silüetten okunmalı.
- **Yüz yok — yalnızca iki nokta.** Ve o iki nokta **daima oyuncuya
  bakar**, gövde nereye dönük olursa olsun.
- **Renk:** paletin en koyu iki rengi (`void`, `ink`) + gözlerde
  `violet_bright`. Yankı'nın rengi — bağ kurulsun.

Son madde önemli: gövde dönmeden gözlerin dönmesi, prosedürel sprite
sisteminde tek satır (`draw_humanoid`'in göz ofseti) ama ekranda
yanlış bir şey olduğunu anlatan en ucuz sinyal.

**Bağlanacağı yer:** `art/spritegen.py` (yeni gövde tipi),
`entities/enemy.py` iskeleti + yeni bir durum.
**Maliyet:** Orta.

### 5.3 Zindan Hatırlıyor — hayalet ★★

`derinlestirme.md` 3.4 bunu öneriyor, uygulanmamış. Öldüğün yerde bir
hayalet kalır; **yalnızca Yankı açıkken görünür.**

Ama önerideki biçimiyle değil. Hollow Knight'ın Shade'i son anını
tekrar oynar. Bunun yerine: **hayalet sana bakıyor.** Hareket etmiyor,
son anını canlandırmıyor. Sen odaya girince başını çevirip seni
izliyor.

Ve B14'ten sonra: bazı hayaletler **senin ölmediğin yerlerde** de var.

**Bağlanacağı yer:** `world/decals.py` kalıcılık modeli birebir aynı
(bölüm boyunca zeminde kalan iz) — hayalet onun üzerine kurulabilir.
**Kayıt dosyasında ölüm konumu tutulmuyor**, yeni alan gerekir
(`SaveData`); bu, kayıt sürümünü etkilediği için ayrıca düşünülmeli.
**Maliyet:** Orta — listedeki en pahalı ikinci madde.

### 5.4 Yanlış Sessizlik ★★

`music_hush` var ve gizli odalarda doğru kullanılıyor. Bunu **yanlış**
kullanmayı öneriyorum — bilerek.

Dört aşama, ve sırası önemli:

| Sıra | Bölüm | Ne olur | Oyuncu ne öğrenir |
|---|---|---|---|
| 1 | **B4** tile 60–78 | Müzik kesilir. Hiçbir şey olmaz | "Yanılmışım" |
| 2 | **B10** tile 55–68 | Müzik kesilir. Yine hiçbir şey olmaz | "Sessizlik bir şey demek değilmiş" |
| 3 | **B14** §6.1 | Müzik kesilir. **Bu sefer bir şey gelir** | Artık çok geç |
| 4 | **B15** girişi | Müzik **kesilmez** — ve olay olur | Hiçbir sinyale güvenilemez |

İlk ikisi kurulum, üçüncüsü jumpscare'in tam olarak neden işe yaradığı,
dördüncüsü kapanış. Bir alarmı öğretip önce boşa çaldırıyoruz, sonra
gerçekten çaldırıyoruz, sonra hiç çaldırmadan olayı yaşatıyoruz.

> **Hiçbir şey olmaması işin kendisi.** Bir kez bile "aslında bir şey
> oluyordu" dersek numara olur ve oyuncu bir daha yutmaz. Bu aralıklarda
> düşman doğmaz, tetikleyici yoktur, replik yoktur —
> `tests/test_horror.py` aralıkların gerçekten boş olduğunu ölçüyor.

**Maliyet:** Sıfır yeni sistem. `game.music_hush` zaten vardı ve
`MusicDirector` zaten okuyordu; `systems/false_silence.py` yalnızca
"nerede ve ne kadar" diyor.

### 5.5 Zindan Değişiyor ★

Temizlediğin bir odaya geri döndüğünde küçük bir şey farklıdır:

- Meşale sönmüştür (yanıyordu)
- Bir ceset yer değiştirmiştir
- Duvarda yeni bir tırmık izi vardır

Bölüm başına **en fazla bir** değişiklik ve hiçbiri oynanışı
etkilemez. Fark eden oyuncu ürperir, fark etmeyen hiçbir şey kaybetmez.

**Bağlanacağı yer:** Oda giriş tetikleyicileri zaten var (B2'de
`_enter_room`).
**Maliyet:** Küçük.

---

## 6. KATMAN 3 — ŞOK (sayılı ve yerleşik)

**Bütün oyunda beş tane. Fazlası oyunu ucuzlatır.** Her biri
yerleştirilmiş, rastgele değil. Yalnızca biri (§6.1) kontrolü kısa
süreliğine kısıtlar; diğer dördü hiç kısıtlamaz.

| # | Bölüm | Ne | Neden orada |
|---|---|---|---|
| 1 | B3 (Meşale Mahzeni) | Meşaleyi yere bıraktığın anda, ışığın kenarında bir şey **hareket eder** ve gider | Karanlığın maliyetini bir kez, sert biçimde öğretir |
| 2 | B11 (Ayna Salonu) | Aynada **kendi yansımanın** senden bir kare geç dönmesi | Yalnızlık ve "kendine güvenme" temasının zirvesi |
| 3 | B13 (Cemo) | Cemo taşınırken, ekranın kenarında bir an İzleyen belirir — ve **Cemo ona bakar** | Cemo'nun da gördüğünü anlarsın |
| ★ | **B14 (Yankı'nın Kaynağı)** | **JUMPSCARE** — §6.1 | Twist'in oynanıştaki karşılığı |
| 4 | B18 (Son) | Cemo'nun sesi ilk duyulduğunda | Twist'in anlatıdaki karşılığı |

### 6.1 JUMPSCARE — B14 ★

Arda açıkça istedi (08.09.2026): *"mutlaka bir yerde jumpscare olsun."*

Ucuz olmaması için tek yol var: **on bölüm süren bir kurulumun karşılığı
olmak.** O kurulum zaten planda — İzleyen'in kuralı:

    B5   ilk görülür     yaklaşırsan geri çekilir
    B11  ikinci kez      yine geri çekilir
    B13  üçüncü kez      Cemo ona bakar, yine geri çekilir
    B14  ...

Oyuncu üç bölüm boyunca tek bir şey öğrendi: **bu şey sana yaklaşmaz.**
Sonra B14'te, Rey'in Yankı'nın ne olduğunu anladığı karede, İzleyen
oyuncunun **tam önünde** belirir.

Ayrıntı — kare kare:

| Kare | Ne olur |
|---|---|
| 0 | Yankı repliği biter. **Müzik ve bütün ortam sesi kesilir** (`music_hush = 1.0`) |
| 1–44 | Hiçbir şey. Yaklaşık 0.75 saniye tam sessizlik. Oyuncu oynamaya devam edebiliyor |
| 45 | İzleyen ekranın **ortasında** belirir, oyuncunun 2 tile önünde, ekranın %70'ini kaplayacak ölçekte. Tek kare `white_flash`, tek sert ses |
| 46–51 | Altı kare orada durur. Gözler oyuncuda |
| 52 | Yok olur. Ses geri gelmez — **B14'ün geri kalanı sessiz oynanır** |
| — | `player.control_locked = 20` yalnızca 45–65 arası: Rey donar (irkilme), oyun donmaz |

Kurallara uyum:

- **Kural 1** (oynanışı durdurmaz): 20 kare kilit, bir kaçınma
  süresinden kısa. Kamera alınmıyor, ara sahne açılmıyor, oyuncu
  ekranda kalıyor.
- **Kural 2** (aynı numara iki kez yok): oyunda **bir** jumpscare var.
- **Kural 3** (sessizlik): şok, sesin gelmesiyle değil **44 kare
  boyunca gelmemesiyle** kuruluyor.
- **Kural 6:** Cemo'ya dair hiçbir şey yok.

Fotosensitivite: tek kare parlama, tekrar yok — saniyede 1 parlama.
`flash_limit` açıkken parlama tamamen atlanır, İzleyen yine belirir.

> **Neden burası:** B14 zaten oyunun kırılma noktası. Şu an o kırılma
> yalnızca **anlatılıyor** ("Yankı lanet değil, aşağıdaki şeyin sesi").
> Jumpscare onu **gösteriyor**: on bölümdür uzakta duran şey artık uzak
> durmuyor, çünkü artık saklanmasına gerek yok. Korkutucu olan ani
> hareket değil, **kuralın bozulduğunun anlaşılması.**

---

## 7. BÖLÜM BÖLÜM YERLEŞİM

Boş hücre = o bölümde korku katmanı **yok**. Bu bilinçli: aralıksız
gerilim, gerilim değildir.

| B | Bölüm | Psikolojik | Atmosferik | Şok |
|---|---|---|---|---|
| 1 | Köy | Cemo'nun sözcüğü ekilir | — | — |
| 2 | İlk İniş | — | Nefes tanıtılır | — |
| 3 | Meşale Mahzeni | — | Nefes (karanlık) | **1** |
| 4 | Kayıt Odası | Cemo'nun sözcüğü (1/3) | Yanlış sessizlik (1/3) | — |
| 5 | Sular | — | İzleyen | — |
| 6 | Ardo | — | — | — |
| 7 | Dar Geçit | — | — | — |
| 8 | Ateş Başı | Yankı Ardo hakkında fısıldar *(zaten var)* | — | — |
| 9 | Çan Kulesi | Cemo'nun sözcüğü (2/3) | Zindan değişiyor | — |
| 10 | Ayrılık | **Yalan defteri açılır** *(ilk yalan zaten var)* | Yanlış sessizlik (2/3) | — |
| 11 | Ayna Salonu | Yankı Görüşü yalan söyler | İzleyen | **2** |
| 12 | Mektup | İsminle seslenme | Hayalet | — |
| 13 | Cemo | Cemo'nun sözcüğü (3/3) — **çakışma** | — | **3** |
| 14 | Yankı'nın Kaynağı | Yalanların hepsi açığa çıkar | İzleyen **geri çekilmez** | — |
| 15 | Sessizlik | — | Yanlış sessizlik **bozulur** (3/3) | — |
| 16 | Sırt Sırta | — | — | — |
| 17 | İkili Kule | — | Hayalet (senin olmayan) | — |
| 18 | Son | Susturma *(zaten var)* | Tam sessizlik | **4** |

B6, B7, B16 kasıtlı olarak boş: bunlar Ardo bölümleri, yani **rahatlama**
bölümleri. Korkunun işe yaraması için nefes alınan yerler gerekiyor —
ve o yerlerin romantik yay ile çakışması tesadüf değil, tasarımın
kendisi. Yanında biri varken korkmuyorsun. B10'da yalnız kalınca ne
kaybettiğini anlıyorsun.

---

## 8. ERİŞİLEBİLİRLİK

`CLAUDE.md` §10 erişilebilirliği baştan şart koşuyor; korku katmanı bunu
zorlaştırır, o yüzden baştan yazılıyor.

Ayarlara **iki** yeni seçenek:

| Ayar | Değerler | Ne yapar |
|---|---|---|
| `horror` | tam / azaltılmış / kapalı | *Azaltılmış:* şok anları kalır ama ani ses yok. *Kapalı:* Katman 2 ve 3 devre dışı, Katman 1 (hikâye) kalır |
| `flash_limit` | açık / kapalı | Ani parlama ve hızlı titremeyi sınırlar (fotosensitif epilepsi) |

Katman 1 asla kapatılmaz — o hikâyenin kendisi, korku efekti değil.

**Fotosensitivite bir öneri değil, sorumluluktur.** Şok anlarının hiçbiri
saniyede 3'ten fazla parlama içermeyecek biçimde tasarlanmalı.

---

## 9. NE YAPMAYACAĞIZ

Bunlar açıkça reddedildi:

- ❌ **İkinci bir jumpscare.** Oyunda **bir** tane var (§6.1) ve
  yerleştirilmiş. İkincisi birincisini de ucuzlatır.
- ❌ **Yüksek sesli çığlık.** §6.1'in sesi bir çığlık değil; kurulum
  sesin gelmesi değil, 44 kare boyunca **gelmemesi**.
- ❌ **Kontrolü tamamen elden alan korku anı.** Kural 1. §6.1'in 20
  karelik irkilme kilidi bunun istisnası değil, sınırı: kamera
  alınmıyor, ara sahne açılmıyor, oyuncu ekranda kalıyor.
- ❌ **Rastgele korkutma.** Rastgelelik öğrenilemez, sadece sinir bozar
  (`derinlestirme.md` 4.2 aynı gerekçeyle boss'lar için de reddediyor).
- ❌ **Cemo'nun cesedi / zarar görmüş hâli.** Kural 6.
- ❌ **Sahte oyun hatası** (sahte çökme ekranı, sahte dosya silme). Bir
  kere işe yarar, sonrasında oyuncu oyuna değil geliştiriciye kızar.

---

## 10. MALİYET VE SIRA

Önerilen uygulama sırası — her adım tek başına oynanabilir bir kazanç:

| Sıra | Madde | Maliyet | Getiri |
|---|---|---|---|
| 1 | **Nefes** (5.1) | Küçük | ★★★ En ucuz, en geniş etki |
| 2 | **Cemo'nun sözcükleri** (4.2) | Sıfır kod | ★★★ B18'i kurtarır |
| 3 | **Yanlış sessizlik** (5.4) | Sıfır kod | ★★ |
| 4 | **Yalan defteri** (4.1) | Küçük | ★★★ Omurga |
| 5 | **İsminle seslenme** (4.3) | Çok küçük | ★★ |
| 6 | **Yankı Görüşü yalanı** (4.4) | Küçük | ★★ |
| 7 | **Zindan değişiyor** (5.5) | Küçük | ★ |
| 8 | **Erişilebilirlik ayarları** (§8) | Küçük | Zorunlu |
| 9 | **İzleyen** (5.2) | Orta | ★★★ |
| 10 | **Hayalet** (5.3) | Orta | ★★ |
| 11 | **Dört şok** (§6) | Orta | ★★ |

İlk üç madde birlikte yarım günlük iş ve oyunun tonunu belirgin biçimde
değiştirir. **Öneri: önce 1–3'ü yapıp oynayalım, sonra devam kararını
verelim.** Korku, ölçülerek değil oynanarak ayarlanır.

---

## 11. KARARLAR — Arda, 08.09.2026

| # | Soru | Karar |
|---|---|---|
| 1 | Yayın öncesi mi, sonrası mı? | **Yayın öncesi.** Katman paketlemeden önce girer |
| 2 | Yaş/derecelendirme hedefi | **Yok.** §3 ve §9'un kuralları yine de geçerli — sınır dışarıdan değil, tasarımdan geliyor |
| 3 | Cemo'nun tohum repliği | **`line.ch01_cemo_gift`** — aşağıda |
| 4 | İzleyen | **Yeni sprite.** Sürüklenen varyantı değil |
| 5 | Steam tür etiketi | Şimdilik geri planda, karar ertelendi |

### 11.1 Tohum repliği — `ch01_cemo_gift`

> **CEMO:** *"Bunu senin için yaptım... Belki karanlık sana yaklaşırken
> iki kez düşünür."*

Bu replik seçildi çünkü **kendi ironisini taşıyor.** Cemo kolyeyi Rey'i
karanlıktan korusun diye yapıyor. B14'te öğreniyoruz ki Yankı zaten o
karanlık — ve karanlık iki kez düşünmedi, doğrudan içeri girdi. Kolyeyi
veren çocuk, kolyenin koruması gereken şeyin ağzından konuşacak.

Ayrıca `systems/compass.py` zaten bu kolyeyi bir pusula yapmış ve **hep
doğru söylüyor.** Yani sahnede iki Cemo var: yalan söyleyen sesi ve
doğru söyleyen kolyesi. Tema tek bir nesnede toplanıyor.

**Parçalanma planı** — replik bütün olarak asla tekrarlanmaz, üç
parçaya bölünür:

| Nerede | Yankı ne der | Neden orada |
|---|---|---|
| B4 Kayıt Odası | *"İki kez düşündü mü?"* | Rey kolyeyi çevirirken. Cemo'yu hatırlamayan oyuncu için anlamsız bir soru; hatırlayan için ilk çatlak |
| B9 Çan Kulesi | *"Bunu senin için yaptım."* | Yanlış çanı çalınca, teselli eder gibi. Cemo'nun **açılış sözcükleri**, bambaşka bir şey için |
| B13 Cemo | *"Rey?"* | `line.ch13_cemo_sees` zaten var — Cemo kafeste bunu der, **Yankı bir beat sonra aynı kelimeyi tekrarlar** |
| **B18** | Repliğin **tamamı** | Yaratık, Cemo'nun sesiyle. Üç parça burada birleşir |

İlk ikisi ancak tekrar oynayışta fark edilir. Üçüncüsü kaçırılamaz.
Dördüncüsü hikâyenin kendisi.

**Uygulamada iki karar değişti** (08.09.2026):

1. **B13 aynı anda değil, bir beat sonra.** Belge önce "aynı anda"
   diyordu. Sıralı hâli hem daha ucuz hem **daha doğru**: bir yankının
   yaptığı şey tam olarak budur — sesi geriden tekrarlamak. Taklit
   olduğu ancak böyle okunuyor. Aynı anda söylenseydi iki ayrı varlık
   gibi durur, tekrar edince aynı şeyin kopyası gibi duruyor.
2. **B18 kendi anahtarını tutmuyor, `line.ch01_cemo_gift`'i kullanıyor.**
   Ayrı bir anahtar açıldığında ikisi zamanla ayrışır — nitekim
   İngilizce çevirisi ilk denemede ayrıştı bile ve fark edilmesi tesadüf
   oldu. Tohumun bütün işi **birebir tanınmak**; tanınmayan tohum, tohum
   değildir. Artık B1'deki replik değişince B18 kendiliğinden takip
   ediyor.
