# SENARYO AKIŞI — Bütün diyaloglar, oynanış sırasıyla

Oyundaki **bütün konuşmalar, oyuncunun yaşadığı sırayla**; her anın başında
ne olduğunu ve replikleri neyin tetiklediğini anlatan bir not var. Notlar sahne
kodu okunarak çıkarıldı (23.09.2026). Metinler dil tablolarından
(`src/ui/lang/tr.json`, `en.json`) birebir alındı.

**Akış:** intro → ana menü → karakter seçimi → **Prolog** → dikey yolculuk
(yukarı) → **Bölüm 1 … Bölüm 18** → **Kapanış** (şafak + jenerik) → ana menü.
Intro, menü ve dikey yolculukta replik yok. DEVAM ET kayıtlı bölüme aşağı iner.

## Nasıl okunur

- Her `##` başlık bir bölüm: altında 1–2 cümlelik özet, sonra numaralı anlar
  (`###`), oyunda tetiklendikleri sırayla.
- Her anın başında `> Ne oluyor:` satırı: oyuncu nerede, repliği ne tetikliyor.
- **Rey ile oynarken:** / **Ardo ile oynarken:** — karakter seçimine göre
  değişen replikler. **İki karakterde de:** — iki seçimde de aynı replik.
  Etiket yoksa replik iki oynanışta da çıkar.
- *Koşullu* / *isteğe bağlı* işaretli anlar ve replikler yalnızca belirtilen
  durumda görünür. ⚠ işareti kodda bulunan bir sorunu gösterir (ayrıntı en
  sondaki **Denetim** bölümünde).
- Konuşmacı: **YANKI** Rey'in kafasındaki ses (mor, çerçevesiz). Ardo'da Yankı
  yok; onun yerine kendi gözlemi / iz okuması konuşur (`_trace_` anahtarları).
- Her bölümün sonunda **Ekran yazıları** listesi: ipucu kartları,
  bildirimler, boss ve bölüm adları — aynı biçimde düzenlenebilir.

## Nasıl düzenlenir

1. Yalnızca **tırnak içindeki metni** değiştir. `####` başlığındaki anahtara ve
   `- tr:` / `- en:` öneklerine dokunma. Her replik tek satır kalmalı.
2. `{key}`, `{count}` gibi süslü parantezli yer tutucuları koru; iki dilde de
   aynı yer tutucular olmalı.
3. Bitince dil tablolarına geri yaz, sonra denetle:

```
python tools/dialogue_dump.py --geri docs/senaryo-akisi.md
python tests/test_lang.py
```

Blok biçimi şu (bu kod bloğu geri yazmada **okunmaz**, yalnızca örnek):

```
#### ch01_echo_first
**YANKI**
- tr: "Türkçe metin"
- en: "English text"
```

- Yeni anahtar eklenmez: kodda karşılığı olmayan anahtar atlanır ve ekrana
  yazılır. Yeni bir replik önce kodda yerini bulmalı.
- Aynı anahtar belgede yalnızca **bir kez** düzenlenebilir blok olarak var;
  ikinci kez geçtiği yerde salt okunur bir hatırlatma (`> _Tekrar …_`) durur.
- Anahtar sırasıyla döküm isteyen için `docs/diyaloglar.md` hâlâ var
  (`python tools/dialogue_dump.py` yeniden üretir). İkisini aynı anda
  düzenleme: hangisini geri yazarsan o kazanır.
- Bu belge elle kuruldu; kod değişince anlatım notları kendiliğinden
  güncellenmez. Metinler ise geri yazmayla dil tablolarına geçer.

## İçindekiler

1. Prolog — Açılış filmi
2. Bölüm 1 — Köy
3. Bölüm 2 — İlk İniş
4. Bölüm 3 — Meşale Mahzeni
5. Bölüm 4 — Kayıt Odası
6. Bölüm 5 — Sular
7. Bölüm 6 — ARDO
8. Bölüm 7 — Dar Geçit
9. Bölüm 8 — Ateş Başı
10. Bölüm 9 — Çan Kulesi
11. Bölüm 10 — Ayrılık
12. Bölüm 11 — Ayna Salonu
13. Bölüm 12 — Mektup
14. Bölüm 13 — Cemo
15. Bölüm 14 — Yankı'nın Kaynağı
16. Bölüm 15 — Sessizlik
17. Bölüm 16 — Sırt Sırta
18. Bölüm 17 — İkili Kule
19. Bölüm 18 — Son
20. Kapanış — Şafak ve jenerik
21. Bölümden bağımsız
22. Denetim — bulunamayan, eksik ve görünmeyen anahtarlar

---

## Prolog — Açılış filmi

**Özet:** Karakter seçimi onaylanınca, oynanıştan önce oynayan kısa film. Rey seçildiyse kafasındaki seslerin (Yankı) ne olduğunu ve bedelini öğretir; Ardo seçildiyse onun Yankı'sız, iz okuyan açılışı oynar. Film bitince kamera mor alevden yukarı çıkıp köye varır (dikey yolculuk) ve Bölüm 1 başlar.

### 1. Açılış filmi

> Ne oluyor: Karakter seçiminin hemen ardından, siyah zeminde panel panel (`src/scenes/prologue.py`). Her replik oyuncu onaylayana kadar ekranda kalır. İki karakterin filmi tamamen farklı.

**Rey ile oynarken:**

*Panel 1 · Karanlık* — ekranda yalnızca nefes alan mor bir ışık; önce ses, sonra görüntü.

#### prologue_echo_1
**YANKI**
- tr: "Bizi duyabiliyor musun, Rey?"
- en: "Can you hear us, Rey?"

#### prologue_rey_1
**REY**
- tr: "Yine başladılar... Zihnimdeki fısıltılar. Başka kimsenin duyamadığı sesler."
- en: "They're back... The whispers in my head. Voices no one else can hear."

#### prologue_echo_2
**YANKI**
- tr: "Onlar bizi duyamaz. Sadece sen duyabilirsin."
- en: "They cannot hear us. Only you can."

*Panel 2 · Köy* — gece köyü; köylüler sırtını dönmüş, Rey ortada mor bir hâle içinde.

#### prologue_rey_2
**REY**
- tr: "Bu yüzden mi köydekiler benden korktu? Bana tek bir ad verdiler... Lanetli."
- en: "Is that why the villagers feared me? They gave me a single name... Cursed."

#### prologue_echo_3
**YANKI**
- tr: "İnsanlar anlamadıkları şeyden korkar."
- en: "People fear what they cannot understand."

*Panel 3 · Lanet* — Rey'in yüzü, yakın plan.

#### prologue_rey_3
**REY**
- tr: "Bazen sizden nefret ediyorum... Bazen de sizi kaybetmekten korkuyorum."
- en: "Sometimes I hate you... And sometimes, I'm afraid of losing you."

*Panel 4 · Üçüncü göz* — kaşlarının arasında mor bir göz açılır (prologun kalbi).

#### prologue_echo_4
**YANKI**
- tr: "Kapat gözlerini."
- en: "Close your eyes."

#### prologue_rey_4
**REY**
- tr: "Ne göreceğim?"
- en: "What will I see?"

#### prologue_echo_5
**YANKI**
- tr: "Gözlerinin göremediğini."
- en: "What your eyes cannot."

#### prologue_echo_5b
**YANKI**
- tr: "Etin ötesini... taşın ardını... gölgelerin sakladığı gerçeği."
- en: "Beyond the flesh... behind the stone... the truth hidden in the shadows."

#### prologue_rey_5
**REY**
- tr: "...Görüyorum."
- en: "...I see it."

#### prologue_echo_6
**YANKI**
- tr: "Görmeye başladın."
- en: "You're beginning to see."

#### prologue_rey_6
**REY**
- tr: "Duvarın arkasını görebiliyorum."
- en: "I can see what's behind the wall."

#### prologue_echo_7
**YANKI**
- tr: "Biz sana sadece kapıyı açıyoruz."
- en: "We only open the door."

*Panel 5 · Bedel* — göz açık ama ekran kararıyor (oyundaki Yankı karartmasının aynısı).

#### prologue_rey_7
**REY**
- tr: "Peki bedeli ne?"
- en: "And the price?"

#### prologue_echo_8
**YANKI**
- tr: "Biraz karanlık."
- en: "A little darkness."

#### prologue_rey_8
**REY**
- tr: "Ne kadar?"
- en: "How much?"

#### prologue_echo_9
**YANKI**
- tr: "Şimdilik... sadece biraz."
- en: "For now... only a little."

*Panel 6 · Korku* — göz söner ama karanlık geri çekilmez.

#### prologue_rey_9
**REY**
- tr: "Sizden korkuyorum..."
- en: "I'm afraid of you..."

#### prologue_echo_10
**YANKI**
- tr: "Kork."
- en: "Fear."

#### prologue_rey_10
**REY**
- tr: "Neden?"
- en: "Why?"

#### prologue_echo_11
**YANKI**
- tr: "Çünkü korku, yaklaşanı herkesten önce hisseder."
- en: "Because fear senses what is coming before anyone else."

