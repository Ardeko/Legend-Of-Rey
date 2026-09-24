# ÖNERİLEN YENİ REPLİKLER

> **Bu belge bir öneridir, bağlayıcı değildir.** ✅ ile işaretli maddeler
> uygulandı (anahtarları artık tablolarda); geri kalanların anahtarları
> kodda ya da dil tablolarında yok. Bir öneri onaylanırsa önce
> kodda yerini bulmalı (düz dize anahtar, `tests/test_lang.py` kuralı),
> sonra `tr.json` / `en.json`'a eklenmeli, en son `docs/senaryo-akisi.md`'ye
> blok olarak girmeli. Bu dosya `dialogue_dump.py --geri` ile **okunmaz**.
>
> 24.09.2026, `docs/senaryo-akisi.md` yeniden yazımıyla birlikte hazırlandı.
> Bütün metinler oyundaki diyalog kutusunun sınırından geçirildi (portreli
> kutu: satır başına 59 karakter, en fazla 3 satır).

Sıralama öncelik sırasıdır. Her maddede: yer, tetikleyici, karakter seçimi,
önerilen anahtar, konuşmacı ve metin.

---

## Öncelik 1 — Hikâyede boşluk kapatanlar

### 1. ✅ Kapanış — Cemo kolye cümlesini kapatıyor

> **Uygulandı (24.09.2026)** — anahtarlar ve metinler aynen; `ending.py`
> "kolye" paneli artık `lines=` dizisi. Yeri: `docs/senaryo-akisi.md` →
> Kapanış → Şafak.

- **Yer:** Kapanış, "kolye" paneli; `ch18_rey_dawn` / `ch18_ardo_dawn` repliğinden hemen sonra.
- **Tetikleyici:** Aynı panelin ikinci ve üçüncü repliği. `ending.py` bu paneli şu an tek `line=` ile kuruyor; `lines=` dizisine çevrilmeli.
- **Karakter seçimi:** Cemo'nun sorusu ikisinde de; cevap karaktere göre.
- **Önerilen anahtarlar:** `ch18_cemo_dawn`, `ch18_rey_dawn_answer`, `ch18_ardo_dawn_answer`
- **Neden:** B1'de Cemo'nun umudu, B4'te Yankı'nın alayı ("Peki... iki kere düşündü mü?"), B18'de yaratığın silahı olan cümle, son kez sahibinin ağzından ve cevabıyla kapanıyor.

- Konuşmacı: **CEMO**
  - TR: "İki kere düşündü mü?"
  - EN: "Did it think twice?"
- Konuşmacı: **REY** (Rey ile)
  - TR: "Düşündü. Hem de uzun uzun."
  - EN: "It did. Long and hard."
- Konuşmacı: **ARDO** (Ardo ile)
  - TR: "Düşündü, evlat. Ben şahidim."
  - EN: "It did, kid. I saw it myself."

### 2. ✅ Kapanış — Jet ipin başında

> **Karşılandı, başka biçimde (24.09.2026).** Kapanışa panel eklenmedi;
> ip bir **epilog** oldu (`docs/yapi.md` Epilog). Kuyunun dibinde oyuncu
> Jet'e adıyla seslenir (`epi_rey_call` / `epi_ardo_call`, cevap
> `epi_jet_answer`), köyde Jet ipin başında karşılar (`epi_jet_welcome`,
> `epi_cemo_thanks`, `epi_jet_name`). Aşağıdaki `ch18_jet_rope*`
> anahtarları **eklenmedi**.

- **Yer:** Kapanış, "üçlü" panelinden sonra yeni bir panel ("ip").
- **Tetikleyici:** Jet'in dönüşlerinden en az biri görüldüyse (`ch04_jet_return_seen`, `ch09_jet_return_seen` ya da `ch15_jet_return_seen`). Hiçbiri görülmediyse panel atlanır.
- **Karakter seçimi:** Jet ikisinde de; cevap karaktere göre.
- **Önerilen anahtarlar:** `ch18_jet_rope`, `ch18_rey_jet_rope`, `ch18_ardo_jet_rope`
- **Neden:** Jet üç kez "ip yerinde, burada olacağım" diyor ve oyun bu sözün karşılığını hiç göstermiyor.

- Konuşmacı: **JET**
  - TR: "İp yerinde, söz verdiğim gibi. Hoş geldin, Cemo."
  - EN: "The rope is where I promised it would be. Welcome back, Cemo."
- Konuşmacı: **REY** (Rey ile)
  - TR: "Emre. Beklemişsin."
  - EN: "Emre. You waited."
- Konuşmacı: **ARDO** (Ardo ile)
  - TR: "Hâlâ buradasın. Hiç söz dinlemedin."
  - EN: "Still here. You never did listen."

### 3. B13 — Kalachev yaralanınca kendi sözü

- **Yer:** B13, 7. an; `ch13_rey_wound` / `ch13_ardo_wound` repliğinden hemen sonra, aynı `say()` çağrısında.
- **Tetikleyici:** `on_boss_phase`: Zindancı Kalachev'i yakaladığı an.
- **Karakter seçimi:** Kalachev ikisinde de, lakap karaktere göre.
- **Önerilen anahtarlar:** `ch13_kalachev_scratch` (Rey ile), `ch13_kalachev_tab` (Ardo ile)
- **Neden:** Hiç susmayan adam en ağır anında sessiz kalıyor; sessizliği B18'e saklamak daha güçlü.

- Konuşmacı: **KALACHEV** (Rey ile)
  - TR: "Sıyrık bu, sıyrık! ...Tamam, biraz geri çekiliyorum, Kırmızı Başlıklı. Nefeslenmek için. Tek kelime etme."
  - EN: "It's a scratch, a scratch! ...Fine, I'm stepping back, Red. Just to catch my breath. Not a word."
- Konuşmacı: **KALACHEV** (Ardo ile)
  - TR: "Bağırma, Ayı; sağır olmadım, sadece delindim. Bunu da yukarıda hesaba yazarsın."
  - EN: "Stop yelling, Bear. I'm not deaf, just leaking. Put it on my tab for topside."

### 4. B18 faz 1 — Kalachev'in son şakası

- **Yer:** B18, arena mühürlendikten sonra, faz 1.
- **Tetikleyici:** Kalachev'in Çağıran'a ilk isabetinde, bir kez (`PHASE_TOGETHER`).
- **Karakter seçimi:** İkisinde de (lakapsız, tek anahtar).
- **Önerilen anahtar:** `ch18_kalachev_bark`
- **Neden:** Faz 2'deki kısa son sözün ("Buradayım. Bu kez bırakmam.") karşıtlığı, hemen öncesinde bir kez daha gevezelik duyulursa işliyor.

- Konuşmacı: **KALACHEV**
  - TR: "Çağıran bu mu? Ben bundan büyüklerini kahvaltıda yerim! ...Tamam, bu biraz büyük."
  - EN: "This is the Caller? I eat bigger things for breakfast! ...All right, this one's a bit big."

### 5. B18 — Çağıran düştükten sonra

- **Yer:** B18, Çağıran öldükten sonra, çıkışa yürürken (kapanıştan önce).
- **Tetikleyici:** Boss öldüğünde, bir kez.
- **Karakter seçimi:** Rey ile / Ardo ile ayrı.
- **Önerilen anahtarlar:** `ch18_rey_caller_down`, `ch18_ardo_caller_down`
- **Neden:** Final dövüşü şu an sözsüz bitiyor; Ardo'nun satırı B6'dan beri açık kalan borç ipliğini kapatıyor.

- Konuşmacı: **REY**
  - TR: "Sustun. Bu sefer sonsuza kadar."
  - EN: "You're quiet. This time for good."
- Konuşmacı: **ARDO**
  - TR: "Bitti, Efe. Borcun ödendi."
  - EN: "It's done, Efe. Your debt is paid."

### 6. B16 — Yoldaş kaldırılınca

- **Yer:** B16, 3. an (Kaldır), oyuncu yoldaşı ayağa kaldırdıktan hemen sonra.
- **Tetikleyici:** Kaldırma ilk kez tamamlandığında (`chapter16.lifted` bayrağının ilk True olduğu kare), bir kez.
- **Karakter seçimi:** Rey ile ARDO konuşur, Ardo ile REY konuşur.
- **Önerilen anahtarlar:** `ch16_ardo_lifted`, `ch16_rey_lifted`
- **Neden:** `docs/yapi.md` B16'nın kalbi "bu sefer Rey de onu kurtarır"; kurtarılan tarafın tek bir tepkisi yok.

- Konuşmacı: **ARDO** (Rey ile)
  - TR: "Kalktım. Bunu kimseye anlatma. Hele Efe'ye hiç."
  - EN: "I'm up. Don't tell anyone. Especially not Efe."