*Panel 7 · Bugün* — kolyeli figür ve yerden açılan küçük mor bir yarık (B1'in habercisi).

#### prologue_echo_12
**YANKI**
- tr: "Derine..."
- en: "Deeper..."

#### prologue_echo_13
**YANKI**
- tr: "Daima derine."
- en: "Always deeper."

**Ardo ile oynarken:**

*Panel 1 · İz* — karanlıkta beliren ayak izleri.

#### prologue_ardo_1
**ARDO**
- tr: "Yıllardır yollardaki izleri okurum. Buda benim bir lanetim sanırım."
- en: "I've read trails for years. Guess that's my curse, too."

*Panel 2 · İz* — izler bir figüre varır.

#### prologue_ardo_2
**ARDO**
- tr: "Buradan biri geçmiş..."
- en: "Someone came through here..."

#### prologue_ardo_3
**ARDO**
- tr: "Ve geri dönmemiş."
- en: "And never came back."

*Panel 3 · Köy*

#### prologue_ardo_4
**ARDO**
- tr: "Derinlerde neyin beklediğini biliyorum."
- en: "I know what waits below."

*Panel 4 · Bugün*

#### prologue_ardo_5
**ARDO**
- tr: "Onu orada bırakmayacağım."
- en: "I won't leave them down there."

---

## Bölüm 1 — Köy

**Özet:** Gece köyünde Cemo kolyeyi verir; yer yarılır ve Cemo yarığa çekilir — oyuncu koşar ama yetişemez. Köye yaratıklar sızar, Jet silahsız oyuncuya kılıç verir. Rey burada Yankı Görüşü'nü kazanır; bölüm yarıktan aşağı düşüşle biter.

### 1. Uyanış

> Ne oluyor: Bölüm açılır açılmaz, Rey evin önünde uyanırken (oyuncu zaten hareket edebilir). Sesin ilk kelimesi.

**Rey ile oynarken:**

#### ch01_echo_first
**YANKI**
- tr: "Uyan... Karanlık çoktan uyandı."
- en: "Wake up... The dark is already awake."

**Ardo ile oynarken:**

_(Bu anda replik yok — Ardo'nun Yankı'sı yok.)_

### 2. Kolye

> Ne oluyor: Birkaç saniye sonra Cemo oyuncuya yürür ve kolyeyi uzatır (Raze müziği); kolye bir yay çizip oyuncunun göğsüne uçar. Teşekkür oynanan karakterin ağzından.

#### ch01_cemo_gift
**CEMO** — _B18'de aynı anahtarla yeniden duyulur_
- tr: "Bunu senin için yaptım... Belki karanlık sana yaklaşırken iki kez düşünür."
- en: "I made this for you... Maybe it'll make the darkness think twice."

**Rey ile oynarken:**

#### ch01_rey_thanks
**REY**
- tr: "Teşekkürler, Cemo. Bunu yanımda taşıyacağım."
- en: "Thank you, Cemo. I'll keep it with me."

**Ardo ile oynarken:**

#### ch01_ardo_thanks
**ARDO**
- tr: "Sağ ol evlat. Bu koruma belki işime yarar."
- en: "Thank you, kid. This might keep me alive."

### 3. Yarık açılıyor

> Ne oluyor: Yer sarsılır, Cemo'nun ayağının dibinde yarık açılır ve oyuncuyu yere serer; köylüler evlerine kaçar. Hemen ardından Cemo yarığa çekilir — o an bilerek kelimesiz (oyuncu koşar, yetişemez).

**Rey ile oynarken:**

#### ch01_echo_rift
**YANKI**
- tr: "Aşağıda bir şey seni çağırıyor."
- en: "Something below is waiting for you..."

**Ardo ile oynarken:**

#### ch01_ardo_rift
**ARDO**
- tr: "Bu yarığı daha önce gördüm. Taş bile içeriden yarılmış."
- en: "I've seen a wound like this before. Even the stone was torn from within."

### 4. Yalnız

> Ne oluyor: Yarık kapanır, elde yalnızca kolye kalır. Ardından yaratıklar köye sızar.

**Rey ile oynarken:**

#### ch01_echo_alone
**YANKI**
- tr: "Onu geri istiyorsun... değil mi?"
- en: "You want them back... don't you?"

**Ardo ile oynarken:**

#### ch01_ardo_alone
**ARDO**
- tr: "Aşağıda neyin yattığını biliyorum. Onu o karanlıkta bırakamam."
- en: "I know what lies below. I won't leave them in that darkness."

### 5. Jet kılıcı veriyor

> Ne oluyor: Oyuncu silahsız sağa yürüyüp kılıcın durduğu noktaya (yaratıklardan önce) gelince ara sahne: Jet yaklaşır, kılıcı uzatır, ilk onayda kılıç el değiştirir; üçüncü panel Jet'in yakın planı (`chapter01_cinematics.py`). Rey için bir tanışma, Ardo için eski bir arkadaş.

**Rey ile oynarken:**

*Uzatma*

#### ch01_jet_offer
**JET**
- tr: "Bunu al. Bu gece dışarıda kalma."
- en: "Take this. Do not stay out tonight."

#### ch01_rey_jet
**REY**
- tr: "Neden bana veriyorsun? Kimse bana yaklaşmıyor bile."
- en: "Why give it to me? No one even comes near me."

*İsim — Jet'in yakın planı*

#### ch01_jet_name
**JET**
- tr: "Köyde bir arkadaşım vardı. Berke. Bana hep "Emre" derdi."
- en: "I had a friend in the village. Berke. He always called me "Emre.""

#### ch01_rey_name
**REY**
- tr: "Ama herkes sana Jet diyor."
- en: "But everyone calls you Jet."

#### ch01_jet_name2
**JET**
- tr: "Jet… başkalarının verdiği isim. Adımıysa, beni gerçekten tanıyanlar söyler."
- en: "Jet… that is the name others give. My name is what the people who know me say."

#### ch01_rey_which
**REY**
- tr: "Peki sen hangisisin?"
- en: "So which one are you?"

#### ch01_jet_both
**JET**
- tr: "Bilmiyorum. Belki ikisi de."
- en: "I do not know. Maybe both."

*Ayrılık*

#### ch01_jet_leave
**JET**
- tr: "Kendine iyi bak, Rey. Ben doğuya gidiyorum."
- en: "Look after yourself, Rey. I am heading east."

**Ardo ile oynarken:**

*Uzatma*

#### ch01_jet_offer_ardo
**JET**
- tr: "Yine yollardasın demek. Al şunu."
- en: "On the road again, then. Take this."

#### ch01_ardo_jet
**ARDO**
- tr: "Sen de hiç değişmemişsin."
- en: "You have not changed either."

#### ch01_jet_changed
**JET**
- tr: "Değiştim. Sadece bazı şeyleri değiştirmedim."
- en: "I have. I just did not change some things."

#### ch01_jet_offer_ardo2
**JET**
- tr: "Bu gece dışarıda kalma istersen."
- en: "Do not stay out tonight, if you can help it."

#### ch01_ardo_jet2
**ARDO**
- tr: "Bana bunu mu söylüyorsun cidden?"
- en: "You are really saying that to me?"

#### ch01_jet_must
**JET**
- tr: "Birinin söylemesi lazım."
- en: "Someone has to."

*İsim — Jet'in yakın planı*

#### ch01_jet_name_ardo
**JET**
- tr: "Köyde Berke vardı. Bana ne derdi, biliyor musun?"
- en: "There was Berke, back in the village. You know what he called me?"

#### ch01_ardo_emre
**ARDO**
- tr: "Emre."
- en: "Emre."

#### ch01_jet_remember
**JET**
- tr: "Hatırlıyorsun."
- en: "You remember."

#### ch01_ardo_names
**ARDO**
- tr: "Bazı isimler unutulmaz."
- en: "Some names do not fade."

#### ch01_jet_name2_ardo
**JET**
- tr: "Jet'i herkes söyler. Emre'yi… beni gerçekten tanıyanlar."
- en: "Everyone says Jet. Emre… that is for the ones who actually know me."

#### ch01_ardo_name
**ARDO**
- tr: "Berke'yi hâlâ yanında taşıyorsun."
- en: "You still carry Berke with you."

#### ch01_jet_stay
**JET**
- tr: "Bazı insanlar gitse de insanın içinde kalır."
- en: "Some people leave and still stay inside you."

*Ayrılık*

#### ch01_jet_leave_ardo
**JET**
- tr: "Kendine iyi bak, Ardo."
- en: "Look after yourself, Ardo."

#### ch01_ardo_leave
**ARDO**
- tr: "Sen de."
- en: "You too."

#### ch01_jet_east
**JET**
- tr: "Ben doğuya gidiyorum."
- en: "I am heading east."

### 6. Jet gittikten sonra

> Ne oluyor: Ara sahne kapanıp oyuna dönülünce. Ardından yaratıklarla ilk dövüş.

**Rey ile oynarken:**

#### ch01_echo_sword_given
**YANKI**
- tr: "Sana bir şey verdi. Bunu unutma."
- en: "He gave you something. Do not forget it."

**Ardo ile oynarken:**

_(Bu anda replik yok — Ardo'nun Yankı'sı yok.)_

### 7. Yankı Görüşü

> Ne oluyor: Köyün sağ ucunda, kırılabilir duvarın hemen önündeki noktaya gelince 'YANKI GÖRÜŞÜ' yeteneği açılır ve ses kendini ilk kez yeteneğin sahibi olarak tanıtır. Ardo duvarı kılıçla kırar, replik yok. Duvarın ötesindeki çıkışla bölüm biter ve yarığa düşüş sahnesi (Bölüm 2'nin başı) oynar.

**Rey ile oynarken:**

#### ch01_echo_gift
**YANKI**
- tr: "Gözlerimizi sana ödünç veriyoruz... şimdilik."
- en: "We lend you our sight... for now."

#### ch01_echo_wall
**YANKI**
- tr: "Gördün mü? Burada perde inceliyor."
- en: "Do you feel it? The veil is thin here."

**Ardo ile oynarken:**

_(Bu anda replik yok — Ardo'nun Yankı'sı yok.)_

### Ekran yazıları — Bölüm 1

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.village
_Bölüm kartında ve kayıt yuvasında görünen ad_
- tr: "Köy"
- en: "Village"

#### chapter01.hint_move
_Prologdan sonra oyuncu bir süre hiç yürümezse, ekranın altında sönük_
- tr: "{left} {right} ile yürü"
- en: "Walk with {left} {right}"

#### chapter01.hint_attack
_Yaratıklar göründüğü hâlde oyuncu henüz saldırmadıysa_
- tr: "{key} ile saldır"
- en: "Attack with {key}"

---

## Bölüm 2 — İlk İniş

**Özet:** Yarıktan zindana düşüş. Taş koridorlarda ilk yaratıklar, sesin kendiliğinden yükseldiği 'Yankı odası', isteğe bağlı gizli oda, ilk mini-boss Şişmiş Olan ve duvarda Cemo boyunda tırmık izleri.

### 1. Yarıktan düşüş

> Ne oluyor: B1'in çıkışında oynayan ara sahne: oyuncu düşer, yere çarpar, dar bir dehlizde doğrulur; replik son panelde. ⚠ Kodda karakter kontrolü yok — bu Yankı repliği Ardo ile de çıkıyor (bkz. Denetim).

#### ch02_echo_fall
**YANKI** — _Ardo ile de oynuyor_
- tr: "Güzel... Bırak kendini. Karanlık seni taşıyacak."
- en: "Good... Let yourself fall. The darkness will carry you."

### 2. Yankı odası

> Ne oluyor: Dördüncü odada oyuncu bir süre takılınca ses kendiliğinden yükselir, çatlak parlar, ekran kararır (kazanç ve bedel aynı anda).

**Rey ile oynarken:**

#### ch02_echo_wall
**YANKI**
- tr: "Dinle... Taşın altında hâlâ bir şey nefes alıyor."
- en: "Listen... Something is still breathing beneath the stone."

**Ardo ile oynarken:**

_(Replik yok; aynı anda `chapter02.ardo_tracks` bildirimi çıkar — aşağıdaki listede.)_

### 3. Gizli oda *(isteğe bağlı)*

> Ne oluyor: Alt koridordaki ikinci, ipucusuz çatlak kırılınca ('Gizli oda açıldı'). İçeride bir iskelet — sahibinin kim olduğu B4'te anlaşılacak.

**Rey ile oynarken:**

#### ch02_echo_secret
**YANKI**
- tr: "Senden önce biri de bu sırrı aradı... sonra sesi kesildi."
- en: "Someone searched for this secret before you... then their voice went silent."

#### ch02_echo_bones
**YANKI**
- tr: "Senden önce biri gelmiş. Adını sonra öğreneceksin."
- en: "Someone came before you. You will learn his name later."

**Ardo ile oynarken:**

#### ch02_ardo_secret
**ARDO**
- tr: "Buradan daha önce biri geçmiş. Ama geri dönüş izi yok."
- en: "Someone came through here before. There are no tracks leading back."

### 4. Mini-boss odası — Şişmiş Olan

> Ne oluyor: Mini-boss odasına ilk girişte; kapı oyuncu içeri geçince kapanır. Boss ölünce silah seçimi ekranı açılır ve anahtar düşer.

**Rey ile oynarken:**

#### ch02_echo_boss
**YANKI**
- tr: "Bu yaratık seni bekliyordu... sanki geleceğini biliyordu."
- en: "This creature was waiting for you... as if it knew you would come."

**Ardo ile oynarken:**

#### ch02_ardo_boss
**ARDO**
- tr: "Zaman onu değiştirmiş. Karanlık da geriye kalan ne varsa büyütmüş."
- en: "Time changed it. The darkness fed on what remained."

### 5. Çıkış — ikinci tırmık izi

> Ne oluyor: Son odaya girişte: duvarda Cemo boyunda, daha derin ikinci tırmık izi (kamera bir an oyalanır). Kapı anahtarla açılır; bölüm sonu ekranından sonra Bölüm 3.

**Rey ile oynarken:**

#### ch02_rey_claw2
**REY**
- tr: "Bu izler... Son ana kadar direnmiş."
- en: "These marks... They fought until the end."

#### ch02_echo_exit
**YANKI**
- tr: "Henüz bitmedi."
- en: "Not yet."

**Ardo ile oynarken:**

#### ch02_ardo_claw2
**ARDO**
- tr: "Tırnak izleri... Son ana kadar direnmiş."
- en: "Claw marks... They fought until the very end."

#### ch02_ardo_exit
**ARDO**
- tr: "İzler daha derine gidiyor. Onu buradan öteye götürmüşler."
- en: "The trail goes deeper. They took them beyond this place."

### Ekran yazıları — Bölüm 2

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.first_descent
_Bölüm kartı / kayıt yuvası adı_
- tr: "İlk İniş"
- en: "First Descent"

#### ability.dodge
_Bölüm başında kaçınma açılınca (yetenek bildirimi)_
- tr: "KAÇINMA  ·  [{key}] ile atıl"
- en: "DODGE  ·  dash with [{key}]"

#### chapter02.ardo_tracks
_Ardo ile: Yankı odasında, Yankı repliğinin yerine_
- tr: "Duvarda bir çatlak — iz sürüldü"
- en: "A crack in the wall - tracked"

#### chapter02.secret_found
_Gizli oda duvarı kırılınca_
- tr: "Gizli oda açıldı"
- en: "Hidden room opened"

#### chapter02.gold_found
_Sandık açılınca ({count} = altın)_
- tr: "{count} altın"
- en: "{count} gold"

#### boss.bloated_one
_Mini-boss can barındaki ad_
- tr: "ŞİŞMİŞ OLAN"
- en: "THE BLOATED ONE"

#### chapter02.boss_gold
_Mini-boss ölünce_
- tr: "{count} altın"
- en: "{count} gold"

#### hint.inventory_title
_İkinci silah alınınca bir kez açılan mekanik kartının başlığı_
- tr: "ENVANTER"
- en: "INVENTORY"

#### hint.inventory
_Aynı kartın gövdesi ({key} = atanmış tuş)_
- tr: "[{key}] envanter — silah değiştir"
- en: "[{key}] inventory — switch weapon"

#### chapter02.door_locked
_Anahtarsız kilitli kapıya dokununca (B3'te de)_
- tr: "Kilitli. Bir anahtar gerek."
- en: "Locked. A key is needed."

#### chapter02.key_taken
_Anahtar alınınca (B3'te de)_
- tr: "ANAHTAR ALINDI  ·  çıkış açıldı"
- en: "KEY TAKEN  ·  the exit is open"

---

## Bölüm 3 — Meşale Mahzeni

**Özet:** Zifiri karanlık bir mahzen: ışık taşımak ve meşale ekonomisi. Gizli bir cepte konuşmayan tüccar Mum Bekçisi, alınıp alınmaması oyuncuya kalmış Mor Alev, sonda mini-boss Sönmüş Olan.

### 1. Işığın kuralı

> Ne oluyor: İlk odaya girişte (tek bir meşale yanıyor, gerisi karanlık).

**Rey ile oynarken:**

#### ch03_echo_enter
**YANKI**
- tr: "Gözlerimiz bile bu karanlığı delemez. Bir kıvılcım lazım."
- en: "Even our sight cannot pierce this darkness. We need a spark."

**Ardo ile oynarken:**

#### ch03_ardo_enter
**ARDO**
- tr: "Karanlık burada yoğun. Ateş olmadan ilerleyemeyiz."
- en: "The darkness is thick here. We won't get far without fire."

### 2. Mum Bekçisi *(isteğe bağlı — gizli cep)*

> Ne oluyor: Üçüncü odanın (yuva bulmacası) üst tarafındaki kırılabilir duvarın arkasındaki cepte, Bekçi'ye ilk yaklaşınca. Bekçi'nin kendisi konuşmaz; tepki oyuncunun. Etkileşim tuşuyla ticaret ekranı açılır. Mor Alev alındıysa Bekçi tepki vermez.

**Rey ile oynarken:**

#### ch03_echo_keeper
**YANKI**
- tr: "Bana bakmıyor... seni tanıyor."
- en: "It isn't looking at me... It recognizes you."

**Ardo ile oynarken:**

#### ch03_ardo_keeper
**ARDO**
- tr: "Saldırmaya hazırlanmıyor. Bir şey istiyor."
- en: "It's not preparing to attack. It wants something."

### 3. Mor Alev *(alması isteğe bağlı)*

> Ne oluyor: Beşinci odaya girince kelimesiz bir ara sahne oynar. Alev etkileşim tuşuyla alınırsa meşale bırakılır, Yankı bir kademe güçlenir ve bu replik gelir (B14'teki dönüşün tohumu). Bölüm sonu ekranında 'Mor Alev: alındı / bırakıldı' satırı var.

**Rey ile oynarken:**

#### ch03_echo_purple
**YANKI**
- tr: "Evet... Bu alev yalnızca bizi beslemiyor."
- en: "Yes... This flame feeds more than us."

**Ardo ile oynarken:**

#### ch03_ardo_purple
**ARDO**
- tr: "Bu alev doğal değil. Yüzyıllardır aynı şekilde yanıyor."
- en: "This flame isn't natural. It's burned the same way for centuries."

### 4. Sönmüş Olan

> Ne oluyor: Son odaya (arena) ilk girişte; kapı oyuncu içeri geçince kapanır. Boss ölünce çıkış açılır, ardından Bölüm 4.

**Rey ile oynarken:**

#### ch03_echo_boss
**YANKI**
- tr: "Bu beden bir zamanlar ışık taşıyordu... şimdi yalnızca kabuğu kalmış."
- en: "This vessel once carried light... now only the shell remains."

**Ardo ile oynarken:**

#### ch03_ardo_boss
**ARDO**
- tr: "İçindeki ışık sönmüş. Geriye sadece çürümüş bir kabuk kalmış."
- en: "The light inside it is gone. Only a rotting shell remains."

### Ekran yazıları — Bölüm 3

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.torch_crypt
_Bölüm kartı / kayıt yuvası adı_
- tr: "Meşale Mahzeni"
- en: "The Torch Crypt"

#### chapter03.puzzle_solved
_Üçüncü odada beş meşale yuvasının hepsi yanınca_
- tr: "Beş yuva da yanıyor"
- en: "All five sconces are lit"

#### chapter03.pocket_open
_Gizli cebin duvarı kırılınca_
- tr: "Gizli bir geçit açıldı"
- en: "A hidden passage opened"

#### chapter03.secret_found
_Gizli cepteki sandık açılınca_
- tr: "Mum Bekçisi'nin odası açıldı"
- en: "The Candle Keeper's chamber opened"

#### chapter03.gold_found
_Sıradan sandık açılınca_
- tr: "{count} altın"
- en: "{count} gold"

#### chapter03.trade_title
_Ticaret ekranının başlığı_
- tr: "MUM BEKÇİSİ"
- en: "THE CANDLE KEEPER"

#### chapter03.trade_owned
_Ticaret ekranında zaten alınmış malın yanında_
- tr: "alındı"
- en: "owned"

#### chapter03.bought_item
_Bir şey satın alınınca ({name}, {count})_
- tr: "{name} alındı — elinde {count}"
- en: "{name} bought — you have {count}"

#### chapter03.already_bought
_Zaten alınmış bir mal seçilince_
- tr: "Zaten aldın"
- en: "Already bought"

#### chapter03.not_enough_gold
_Altın yetmeyince_
- tr: "Yetersiz altın"
- en: "Not enough gold"

#### hint.throw_title
_Fırlatılabilir malzeme ilk kez alınınca açılan kartın başlığı_
- tr: "UZAKTAN DÖVÜŞ"
- en: "RANGED COMBAT"

#### hint.throw
_Aynı kartın gövdesi_
- tr: "{key} ile seçili malzemeyi fırlat"
- en: "{key} to throw the selected item"

#### chapter03.purple_taken
_Mor Alev alınınca_
- tr: "Alev ellerinde."
- en: "The flame is in your hands."

#### chapter03.brazier_snuffed
_Arenadaki mangal sönünce_
- tr: "Mangal söndü"
- en: "The brazier went out"

#### boss.extinguished_one
_Mini-boss can barındaki ad_
- tr: "SÖNMÜŞ OLAN"
- en: "THE EXTINGUISHED ONE"

#### chapter03.boss_gold
_Mini-boss ölünce_
- tr: "{count} altın · Fener tılsımı"
- en: "{count} gold · Lantern charm"

---

## Bölüm 4 — Kayıt Odası

**Özet:** Dövüşsüz bir nefes bölümü: önceki maceracının terk edilmiş kampı — iskelet, kelimesiz günlük, yarım harita. Kampta dinlenince ilk yetenek puanı ve yetenek ağacı; sonda Rey kolyeyi ilk kez çevirir ve çıkışta Jet'le yeniden karşılaşılır.

### 1. İniş

> Ne oluyor: İlk odaya girişte.

**Rey ile oynarken:**

#### ch04_echo_enter
**YANKI**
- tr: "Burada yaşam çoktan sustu."
- en: "Life went silent here long ago."

**Ardo ile oynarken:**

#### ch04_ardo_enter
**ARDO**
- tr: "Burada kan yok. Sadece bekleyişin izleri var."
- en: "No blood here. Only signs of someone waiting."

### 2. Kamp

> Ne oluyor: İkinci odaya (kamp) girişte. Odada soldan sağa: duvara yaslanmış iskelet, sönmüş ateş (etkileşimle dinlenilir → can dolar, ilk yetenek puanı, yetenek ağacı açılır) ve kelimesiz resimli günlük (yaklaşınca sayfalar kendiliğinden çevrilir).

**Rey ile oynarken:**

#### ch04_echo_camp
**YANKI**
- tr: "Burada birileri kamp kurmuş. İkisi inmiş, biri kalkmış."
- en: "Someone camped here. Two came down, one got up."

**Ardo ile oynarken:**

#### ch04_ardo_camp
**ARDO**
- tr: "Burada durmuşlar. Sonra biri tek başına devam etmiş."
- en: "They stopped here. Then one went on alone."

### 3. İskeletin hatırası *(Yankı Görüşü / İz Sürme açıkken)*

> Ne oluyor: İskeletin başında Rey Yankı Görüşü'nü, Ardo İz Sürme'yi açınca kampın sahibinin yüzü mor bir hatıra olarak belirir, altında adı yazar. ⚠ Aşağıdaki iki replik kodda tetikleniyor ama **ekrana hiç gelmiyor**: `chapter04.py` `self.say(self._voice(...))` diyor, `_voice` bir şey döndürmediği için hemen ardından `say(None)` repliği siliyor (çalıştırılarak doğrulandı — bkz. Denetim).

#### kalachev_name
**YAZI — hatıra portresinin altındaki ad**
- tr: "E. KALACHEV"
- en: "E. KALACHEV"

**Rey ile oynarken:**

#### ch04_echo_name
**YANKI**
- tr: "Günlük Kalachev'in. Ama neyse ki kemikler onun değil; geride bıraktığı dostunun."
- en: "Kalachev's journal. Thankfully, those bones belong to the friend he left behind."

**Ardo ile oynarken:**

#### ch04_ardo_name
**ARDO**
- tr: "Kalachev'in kampı. İki kişi gelmişler. Giden tek bir çift ayak izi."
- en: "Kalachev's camp. Two came in. Only one set of tracks leads out."

### 4. Yarım harita

> Ne oluyor: Üçüncü odada (kırık merdiven) yüksekteki çıkıntıda duran haritaya dokununca: 'YARIM HARİTA' bildirimi ve replik.

**Rey ile oynarken:**

#### ch04_echo_map
**YANKI**
- tr: "Eksik olan yer... haritanın göstermeye korktuğu yer."
- en: "The missing part... is the place the map was afraid to show."

**Ardo ile oynarken:**

#### ch04_ardo_map
**ARDO**
- tr: "Haritanın yarısını çizmiş. Gerisini çizmeye vakti olmamış."
- en: "He drew half the map. Never had time for the rest."

### 5. Eşik

> Ne oluyor: Son odaya girişte.

**Rey ile oynarken:**

#### ch04_echo_exit
**YANKI**
- tr: "Yeterince bekledin. Artık yol seni bekliyor."
- en: "You've waited long enough. The path is waiting."

**Ardo ile oynarken:**

#### ch04_ardo_exit
**ARDO**
- tr: "Dinlenmek için fazla derindeyiz."
- en: "We're too deep to stop now."

### 6. Kolye anı

> Ne oluyor: Eşik odasının ortasında Rey kolyeyi ilk kez çevirir — kelimesiz, oynanış durmaz. An sürerken Yankı sorar: Cemo'nun B1'deki kolye cümlesine ilk gönderme (tohum 1/3).

**Rey ile oynarken:**

#### ch04_echo_seed
**YANKI**
- tr: "İki kez düşündü mü?"
- en: "Did it think twice?"

**Ardo ile oynarken:**

_(Bu anda replik yok — Ardo'nun Yankı'sı yok.)_

### 7. Jet'in dönüşü

> Ne oluyor: Çıkışa varınca, bölüm sonu ekranından önce. Kayıt yuvası başına bir kez (görüldükten sonra tekrar oynamaz). Jet sağdan gelir; son replik Jet'in yakın planı.

#### ch04_jet_return
**JET**
- tr: "Doğu yolu buraya çıkıyormuş. Dönüş için ip bıraktım."
- en: "The eastern path led here. I left a rope for the way back."

**Rey ile oynarken:**

#### ch04_rey_jet_return
**REY**
- tr: "Geri dön, Jet. Burası sandığın gibi değil."
- en: "Go back, Jet. This place is worse than you think."

**Ardo ile oynarken:**

#### ch04_ardo_jet_return
**ARDO**
- tr: "Doğuya gidiyordun. Yine kestirme mi buldun?"
- en: "You were heading east. Another shortcut?"

**İki karakterde de:**

#### ch04_jet_route
**JET**
- tr: "Senin yolun aşağıdan. Merak etme. Ben yukarıyı açık tutarım."
- en: "Your way is down below. Don't worry. I'll keep the way up clear."

#### ch04_jet_promise
**JET**
- tr: "Çocuğu bulunca birlikte dönün. İp sağlam."
- en: "When you find the child, come back together. The rope will hold."

### Ekran yazıları — Bölüm 4

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.record_room
_Bölüm kartı / kayıt yuvası adı_
- tr: "Kayıt Odası"
- en: "The Record Room"

#### chapter04.hint_rest
_Sönmüş ateşin yanına ilk gelişte ({key} = etkileşim tuşu)_
- tr: "{key} — ateşin başında dinlen"
- en: "{key} - rest by the fire"

#### chapter04.rested
_Dinlenince_
- tr: "Ateş yeniden yandı"
- en: "The fire is burning again"

#### chapter04.map_found
_Yarım harita alınınca_
- tr: "YARIM HARİTA"
- en: "HALF A MAP"

#### chapter04.gold_found
_Sandık açılınca_
- tr: "{count} altın"
- en: "{count} gold"

---

## Bölüm 5 — Sular

**Özet:** Su basmış mahzen ve vana bulmacası: suyu yükselt, yüzerek üste çık, indir, alttaki kapıyı aç. Su yükselirken karşı çıkıntıda Kalachev üç yaratığa dalar — ilk karşılaşma. Yeni düşman: Kalkanlı.

### 1. Eşik

> Ne oluyor: İlk odaya girişte.

**Rey ile oynarken:**

#### ch05_echo_enter
**YANKI**
- tr: "Su her şeyi saklar. Sırları bile."
- en: "Water hides everything. Even secrets."

**Ardo ile oynarken:**

#### ch05_ardo_enter
**ARDO**
- tr: "Zindanları su basmış. Mekanizmaların çoğu paslanmış."
- en: "The dungeons are flooded. Most of the mechanisms have rusted shut."

### 2. Vana odası

> Ne oluyor: İkinci odaya girişte (odanın uzak ucunda İzleyen belirir ve geri çekilir — korku katmanı).

**Rey ile oynarken:**

#### ch05_echo_valve
**YANKI**
- tr: "Çevir onu... Su bazen yol açar. Bazen de mezar."
- en: "Turn it... Water can open a path. Or become a grave."

**Ardo ile oynarken:**

#### ch05_ardo_valve
**ARDO**
- tr: "Eski bir vana. Hâlâ çalışıyorsa suyun yönünü değiştirebiliriz."
- en: "An old valve. If it still works, we can redirect the water."

### 3. Kalachev — ilk görüş

> Ne oluyor: Su yükselmeye başlayıp oyuncu karşıdaki çıkıntıya ~13 tile yaklaşınca: Kalachev çıkıntıda üç yaratığa dalar ve sahne açılır (iki kıyı arasında akan su). Kayıt yuvası başına bir kez. Rey onu tanımıyor (adını B6'da Ardo'dan öğrenecek); Ardo eski dostuna 'Efe' diye seslenir. Son panelde Kalachev sürüye atılır, dövüş oynanışta sürer.

**Rey ile oynarken:**

*Bakışma*

#### ch05_rey_kalachev_call
**REY**
- tr: "Hey! Sen... canlısın, değil mi?"
- en: "Hey! You're... alive, aren't you?"

#### ch05_kalachev_quiet
**KALACHEV**
- tr: "Şimdilik. Şimdi kes o lanet sesini!şu piçler de duyuyor."
- en: "For now. Shut your damn mouth! Those bastards can hear you."

*Yakın plan*

#### ch05_rey_kalachev_child
**REY**
- tr: "Bir çocuk arıyorum. Buralardan geçti mi?"
- en: "I'm looking for a child. Did he come this way?"

#### ch05_kalachev_valve
**KALACHEV**
- tr: "Görmedim. Üst vanaya çık. Geçit oradan açılır."
- en: "Haven't seen him. The upper valve opens the passage."

*Karar*

#### ch05_rey_kalachev_stay
**REY**
- tr: "Ya sen? Kafasındaki seslerle konuşan ben değilim"
- en: "What about you? I'm not the one talking to voices in my head."

#### ch05_kalachev_pack
**KALACHEV**
- tr: "Önce şu üçüyle ufak bir işim var *sinsice sırıtır*."
- en: "I've got a little business with those three first. *grins slyly*"

**Ardo ile oynarken:**

*Bakışma*

#### ch05_ardo_kalachev_call
**ARDO**
- tr: "Efe! Seni gördüğümde sevinsem mi üzülsem mi bilemedim haha! Seni bulmak için gürültüyü izlemek yetiyor."
- en: "Efe! Can't tell if I'm glad to see you, haha! All I have to do is follow the noise."

#### ch05_kalachev_late
**KALACHEV**
- tr: "İş bittikten sonra gelmenin ne anlamı var lanet adam?"
- en: "What's the point of showing up when the work's done, you damn fool?"

*Yakın plan*

#### ch05_ardo_kalachev_pack
**ARDO**
- tr: "Üçüne birden mi dalacaksın?"
- en: "All three at once?"

#### ch05_kalachev_count
**KALACHEV**
- tr: "Saymayı bırak da üst vanaya git."
- en: "Stop counting. Get to the upper valve."

*Karar*

#### ch05_ardo_kalachev_back
**ARDO**
- tr: "Sana arkanı kollayacak biri lazım."
- en: "You need someone watching your back."

#### ch05_kalachev_below
**KALACHEV**
- tr: "O zaman buradan canlı kurtulmaya çalış bence haha. Aşağıda görüşürüz."
- en: "Then try getting out of here alive, haha. See you below."

### 4. Alt geçit — Kalkanlı

> Ne oluyor: Üçüncü odaya girişte; Kalkanlı görünmeden önce tanıtılıyor.

**Rey ile oynarken:**

#### ch05_echo_guard
**YANKI**
- tr: "Bu sadece bir ceset değil... içinde hâlâ bir şey uyanık."
- en: "This is more than a corpse... something inside is still awake."

**Ardo ile oynarken:**

#### ch05_ardo_guard
**ARDO**
- tr: "Eski bir muhafız. Karanlık onu yeniden ayağa kaldırmış."
- en: "An old guardian. The darkness brought it back."

### 5. Kalkan ilk kez blokladığında

> Ne oluyor: Oyuncunun vuruşu Kalkanlı'nın kalkanına ilk kez çarpınca (bir kez).

**Rey ile oynarken:**

#### ch05_echo_block
**YANKI**
- tr: "Kalkanına güveniyor. Bu onun zayıflığı."
- en: "It trusts its shield. That's its weakness."

**Ardo ile oynarken:**

#### ch05_ardo_block
**ARDO**
- tr: "Kalkanı ağır. Önünden değil, arkasından vur."
- en: "The shield is heavy. Don't fight it from the front. Get behind it."

### Ekran yazıları — Bölüm 5

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.waters
_Bölüm kartı / kayıt yuvası adı_
- tr: "Sular"
- en: "The Waters"

#### chapter05.valve_turned
_Vana çevrilince_
- tr: "Vana çevrildi · su hareket ediyor"
- en: "Valve turned · the water moves"

#### chapter05.chest_found
_Gizli sandık açılınca_
- tr: "Gizli sandık · {count} altın"
- en: "Hidden chest · {count} gold"

---

## Bölüm 6 — ARDO

**Özet:** Oyuncu köşeye sıkışır; öteki karakter yukarıdan düşüp üç yaratığı biçer — 'havalı giriş' ve tanışma. Kalachev de oradadır. Sonra ilk ortak dövüş, iki kişilik ağırlık plakaları ve ilk büyük boss Çürümüş Olan.

### 1. Havalı giriş ve tanışma

> Ne oluyor: Bölümün ilk odasında (köşe) üç yaratık oyuncuyu sıkıştırır; kısa bir gecikmeden sonra öteki karakter yukarıdan düşer, yaratıkları biçer ve ara sahne açılır (Ardo.mp3). Roller seçime bağlı: Rey ile oynarken köşedeki Rey, düşen Ardo; Ardo ile oynarken köşedeki Ardo, düşen Rey. Bakışmada ikisinin arasında bir soru işareti; ardından kurtaranın yüzü (yakın plan). *Neden / Geçmiş / Tereddüt / Güven* kısmı iki oynanışta aynı.

**Rey ile oynarken (düşen Ardo):**

*Bakışma*

#### ch06_meet_ardo_first
**ARDO**
- tr: "Üçü de arkandaydı. Arkanı hiç kollamıyorsun."
- en: "All three were behind you. You never watch your back."

*Soru*

#### ch06_meet_rey_who
**REY**
- tr: "Sen kimsin?"
- en: "Who are you?"

*İsim*

#### ch06_meet_ardo_name
**ARDO**
- tr: "Ardo. Ve buraya kadar inen tek şey ben değilim."
- en: "Ardo. And I'm not the only thing that came down this far."

*İz*

#### ch06_meet_rey_child
**REY**
- tr: "Ben Rey. Kardeşim Cemo'yu götürdüler. Onu kurtarmaya gidiyorum!"
- en: "I'm Rey. They took my brother, Cemo. I'm going to save him!"

#### ch06_meet_ardo_trail
**ARDO**
- tr: "İzini buraya kadar mı sürdün?"
- en: "You followed his trail down here?"

#### ch06_meet_rey_below
**REY**
- tr: "Buraya kadar. Aşağıda olduğunu biliyorum."
- en: "This far. I know he's below us."

**Ardo ile oynarken (düşen Rey):**

*Bakışma*

#### ch06_meet_rey_first
**REY**
- tr: "Üçü de arkandaydı. Bir tanesini duymadın bile."
- en: "All three were behind you. You didn't even hear one of them."

*Soru*

#### ch06_meet_ardo_who
**ARDO**
- tr: "Sen kimsin?"
- en: "Who are you?"

*İsim*

#### ch06_meet_rey_name
**REY**
- tr: "Rey. Kardeşimi arıyorum."
- en: "Rey. I'm looking for my brother."

*İz*

#### ch06_meet_ardo_child
**ARDO**
- tr: "Kardeşin... Adı ne?"
- en: "Your brother... What's his name?"

#### ch06_meet_rey_trail
**REY**
- tr: "Cemo. İzini bu kata kadar sürdüm."
- en: "Cemo. I followed his trail to this floor."

#### ch06_meet_ardo_below
**ARDO**
- tr: "O zaman aşağıya bakacağız."
- en: "Then we'll look below."

**İki karakterde de:**

*Neden*

#### ch06_meet_rey_reason
**REY**
- tr: "Sen ne arıyorsun burada?"
- en: "What are you looking for down here?"

*Geçmiş — Ardo'nun yakın planı*

#### ch06_meet_ardo_reason
**ARDO**
- tr: "Yarım bıraktığım bir şey var."
- en: "Something I left unfinished."

*Tereddüt*

#### ch06_meet_rey_help
**REY**
- tr: "Bana yardım etmek zorunda değilsin."
- en: "You don't have to help me."

#### ch06_meet_ardo_choice
**ARDO**
- tr: "Biliyorum. Ama şu an ikimiz de aynı yöne gidiyoruz."
- en: "I know. But we're heading the same way for now."

*Güven*

#### ch06_meet_rey_follow
**REY**
- tr: "Önden gidersen yetişirim."
- en: "Go ahead. I'll keep up."

#### ch06_meet_ardo_together
**ARDO**
- tr: "Yanımda kal. Birinin de benim arkamı kollaması lazım."
- en: "Stay beside me. Someone has to watch my back, too."

### 2. Kalachev ile tanışma

> Ne oluyor: Giriş sahnesi biter bitmez ikinci sahne: biraz ötede duran Kalachev yaklaşır, bakışma, yüzünün yakın planı. Rey için bir tanışma (onu Ardo tanıtır), Ardo için eski bir dost. Ölüp yeniden denenirse tekrar oynamaz.

**Rey ile oynarken:**

*Bakışma*

#### ch06_kalachev_ardo_intro
**ARDO**
- tr: "Kalachev. Eski dostum. Yolundan çekil."
- en: "Kalachev. Old friend. Get out of his way."

*Yakın plan*

#### ch06_kalachev_rey_ask
**REY**
- tr: "Bizimle mi geliyor?"
- en: "Is he coming with us?"

#### ch06_kalachev_ardo_stay
**ARDO**
- tr: "Yolumuz kesişirse artık. Bu ibne de kimseyi beklemez."
- en: "If our paths cross. That fucker doesn't wait for anyone."

#### ch06_kalachev_meet
**KALACHEV**
- tr: "Tanışma bittiyse yol açık."
- en: "Done talking? The way's clear."

#### ch06_echo_kalachev
**YANKI**
- tr: "Ardo'yu tanıyor. Seni değil."
- en: "He knows Ardo. Not you."

**Ardo ile oynarken:**

*Bakışma*

#### ch06_ardo_kalachev
**ARDO**
- tr: "Kalachev. SAnırım kurtarma konusunda ödeşmiş olduk ha?"
- en: "Kalachev. Guess that makes us even on the rescues, huh?"

#### ch06_kalachev_familiar
**KALACHEV**
- tr: "O kadar bekleyemem."
- en: "Can't wait that long."

*Yakın plan*

#### ch06_kalachev_ardo_know
**ARDO**
- tr: "Hâlâ borçlusun bana. Unutmadım."
- en: "You still owe me. I haven't forgotten."

#### ch06_kalachev_debt
**KALACHEV**
- tr: "Yukarıda hallederiz. Önce buradan çık."
- en: "We'll settle up topside. Get out of here first."

### 3. Plaka odası

> Ne oluyor: Üçüncü odaya girişte: iki ağırlık plakası; ikisi aynı anda basılı kalmalı (yoldaşa etkileşim tuşuyla 'plakaya bas' emri).

**Rey ile oynarken:**

#### ch06_rey_plates
**REY**
- tr: "İki plaka... Birinin diğerine yardım etmesi gerekiyor."
- en: "Two plates... Someone has to hold the other one."

**Ardo ile oynarken:**

#### ch06_ardo_plates
**ARDO**
- tr: "İki plaka. Tek kişiyle çalışmaz."
- en: "Two plates. One person won't be enough."

### 4. Arena — Çürümüş Olan

> Ne oluyor: Son odaya girişte, boss belirir. Vuruşlar mühre işlemez; plakalarla mühür kırılınca boss savunmasız kalır. Boss düşünce bölüm sonu ekranı, ardından Bölüm 7'nin açılış sahnesi.

**Rey ile oynarken:**

#### ch06_rey_arena
**REY**
- tr: "Bu varlık diğerlerine benzemiyor..."
- en: "This thing isn't like the others..."

**Ardo ile oynarken:**

#### ch06_ardo_arena
**ARDO**
- tr: "Bunun izi yok. Hiçbir yerden gelmemiş — burada mı büyümüş lan?."
- en: "No trail. It didn't come from anywhere — did it grow here, damn it?"

### Ekran yazıları — Bölüm 6

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.ardo
_Bölüm kartı / kayıt yuvası adı_
- tr: "ARDO"
- en: "ARDO"

#### hint.companion_wait_title
_Yoldaş ilk kez yanındayken bir kez açılan kartın başlığı_
- tr: "YOLDAŞA KOMUT"
- en: "COMPANION ORDER"

#### hint.companion_wait
_Aynı kartın gövdesi_
- tr: "[{key}] yoldaşa: burada bekle"
- en: "[{key}] tell them to wait here"

#### chapter06.plate_hint
_Tek plakaya basılı kalınca_
- tr: "Plaka basılı kaldı — ikisi birden gerek"
- en: "The plate stayed down — both are needed"

#### chapter06.gate_open
_İki plaka birden basılınca_
- tr: "Kapı açıldı"
- en: "The gate opened"

#### boss.rotted_one
_Boss can barındaki ad_
- tr: "ÇÜRÜMÜŞ OLAN"
- en: "THE ROTTED ONE"

#### chapter06.seal_hint
_Mühürlü boss'a vuruş işlemeyince_
- tr: "Vuruşlar işlemiyor. Plakalar…"
- en: "The blows do nothing. The plates…"

#### chapter06.seal_broken
_Mühür kırılınca_
- tr: "Mühür kırıldı — şimdi!"
- en: "The seal broke — now!"

#### chapter06.companion_down
_Yoldaş dövüşte diz çökünce (B7'de de)_
- tr: "Diz çöktü — toparlanacak"
- en: "Down — but getting up"

#### chapter06.boss_down
_Boss düşünce_
- tr: "Çürümüş Olan düştü — {count} altın"
- en: "The Rotted One has fallen — {count} gold"

#### chapter06.chest_found
_Gizli sandık açılınca_
- tr: "Gizli sandık — {count} altın"
- en: "Hidden chest — {count} gold"

---

## Bölüm 7 — Dar Geçit

**Özet:** Tek kişilik bir çatlak: Ardo geçemez, Rey geçer ve öbür taraftan çarkı çevirip kapıyı açar. Ardından ilk fiziksel temas — uçurumun kenarında uzatılan el, bilerek kelimesiz.

### 1. Mühür — açılış sahnesi

> Ne oluyor: B6'nın bölüm sonu ekranından sonra, Bölüm 7 başlamadan: iki siluet karanlıkta yürür, meşale yanınca mühürlü kapı görünür. Replik oynanan karakterin.

**Rey ile oynarken:**

#### ch07_rey_seal
**REY**
- tr: "Mühür... Bu kapıyı biri kapatmış. İçeriden."
- en: "A seal... Someone shut this door. From the inside."

**Ardo ile oynarken:**

#### ch07_ardo_seal
**ARDO**
- tr: "Muhafız mührü. Aşağıdakiler kendilerini içeri kilitlemiş."
- en: "A guardian seal. Whatever is down there locked itself in."

### 2. Kapının önü

> Ne oluyor: Bölüm başlayınca ilk odada.

**Rey ile oynarken:**

#### ch07_rey_door
**REY**
- tr: "Kapı açılmıyor. Ama duvar çatlamış — orada bir aralık var."
- en: "The door won't open. But the wall is cracked — there's a gap."

**Ardo ile oynarken:**

#### ch07_ardo_door
**ARDO**
- tr: "Bu kapı bu taraftan açılmaz. Kolu öbür tarafta olmalı."
- en: "This door won't open from here. The lever must be on the far side."

### 3. Sığmıyor *(kelimesiz)*

> Ne oluyor: Çatlaktan her zaman Rey geçer (kanon bedene bağlı). Ardo ile oynarken oyuncu Rey'i etkileşim tuşuyla çatlağa gönderir. Geniş omuzlu karakter çatlağa birkaç kez takılınca kısa bir ara sahne oynar; ilk takılmada 'Bu aralıktan geçemezsin' bildirimi.

_(Bu anda replik yok.)_

### 4. Öbür taraf — yalnız

> Ne oluyor: Çatlaktan geçilince (Rey ile oyuncunun kendisi, Ardo ile gönderilen Rey) ara sahne: arkasına bakar, yalnızdır; vinyet kapanır.

**Rey ile oynarken:**

#### ch07_rey_alone
**REY**
- tr: "Öbür taraftayım. Sesler hâlâ benimle... ama o değil."
- en: "I'm on the other side. The voices are still with me... but he isn't."

**Ardo ile oynarken:**

#### ch07_ardo_alone
**ARDO**
- tr: "Geçti. Bu sefer bekleyen benim."
- en: "She's through. This time I'm the one waiting."

### 5. El *(kelimesiz)*

> Ne oluyor: Çark çevrilip kapı açılınca yoldaş yetişir; uçurumun kenarına gelince ara sahne: Ardo elini uzatır, Rey tutar — eller birleştikten sonra bir saniye fazla tutulur. Belgenin açık talimatı: balon yok, replik yok.

_(Bu anda replik yok.)_

### 6. Geçit — yine birlikte

> Ne oluyor: Dördüncü odaya girişte.

**Rey ile oynarken:**

#### ch07_rey_together
**REY**
- tr: "Yine yanımda."
- en: "Beside me again."

**Ardo ile oynarken:**

#### ch07_ardo_together
**ARDO**
- tr: "Beraber daha hızlı gideriz."
- en: "We move faster together."

### Ekran yazıları — Bölüm 7

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.narrow_pass
_Bölüm kartı / kayıt yuvası adı_
- tr: "Dar Geçit"
- en: "The Narrow Pass"

#### chapter07.gap_blocked
_Çatlağa ilk takılınca_
- tr: "Bu aralıktan geçemezsin"
- en: "You can't fit through this gap"

#### chapter07.order_hint
_Ardo ile: Rey'i çatlağa gönderme ipucu_
- tr: "[{key}] Rey'i dar geçitten gönder"
- en: "[{key}] Send Rey through the gap"

#### chapter07.door_open
_Çark çevrilip kapı açılınca_
- tr: "Kapı açıldı"
- en: "The door is open"

---

## Bölüm 8 — Ateş Başı

**Özet:** Dövüşsüz bir nefes: ateş başında yara sarma, kolye ve Yankı Rezonansı dersi (sesi silah olarak kullanmak). Kristaller kırılır, mandal açılır; bölüm sonunda Yankı ilk kez yoldaş hakkında fısıldar.

### 1. Ateş başı

> Ne oluyor: İlk odada ateşin yanına varınca ara sahne (Raze): iki siluet oturur, yoldaşın yarası sarılır, kolye çevrilir, sonra rezonans dersi. Sahne bitince Rezonans açılır ve Yankı bir kademe güçlenir. *Ders* kısmı iki oynanışta aynı: öğreten Ardo, öğrenen Rey.

**Rey ile oynarken:**

*Yara*

#### ch08_fire_ardo_wound
**ARDO**
- tr: "Omzum. Düşerken taşa çarpmışım — önemli değil."
- en: "My shoulder. Caught a rock on the way down — it's nothing."

*Kolye*

#### ch08_fire_rey_necklace
**REY**
- tr: "Cemo bunu bana verdi. Karanlık yaklaşırken iki kez düşünsün diye."
- en: "Cemo gave me this. So the dark would think twice."

**Ardo ile oynarken:**

*Yara*

#### ch08_fire_rey_wound
**REY**
- tr: "Omzum. Düşerken taşa çarpmışım — önemli değil."
- en: "My shoulder. Caught a rock on the way down — it's nothing."

*Kolye*

#### ch08_fire_ardo_necklace
**ARDO**
- tr: "Yukarıda bekleyen kimse yok. Bu yüzden aşağı inmek kolay oldu."
- en: "There's no one waiting up there. That made coming down easy."

**İki karakterde de:**

*Ders*

#### ch08_fire_ardo_teach
**ARDO**
- tr: "Bağırmak değil. Taşın kendi perdesini bulacaksın."
- en: "Not shouting. You find the stone's own pitch."

*Ders — cevap*

#### ch08_fire_rey_learn
**REY**
- tr: "Kafamdaki sesler bunu zaten biliyordu. Bana hiç söylemediler."
- en: "The voices in my head already knew that. They never told me."

### 2. Öğrenme

> Ne oluyor: İkinci odaya girişte (ilk kristal). Rezonans bir süre kullanılmazsa 'YANKI REZONANSI' kartı açılır.

**Rey ile oynarken:**

#### ch08_rey_learn
**REY**
- tr: "Şu kristal... titriyor. Sanki bir şey bekliyor."
- en: "That crystal... it's humming. Like it's waiting for something."

**Ardo ile oynarken:**

#### ch08_ardo_learn
**ARDO**
- tr: "Kristal ses tutuyor. Doğru perdede kırılır."
- en: "The crystal holds sound. It breaks at the right pitch."

### 3. Geçit

> Ne oluyor: Üçüncü odaya girişte: mandal duvarın arkasında.

**Rey ile oynarken:**

#### ch08_rey_gate
**REY**
- tr: "Yol kapalı. Ve kolun olduğu yere ulaşamıyorum."
- en: "The way's blocked. And I can't reach the lever."

**Ardo ile oynarken:**

#### ch08_ardo_gate
**ARDO**
- tr: "Mandal duvarın ardında. Elimiz yetmez — sesimiz yeter."
- en: "The latch is behind the wall. Our hands won't reach — our voice will."

### 4. Fısıltı

> Ne oluyor: Son odaya (çıkış) girince ara sahne; yoldaş sahnede yok. Rey'de Yankı ilk kez yoldaş hakkında konuşur ve Rey rahatsız olur (yüzüne kesme); Ardo'da aynı an İz Sürme ile: Rey'in izinin arkasında ikinci bir iz.

**Rey ile oynarken:**

#### ch08_echo_ardo
**YANKI**
- tr: "O da bizim gibi çağrıldı... ama onu çağıran şey senin duyduğun değil."
- en: "He was called down too... but the thing calling him isn't the one you hear."

#### ch08_echo_rey_react
**REY**
- tr: "Kes sesini. Onun hakkında konuşmanı istemedim."
- en: "Be quiet. I didn't ask you about him."

**Ardo ile oynarken:**

#### ch08_trace_ardo
**ARDO**
- tr: "İzinin arkasında ikinci bir iz var. Takip etmiyor — bekliyor."
- en: "There's a second trail behind hers. Not following — waiting."

#### ch08_trace_ardo_react
**ARDO**
- tr: "Bunu ona söylemeyeceğim. Henüz değil."
- en: "I won't tell her. Not yet."

### Ekran yazıları — Bölüm 8

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.fireside
_Bölüm kartı / kayıt yuvası adı_
- tr: "Ateş Başı"
- en: "The Fireside"

#### hint.resonance_title
_Rezonans bir süre kullanılmazsa açılan kartın başlığı_
- tr: "YANKI REZONANSI"
- en: "ECHO RESONANCE"

#### hint.resonance
_Aynı kartın gövdesi_
- tr: "[{key}] ses gönder — kristali kır"
- en: "[{key}] send sound — break crystals"

#### chapter08.first_crystal
_İlk kristal kırılınca_
- tr: "Kristal kırıldı — ses bir silah"
- en: "Crystal shattered — sound is a weapon"

#### chapter08.latch
_Mandal açılınca_
- tr: "Mandal açıldı"
- en: "The latch gave way"

---

## Bölüm 9 — Çan Kulesi

**Özet:** Dikey bir kule: yoldaş oyuncuyu platformlara fırlatır (güven), üç çan rezonansla doğru sırayla çalınır; sıranın ipucu taban kattaki freskte. Çıkışta Jet yine karşılar.

### 1. Kulenin tabanı

> Ne oluyor: Bölüm başında taban katta.

**Rey ile oynarken:**

#### ch09_rey_tower
**REY**
- tr: "Bir kule... ve içi boş. Yukarıda üç çan asılı."
- en: "A tower... and it's hollow. Three bells hanging up there."

**Ardo ile oynarken:**

#### ch09_ardo_tower
**ARDO**
- tr: "Çan kulesi. Yukarısı çökmüş ama merdiven yok — hiç olmamış."
- en: "A bell tower. The top has fallen in — and there were never any stairs."

### 2. Güven — fırlatma

> Ne oluyor: ~1,5 sn sonra ara sahne: yoldaş elini basamak yapmayı teklif eder, oyuncu kabul eder, fırlatılır; son panel oyuncunun yakın planı. Ardından 'BİRLİKTE TIRMANIŞ' kartı.

**Rey ile oynarken:**

#### ch09_trust_offer_ardo
**ARDO**
- tr: "Buradan atlayamazsın. Elimi basamak yap — seni ben kaldırırım."
- en: "You can't make that jump. Use my hands as a step — I'll lift you."

#### ch09_trust_accept_rey
**REY**
- tr: "Tamam. Bırakmazsın, değil mi?"
- en: "All right. You won't let go, will you?"

**Ardo ile oynarken:**

#### ch09_trust_offer_rey
**REY**
- tr: "Buradan atlayamazsın. Elimi basamak yap — seni ben kaldırırım."
- en: "You can't make that jump. Use my hands as a step — I'll lift you."

#### ch09_trust_accept_ardo
**ARDO**
- tr: "Tamam. Sıkı tut."
- en: "All right. Hold tight."

### 3. Yanlış sıra *(koşullu, ilk seferde)*

> Ne oluyor: Çanlar yanlış sırayla çalınınca hepsi susar ('Yanlış sıra...' bildirimi). İlk seferde Yankı teselli eder gibi Cemo'nun B1 sözünü kullanır (tohum 2/3).

**Rey ile oynarken:**

#### ch09_echo_seed
**YANKI**
- tr: "Bunu senin için yaptım."
- en: "I made this for you."

**Ardo ile oynarken:**

_(Bu anda replik yok — Ardo'nun Yankı'sı yok.)_

### 4. Tepe

> Ne oluyor: En üst kata ilk çıkışta. İki dal: çanlar **önceden** doğru sırayla çalındıysa oynanan karakterin repliği gelir; çalınmadıysa Yankı/iz uyarısı gelir ve aynı karede tepe repliğini ezer — tepe repliği o oynayışta hiç görünmez, çünkü kat anlatımı yalnızca ilk girişte oynuyor (bkz. Denetim).

**Çanlar önceden çözüldüyse:**

**Rey ile oynarken:**

#### ch09_rey_top
**REY** — _koşullu_
- tr: "Fresk doğruydu. Sıra buymuş."
- en: "The fresco was right. That was the order."

**Ardo ile oynarken:**

#### ch09_ardo_top
**ARDO** — _koşullu_
- tr: "Kapı sesi tanıdı. Doğru sıra."
- en: "The door recognised the sound. Right order."

**Çözülmeden çıkıldıysa (bir kez):**

**Rey ile oynarken:**

#### ch09_echo_locked
**YANKI**
- tr: "Kapı üç çan bekliyor. Hiçbiri çalmadı — aşağı in."
- en: "The door is waiting for three bells. None have rung — go back down."

**Ardo ile oynarken:**

#### ch09_trace_locked
**ARDO**
- tr: "Kapıda üç yuva var, üçü de boş. Çanlar aşağıda kaldı."
- en: "Three sockets in the door, all empty. The bells are below."

### 5. Jet'in dönüşü

> Ne oluyor: Çıkışta, bölüm sonu ekranından önce (kayıt yuvası başına bir kez). Arka planda çanlar; yoldaş da sahnede.

#### ch09_jet_return
**JET**
- tr: "Çanları yukarıdan da duydum. İp hâlâ yerinde."
- en: "I heard the bells from above. The rope is still there."

**Rey ile oynarken:**

#### ch09_rey_jet_return
**REY**
- tr: "Bizi beklemeni istemedim."
- en: "I never asked you to wait for us."

**Ardo ile oynarken:**

#### ch09_ardo_jet_return
**ARDO**
- tr: "Senin de bir gün söz dinlediğini göreceğim."
- en: "One day you might actually listen."

**İki karakterde de:**

#### ch09_jet_route
**JET**
- tr: "Bu galeriden yukarı çıkılıyor. Bir taş düşmüş; kaldırdım."
- en: "This gallery leads up. A stone had fallen. I moved it."

#### ch09_jet_promise
**JET**
- tr: "Acele etmeyin. Birinin beklediğini bilin yeter."
- en: "Take your time. Just know someone is waiting."

### Ekran yazıları — Bölüm 9

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.bell_tower
_Bölüm kartı / kayıt yuvası adı_
- tr: "Çan Kulesi"
- en: "The Bell Tower"

#### hint.boost_title
_Güven sahnesinden sonra açılan kartın başlığı_
- tr: "BİRLİKTE TIRMANIŞ"
- en: "CLIMB TOGETHER"

#### hint.boost
_Aynı kartın gövdesi_
- tr: "[{key}] yoldaşın yanında: seni fırlatır"
- en: "[{key}] beside them: they'll launch you"

#### chapter09.first_boost
_İlk fırlatmada_
- tr: "Yukarı — birlikte çıkılıyor"
- en: "Up — you climb together"

#### hint.bell_title
_Bir çana ilk yaklaşınca açılan kartın başlığı_
- tr: "ÇANI ÇAL"
- en: "RING THE BELL"

#### hint.bell
_Aynı kartın gövdesi_
- tr: "{key} ile sesini gonder — çanı çal"
- en: "{key} to send your voice — ring the bell"

#### chapter09.wrong_order
_Çanlar yanlış sırayla çalınınca_
- tr: "Yanlış sıra. Çanlar sustu — freske bak."
- en: "Wrong order. The bells fell silent — check the fresco."

#### chapter09.solved
_Üç çan doğru sırayla çalınınca_
- tr: "Üç çan, doğru sıra. Kapı açıldı."
- en: "Three bells, right order. The door is open."

---

## Bölüm 10 — Ayrılık

**Özet:** Yol ikiye ayrılır, yoldaş öbür yoldan gider; oyuncu yalnız kalır ve Yankı yükselir. Çatalda Yankı üst yolu gösterir — ilk kez yanlış bilgi, üst yolda çürük zemin var. Kalachev tuzağı önceden çökertir. Oyuncunun seçimi görünmeden kaydedilir ve Yalan sahnesinin tonunu belirler.

### 1. Ayrılık

> Ne oluyor: İlk odada yolların ayrıldığı noktayı geçince ara sahne: yoldaş işaret eder, yürür, bir kez dönüp bakar ve gider; son panelde yalnızlık (Rey'de Yankı, Ardo'da iz).

**Rey ile oynarken:**

*İşaret*

#### ch10_part_ardo
**ARDO**
- tr: "Yol ikiye ayrılıyor. Ben soldan bakarım, sen sağdan."
- en: "The path splits. I'll take the left, you take the right."

*Bakış*

#### ch10_part_look_rey
**REY**
- tr: "...Tamam."
- en: "...All right."

*Yalnız*

#### ch10_echo_rises
**YANKI**
- tr: "Gitti. Şimdi daha net duyuyorsun, değil mi?"
- en: "He's gone. You hear me more clearly now, don't you?"

**Ardo ile oynarken:**

*İşaret*

#### ch10_part_rey
**REY**
- tr: "Yol ikiye ayrılıyor. Ben soldan bakarım, sen sağdan."
- en: "The path splits. I'll take the left, you take the right."

*Bakış*

#### ch10_part_look_ardo
**ARDO**
- tr: "...Tamam."
- en: "...All right."

*Yalnız*

#### ch10_trace_rises
**ARDO**
- tr: "İzi soldan gidiyor. Benimki sağa dönüyor."
- en: "Her trail goes left. Mine turns right."

### 2. Yalnız

> Ne oluyor: İkinci odaya girişte.

**Rey ile oynarken:**

#### ch10_rey_alone
**REY**
- tr: "Yalnızım. Sesler her zamankinden yüksek."
- en: "Alone. The voices are louder than they've ever been."

**Ardo ile oynarken:**

#### ch10_ardo_alone
**ARDO**
- tr: "Yalnız. Tanıdık bir şey — ama artık rahatsız edici."
- en: "Alone. Familiar — but it doesn't sit right any more."

### 3. Çatal — Yankı üst yolu gösteriyor

> Ne oluyor: Üçüncü odaya (çatal) girince. Rey'de Yankı üst yolu önerir (yalan: üst yolda çürük zemin); Ardo'da iz aynı yolu gösterir.

**Rey ile oynarken:**

#### ch10_echo_lure
**YANKI**
- tr: "Yukarıdan. Yol açık — güven bana, hep açtım."
- en: "Up there. The way is clear — trust me, it always was."

**Ardo ile oynarken:**

#### ch10_trace_lure
**ARDO**
- tr: "İz yukarıyı gösteriyor. Taze, net, davetkâr."
- en: "The trail points up. Fresh, clear, inviting."

### 4. Kalachev tuzağı kırıyor

> Ne oluyor: Oyuncu tuzağın ~11 tile soluna gelince — **hangi yoldan gidilirse gitsin** (tetikleyicide satır kontrolü yok; çalıştırılarak doğrulandı): Kalachev belirir, üst yoldaki çürük zemini önceden çökertir ('Zemini biri çökertti...' bildirimi) ve kısa karşılaşma sahnesi oynar. Bu, seçim kaydedilmeden önce oluyor.

**Rey ile oynarken:**

#### ch10_rey_kalachev
**REY**
- tr: "Kalachev? Az önce oraya basacaktım."
- en: "Kalachev? I was about to step there."

#### ch10_kalachev_crack
**KALACHEV**
- tr: "Şimdi nereye basmayacağını biliyorsun."
- en: "Now you know where not to step."

**Ardo ile oynarken:**

#### ch10_ardo_kalachev
**ARDO**
- tr: "Kalachev. Yol aç dedim, uçurum değil."
- en: "Kalachev. I said clear a path, not dig a pit."

#### ch10_kalachev_detour
**KALACHEV**
- tr: "Geçersin. Daha kötülerinden geçtin."
- en: "You'll get across. You've crossed worse."

### 5. Alt yolu seçmek *(koşullu)*

> Ne oluyor: Oyuncu Yankı'yı dinlemeyip alt yoldan ilerleyince (görünmez sadakat sayacı bir düşer). Üst yolu seçene replik yok, sayaç bir artar.

**Rey ile oynarken:**

#### ch10_echo_ignored
**YANKI**
- tr: "...Aşağıdan mı? Peki. Nasıl istersen."
- en: "...Down there? Fine. Have it your way."

**Ardo ile oynarken:**

#### ch10_trace_ignored
**ARDO**
- tr: "İz fazla temiz. Kimse bu kadar düzgün yürümez."
- en: "That trail is too clean. Nobody walks that neatly."

### 6. Yalan

> Ne oluyor: Dördüncü odaya (ders) girince ara sahne: Yankı konuşur ve özür dilemez; oyuncunun tepkisi, son panel yüz. Çataldaki davranışa göre dört varyant. Tepki repliği iki karakterde aynı anahtar, oynanan karakter söyler.

**Üst yoldan geçtiyse (Yankı'yı dinledi) — normal akış:**

**Rey ile oynarken:**

#### ch10_lie_survived
**YANKI**
- tr: "Gördün mü? Geçtin işte. Ben yanılmam."
- en: "See? You made it. I'm never wrong."

**Ardo ile oynarken:**

#### ch10_trace_survived
**ARDO**
- tr: "Zemin çöktü. O iz oraya bir sebeple bırakılmış."
- en: "The floor gave way. That trail was left there for a reason."

**İki karakterde de:**

#### ch10_lie_survived_react
**OYUNCU — Rey ile REY, Ardo ile ARDO**
- tr: "Zemin çöktü. Az kalsın altında kalıyordum."
- en: "The floor gave way. It nearly took me with it."

**Alt yoldan geçtiyse (dinlemedi):**

**Rey ile oynarken:**

#### ch10_lie_ignored
**YANKI**
- tr: "Beni dinlemedin. Uzun yoldan geldin ve yoruldun."
- en: "You didn't listen. You took the long way and tired yourself."

**Ardo ile oynarken:**

#### ch10_trace_ignored_after
**ARDO**
- tr: "Doğru okumuşum. İz fazla temizdi."
- en: "I read it right. That trail was too clean."

**İki karakterde de:**

#### ch10_lie_ignored_react
**OYUNCU — Rey ile REY, Ardo ile ARDO**
- tr: "Ama geldim. Kendi ayaklarımla."
- en: "But I got here. On my own feet."

**Seçim kaydedilmediyse (iki yolun koşulunu da tutturmadan geçmek — nadir):**

**Rey ile oynarken:**

#### ch10_lie_neutral
**YANKI**
- tr: "Buradasın işte. Nasıl geldiğin önemli değil."
- en: "Here you are. How you got here doesn't matter."

**Ardo ile oynarken:**

#### ch10_trace_neutral
**ARDO**
- tr: "Bir iz daha. Ama artık hepsine iki kez bakıyorum."
- en: "Another trail. I look at all of them twice now."

**İki karakterde de:**

#### ch10_lie_neutral_react
**OYUNCU — Rey ile REY, Ardo ile ARDO**
- tr: "Bana öyle gelmiyor."
- en: "It does to me."

**Üst yolda zemin oyuncunun altında çöktüyse — ⚠ normal oyunda ulaşılamıyor** (Kalachev zemini her zaman önceden çökertiyor; bkz. Denetim):

**Rey ile oynarken:**

#### ch10_lie_sprung
**YANKI** — _ulaşılamıyor_
- tr: "Zemin çürüktü. Bunu bilemezdim."
- en: "The floor was rotten. I couldn't have known."

**Ardo ile oynarken:**

#### ch10_trace_sprung
**ARDO** — _ulaşılamıyor_
- tr: "Sahte iz. Biri buraya yürümüş gibi yapmış — ve zemini oymuş."
- en: "A false trail. Someone faked a walk here — and cut the floor."

**İki karakterde de:**

#### ch10_lie_sprung_react
**OYUNCU — Rey ile REY, Ardo ile ARDO — ulaşılamıyor**
- tr: "Bilemez miydin? Sen bu taşın altını görüyorsun."
- en: "Couldn't you? You see through stone."

### 7. Ders

> Ne oluyor: Yalan sahnesi kapanınca oynanışta. Aslında ders odasının giriş repliği; ara sahne aynı karede üstüne açıldığı için sahneden sonra okunur.

**Rey ile oynarken:**

#### ch10_rey_after
**REY**
- tr: "Bir daha o sesin gösterdiği yerden gitmeyeceğim."
- en: "I won't take the way that voice points to again."

**Ardo ile oynarken:**

#### ch10_ardo_after
**ARDO**
- tr: "İzler yalan söylemez. Ama biri onları bırakabilir."
- en: "Trails don't lie. But someone can leave one."

### Ekran yazıları — Bölüm 10

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.parting
_Bölüm kartı / kayıt yuvası adı_
- tr: "Ayrılık"
- en: "The Parting"

#### chapter10.trap_broken
_Kalachev üst yoldaki zemini çökertince_
- tr: "Zemini biri çökertti. Tuzak artık bir delik."
- en: "Someone caved the floor in. The trap is just a hole now."

#### chapter10.creak
_Sağlam tuzağın üstüne basınca — ⚠ normal oyunda ulaşılamıyor_
- tr: "Zemin gıcırdıyor..."
- en: "The floor is creaking..."

#### chapter10.trap
_Tuzak oyuncunun altında çökünce — ⚠ normal oyunda ulaşılamıyor_
- tr: "Zemin çöktü"
- en: "The floor gave way"

---

## Bölüm 11 — Ayna Salonu

**Özet:** Oyuncu yalnız; gölge yaratıklar yalnızca ışıkta ölür. Aynaları çevirerek ışın yönlendirilir — ve Yankı yanlış aynayı gösterir.

### 1. Giriş

> Ne oluyor: İlk odaya girişte.

**Rey ile oynarken:**

#### ch11_rey_hall
**REY**
- tr: "Aynalar... ve içlerinde ben yokum."
- en: "Mirrors... and I'm not in any of them."

**Ardo ile oynarken:**

#### ch11_ardo_hall
**ARDO**
- tr: "Ayna salonu. Buradan geçen herkesin izi var — ama hiçbiri çıkmamış."
- en: "A hall of mirrors. Everyone who came through left a trail — none of them left."

### 2. Öğrenme

> Ne oluyor: İkinci odaya girişte: ilk ayna, ışık dönüyor.

**Rey ile oynarken:**

#### ch11_rey_mirror
**REY**
- tr: "Işık aynadan dönüyor. Onu çevirebilirim."
- en: "The light turns off the mirror. I can rotate it."

**Ardo ile oynarken:**

#### ch11_ardo_mirror
**ARDO**
- tr: "Ayna dönüyor. Işığı istediğim yere gönderebilirim."
- en: "The mirror turns. I can send the light where I want."

### 3. Salon — Yankı'nın yalanı

> Ne oluyor: Üçüncü odaya (salon) girince; odanın ucunda İzleyen belirir. Yankı zaten doğru duran ortadaki aynayı 'yanlış' diye gösterir (Ardo'da taze parmak izi aynı aynayı işaret eder). B10'da Yankı'yı dinlemeyen oyuncuda (sadakat < 0) ardından şüphe repliği gelir — ama aynı karede başladığı için yalan repliğini ekrandan siler; o oyuncu yalanı hiç görmeden ona verilen cevabı görür (bkz. Denetim).

**Her durumda (sadakat < 0 ise hemen ezilir):**

**Rey ile oynarken:**

#### ch11_echo_lie
**YANKI**
- tr: "Ortadaki yanlış duruyor. Onu çevir — zinciri o bozuyor."
- en: "The middle one is wrong. Turn it — that's what breaks the chain."

**Ardo ile oynarken:**

#### ch11_trace_lie
**ARDO**
- tr: "Ortadaki aynada taze parmak izi. Biri onu son anda çevirmiş."
- en: "Fresh fingerprints on the middle mirror. Someone turned it at the last moment."

**B10'da alt yolu seçtiyse (sadakat < 0):**

**Rey ile oynarken:**

#### ch11_rey_doubt
**REY** — _koşullu_
- tr: "Geçen sefer de böyle söylemiştin."
- en: "That's what you said last time, too."

**Ardo ile oynarken:**

#### ch11_ardo_doubt
**ARDO** — _koşullu_
- tr: "Bir izin taze olması doğru olduğu anlamına gelmiyor."
- en: "A fresh trail doesn't mean a true one."

### Ekran yazıları — Bölüm 11

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.mirror_hall
_Bölüm kartı / kayıt yuvası adı_
- tr: "Ayna Salonu"
- en: "The Hall of Mirrors"

#### chapter11.rule
_Gölge yaratığa karanlıkta vurup etkisiz kalınca, bir kez_
- tr: "Karanlıkta ona dokunamıyorsun — ışığa çek"
- en: "You can't touch it in the dark — pull it into the light"

#### chapter11.solved
_Işın hedefe ulaşınca_
- tr: "Işın yerine ulaştı. Kapı açıldı."
- en: "The beam found its mark. The door is open."

---

## Bölüm 12 — Mektup

**Özet:** Tek bir dövüş yok: yoldaşın geçtiği yoldan iniş. Kuyu başında bırakılmış kamp, sonra kafesle yavaş iniş; yavaşlarsan duvardaki izleri okursun. Dipte okunan iz sayısına göre 'mektup'.

### 1. Kuyu başı — kamp

> Ne oluyor: Üst katta, kuyu ağzının solundaki noktaya gelince ara sahne: soğumuş ateş, bırakılmış denk, kurulu iniş düzeneği. Rey ile oynarken bunlar Ardo'nun **bilerek** bıraktıkları, Ardo ile oynarken Rey'in **istemeden** bıraktıkları.

*Ateş*

**Rey ile oynarken:**

#### ch12_cine_fire
**REY**
- tr: "Ateş sönmüş ama küller hâlâ ılık. Az önce buradaymış."
- en: "The fire's out but the ash is still warm. He was here moments ago."

**Ardo ile oynarken:**

#### ch12_cine_fire_ardo
**ARDO**
- tr: "Küller ılık. Beni bekleyip vazgeçmiş."
- en: "The ash is warm. He waited for me and gave up."

*Denk*

**Rey ile oynarken:**

#### ch12_cine_pack
**REY**
- tr: "Denk açık. İçindekini ikiye bölmüş."
- en: "The pack is open. He split what was inside in two."

**Ardo ile oynarken:**

#### ch12_cine_pack_ardo
**ARDO**
- tr: "Denği açmış, karıştırmış, hiçbir şey almamış."
- en: "He opened the pack, went through it, took nothing."

*Düzenek*

**Rey ile oynarken:**

#### ch12_echo_rig
**YANKI**
- tr: "Bunu kurmak vakit almış. Seni bekleyecek vakti yokmuş — kuracak vakti varmış."
- en: "This took time to build. He had no time to wait — but time to build."

**Ardo ile oynarken:**

#### ch12_trace_rig
**ARDO**
- tr: "Düzenek sağlam. Acele etmemiş — inen kişi düşmesin diye."
- en: "The rig is solid. He didn't rush it — so whoever came down wouldn't fall."

### 2. Kafesle iniş — duvardaki izler *(her biri isteğe bağlı)*

> Ne oluyor: Kafese binince iniş başlar ('Kafes iniyor...'). Aşağı tuşu basılı tutulursa kafes yavaşlar; yavaşken ve doğru taraftayken geçilen her iz okunur. Yedi iz, derinlik sırasıyla; kaçırılan iz okunmaz ve dipteki mektubun varyantını değiştirir. Anahtarlar `src/world/rooms/chapter12.py` içindeki `MARKS` tablosunda.

*İz 1 — ok (sol duvar)*

**Rey ile oynarken:**

#### ch12_mark_arrow
**REY** — _isteğe bağlı_
- tr: "Ok. Sağa. Benim için çizmiş."
- en: "An arrow. Right. He drew it for me."

**Ardo ile oynarken:**

#### ch12_mark_arrow_ardo
**ARDO** — _isteğe bağlı_
- tr: "Ayak izi. Burada durup iki yana bakmış — yolu bilmiyormuş."
- en: "A footprint. He stood here and looked both ways — he didn't know the road."

*İz 2 — erzak (sağ duvar; +30 altın)*

**Rey ile oynarken:**

#### ch12_mark_cache
**REY** — _isteğe bağlı_
- tr: "Erzak. Payını ayırmış, benimkini bırakmış."
- en: "Supplies. He split his share and left mine."

**Ardo ile oynarken:**

#### ch12_mark_cache_ardo
**ARDO** — _isteğe bağlı_
- tr: "Bıraktığım erzağa dokunmamış. Ya bulmamış, ya almaya utanmış."
- en: "He never touched the food I left. Missed it, or was ashamed to take it."

*İz 3 — kamp izi (sol duvar)*

**Rey ile oynarken:**

#### ch12_mark_camp
**REY** — _isteğe bağlı_
- tr: "Burada uyumuş. Ateşi küçük tutmuş — görülmek istememiş."
- en: "He slept here. Kept the fire small — he didn't want to be seen."

**Ardo ile oynarken:**

#### ch12_mark_camp_ardo
**ARDO** — _isteğe bağlı_
- tr: "Burada uyumamış. Oturmuş, kalkmış, tekrar oturmuş."
- en: "He didn't sleep here. Sat down, got up, sat down again."

*İz 4 — iki kişinin izi (sağ duvar)*

**Rey ile oynarken:**

#### ch12_mark_pair
**REY** — _isteğe bağlı_
- tr: "İki çift ayak izi. Biri önden gidiyor, öteki her durduğunda beklemiş."
- en: "Two sets of tracks. The one in front waited whenever the other stopped."

**Ardo ile oynarken:**

#### ch12_mark_pair_ardo
**ARDO** — _isteğe bağlı_
- tr: "Kalachev. Burada beni beklemişti. Söylesem inkâr eder."
- en: "Kalachev. He waited for me here. He'd deny it if I asked."

*İz 5 — çentikler (sağ duvar)*

**Rey ile oynarken:**

#### ch12_mark_count
**REY** — _isteğe bağlı_
- tr: "Çentikler. Günleri saymış."
- en: "Notches. He was counting the days."

**Ardo ile oynarken:**

#### ch12_mark_count_ardo
**ARDO** — _isteğe bağlı_
- tr: "Duvarda çentikler var. Sayarken elleri titremiş."
- en: "Notches on the wall. His hand shook while he counted."

*İz 6 — kırık kömür (sol duvar)*

**Rey ile oynarken:**

#### ch12_mark_pencil
**REY** — _isteğe bağlı_
- tr: "Kırık bir kömür ucu. Bir şey çizerken kırılmış."
- en: "A broken piece of charcoal. It snapped while he was drawing."

**Ardo ile oynarken:**

#### ch12_mark_pencil_ardo
**ARDO** — _isteğe bağlı_
- tr: "Kömür tozu. Bir şey çizmiş, sonra silmeye çalışmış."
- en: "Charcoal dust. He drew something, then tried to rub it out."

*İz 7 — duvara kazınmış figür (sağ duvar; kolye ısınır)*

**Rey ile oynarken:**

#### ch12_mark_figure
**REY** — _isteğe bağlı_
- tr: "Bu... ben'im. Beni çizmiş."
- en: "That's... me. He drew me."

**Ardo ile oynarken:**

#### ch12_mark_figure_ardo
**ARDO** — _isteğe bağlı_
- tr: "Beni çizmiş. Kaba, acele — ama gözlerini doğru yapmış."
- en: "He drew me. Rough, rushed — but he got the eyes right."

### 3. Dip — mektup

> Ne oluyor: Kafes dibe inince, yanındaki noktada ara sahne: dip, yüz (yakın plan), son söz, devam. Okunan iz sayısına göre üç varyant; son panel her varyantta aynı.

**Yedi izin hepsi okunduysa:**

**Rey ile oynarken:**

#### ch12_letter_all
**REY**
- tr: "Hepsini gördüm. Baştan sona bana yazmış."
- en: "I saw all of it. He was writing to me the whole way down."

#### ch12_after_all
**REY**
- tr: "Aşağıda buluşacağız. Söz vermedi ama ben verdim."
- en: "We'll meet down there. He didn't promise — I did."

**Ardo ile oynarken:**

#### ch12_letter_all_ardo
**ARDO**
- tr: "Hepsini gördüm. Yalnız olduğunu bir kere bile yazmamış."
- en: "I saw all of it. Not once did he write that he was alone."

#### ch12_after_all_ardo
**ARDO**
- tr: "Aşağıda buluşacağız. Bu sefer geç kalmayacağım."
- en: "We'll meet down there. This time I won't be late."

**3–6 iz okunduysa:**

**Rey ile oynarken:**

#### ch12_letter_some
**REY**
- tr: "Bir kısmını gördüm. Gerisi yukarıda kaldı."
- en: "I saw some of it. The rest stayed up there."

#### ch12_after_some
**REY**
- tr: "Geri dönemem. Yukarısı artık kapalı."
- en: "I can't go back. Up there is closed now."

**Ardo ile oynarken:**

#### ch12_letter_some_ardo
**ARDO**
- tr: "Bir kısmını gördüm. Hızlı inmişim."
- en: "I saw some of it. I came down too fast."

#### ch12_after_some_ardo
**ARDO**
- tr: "Geri dönmek yok. Aşağısı neyse odur."
- en: "No going back. Whatever's below is what there is."

**0–2 iz okunduysa:**

**Rey ile oynarken:**

#### ch12_letter_few
**REY**
- tr: "Çok hızlı indim. Arkamda bıraktığım şeyler vardı."
- en: "I came down too fast. I left things behind me."

#### ch12_after_few
**REY**
- tr: "Bir dahakine yavaşlarım."
- en: "Next time I'll slow down."

**Ardo ile oynarken:**

#### ch12_letter_few_ardo
**ARDO**
- tr: "Bakmadım. Bakmak için zamanım yok sanmıştım."
- en: "I didn't look. I thought I had no time to look."

#### ch12_after_few_ardo
**ARDO**
- tr: "Bir dahakine bakarım."
- en: "Next time I'll look."

**Son panel (her varyantta):**

**Rey ile oynarken:**

#### ch12_echo_deeper
**YANKI**
- tr: "Aşağı iniyorsun. Güzel. Ben de aşağıdayım."
- en: "You're going down. Good. I'm down there too."

**Ardo ile oynarken:**

#### ch12_trace_deeper
**ARDO**
- tr: "İzler burada bitiyor. Bundan sonrası benim."
- en: "The tracks end here. What comes next is mine."

### 4. Mum Bekçisi

> Ne oluyor: Dipte, çıkışın hemen önünde Bekçi'ye yaklaşınca. Ticaret yok; mumları bir öncekinden az.

**Rey ile oynarken:**

#### ch12_keeper
**REY**
- tr: "Yine sen. Mumların iyice azalmış."
- en: "You again. Your candles have burned down."

**Ardo ile oynarken:**

#### ch12_keeper_ardo
**ARDO**
- tr: "Her indiğimde bir mum eksik. Sonuncusunda ne olacak?"
- en: "One candle fewer every time I come down. What happens after the last one?"

### Ekran yazıları — Bölüm 12

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.letter
_Bölüm kartı / kayıt yuvası adı_
- tr: "Mektup"
- en: "The Letter"

#### chapter12.descend
_Kafese binince_
- tr: "Kafes yavaşça iniyor. Acele edersen kaçırırsın."
- en: "The rig creeps down. Hurry, and you'll miss things."

#### hint.rig_fast
_Kafes inmeye başlayınca bir kez (bildirim). 24.09.2026: kafes varsayılan olarak yavaş, tuş hızlandırıyor_
- tr: "[{key}] basılı tut — fren bırakılır, kafes hızlanır"
- en: "[{key}] hold — release the brake, the rig speeds up"

---

## Bölüm 13 — Cemo

**Özet:** Cemo kafeste, canlı — ama oyuncu ulaşamadan taşınır. Kovalamaca: kol çevrilince süreli açılan zaman kapıları. Cemo'nun kaçmayı denediği yer ve duvara kazıdığı işaret; sonda ikinci büyük boss Zindancı ve Kalachev'in yaralanması. Kapı açılır — arkası boş.

### 1. Kafes

> Ne oluyor: İlk odada tetik noktasına gelince atlanamaz ara sahne: Cemo yüksekteki kafeste belirir, Cemo'nun ve oyuncunun yüzü (yakın plan), oyuncu koşar ve parmaklığa çarpar, Cemo taşınır, kafes boş kalır. Korku katmanı açıksa bu sırada İzleyen de görünür.

*Görüş*

#### ch13_cemo_sees
**CEMO**
- tr: "Rey?"
- en: "Rey?"

**Rey ile oynarken:**

#### ch13_echo_seed
**YANKI** — _Yankı Cemo'nun sesini tekrarlar — tohum 3/3_
- tr: "Rey?"
- en: "Rey?"

*Koşu*

**Rey ile oynarken:**

#### ch13_rey_reach
**REY**
- tr: "CEMO!"
- en: "CEMO!"

**Ardo ile oynarken:**

#### ch13_ardo_reach
**ARDO**
- tr: "Dur! Dur, geliyorum —"
- en: "Wait! Wait, I'm coming —"

*Boş*

**Rey ile oynarken:**

#### ch13_echo_cage
**YANKI**
- tr: "Görüyorsun. Yaşıyor. Şimdi daha hızlı ineceksin."
- en: "You see. He's alive. Now you'll come down faster."

**Ardo ile oynarken:**

#### ch13_trace_cage
**ARDO**
- tr: "Yaşıyor. Bunu bilmek her şeyi kolaylaştırmıyor."
- en: "He's alive. Knowing that doesn't make it easier."

### 2. Kol

> Ne oluyor: İkinci odaya girişte: ilk zaman kapısı (kolun yanında ipucu).

**Rey ile oynarken:**

#### ch13_rey_lever
**REY**
- tr: "Bir kol. Ve ötesinde inen bir demir."
- en: "A lever. And beyond it, iron coming down."

**Ardo ile oynarken:**

#### ch13_ardo_lever
**ARDO**
- tr: "Kol, kapı, sayaç. Birileri buradan geçenleri saymış."
- en: "Lever, gate, timer. Someone counted who passed here."

### 3. Okçu

> Ne oluyor: Üçüncü odaya girişte — kapı inerken dövüşmek yerine koşmak.

**Rey ile oynarken:**

#### ch13_rey_run
**REY**
- tr: "Durursam kapanıyor. Öyleyse durmayacağım."
- en: "It closes if I stop. So I won't stop."

**Ardo ile oynarken:**

#### ch13_ardo_run
**ARDO**
- tr: "Kavga zaman ister. Bende zaman yok."
- en: "A fight costs time. I don't have any."

### 4. İşaret

> Ne oluyor: Beşinci odaya girişte oyuncunun repliği; birkaç adım sonra ara sahne: duvardaki kazıma, kan, yüz.

**Rey ile oynarken:**

#### ch13_rey_mark
**REY**
- tr: "Bu çizgiyi tanıyorum."
- en: "I know this mark."

**Ardo ile oynarken:**

#### ch13_ardo_mark
**ARDO**
- tr: "Bir çocuk burada durup duvara bir şey kazımış."
- en: "A child stood here and cut something into the wall."

*Ara sahne — işaret*

**Rey ile oynarken:**

#### ch13_rey_sign
**REY**
- tr: "Benim için bıraktı. Yolu işaretlemiş."
- en: "He left it for me. He marked the way."

**Ardo ile oynarken:**

#### ch13_ardo_sign
**ARDO**
- tr: "Kaçmayı denemiş. Ve denerken birini yaralamış."
- en: "He tried to run. And hurt someone trying."

*Ara sahne — kan*

**Rey ile oynarken:**

#### ch13_echo_blood
**YANKI**
- tr: "Kan taze değil. Ama korkusu taze."
- en: "The blood isn't fresh. His fear is."

**Ardo ile oynarken:**

#### ch13_trace_blood
**ARDO**
- tr: "Zincir kopmuş, kilit değil. Demek ki çekiştirmiş."
- en: "The chain broke, not the lock. So he pulled."

### 5. Zindancı

> Ne oluyor: Son odaya (zindan) girer girmez ara sahne: karanlık, fener, gövde, yüz; mühür iner.

*Gövde*

**Rey ile oynarken:**

#### ch13_echo_gaoler
**YANKI**
- tr: "İşte bu odanın sahibi. Fenerini bırakmaz."
- en: "There. The one this room belongs to. He never sets down the lantern."

**Ardo ile oynarken:**

#### ch13_trace_gaoler
**ARDO**
- tr: "Anahtarları belinde. Yani kapıyı açan o."
- en: "Keys on his belt. So he's the one who opens the door."

*Mühür*

**Rey ile oynarken:**

#### ch13_rey_gaoler
**REY**
- tr: "Kardeşimi nereye götürdün?"
- en: "Where did you take my brother?"

**Ardo ile oynarken:**

#### ch13_ardo_gaoler
**ARDO**
- tr: "Anahtarları ver. Kolay yolu bir kez teklif ediyorum."
- en: "Give me the keys. I'm offering the easy way once."

### 6. Kalachev kapıda

> Ne oluyor: Birkaç adım sonra arena mühürlenirken Kalachev içeri süzülür; kısa karşılaşma sahnesi. Önceki bir denemede yaralandıysa bir daha gelmez.

**Rey ile oynarken:**

#### ch13_rey_kalachev
**REY**
- tr: "Kalachev! Kapı kapanıyordu!"
- en: "Kalachev! The gate was closing!"

#### ch13_kalachev_child
**KALACHEV**
- tr: "Gördüm. Sen çocuğa bak."
- en: "I saw. Keep your eyes on the boy."

**Ardo ile oynarken:**

#### ch13_ardo_kalachev
**ARDO**
- tr: "Kalachev! Bir an daha geciksen..."
- en: "Kalachev! A second later and..."

#### ch13_kalachev_late
**KALACHEV**
- tr: "Gecikmedim."
- en: "I wasn't late."

### 7. Kalachev yaralanıyor

> Ne oluyor: Boss dövüşünde belirli faza gelince (senaryolu, kaçınılmaz) Zindancı Kalachev'i yakalar; kan, sarsıntı; Kalachev çekilir ama ölmez.

**Rey ile oynarken:**

#### ch13_rey_wound
**REY**
- tr: "Kalachev, kanıyorsun! Dur artık!"
- en: "Kalachev, you're bleeding! Stop!"

**Ardo ile oynarken:**

#### ch13_ardo_wound
**ARDO**
- tr: "Elini yaraya bastır! Bana bak, Efe. Buradan çıkacaksın."
- en: "Hold the wound! Look at me, Efe. You're getting out of here."

### 8. Kapı açık — arkası boş

> Ne oluyor: Zindancı düşünce ('Zindancı düştü. Kapı açık.') son ara sahne: kapı açılır, kafes boş, yüz, aşağı.

*Boş kafes*

**Rey ile oynarken:**

#### ch13_rey_empty
**REY**
- tr: "Boş. Yine boş."
- en: "Empty. Empty again."

**Ardo ile oynarken:**

#### ch13_ardo_empty
**ARDO**
- tr: "Geç kaldım. Yine."
- en: "Too late. Again."

*Aşağı*

**Rey ile oynarken:**

#### ch13_echo_deeper
**YANKI**
- tr: "Aşağıda. Hep aşağıdaydı. Artık beni duyduğun yere yakınsın."
- en: "Below. It was always below. You're close to where you hear me now."

**Ardo ile oynarken:**

#### ch13_trace_deeper
**ARDO**
- tr: "İzler aşağı iniyor. Bu sefer geri dönmüyorlar."
- en: "The tracks go down. This time they don't come back."

### Ekran yazıları — Bölüm 13

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.cemo
_Bölüm kartı / kayıt yuvası adı_
- tr: "Cemo"
- en: "Cemo"

#### hint.lever
_Bir kolun yanına ilk gelişte (bildirim)_
- tr: "[{key}] kolu çevir — kapı süreli açılır"
- en: "[{key}] pull the lever — the gate is timed"

#### chapter13.run
_Kol ilk kez çevrilip kapı açılınca_
- tr: "KOŞ — kapı iniyor"
- en: "RUN — the gate is falling"

#### boss.gaoler
_Boss can barındaki ad_
- tr: "ZİNDANCI"
- en: "THE GAOLER"

#### chapter13.dark
_Boss'un feneri kırılınca (arena kararır)_
- tr: "Fener kırıldı. Mangalları yak."
- en: "The lantern broke. Light the braziers."

#### chapter13.gate_open
_Boss düşünce_
- tr: "Zindancı düştü. Kapı açık."
- en: "The Gaoler has fallen. The gate is open."

---

## Bölüm 14 — Yankı'nın Kaynağı

**Özet:** Dönüm noktası: Yankı lanet değil, aşağıdaki şeyin sesi — hep yardım ediyordu çünkü onu çağırıyordu. Bundan sonra duyu tersine döner: Yankı (Ardo'da iz sürme) açılınca düşmanlar da oyuncuyu görür. Boss Kaynak düşer ama ölmez.

### 1. Sessiz oda

> Ne oluyor: İkinci odaya girişte.

**Rey ile oynarken:**

#### ch14_rey_empty
**REY**
- tr: "Oda boş görünüyor. Ama boş hissettirmiyor."
- en: "The room looks empty. It doesn't feel empty."

**Ardo ile oynarken:**

#### ch14_ardo_empty
**ARDO**
- tr: "Hiç iz yok. Hiç iz olmaması da bir iz."
- en: "No tracks at all. No tracks is also a track."

### 2. Kaynak

> Ne oluyor: Aynı odadaki tetikte ara sahne: oyuncu sorar/izi okur, ses cevap verir (ekran sarsılır), geri çekilir, yüz, kabul. Bitince sözleşme değişir: 'Yankı artık iki tarafa da açık' (korku katmanı açıksa bir sıçratma kurulur).

*Açılış*

**Rey ile oynarken:**

#### ch14_cine_open
**REY**
- tr: "Bir şey var. Sorayım."
- en: "Something's there. Let me ask."

**Ardo ile oynarken:**

#### ch14_cine_open_ardo
**ARDO**
- tr: "Burada biri durmuş. İzi okuyayım."
- en: "Someone stood here. Let me read it."

*Cevap*

**Rey ile oynarken:**

#### ch14_echo_answer
**YANKI**
- tr: "BURADAYIM. HEP BURADAYDIM."
- en: "I AM HERE. I WAS ALWAYS HERE."

**Ardo ile oynarken:**

#### ch14_trace_answer
**ARDO**
- tr: "İzler taze. Ve tek yöne gitmiyorlar — biri geri gelmiş."
- en: "The tracks are fresh. And they don't go one way — someone came back."

*Geri*

**Rey ile oynarken:**

#### ch14_cine_back
**REY**
- tr: "Bu ses... kafamın içinden gelmiyor."
- en: "That voice... it isn't coming from inside my head."

**Ardo ile oynarken:**

#### ch14_cine_back_ardo
**ARDO**
- tr: "Bu izler benim için bırakılmış. Baştan beri."
- en: "These tracks were left for me. From the start."

*Kabul*

**Rey ile oynarken:**

#### ch14_cine_accept
**REY**
- tr: "Bana yardım etmiyordun. Beni çağırıyordun."
- en: "You weren't helping me. You were calling me."

**Ardo ile oynarken:**

#### ch14_cine_accept_ardo
**ARDO**
- tr: "Takip etmiyordum. Çağrılıyordum."
- en: "I wasn't following. I was being called."

### 3. Ters

> Ne oluyor: Üçüncü odaya girişte; artık Yankı/iz açılınca düşmanlar başlarını çevirir (ilk uyanışta 'Seni duydular.').

**Rey ile oynarken:**

#### ch14_rey_turned
**REY**
- tr: "Açtığım an başlarını çevirdiler. Bana mı baktılar?"
- en: "They turned the moment I opened it. Did they look at me?"

**Ardo ile oynarken:**

#### ch14_ardo_turned
**ARDO**
- tr: "Baktığım an bana baktılar. İz sürmek iki taraflıymış."
- en: "They looked back when I looked. Tracking goes both ways."

### 4. Bölünen

> Ne oluyor: Beşinci odaya girişte: vurdukça çoğalan düşmanlar; İzleyen bu kez geri çekilmez.

**Rey ile oynarken:**

#### ch14_rey_split
**REY**
- tr: "Vurdukça çoğalıyor. Ne kadar iyiysem o kadar kötü."
- en: "It multiplies as I hit it. The better I am, the worse it gets."

**Ardo ile oynarken:**

#### ch14_ardo_split
**ARDO**
- tr: "Kılıcım işe yaramıyor — işi kolaylaştırıyor."
- en: "My blade isn't working — it's helping."

### 5. Kaynak'ın eşiği

> Ne oluyor: Aynı odanın sonundaki tetikte ara sahne: eşik, ses, gövde, Kaynak'ın yüzü.

*Ses*

**Rey ile oynarken:**

#### ch14_echo_arena
**YANKI**
- tr: "Geldin. Ne kadar da uzun sürdü."
- en: "You came. It took you so long."

**Ardo ile oynarken:**

#### ch14_trace_arena
**ARDO**
- tr: "Bütün izler burada bitiyor. Kimse buradan çıkmamış."
- en: "Every track ends here. Nobody walked back out."

*Gövde*

**Rey ile oynarken:**

#### ch14_rey_arena
**REY**
- tr: "Kardeşim nerede?"
- en: "Where is my brother?"

**Ardo ile oynarken:**

#### ch14_ardo_arena
**ARDO**
- tr: "Onu bırak. Konuşacaksan benimle konuş."
- en: "Leave him out of it. If you're talking, talk to me."

### 6. Düştü ama ölmedi

> Ne oluyor: Arenada Kaynak yenilince ('Düştü. Ama ölmedi.') ara sahne: dağılma, sessizlik, 'yine', karar (yakın plan).

*Sessizlik*

**Rey ile oynarken:**

#### ch14_rey_quiet
**REY**
- tr: "Bitti mi?"
- en: "Is that it?"

**Ardo ile oynarken:**

#### ch14_ardo_quiet
**ARDO**
- tr: "Fazla kolay oldu."
- en: "That was too easy."

*Yine*

**Rey ile oynarken:**

#### ch14_echo_again
**YANKI**
- tr: "O bendim. Ama ben o değilim."
- en: "That was me. But I am not that."

**Ardo ile oynarken:**

#### ch14_trace_again
**ARDO**
- tr: "İzler hâlâ aşağı gidiyor. Yendiğim şey duruyordu."
- en: "The tracks still go down. What I beat was standing still."

*Karar*

**Rey ile oynarken:**

#### ch14_rey_decide
**REY**
- tr: "Öyleyse seni dinlemeyi bırakıyorum."
- en: "Then I stop listening to you."

**Ardo ile oynarken:**

#### ch14_ardo_decide
**ARDO**
- tr: "Öyleyse artık bakmayacağım. Kendim bulurum."
- en: "Then I stop looking. I'll find it myself."

### Ekran yazıları — Bölüm 14

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.source
_Bölüm kartı / kayıt yuvası adı_
- tr: "Yankı'nın Kaynağı"
- en: "The Source of the Echo"

#### chapter14.betrayed
_Kaynak sahnesi bitince_
- tr: "Yankı artık iki tarafa da açık."
- en: "The Echo opens both ways now."

#### chapter14.silent
_Rey ile: Yankı'da görünmeyen Sessiz düşman ilk kez fark edince_
- tr: "Yankı onu göstermiyor. Gözünle bak."
- en: "The Echo doesn't show it. Use your eyes."

#### chapter14.heard
_Yankı/iz yüzünden ilk düşman uyanınca_
- tr: "Seni duydular."
- en: "They heard you."

#### boss.source
_Boss can barındaki ad_
- tr: "KAYNAK"
- en: "THE SOURCE"

#### chapter14.not_dead
_Kaynak yenilince_
- tr: "Düştü. Ama ölmedi."
- en: "It fell. It didn't die."

---

## Bölüm 15 — Sessizlik

**Özet:** Uyuyan sürü: Yankı'sız, sessizce geçmek. Koşarsan uyanırlar; gürültü kaynaklarıyla dikkat dağıtılır. Kimseyi uyandırmadan geçmek ('hayalet') daha iyi ödül verir. Sürünün arasında Kalachev de sessizce bekler.

### 1. Uyku

> Ne oluyor: İlk odaya girişte (uyuyanlara yaklaşınca 'Yürü. Koşarsan duyarlar.').

**Rey ile oynarken:**

#### ch15_rey_sleep
**REY**
- tr: "Uyuyorlar. Uyandırmazsam geçebilirim."
- en: "They're asleep. I can pass if I don't wake them."

**Ardo ile oynarken:**

#### ch15_ardo_sleep
**ARDO**
- tr: "Uyuyorlar. Ayak sesim onlardan yüksek."
- en: "They're asleep. My footsteps are louder than they are."

### 2. Sürü — sessiz Kalachev

> Ne oluyor: Üçüncü odada (sürü) Kalachev sessizce durur ve hiç konuşmaz. Oyuncu ona yaklaşınca Yankı yorum yapar; sürü uyanırsa Kalachev öne atılır ve Yankı ikinci yorumu yapar. ⚠ Bu iki Yankı repliğinde karakter kontrolü yok — Ardo ile de çıkıyor (bkz. Denetim).

*Kalachev'e yaklaşınca*

#### ch15_echo_kalachev
**YANKI** — _Ardo ile de oynuyor_
- tr: "Bak, beklemeyi öğrenmiş. İnsan neler öğreniyor burada."
- en: "Look. He's learned to wait. This place teaches so much."

*Sürü uyanırsa (koşullu)*

#### ch15_echo_kalachev_wakes
**YANKI** — _koşullu; Ardo ile de oynuyor_
- tr: "Yine öne atıldı. Yarasını unuttu mu dersin?"
- en: "There he goes again. Think he's forgotten the wound?"

### 3. Damla

> Ne oluyor: Dördüncü odaya girişte.

**Rey ile oynarken:**

#### ch15_rey_drip
**REY**
- tr: "Su damlıyor. Onlar da her damlada başlarını çeviriyor."
- en: "Water is dripping. They turn their heads at every drop."

**Ardo ile oynarken:**

#### ch15_ardo_drip
**ARDO**
- tr: "Damla düştükçe kımıldıyorlar. Ritmi var."
- en: "They stir with each drop. There's a rhythm to it."

### 4. Dar

> Ne oluyor: Beşinci odaya girişte.

**Rey ile oynarken:**

#### ch15_rey_narrow
**REY**
- tr: "Burada çan yok. Sadece yavaş."
- en: "No bells here. Only slow."

**Ardo ile oynarken:**

#### ch15_ardo_narrow
**ARDO**
- tr: "Dar. Kaçacak yer de yok, ses çıkaracak yer de."
- en: "Narrow. Nowhere to run, nowhere to make noise either."

### 5. Geçtin

> Ne oluyor: Beşinci odanın (dar) sonundaki tetikte ara sahne: oyuncu arkasına bakar, sessizlik, yüz. Geçişin nasıl yapıldığına göre iki varyant.

**Hayalet — kimse uyanmadı, kimse ölmedi:**

**Rey ile oynarken:**

#### ch15_rey_ghost
**REY**
- tr: "Hiçbiri uyanmadı."
- en: "Not one of them woke."

#### ch15_rey_ghost_face
**REY**
- tr: "Sensiz de yapabiliyormuşum."
- en: "Turns out I can do it without you."

**Ardo ile oynarken:**

#### ch15_ardo_ghost
**ARDO**
- tr: "Hiçbiri kalkmadı. Buradan geçtiğimi bilmiyorlar."
- en: "Not one of them stirred. They don't know I came through."

#### ch15_ardo_ghost_face
**ARDO**
- tr: "Kılıç her sorunun cevabı değilmiş."
- en: "So the blade isn't the answer to everything."

**Biri uyandı ya da öldü:**

**Rey ile oynarken:**

#### ch15_rey_woke
**REY**
- tr: "Duydular. Ama geçtim."
- en: "They heard me. But I got through."

#### ch15_rey_woke_face
**REY**
- tr: "Bir dahakine daha yavaş."
- en: "Slower, next time."

**Ardo ile oynarken:**

#### ch15_ardo_woke
**ARDO**
- tr: "Gürültü yaptım. Yine de arkamda kaldılar."
- en: "I made noise. They're still behind me."

#### ch15_ardo_woke_face
**ARDO**
- tr: "Geçmek yetmez. Sessiz geçmek gerekiyormuş."
- en: "Getting through isn't enough. It had to be quiet."

### 6. Jet'in dönüşü

> Ne oluyor: Çıkışta, bölüm sonu ekranından önce (kayıt yuvası başına bir kez). Arka planda bir kapı; Jet fısıldar gibi konuşur.

#### ch15_jet_return
**JET**
- tr: "Yavaş. Şu kapının ötesinden geldim. Ses buraya taşınıyor."
- en: "Easy. I came through that gate. Sound carries here."

**Rey ile oynarken:**

#### ch15_rey_jet_return
**REY**
- tr: "Jet... Sesini duyunca bir an korktum."
- en: "Jet... Your voice scared me for a moment."

**Ardo ile oynarken:**

#### ch15_ardo_jet_return
**ARDO**
- tr: "Bir adım daha atma. Arkandakiler uyuyor."
- en: "Stay there. The things behind you are asleep."

**İki karakterde de:**

#### ch15_jet_route
**JET**
- tr: "Tamam. Kapıyı sessizce kapatırım. Sen devam et."
- en: "All right. I will close the gate quietly. Keep going."

#### ch15_jet_promise
**JET**
- tr: "Dönüşte seslenmene gerek yok. Burada olacağım."
- en: "You will not have to call out on the way back. I will be here."

### Ekran yazıları — Bölüm 15

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.silence
_Bölüm kartı / kayıt yuvası adı_
- tr: "Sessizlik"
- en: "Silence"

#### chapter15.walk
_Uyuyan bir düşmana ilk yaklaşınca_
- tr: "Yürü. Koşarsan duyarlar."
- en: "Walk. They'll hear you if you run."

#### hint.chime
_İkinci odaya girişte bir kez (bildirim)_
- tr: "[{key}] rezonans — uzaktaki çanı çal"
- en: "[{key}] resonance — ring a distant bell"

#### chapter15.ghost
_Hayalet geçişte, bölüm biterken_
- tr: "Hiçbiri uyanmadı. Sessizlik ödülü."
- en: "Nobody woke. Reward for silence."

---

## Bölüm 16 — Sırt Sırta

**Özet:** Yalnız ve sıkışmışken yoldaş geri döner — havalı giriş. Bu kez oyuncu da onu kurtarır: diz çöken yoldaşı kaldırmak. En uzun ortak dövüş; sonda kelimesiz bir jest seçimi.

### 1. Kalabalık

> Ne oluyor: İlk odaya girişte — beşi birden.

**Rey ile oynarken:**

#### ch16_rey_many
**REY**
- tr: "Kaç tane? Sayamıyorum. Sesler bile sustu."
- en: "How many? I can't count them. Even the voices went quiet."

**Ardo ile oynarken:**

#### ch16_ardo_many
**ARDO**
- tr: "Beşi birden. Sırayla gelmeyecekler."
- en: "Five at once. They won't come one at a time."

### 2. Dönüş

> Ne oluyor: İkinci odadaki tetikte ara sahne: oyuncu sıkışır, yoldaş gelir (havalı giriş), yüz.

**Rey ile oynarken:**

#### ch16_rey_alone
**REY**
- tr: "Arkam duvar. Bu sefer kimse gelmeyecek."
- en: "Wall behind me. Nobody's coming this time."

#### ch16_rey_return_face
**REY**
- tr: "Geldin. Sormadan geldin."
- en: "You came. You didn't even ask."

**Ardo ile oynarken:**

#### ch16_ardo_alone
**ARDO**
- tr: "Sıkıştım. Kendi hatam."
- en: "Cornered. My own fault."

#### ch16_ardo_return_face
**ARDO**
- tr: "Onu geride bırakmıştım. O beni bırakmamış."
- en: "I left her behind. She didn't leave me."

### 3. Kaldır

> Ne oluyor: Dördüncü odadaki tetikte yoldaş senaryolu olarak diz çöker; ara sahne ona gitmeyi ve kolundan tutmayı gösterir. Sonra oyuncu kendisi kaldırır ('KALDIR' kartı).

*Yanına*

**Rey ile oynarken:**

#### ch16_rey_fell
**REY**
- tr: "Düştü. Bu sefer kendi kalkmıyor."
- en: "Down. This time they're not getting up alone."

**Ardo ile oynarken:**

#### ch16_ardo_fell
**ARDO**
- tr: "Yere indi. Kalkmasını bekleyemem."
- en: "She's down. I can't wait for her to rise."

*Tut*

**Rey ile oynarken:**

#### ch16_rey_hold
**REY**
- tr: "Elimi uzatıyorum. Tutana kadar bırakmayacağım."
- en: "I'm reaching out. I won't let go until they take it."

**Ardo ile oynarken:**

#### ch16_ardo_hold
**ARDO**
- tr: "Kolundan tut. Bırakma."
- en: "Take her arm. Don't let go."

### 4. Koridor

> Ne oluyor: Beşinci odaya girişte.

**Rey ile oynarken:**

#### ch16_rey_corridor
**REY**
- tr: "Uzun. Ama artık iki kişiyiz."
- en: "Long. But there are two of us now."

**Ardo ile oynarken:**

#### ch16_ardo_corridor
**ARDO**
- tr: "Dar ve uzun. İkimiz de ayakta kalmalıyız."
- en: "Narrow and long. We both have to stay standing."

### 5. Sırt sırta

> Ne oluyor: Altıncı odaya girişte: iki yandan gelen düşmanlar.

**Rey ile oynarken:**

#### ch16_rey_back
**REY**
- tr: "İki yandan geliyorlar. Sırtımı sana veriyorum."
- en: "They're coming from both sides. I'm giving you my back."

**Ardo ile oynarken:**

#### ch16_ardo_back
**ARDO**
- tr: "İkiye bölündüler. Sırtını bana ver."
- en: "They've split in two. Put your back to mine."

### 6. Kalp

> Ne oluyor: Son odadaki tetikte ara sahne: ikisi ayakta; ardından **kelimesiz** jest seçimi (elini uzat / başını salla / geri çekil). Seçim kaydedilir ve kapanışta yoldaşın ne kadar geride durduğunu belirler.

**Rey ile oynarken:**

#### ch16_rey_stand
**REY**
- tr: "Bitti. İkimiz de ayaktayız."
- en: "It's over. We're both still standing."

**Ardo ile oynarken:**

#### ch16_ardo_stand
**ARDO**
- tr: "Hepsi yerde. İkimiz değiliz."
- en: "All of them down. Not us."

### Ekran yazıları — Bölüm 16

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.backtoback
_Bölüm kartı / kayıt yuvası adı_
- tr: "Sırt Sırta"
- en: "Back to Back"

#### hint.rescue_title
_Yoldaş yerdeyken bir kez açılan kartın başlığı_
- tr: "KALDIR"
- en: "LIFT"

#### hint.rescue
_Aynı kartın gövdesi_
- tr: "[{key}] basılı tut — onu kaldır"
- en: "Hold [{key}] — lift them up"

#### chapter16.lifted
_Bölüm biterken — yoldaş en az bir kez kaldırıldıysa_
- tr: "Onu ayağa kaldırdın."
- en: "You pulled them back up."

---

## Bölüm 17 — İkili Kule

**Özet:** Ayrı yollardan tırmanış: iki karakter arasında geçiş yapılır (biri kolu tutar, öteki geçer). Camdan/parmaklıktan birbirlerini görürler ama dokunamazlar. Tepede kapıyı tutan yoldaş. Replikler bölüm başında seçilen karaktere göre (o an kontrol edilene göre değil).

### 1. Taban — ayrı yollar

> Ne oluyor: Bölüm başında taban katta ('KARAKTER DEĞİŞTİR' kartı).

**Rey ile oynarken:**

#### ch17_rey_split
**REY**
- tr: "Yol ikiye ayrılıyor. Sen o tarafta, ben bu tarafta."
- en: "The path splits. You on that side, me on this one."

**Ardo ile oynarken:**

#### ch17_ardo_split
**ARDO**
- tr: "İki ayrı yol. Aramızda demir var."
- en: "Two separate ways. Iron between us."

### 2. Cam

> Ne oluyor: Üçüncü kata ilk çıkışta.

**Rey ile oynarken:**

#### ch17_rey_glass
**REY**
- tr: "Seni görüyorum. Uzatsam elim yetmez."
- en: "I can see you. My hand wouldn't reach."

**Ardo ile oynarken:**

#### ch17_ardo_glass
**ARDO**
- tr: "Bir kol boyu. Ve geçilmiyor."
- en: "An arm's length. And no way across."

### 3. Zirve

> Ne oluyor: Zirveye ilk çıkışta.

**Rey ile oynarken:**

#### ch17_rey_top
**REY**
- tr: "Tepe. İkimiz de geldik."
- en: "The top. We both made it."

**Ardo ile oynarken:**

#### ch17_ardo_top
**ARDO**
- tr: "Çıktık. Ayrı ayrı ama aynı anda."
- en: "We're up. Apart, but at the same time."

### 4. Tutulan kapı

> Ne oluyor: Zirvedeki tetikte ara sahne: yoldaş kapıyı tutar ki oyuncu geçsin; yakın plan.

*Kapı*

**Rey ile oynarken:**

#### ch17_rey_held
**REY**
- tr: "Kapıyı sen tutuyorsun. Bıraksan kapanır."
- en: "You're holding the door. Let go and it shuts."

**Ardo ile oynarken:**

#### ch17_ardo_held
**ARDO**
- tr: "Tutuyor. Ben geçeyim diye orada duruyor."
- en: "She's holding it. Standing there so I can pass."

*Yüz*

**Rey ile oynarken:**

#### ch17_rey_held_face
**REY**
- tr: "Bütün kule bunu öğretiyormuş."
- en: "The whole tower was teaching me this."

**Ardo ile oynarken:**

#### ch17_ardo_held_face
**ARDO**
- tr: "Yalnız tırmandığımı sanıyordum."
- en: "I thought I climbed it alone."

### Ekran yazıları — Bölüm 17

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.twintower
_Bölüm kartı / kayıt yuvası adı_
- tr: "İkili Kule"
- en: "Twin Tower"

#### hint.switch_title
_Hiç karakter değiştirilmemişken bir kez açılan kartın başlığı_
- tr: "KARAKTER DEĞİŞTİR"
- en: "SWITCH CHARACTER"

#### hint.switch
_Aynı kartın gövdesi_
- tr: "[{key}] öteki karaktere geç"
- en: "[{key}] switch to the other"

#### chapter17.tidy
_Bölüm biterken — az karakter değişimiyle çözüldüyse_
- tr: "Kuleyi az geçişle çözdün."
- en: "You solved the tower with few switches."

---

## Bölüm 18 — Son

**Özet:** Zindanın dibi. Yaratık Yankı'yı kullanarak Cemo'nun sesiyle konuşur; son boss Çağıran. Kalachev dördüncü kez gelir ve bu kez ölür, yoldaş kapının dışında kalır. Oyuncu sesi susturmayı seçer ve yardımsız savaşır. Boss düşünce doğrudan kapanış.

### 1. Dip

> Ne oluyor: İlk bölgeye girişte.

**Rey ile oynarken:**

#### ch18_rey_bottom
**REY**
- tr: "Daha aşağısı yok. Burası dibi."
- en: "There's nothing below this. This is the bottom."

**Ardo ile oynarken:**

#### ch18_ardo_bottom
**ARDO**
- tr: "Zindan bitti. Buradan sonrası kaya."
- en: "The dungeon ends here. Past this it's just rock."

### 2. İniş

> Ne oluyor: Aynı bölgedeki tetikte ara sahne: dip, bakış, yüz.

**Rey ile oynarken:**

#### ch18_rey_deep
**REY**
- tr: "On sekiz kat indim. Sesler hep buraya çağırdı."
- en: "Eighteen floors down. The voices called me here the whole way."

#### ch18_rey_deep_face
**REY**
- tr: "Neredeyse geldim Cemo."
- en: "I'm almost there, Cemo."

**Ardo ile oynarken:**

#### ch18_ardo_deep
**ARDO**
- tr: "Aşağı inmek kolaydı. Asıl soru neden çağırdığı."
- en: "Going down was easy. The question is why it called."

#### ch18_ardo_deep_face
**ARDO**
- tr: "Onu bulacağım. Sonra buradan çıkarız."
- en: "I'll find him. Then we get out."

### 3. Cemo'nun sesi

> Ne oluyor: İkinci bölgeye (ses) girişte: müzik tamamen kesilir, zaman bir an durur (Şok 4). Rey'de Cemo'nun B1'deki kolye cümlesi **aynı anahtarla** geri gelir — ama bu kez yaratığın ağzından; Ardo'da yalnızca kendi gözlemi.

**Rey ile oynarken:**

> _Tekrar — aynı anahtar, düzenlenebilir blok Bölüm 1, 2. an (Kolye):_ **CEMO** · `ch01_cemo_gift` — "Bunu senin için yaptım... Belki karanlık sana yaklaşırken iki kez düşünür."

#### ch18_rey_voice
**REY**
- tr: "Cemo? — Sesi bu taraftan geliyor."
- en: "Cemo? — The voice is coming from over there."

**Ardo ile oynarken:**

#### ch18_ardo_voice
**ARDO**
- tr: "Bir çocuk sesi. Ama duvarlar da fısıldıyor."
- en: "A child's voice. But the walls whisper too."

### 4. Ses — boşluk

> Ne oluyor: Aynı bölgedeki tetikte ara sahne: oyuncu sese koşar, durur, orada kimse yok; yüz.

*Duy*

**Rey ile oynarken:**

#### ch18_rey_hear
**REY**
- tr: "Cemo! Duyuyorum seni!"
- en: "Cemo! I can hear you!"

**Ardo ile oynarken:**

#### ch18_ardo_hear
**ARDO**
- tr: "İşte. Tam ileride."
- en: "There. Straight ahead."

*Dur*

**Rey ile oynarken:**

#### ch18_rey_empty
**REY**
- tr: "...boş. Hiç kimse yok."
- en: "...empty. There's no one here."

**Ardo ile oynarken:**

#### ch18_ardo_empty
**ARDO**
- tr: "Elimi geçirdim. Orada bir şey yoktu."
- en: "My hand went right through. Nothing was there."

*Yüz*

**Rey ile oynarken:**

#### ch18_rey_empty_face
**REY**
- tr: "Onun sesiyle konuştu. Onun sesiyle."
- en: "It spoke with his voice. With his voice."

**Ardo ile oynarken:**

#### ch18_ardo_empty_face
**ARDO**
- tr: "Beni buraya kadar böyle getirdi."
- en: "That's how it walked me all the way down."

### 5. Çağıran'ın adı

> Ne oluyor: Arenanın girişindeki tetikte arena mühürlenir, boss belirir ve ara sahne oynar: karanlık, yükselen gövde, ad, yüz.

*Ad*

**Rey ile oynarken:**

#### ch18_rey_name
**REY**
- tr: "Sen değildin. Hiç sen olmamışsın."
- en: "It was never you. It was never you at all."

**Ardo ile oynarken:**

#### ch18_ardo_name
**ARDO**
- tr: "Bunca yol. Ve çağıran hep buydu."
- en: "All this way. And the thing calling was this."

*Yüz*

**Rey ile oynarken:**

#### ch18_rey_name_face
**REY**
- tr: "Kafamdaki ses. Hep senmişsin."
- en: "The voice in my head. It was always you."

**Ardo ile oynarken:**

#### ch18_ardo_name_face
**ARDO**
- tr: "Ona güvenmiştim. O da bunu biliyordu."
- en: "I trusted it. And it knew that."

### 6. Kalachev — son kez

> Ne oluyor: Aynı tetikle çağrılan Kalachev'in karşılaşma sahnesi, Çağıran sahnesinden hemen sonra oynar (kod önce Kalachev sahnesini, üstüne ad sahnesini yığına koyuyor). Dördü birlikte arenada.

**Rey ile oynarken:**

#### ch18_rey_kalachev
**REY**
- tr: "Kalachev. Kapı kapanırsa dönüş yok."
- en: "Kalachev. Once that gate shuts, there's no way back."

#### ch18_kalachev_gate
**KALACHEV**
- tr: "Biliyorum. Çocuğu al, gerisini bana bırak."
- en: "I know. Get the boy. Leave the rest to me."

**Ardo ile oynarken:**

#### ch18_ardo_kalachev
**ARDO**
- tr: "Kalachev. Şu işi bitirelim. Hesabımız kaldı."
- en: "Kalachev. Let's finish this. You still owe me."

#### ch18_kalachev_debt
**KALACHEV**
- tr: "Yukarıda, Ardo. Buradan çıkınca."
- en: "Topside, Ardo. Once we're out."

### 7. Alınıyor — faz 2 (oyuncu izler)

> Ne oluyor: Çağıran ilk kez diz çöktüğünde kontrol kilitlenir ve zamanlı bir dizi işler: Cemo'nun sesi (yaratığın taklidi) → mühür açılır → Kalachev sese koşar, oyuncu bağırır → Kalachev ölür → yoldaş peşinden gider → kapı iner, yoldaş dışarıda kalır → kontrol geri gelir. Replikler zamanlayıcıyla geldiği için okunmamış bir satır bir sonrakiyle değişebilir.

*Ses*

#### ch18_cemo_call
**CEMO — Çağıran, Cemo'nun sesini taklit ediyor**
- tr: "Beni burada bırakma. Ne olur... buradayım."
- en: "Don't leave me here. Please... I'm here."

*Koşu*

**Rey ile oynarken:**

#### ch18_rey_stop
**REY**
- tr: "Kalachev, dur! Kardeşim orada değil!"
- en: "Kalachev, stop! My brother isn't over there!"

**Ardo ile oynarken:**

#### ch18_ardo_stop
**ARDO**
- tr: "Efe! O ses gerçek değil. Bana bak!"
- en: "Efe! That voice isn't real. Look at me!"

*Kalachev'in son sözü*

#### ch18_kalachev_last
**KALACHEV**
- tr: "Buradayım. Bu kez bırakmam."
- en: "I'm here. Not leaving you this time."

*Yoldaş peşinden*

#### ch18_ally_after
**YOLDAŞ — Rey ile ARDO, Ardo ile REY**
- tr: "Geri dur! Onu buradan çıkaracağım!"
- en: "Stay back! I'm getting him out!"

*Kontrol geri gelince*

**Rey ile oynarken:**

#### ch18_rey_alone
**REY**
- tr: "Bir kişiyi daha alamayacaksın."
- en: "You don't get to take anyone else."

**Ardo ile oynarken:**

#### ch18_ardo_alone
**ARDO**
- tr: "Efe... Bunca yolu bunun için yürümedik."
- en: "Efe... We didn't come all this way for this."

### 8. Susturma kararı

> Ne oluyor: Faz 2 bitince ara sahne: oyuncu durur, soru, kelimesiz jest seçimi, cevap, yüz. Sonra Yankı tuşu basılı tutularak ses susturulur ve dövüş yardımsız sürer. Boss düşüp çıkışa varılınca bölüm sonu ekranı olmadan kapanışa geçilir.

*Duruş*

**Rey ile oynarken:**

#### ch18_rey_ask
**REY**
- tr: "Ölmüyor. Ben dinledikçe ölmüyor."
- en: "It won't die. It won't die while I'm listening."

**Ardo ile oynarken:**

#### ch18_ardo_ask
**ARDO**
- tr: "Yankı açıkken kalkıyor. Bağ o."
- en: "It rises while the Echo is open. That's the tie."

*Yüz*

**Rey ile oynarken:**

#### ch18_rey_ask_face
**REY**
- tr: "Bırakırsam kör kalırım. Bırakmazsam bitmez."
- en: "Let go and I'm blind. Hold on and it never ends."

**Ardo ile oynarken:**

#### ch18_ardo_ask_face
**ARDO**
- tr: "Yardımsız. Zaten hep öyle dövüştüm."
- en: "Unaided. That's how I always fought anyway."

### Ekran yazıları — Bölüm 18

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### chapter.end
_Bölüm kartı / kayıt yuvası adı_
- tr: "Son"
- en: "The End"

#### boss.caller
_Boss can barındaki ad_
- tr: "ÇAĞIRAN"
- en: "THE CALLER"

#### hint.silence
_Susturma açılınca bir kez (bildirim)_
- tr: "[{key}] basılı tut — sesi sustur"
- en: "Hold [{key}] — silence the voice"

#### chapter18.silenced
_Ses susturulunca_
- tr: "Sustu. İlk kez kendi başınasın."
- en: "Silence. For the first time, you're alone."

---

## Kapanış — Şafak ve jenerik

**Özet:** B18'in çıkışından doğrudan: gün ışığı, üçlü son panel (Cemo önde, oyuncu ortada, yoldaş arkada — mesafe B16'daki jeste göre) ve Rey'in kafası ilk kez sessiz. Ardından jenerik ve ana menü.

### 1. Şafak

> Ne oluyor: Çağıran yenilip çıkışa varılınca (`src/scenes/ending.py`). Panel panel; her replik oynanan karakterin.

*Kolye*

**Rey ile oynarken:**

#### ch18_rey_dawn
**REY**
- tr: "Kolyen. Sende kalsın."
- en: "Your necklace. Keep it."

**Ardo ile oynarken:**

#### ch18_ardo_dawn
**ARDO**
- tr: "Onu ablasına götürdüm. Kolye de yanında."
- en: "I brought him back to his sister. The necklace too."

*Üçlü*

**Rey ile oynarken:**

#### ch18_rey_three
**REY**
- tr: "Üçümüz. Yukarı."
- en: "The three of us. Upward."

**Ardo ile oynarken:**

#### ch18_ardo_three
**ARDO**
- tr: "Çıkış orada. Yürüyebiliyoruz."
- en: "The way out is there. We can walk."

*Bakış — yalnızca Kalachev B18'de öldüyse (normal akışta hep)*

**Rey ile oynarken:**

#### ch18_rey_lookback
**REY**
- tr: "Ardo?.. Tamam. Seni bekliyoruz."
- en: "Ardo?.. All right. We'll wait."

**Ardo ile oynarken:**

#### ch18_ardo_lookback
**ARDO**
- tr: "Hadi, Efe... Hep önden giderdin."
- en: "Come on, Efe... You always went first."

*Sessiz — yakın plan*

**Rey ile oynarken:**

#### ch18_rey_quiet
**REY**
- tr: "Kafamda hiçbir şey yok. İlk kez."
- en: "There's nothing in my head. For the first time."

**Ardo ile oynarken:**

#### ch18_ardo_quiet
**ARDO**
- tr: "Sessiz. Onun için de sessiz artık."
- en: "Quiet. Quiet for her too, now."

### 2. Jenerik

> Ne oluyor: Gün ışığının üzerinde aşağıdan yukarı süzülen satırlar; en sonda oyuncunun kendi yolu (kazanılan bayraklara göre). Replik yok — metinler aşağıdaki listede.

_(Bu anda replik yok.)_

### Ekran yazıları — Kapanış

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

#### credits.title
_Jeneriğin ilk satırı_
- tr: "REY EFSANESİ: YANKILAR"
- en: "LEGEND OF REY: ECHOES"

#### credits.studio
_Stüdyo_
- tr: "Ardeko Studios"
- en: "Ardeko Studios"

#### credits.design
_Tasarım satırı_
- tr: "Tasarım — Arda Güner"
- en: "Design — Arda Güner"

#### credits.code
_Kod satırı_
- tr: "Kod — Arda Güner & Claude"
- en: "Code — Arda Güner & Claude"

#### credits.art
_Sanat satırı_
- tr: "Sanat — prosedürel, 37 renk"
- en: "Art — procedural, 37 colours"

#### credits.thanks
_Teşekkür_
- tr: "Oynadığın için teşekkürler."
- en: "Thank you for playing."

#### credits.path
_'Senin yolun' başlığı (en az bir bayrak kazanıldıysa)_
- tr: "— senin yolun —"
- en: "— your path —"

#### credits.path_ghost
_B15'i hayalet geçtiyse_
- tr: "Kimseyi uyandırmadan geçtin."
- en: "You passed without waking anyone."

#### credits.path_lifted
_B16'da yoldaşı kaldırdıysa_
- tr: "Onu yerden kaldırdın."
- en: "You pulled them back up."

#### credits.path_tidy
_B17'yi az geçişle çözdüyse_
- tr: "Kuleyi tereddütsüz çözdün."
- en: "You solved the tower without hesitating."

#### credits.path_clean
_B18'de Çağıran az dirildiyse_
- tr: "Sesi erken bıraktın."
- en: "You let the voice go early."

---

## Bölümden bağımsız

**Özet:** Belirli bir odaya bağlı olmayan replik ve ekran yazıları.

### 1. Yankı'nın tekil konuşması *(koşullu, bir kez)*

> Ne oluyor: Yankı oyun boyunca kendinden çoğul söz eder ('biz'). Sadakat eşiği (3) aşılınca, suren bir konuşma yokken bir kez tekil konuşur — yalnızca Rey'de. ⚠ Şu an **ulaşılamıyor**: sadakat yalnızca B10'da ±1 değişiyor, en fazla 1 olabiliyor (bkz. Denetim).

#### echo_alone_voice
**YANKI** — _şu an ulaşılamıyor_
- tr: "Artık yalnızca ben kaldım. Sen beni seçtin."
- en: "Only I am left now. You chose me."

### Ekran yazıları — Bölümden bağımsız

_İpucu kartları, bildirimler, adlar. Aynı biçimde düzenlenir; anahtar noktalı yazılır (ad alanı.anahtar)._

_23–24.09.2026 eklendi: dünya içi tuş göstergesinin fiilleri, gezgin tezgâh ve yeni silahlar._

#### prompt.place
_Tuş göstergesi — elde meşale varken sönük yuvanın üstünde (B3)_
- tr: "Yerleştir"
- en: "Place"

#### prompt.take_fire
_Tuş göstergesi — elin boşken yanan yuvanın üstünde (B3)_
- tr: "Ateş al"
- en: "Take fire"

#### prompt.take
_Tuş göstergesi — Mor Alev'in üstünde (B3)_
- tr: "Al"
- en: "Take"

#### prompt.trade
_Tuş göstergesi — Mum Bekçisi'nin üstünde (B3, B7, B12, B16)_
- tr: "Takas"
- en: "Trade"

#### prompt.light
_Tuş göstergesi — mangalın üstünde (B3 boss)_
- tr: "Yak"
- en: "Light"

#### prompt.rest
_Tuş göstergesi — sönmüş kamp ateşinin üstünde (B4)_
- tr: "Dinlen"
- en: "Rest"

#### prompt.turn
_Tuş göstergesi — vana / çark / ayna (B5, B7, B11)_
- tr: "Çevir"
- en: "Turn"

#### prompt.send
_Tuş göstergesi — yoldaşı plakaya ya da çatlaktan gönder (B6, B7)_
- tr: "Gönder"
- en: "Send"

#### prompt.release
_Tuş göstergesi — plakada bekleyen yoldaşın üstünde (B6)_
- tr: "Serbest bırak"
- en: "Release"

#### prompt.boost
_Tuş göstergesi — fırlatma hazırken iki karakterin arasında (B9)_
- tr: "Fırlat"
- en: "Launch"

#### prompt.pull
_Tuş göstergesi — kolun üstünde (B13)_
- tr: "Çek"
- en: "Pull"

#### prompt.lift
_Tuş göstergesi — diz çökmüş yoldaşın üstünde, dolan çubukla (B16)_
- tr: "Kaldır (basılı tut)"
- en: "Lift (hold)"

#### prompt.resonate
_Tuş göstergesi — en yakın kristal / çan / çınlak (B8, B9, B15)_
- tr: "Ses gönder"
- en: "Resonate"

#### shop.title_travel
_Gezgin tezgâhın başlığı (B7, B12, B16)_
- tr: "MUM BEKÇİSİ"
- en: "CANDLE KEEPER"

#### shop.footer
_Tezgâhın alt satırı — tuş adları atamadan okunur_
- tr: "[{buy}] al   [{leave}] çık"
- en: "[{buy}] buy   [{leave}] leave"

#### shop.full
_Tezgâhta çanta dolu olan satırın sağında_
- tr: "dolu"
- en: "full"

#### shop.full_toast
_Dolu çantaya almaya çalışınca bildirim_
- tr: "Çantada yer yok"
- en: "No room in the bag"

#### weapon.whisper
_Rey'e özel silahın adı — B10 kaidesi (envanterde de görünür)_
- tr: "Fısıltı"
- en: "Whisper"

#### weapon.spear
_Ardo'ya özel silahın adı — B10 kaidesi_
- tr: "İz Mızrağı"
- en: "Tracker's Spear"

#### weapon.sickle
_Ortak yeni silahın adı — B14 kaidesi, iki karakterde de_
- tr: "Zincir Orak"
- en: "Chain Sickle"

#### hint.weapon_whisper_title
_Fısıltı alınınca açılan mekanik kartının başlığı (B10, Rey)_
- tr: "FISILTI"
- en: "WHISPER"

#### hint.weapon_whisper
_Aynı kartın gövdesi — {key} saldırı tuşu_
- tr: "[{key}] son vuruş ses dalgası atar"
- en: "[{key}] last blow sends a sound wave"

#### hint.weapon_spear_title
_İz Mızrağı alınınca kart başlığı (B10, Ardo)_
- tr: "İZ MIZRAĞI"
- en: "TRACKER'S SPEAR"

#### hint.weapon_spear
_Aynı kartın gövdesi — {key} saldırı tuşu_
- tr: "[{key}] uzaktan vur; sonda ileri atıl"
- en: "[{key}] long reach; last blow lunges"

#### hint.weapon_sickle_title
_Zincir Orak alınınca kart başlığı (B14)_
- tr: "ZİNCİR ORAK"
- en: "CHAIN SICKLE"

#### hint.weapon_sickle
_Aynı kartın gövdesi — {key} saldırı tuşu_
- tr: "[{key}] son vuruş iki yanı biçer"
- en: "[{key}] last blow cuts both sides"

#### hint.dialogue
_İlk replik tamamen yazılınca bir kez (B1)_
- tr: "[{key}] devam"
- en: "[{key}] continue"

#### ability.sword
_Kılıç alınınca — B1'de Jet'ten (tuş adı atamadan okunur — 23.09.2026)_
- tr: "KILIÇ  ·  [{key}] ile saldır"
- en: "SWORD  ·  attack with [{key}]"

#### ability.echo_sight
_Yankı Görüşü açılınca — B1 (tuş adı atamadan okunur — 23.09.2026)_
- tr: "YANKI GÖRÜŞÜ  ·  [{key}] basılı tut"
- en: "ECHO SIGHT  ·  hold [{key}]"

#### ability.echo_ask
_⚠ Hiçbir yerde tetiklenmiyor_
- tr: "YANKI'YA SOR  ·  [{key}]"
- en: "ASK THE ECHO  ·  [{key}]"

#### ability.double_jump
_⚠ Hiçbir yerde tetiklenmiyor_
- tr: "ÇİFT ZIPLAMA  ·  havada tekrar [{key}]"
- en: "DOUBLE JUMP  ·  [{key}] again in the air"

#### ability.wall_jump
_⚠ Hiçbir yerde tetiklenmiyor_
- tr: "DUVAR ZIPLAMASI  ·  duvara yaslan, [{key}]"
- en: "WALL JUMP  ·  lean on a wall, [{key}]"

#### ability.unknown
_Bilinmeyen yetenek için yedek_
- tr: "?"
- en: "?"

#### echo.wall_broken
_Yankı ile kırılabilir duvar yıkılınca_
- tr: "Gizli geçit açıldı"
- en: "A hidden passage opens"

#### echo.tier_up
_Yankı kademesi yükselince_
- tr: "Yankı berraklaşıyor"
- en: "The Echo clears"

#### echo.tier_down
_Yankı kademesi düşünce_
- tr: "Yankı zayıflıyor"
- en: "The Echo weakens"

#### companion.waiting
_Yoldaşa 'bekle' denince_
- tr: "Burada bekliyor"
- en: "Waiting here"

#### companion.following
_Yoldaş yeniden takibe geçince_
- tr: "Peşinden geliyor"
- en: "Following you"

#### boss.unknown
_Adı olmayan boss için yedek_
- tr: "İSİMSİZ"
- en: "NAMELESS"

---

## Denetim — bulunamayan, eksik ve görünmeyen anahtarlar

Kaynak taraması (`src/**/*.py` içinde düz `"line.…"` dizesi; `tests/test_lang.py` ile aynı yöntem) ve oyunu başsız çalıştırarak yapılan doğrulamalar. Tarih: 23.09.2026.

### Dil tablosunda olup kodda bulunamayan diyalog anahtarları

**Yok.** `line.` ad alanındaki 406 anahtarın hepsi kodda düz dize olarak geçiyor ve bu belgede yerleştirildi. Hesaplanmış (f-string) anahtar da yok.

Sahne dosyası dışında (ama kullanılan) yerlerde duranlar:

- `ch12_mark_arrow` — src/world/rooms/chapter12.py
- `ch12_mark_arrow_ardo` — src/world/rooms/chapter12.py
- `ch12_mark_cache` — src/world/rooms/chapter12.py
- `ch12_mark_cache_ardo` — src/world/rooms/chapter12.py
- `ch12_mark_camp` — src/world/rooms/chapter12.py
- `ch12_mark_camp_ardo` — src/world/rooms/chapter12.py
- `ch12_mark_count` — src/world/rooms/chapter12.py
- `ch12_mark_count_ardo` — src/world/rooms/chapter12.py
- `ch12_mark_figure` — src/world/rooms/chapter12.py
- `ch12_mark_figure_ardo` — src/world/rooms/chapter12.py
- `ch12_mark_pair` — src/world/rooms/chapter12.py
- `ch12_mark_pair_ardo` — src/world/rooms/chapter12.py
- `ch12_mark_pencil` — src/world/rooms/chapter12.py
- `ch12_mark_pencil_ardo` — src/world/rooms/chapter12.py
- `kalachev_name` — src/scenes/chapter04_render.py

### Kodda geçip dil tablosunda olmayan diyalog anahtarları

**Yok.** (`line.` dışındaki ad alanları için bkz. `python tests/test_lang.py` — "kodun kullandığı her anahtar tabloda var" denetimi.)

### Kodda geçen ama oyunda görünmeyen ya da yanlış yerde görünen replikler

Anahtar tabloda ve kodda var, test geçiyor — ama oyuncu repliği ya hiç görmüyor ya da beklenmeyen bir durumda görüyor. Metne dokunulmadı; karar tasarımcının.

1. ✅ **Düzeltildi (23.09.2026).** **`ch04_echo_name`, `ch04_ardo_name` — hiç görünmüyordu (hata).** `src/scenes/chapter04.py` iskelet hatırasında `self.say(self._voice("line.ch04_echo_name", "line.ch04_ardo_name"))` diyor. `_voice` repliği kendisi başlatıyor ve `None` döndürüyor; ardından gelen `say(None)` diyalog kuyruğunu `(None,)` ile değiştiriyor ve replik aynı karede siliniyor. Oyun başsız çalıştırılarak doğrulandı: iki karakterde de hatıra belirdiği karede `dialogue.lines == (None,)`. Düzeltme tek satır: dış `self.say(...)` kaldırılmalı. (Aynı yolda Yankı o an susturulmuşsa `say(None)` `None.speaker` yüzünden çöker.)
2. **`echo_alone_voice` — ulaşılamıyor.** `PlayScene._watch_intimacy` sadakat ≥ 3 olunca oynatıyor (`loyalty.INTIMACY_THRESHOLD`). Sadakat yalnızca B10'da değişiyor (`loyalty.followed` / `ignored`, ±1) ve 0'dan başlıyor; en fazla 1 olabiliyor.
3. **`ch10_lie_sprung`, `ch10_lie_sprung_react`, `ch10_trace_sprung` (ve `chapter10.creak`, `chapter10.trap` bildirimleri) — normal oyunda ulaşılamıyor.** `Chapter10Scene._update_ally` oyuncu tuzağın 11 tile soluna gelince Kalachev'i çağırıp zemini önceden çökertiyor; satır kontrolü olmadığı için bu **alt yolda da** oluyor. Başsız simülasyonla doğrulandı: iki yolda da 61. sütunda `trap_broken=True`, `trap_sprung` hiç True olmuyor. Aynı nedenle Kalachev'in B10 sahnesi seçime bağlı değil, her oynayışta çıkıyor. (`tests/test_chapter10.py` tuzağı `_update_trap()`'i doğrudan çağırarak sınıyor, bu yüzden yakalamıyor.)
4. **`ch09_rey_top`, `ch09_ardo_top` — koşullu; çanları tepeye çıkmadan çözmeyen oyuncu hiç görmez.** Tepe katına ilk girişte `_narrate` bu repliği başlatıyor, ama çanlar çözülmemişse aynı karede `_update_top_hint` `ch09_echo_locked` / `ch09_trace_locked` ile üstüne yazıyor. Kat anlatımı yalnızca ilk girişte oynadığı için çanları sonra çözen oyuncu tepe repliğini hiç görmüyor. (Metin "Fresk doğruydu..." olduğundan, çözülmeden görünmesi zaten yanlış olurdu.)
5. **`ch11_echo_lie`, `ch11_trace_lie` — sadakat < 0 iken görünmüyor.** `Chapter11Scene._update_lie` yalanı `say()` ile başlatıp aynı karede `say_player("line.ch11_rey_doubt", ...)` çağırıyor; `say()` kuyruğu değiştirdiği için B10'da alt yolu seçen oyuncu yalanı hiç görmeden ona verilen cevabı ("Geçen sefer de böyle söylemiştin.") görüyor. `chapter18.py`'deki not aynı tuzağı anlatıyor: iki replik tek `say()` çağrısında verilmeli.
6. **Yankı replikleri Ardo ile de çıkıyor (karakter kontrolü yok):** `ch02_echo_fall` (B2 düşüş sahnesinin paneli, `chapter02_cinematics.py`), `ch15_echo_kalachev` ve `ch15_echo_kalachev_wakes` (`chapter15.py` `Line(ECHO, …)`, `has_echo` denetimi yok). Tasarım gereği Ardo Yankı'yı duymaz (`docs/gdd.md` §4).
7. **Kayıt yuvası başına bir kez oynayanlar:** Jet'in dönüşleri (`ch04_/ch09_/ch15_jet_*`), B5'teki Kalachev ilk görüşü, B13'te Kalachev'in kapıya gelişi (yaralanınca bir daha gelmiyor). Aynı yuvada tekrar oynayan onları ikinci kez görmez; yeni oyunda yeniden oynar.
8. ✅ **Tuş adları düzeltildi (23.09.2026)** — `ability.*` artık `{key}` ile atanmış tuşu okuyor. **Ekran yazıları:** `ability.echo_ask`, `ability.double_jump`, `ability.wall_jump` hiçbir yerde gösterilmiyor (bu yetenekler `on_ability_gained` ile verilmiyor). `ability.*` metinleri tuş adını (J, Shift, K, F) metnin içine sabit yazıyor; `hint.*` kartları ise atanmış tuşu `{key}` ile okuyor — tuşu yeniden atayan oyuncu `ability.*` bildiriminde yanlış tuşu görür.