- Konuşmacı: **REY** (Ardo ile)
  - TR: "Bırakmadın... Ben de bırakmazdım."
  - EN: "You didn't let go... Neither would I."

---

## Öncelik 2 — Rey ile Ardo'nun yan yana yürüdüğü anlar

`docs/yapi.md` kuralı geçerli: romantik an diyalogla anlatılmaz. Bu
repliklerin hiçbiri duyguyu söylemiyor; yalnızca iki kişinin birbirini
tanımaya başladığını gösteriyor.

### 7. B8 — Ateş başında "yarım bıraktığın şey"

- **Yer:** B8, 1. an; "kolye" ile "ders" panelleri arasına yeni bir panel.
- **Tetikleyici:** Ateş başı sinematiği (`chapter08_cinematics.py`).
- **Karakter seçimi:** İkisinde de aynı ikili (soran Rey, cevaplayan Ardo).
- **Önerilen anahtarlar:** `ch08_fire_rey_ask`, `ch08_fire_ardo_answer`
- **Neden:** B6'da açılan sır ve prologdaki "Bir kere geç kaldım" burada bir adım ilerliyor, ama çözülmüyor.

- Konuşmacı: **REY**
  - TR: "Yarım bıraktığın şey... Sorsam anlatır mısın?"
  - EN: "The thing you left unfinished... If I asked, would you tell me?"
- Konuşmacı: **ARDO**
  - TR: "Bir kere geç kaldım. O kadar. Gerisini daha aşağıda anlatırım."
  - EN: "I was too late once. That's all. I'll tell you the rest further down."

### 8. B6 — Çürümüş Olan düşünce

- **Yer:** B6, 4. an sonrası; `chapter06.boss_down` bildirimiyle aynı anda.
- **Tetikleyici:** Boss öldüğünde, bir kez.
- **Karakter seçimi:** Yoldaş konuşur: Rey ile ARDO, Ardo ile REY.
- **Önerilen anahtarlar:** `ch06_ardo_boss_after`, `ch06_rey_boss_after`

- Konuşmacı: **ARDO** (Rey ile)
  - TR: "Fena değildin. Arkamı da kolladın; not ettim."
  - EN: "Not bad. You watched my back, too. I noticed."
- Konuşmacı: **REY** (Ardo ile)
  - TR: "Fena değildin, koca adam. Bir dahakine arkana da bak."
  - EN: "Not bad, big man. Next time, look behind you too."

### 9. B7 — Çatlaktan önceki koridorda

- **Yer:** B7, 1. oda (kapının önü), `ch07_rey_door` / `ch07_ardo_door`'dan sonra.
- **Tetikleyici:** Yoldaş yanındayken 15 saniye hiç replik çıkmazsa, bir kez.
- **Karakter seçimi:** Rey ile Ardo sorar, Ardo ile Rey sorar.
- **Önerilen anahtarlar:** `ch07_ardo_ask_cemo` + `ch07_rey_about_cemo` (Rey ile), `ch07_rey_ask_efe` + `ch07_ardo_about_efe` (Ardo ile)

- Konuşmacı: **ARDO** (Rey ile)
  - TR: "Kardeşin... Nasıl biridir?"
  - EN: "Your brother... What's he like?"
- Konuşmacı: **REY** (Rey ile)
  - TR: "Hiç susmaz. Her şeyi sorar. Şimdi o soruların hepsini özlüyorum."
  - EN: "He never stops talking. Asks about everything. I miss every one of those questions now."
- Konuşmacı: **REY** (Ardo ile)
  - TR: "Efe... Hep böyle midir?"
  - EN: "Efe... Is he always like that?"
- Konuşmacı: **ARDO** (Ardo ile)
  - TR: "Hep. Bir kere bile değişmedi. İyi ki de değişmedi."
  - EN: "Always. Never changed once. Just as well."

### 10. B8 — İlk kristal kırılınca

- **Yer:** B8, 2. an (Öğrenme).
- **Tetikleyici:** İlk kristal kırıldığında (`chapter08.first_crystal` bildirimiyle).
- **Karakter seçimi:** Yoldaş konuşur.
- **Önerilen anahtarlar:** `ch08_ardo_crystal` (Rey ile), `ch08_rey_crystal` (Ardo ile)

- Konuşmacı: **ARDO** (Rey ile)
  - TR: "İyi. Taş seni dinliyor. Kafandakiler dinlemese de."
  - EN: "Good. The stone listens to you. Even if the ones in your head don't."
- Konuşmacı: **REY** (Ardo ile)
  - TR: "Taşa bu kadar yumuşak konuşabildiğini bilmiyordum."
  - EN: "I didn't know you could talk to stone that gently."

### 11. B9 — İlk fırlatmadan sonra

- **Yer:** B9, 2. an sonrası.
- **Tetikleyici:** İlk fırlatma bitince (`chapter09.first_boost` bildirimiyle).
- **Karakter seçimi:** Fırlatan konuşur: Rey ile ARDO, Ardo ile REY.
- **Önerilen anahtarlar:** `ch09_ardo_first_boost`, `ch09_rey_first_boost`

- Konuşmacı: **ARDO** (Rey ile)
  - TR: "Gördün mü? Düşürmedim. Sen de korkmadın. İyi gidiyoruz."
  - EN: "See? I didn't drop you. And you didn't flinch. We're doing fine."
- Konuşmacı: **REY** (Ardo ile)
  - TR: "Kaldırdım! Ama bir dahakine zırhını aşağıda bırak."
  - EN: "I lifted you! Next time, leave the armour downstairs."

### 12. B16 — Koridorda yoldaşın cevabı

- **Yer:** B16, 4. an (Koridor); `ch16_rey_corridor` / `ch16_ardo_corridor`'dan hemen sonra.
- **Tetikleyici:** Aynı oda girişi, ikinci replik.
- **Karakter seçimi:** Yoldaş cevap verir.
- **Önerilen anahtarlar:** `ch16_ardo_corridor_reply` (Rey ile), `ch16_rey_corridor_reply` (Ardo ile)
- **Neden:** Ardo'nun satırı Efe'yi B18'den önce son bir kez canlı ve gürültülü hatırlatıyor.

- Konuşmacı: **ARDO** (Rey ile)
  - TR: "İki kişiyiz. Efe de bir yerlerde; gürültüsünden anlarız."
  - EN: "Two of us. And Efe's out there somewhere; we'll know him by the noise."
- Konuşmacı: **REY** (Ardo ile)
  - TR: "Ayakta kalırız. Sen düşersen ben kaldırırım; artık biliyorsun."
  - EN: "We'll stay standing. If you fall, I'll lift you. You know that now."

### 13. B17 — Camın öbür yanından cevap

- **Yer:** B17, 2. an (Cam); `ch17_rey_glass` / `ch17_ardo_glass`'tan hemen sonra.
- **Tetikleyici:** Üçüncü kata ilk çıkış, ikinci replik.
- **Karakter seçimi:** Yoldaş cevap verir.
- **Önerilen anahtarlar:** `ch17_ardo_glass_reply` (Rey ile), `ch17_rey_glass_reply` (Ardo ile)
- **Neden:** Bölümün mekaniğini ("biri kolu tutar, öteki geçer") karakterin ağzından bir kez söylüyor.

- Konuşmacı: **ARDO** (Rey ile)
  - TR: "Yetmez. Ama kolu sen tut, kapıdan ben geçeyim; yetişiriz."
  - EN: "It wouldn't. But you hold the lever, I'll take the gate. We'll get there."
- Konuşmacı: **REY** (Ardo ile)
  - TR: "Bir kol boyu, o kadar. Sıra bende; kolu tutuyorum, geç."
  - EN: "Just an arm's length. My turn. I've got the lever, go."

### 14. B18 — Kapı inince, kapının öbür yanından

- **Yer:** B18, 7. an (faz 2); `ch18_ally_after`'dan sonra, kapı indiği an.
- **Tetikleyici:** `_taken_slam`.
- **Karakter seçimi:** Dışarıda kalan yoldaş konuşur.
- **Önerilen anahtarlar:** `ch18_ardo_through_gate` (Rey ile), `ch18_rey_through_gate` (Ardo ile)
- **Neden:** Faz 3'ün yalnızlığı, yoldaşın sesi duvarın arkasında kalınca daha çok hissediliyor.

- Konuşmacı: **ARDO** (Rey ile)
  - TR: "Rey! Kapıyı açmanın bir yolunu bulacağım. Dayan!"
  - EN: "Rey! I'll find a way to open this. Hold on!"
- Konuşmacı: **REY** (Ardo ile)
  - TR: "Ardo! Buradayım, kapının öbür yanındayım! Sakın ölme!"
  - EN: "Ardo! I'm here, right on the other side! Don't you dare die!"

---

## Öncelik 3 — Kalachev sahneleri

### 15. B5 — Dövüş bitince karşı kıyıdan

- **Yer:** B5, 3. an sonrası.
- **Tetikleyici:** Çıkıntıdaki üç yaratığın sonuncusu ölünce, Kalachev suya atlamadan hemen önce, bir kez.
- **Karakter seçimi:** Kalachev ikisinde de, lakap karaktere göre.
- **Önerilen anahtarlar:** `ch05_kalachev_cheer` (Rey ile), `ch05_kalachev_brag` (Ardo ile)

- Konuşmacı: **KALACHEV** (Rey ile)
  - TR: "Üçü de yerde! Tamam, biri kaçtı ama saymıyoruz. Vana senin, Kırmızı Başlıklı; ben aşağı!"
  - EN: "All three down! Fine, one ran off, but we're not counting. The valve's yours, Red. I'm going down!"
- Konuşmacı: **KALACHEV** (Ardo ile)
  - TR: "Gördün mü, Ayı? Üçü de yerde! Vana senin; ben aşağıdan dolaşıyorum. İçkiyi unutma!"
  - EN: "See that, Bear? All three down! The valve's yours; I'm taking the low road. Don't forget that drink!"

### 16. B6 — Rey lakaba itiraz ediyor (Rey ile)

- **Yer:** B6 Kalachev tanışması; `ch06_kalachev_meet`'ten sonra, `ch06_echo_kalachev`'den önce.
- **Tetikleyici:** Aynı panel ("isim").
- **Karakter seçimi:** Yalnızca Rey ile.
- **Önerilen anahtarlar:** `ch06_rey_kalachev_name`, `ch06_kalachev_names`
- **Neden:** Jet'in "başkalarının taktığı ad" temasına ve Rey'in "Lanetli" adına bağlanıyor.

- Konuşmacı: **REY**
  - TR: "Adım Rey."
  - EN: "My name is Rey."
- Konuşmacı: **KALACHEV**
  - TR: "Biliyorum, Kırmızı Başlıklı. Ben ad takarım, ezberlemem."
  - EN: "I know, Red. I give names. I don't memorise them."

### 17. B10 — Kalachev çekilirken

- **Yer:** B10, 4. an sonrası; sahne kapanıp oyuna dönülünce.
- **Tetikleyici:** `KalachevCinematic(beat="trap")` bittiğinde.
- **Karakter seçimi:** Kalachev ikisinde de, lakap karaktere göre.
- **Önerilen anahtarlar:** `ch10_kalachev_off` (Rey ile), `ch10_kalachev_round` (Ardo ile)

- Konuşmacı: **KALACHEV** (Rey ile)
  - TR: "Ben kaçtım. Başka çukur bulursan haber ver... Yok, verme. Kendin çözersin."
  - EN: "I'm off. Find another pit, let me know... No, don't. You'll work it out."
- Konuşmacı: **KALACHEV** (Ardo ile)
  - TR: "Ben kaçar. Yukarıdaki içkiyi unutma, Ayı; ilk kadeh hâlâ benden."
  - EN: "I'm off. Don't forget that drink topside, Bear. First round's still on me."

### 18. B15 — Sürü geride kalınca

- **Yer:** B15, 3. oda (sürü) ile 4. oda (damla) arası.
- **Tetikleyici:** Sürü hiç uyanmadıysa ve Kalachev hâlâ `silent` iken, oyuncu sürü odasından çıkınca.
- **Karakter seçimi:** Kalachev ikisinde de, lakap karaktere göre.
- **Önerilen anahtarlar:** `ch15_kalachev_hush` (Rey ile), `ch15_kalachev_historic` (Ardo ile)
- **Not:** `docs/kalachev.md` §5 onu B15'te bilerek konuşturmuyor; bu yüzden öneri yalnızca sürü duyamayacak kadar uzaklaşıldıktan sonrası için.

- Konuşmacı: **KALACHEV** (Rey ile)
  - TR: "Hayatımda hiç bu kadar uzun susmadım, Kırmızı Başlıklı. Bir yerim patlayacak."
  - EN: "Never kept my mouth shut this long in my life, Red. Something's going to burst."
- Konuşmacı: **KALACHEV** (Ardo ile)
  - TR: "Ayı... Sessiz ol. Evet, bunu ben söylüyorum. Tarihi an, bir yere yaz."
  - EN: "Bear... Keep quiet. Yes, me saying it. Historic moment, write it down."

---

## Öncelik 4 — Jet'in dönüşleri

### 19. B1 — Rey'in Jet'e vedası (Rey ile)

- **Yer:** B1, 5. an; `ch01_jet_leave`'den sonra (Ardo oynanışındaki "Sen de."nin karşılığı).
- **Tetikleyici:** Jet sahnesinin "ayrılık" paneli.
- **Karakter seçimi:** Yalnızca Rey ile.
- **Önerilen anahtar:** `ch01_rey_leave`

- Konuşmacı: **REY**
  - TR: "Sen de... Jet. Ya da Emre. Hangisiysen."
  - EN: "You too... Jet. Or Emre. Whichever you are."

### 20. B4 — Jet'e teşekkür

- **Yer:** B4, 7. an; `ch04_jet_route`'tan sonra, yakın plandan önce.
- **Tetikleyici:** Jet'in dönüş sahnesi, "karşılaşma" paneli.
- **Karakter seçimi:** Rey ile / Ardo ile ayrı.
- **Önerilen anahtarlar:** `ch04_rey_jet_thanks`, `ch04_ardo_jet_thanks`

- Konuşmacı: **REY**
  - TR: "Sağ ol... Benim için kimse ip bağlamamıştı."
  - EN: "Thank you... No one's ever tied a rope for me before."
- Konuşmacı: **ARDO**
  - TR: "İpe güvenirim. Sana daha çok."
  - EN: "I trust the rope. I trust you more."

### 21. B9 — Jet yoldaşı selamlıyor

- **Yer:** B9, 5. an; `ch09_jet_route`'tan önce.
- **Tetikleyici:** Jet'in dönüş sahnesi (yoldaş sahnede).
- **Karakter seçimi:** İkisinde de.
- **Önerilen anahtar:** `ch09_jet_company`

- Konuşmacı: **JET**
  - TR: "Yanında biri var. İyi. Bu yol tek kişilik değil."
  - EN: "Someone is with you. Good. This is not a road for one."

---

## Öncelik 5 — Boss öncesi ve sonrası

### 22. B2 — Şişmiş Olan düşünce

- **Yer:** B2, 4. an sonrası.
- **Tetikleyici:** Mini-boss öldüğünde, silah seçimi ekranından önce.
- **Karakter seçimi:** Rey ile Yankı, Ardo ile Ardo.
- **Önerilen anahtarlar:** `ch02_echo_boss_down`, `ch02_ardo_boss_down`

- Konuşmacı: **YANKI**
  - TR: "Gördün mü? Biz gösterdik, sen vurdun."
  - EN: "See? We showed you. You struck."
- Konuşmacı: **ARDO**
  - TR: "Patlamadan önce yere indi. Şans mı beceri mi, ikisi de işime gelir."
  - EN: "It went down before it burst. Luck or skill, I'll take either."

### 23. B3 — Sönmüş Olan düşünce

- **Yer:** B3, 4. an sonrası.
- **Tetikleyici:** Mini-boss öldüğünde.
- **Karakter seçimi:** Rey ile Yankı, Ardo ile Ardo.
- **Önerilen anahtarlar:** `ch03_echo_boss_down`, `ch03_ardo_boss_down`
- **Neden:** Yankı'nın satırı, girişteki "Söndüğünde yanında kimse yoktu" cümlesini kapatıyor.

- Konuşmacı: **YANKI**
  - TR: "Söndü. Bu sefer yanında biri vardı."
  - EN: "It went out. This time, someone was there."
- Konuşmacı: **ARDO**
  - TR: "Işığı sevmezdi. Son gördüğü şey ışık oldu."
  - EN: "It hated the light. The light was the last thing it saw."

### 24. B13 — Zindancı düşünce

- **Yer:** B13, 8. an; `chapter13.gate_open` bildirimiyle aynı anda, kapı sahnesinden önce.
- **Tetikleyici:** Boss öldüğünde.
- **Karakter seçimi:** Rey ile / Ardo ile ayrı.
- **Önerilen anahtarlar:** `ch13_rey_gaoler_down`, `ch13_ardo_gaoler_down`
- **Neden:** Ardo'nunki kendi "Kolay yolu bir kez teklif ediyorum" repliğini kapatıyor.

- Konuşmacı: **REY**
  - TR: "Anahtarlar... Hadi, Cemo. Hadi."
  - EN: "The keys... Come on, Cemo. Come on."
- Konuşmacı: **ARDO**
  - TR: "Kolay yolu teklif etmiştim."
  - EN: "I did offer the easy way."
