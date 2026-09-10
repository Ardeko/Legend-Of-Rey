# itch.io sayfası — Legend of Rey

Sayfa: https://ardeko.itch.io/legend-of-rey · Düzenleme: **Edit game** ve **Edit theme**.

Bu dosya sayfayı baştan sona kurmak için gereken her şeyi tutuyor: ne
değişiyor, neden, hangi dosya nereye yüklenecek, hangi alana ne yazılacak.

---

## 0. Şu anki sayfa — teşhis

Tema düzenleyicisinden ve sayfanın kendisinden görülen:

| | Şu an | Sorun |
|---|---|---|
| Tema | itch'in varsayılan açık teması: BG `#eeeeee`, BG2 `#ffffff`, yazı `#222222`, bağlantı `#fa5c5c` | Oyun lacivert, siyah ve mor. Açık gri sayfa oyunun tonunu tamamen kaybettiriyor |
| Banner | Uzun kızıl saçlı, altın zırhlı bir kadın savaşçı (1024×1024) | **Rey değil.** Oyundaki Rey'in koyu saçı, mavi tuniği, kırmızı pelerini var |
| Arka plan | Güneşli bir orman, her yöne döşenmiş | Oyun **yeraltında** geçiyor. Orman oyunun hiçbir yerinde yok |
| Ekran görüntüsü | "LEGEND OF REY" yazılı bir şato tablosu (1792×1024) | Oyundan bir kare değil |
| Açıklama | "Brave warrior", "Melee & Ranged Combat", "Win or Lose scenario" | Eski prototip. Cemo, Yankı, Ardo ve 18 bölüm yok |
| Kısa açıklama | Boş — itch "A downloadable Journey" yazıyor | |
| Dosya | `Legend of Rey.rar`, 331 MB | Eski yapı |
| Etiket | **"No generative AI was used"** | ⚠ bkz. §5 |

**Karar:** sayfada oyunda olmayan hiçbir görsel kalmıyor. Oyuncu sayfada
ne görürse oyunda da onu görmeli — kızıl saçlı zırhlı bir kahraman görüp
zindanda koyu saçlı bir kız bulan oyuncu kandırılmış hisseder.

---

## 1. Görseller

Hepsi oyunun kendisinden, oyunun 480×270'lik görüntüsünün **tam sayı
katları** — piksel sanatı bulanıklaşmıyor.

| Sıra | Dosya | Ne | Boyut |
|---|---|---|---|
| Kapak | `kapak.png` | Rey ve Ardo sırt sırta, mor alev, başlık | 630 × 500 (5×) |
| Banner | `banner.png` | Başlık solda, Rey + Ardo + alev sağda | 960 × 240 (3×) |
| 1 | `ekran-01-dovus.png` | Dövüş — combo, vuruş anı | 1920 × 1080 |
| 2 | `ekran-02-boss.png` | Çürümüş Olan (B6) — boss barı | 1920 × 1080 |
| 3 | `ekran-03-karakter.png` | Karakter seçimi — portreler, Yankı | 1920 × 1080 |
| 4 | `ekran-04-aynalar.png` | Ayna Salonu — ışın bulmacası | 1920 × 1080 |
| 5 | `ekran-05-sessizlik.png` | Uyuyan sürü — gizlilik | 1920 × 1080 |
| 6 | `ekran-06-ates.png` | Ateş başı — Rey ve Ardo | 1920 × 1080 |
| 7 | `ekran-07-kafes.png` | Cemo kafeste — "Rey?" | 1920 × 1080 |

Sıra bilinçli: **ilk ekran görüntüsü dövüş.** itch listelerde ve sayfanın
üstünde ilk görseli öne çıkarıyor; oyunun çekirdeği dövüş.

Hiçbiri finali, Kalachev'in kaderini ya da B14'ün dönüşünü göstermiyor.

### Kaldırılacaklar

* Banner'daki kadın savaşçı → `banner.png` ile değiştir
* Arka plan ormanı → **Remove image**. Zemin düz renk (§3)
* "LEGEND OF REY" şato tablosu (ekran görüntüsü) → sil

---

## 2. Edit game — alan alan

| Alan | Değer |
|---|---|
| **Title** | `Legend of Rey` (şu an `Legend Of Rey`) |
| **Short description or tagline** | `The voices in her head lead her to her brother. They are also calling her down.` |
| **Classification** | Games |
| **Kind of project** | Downloadable |
| **Release status** | Released |
| **Pricing** | Name your own price — olduğu gibi |
| **Genre** | Action |
| **Tags** | `pixel-art` `action-rpg` `platformer` `dark-fantasy` `story-rich` `psychological-horror` `2d` `singleplayer` `atmospheric` |
| **AI generation disclosure** | ⚠ bkz. §5 |
| **Languages** | English, Turkish |
| **Inputs** | Keyboard, Xbox controller, Gamepad (any) |
| **Accessibility** | Color-blind friendly, Configurable controls, Interactive tutorial |
| **Average session** | About an hour |
| **Community** | Comments açık |

### Yüklemeler

1. `Legend of Rey.rar` (331 MB) → **sil**
2. `dist/LegendOfRey-1.0-Windows.zip` (83,6 MB) → yükle
   (içinde: exe, `READ-ME.txt` İngilizce, `OKU-BENI.txt` Türkçe)
3. Dosyanın yanında **Windows** kutusunu işaretle — şu an hiçbir platform
   seçili değil, sayfada Windows rozeti yok
4. Görünen ad: `Legend of Rey — Windows (v1.0)`

---

## 3. Edit theme

| Alan | Değer | Neden |
|---|---|---|
| BG | `#06050B` | void — paletin en koyusu |
| BG 2 | `#100E1A` | ink — içerik kutusu |
| BG2 Alpha | tam | |
| Text | `#E4DECC` | bone — oyundaki yazı rengi |
| Link | `#B47EEA` | violet_bright — Yankı'nın rengi |
| Headers | `#FFC660` | gold — bölüm başlıkları |
| Buttons | `#6A34A0` | violet |
| Font | Lato, Large | okunur kalsın |
| Banner | `banner.png`, Align: Center | |
| Background | **Remove image** | düz renk yeter; ormanı değiştirmek için bir resim gerekmiyor |
| Screenshots | Auto | |

---

## 4. Açıklama

itch'in keşif sayfaları İngilizce: üstte İngilizce, altta Türkçe.
Olduğu gibi yapıştırılabilir.

### İngilizce

```
Rey has always heard voices. The village calls her cursed.

When her little brother Cemo is dragged into a rift beneath the village,
those voices are the only thing that can lead her to him. They show her
what hides behind the walls, where the enemies wait, which path is safe.

They help her. They are also calling her down.

18 chapters · about 4 hours · two playable characters

WHAT YOU'LL FIND
• Fast, readable combat — combo chains, dodge counters, kill-cancel.
  Every enemy attack is telegraphed; if you get hit, you could have seen it.
• The Echo — see through walls, ask the voice questions... and learn
  when it lies to you.
• Two ways to play the same dungeon: Rey hears the voices. Ardo has none,
  and reads the traces the dead left behind instead.
• Puzzles that grow out of the story: carry a single torch through total
  darkness, flood a cellar, bend light with mirrors, walk silently past a
  sleeping pack, control two characters through a twin tower.
• Four bosses — and a finale that takes something from you.
• A psychological horror layer woven into the game. It can be reduced or
  turned off in the settings.

ACCESSIBILITY
Fully remappable keyboard and gamepad controls · three colour-blind modes ·
granular difficulty (damage taken, enemy speed, auto-combo, Echo penalty) ·
screen shake and flash limits · Turkish and English.

CONTROLS
Move: Arrows / A-D · Jump: Space / W / Z · Attack: J / X
Dodge: Shift / L / C · Interact: E · Echo (hold): Q / K · Ask the Echo: F
Pause: Esc — everything can be rebound in Settings. Gamepad is off by
default; turn it on in Settings.

GOOD TO KNOW
• The game starts in Turkish. Switch to English on the main menu:
  AYARLAR → OYNANIŞ → Dil → English.
• Windows only. Unzip and run "Legend of Rey.exe" — no installer.
• The game isn't code-signed, so Windows may show a SmartScreen warning:
  More info → Run anyway.
• The first launch takes a few seconds while the game unpacks itself.
• Saves are kept in %APPDATA%\LegendOfRey — two save slots.

Contains fantasy violence, blood, psychological horror and the death of a
character.

Made by Ardeko Studios.
```

### Türkçe

```
Rey sesler duyuyor. Köy ona lanetli diyor.

Küçük kardeşi Cemo köyün altında açılan bir yarıktan içeri çekildiğinde,
onu bulabilecek tek şey o sesler. Duvarların ardını, düşmanların nerede
beklediğini, hangi yolun güvenli olduğunu gösteriyorlar.

Ona yardım ediyorlar. Ve onu aşağı çağırıyorlar.

18 bölüm · yaklaşık 4 saat · iki oynanabilir karakter

• Hızlı ve okunur dövüş — combo zinciri, kaçınma sonrası karşı vuruş,
  ölünce iptal. Her düşman saldırısı önceden okunabilir.
• Yankı — duvarların ardını gör, sese soru sor... ve ne zaman yalan
  söylediğini öğren.
• Aynı zindan, iki farklı oyun: Rey sesleri duyar. Ardo'nun sesi yoktur;
  ölülerin bıraktığı izleri okur.
• Hikâyeden doğan bulmacalar: tek bir meşaleyle zifiri karanlık, su basan
  mahzen, aynalarla kırılan ışık, uyuyan sürünün arasından sessizce geçiş,
  iki karakterle ikiz kule.
• Dört boss — ve senden bir şey alan bir final.
• Oyuna işlenmiş bir psikolojik korku katmanı; ayarlardan azaltılabilir ya
  da kapatılabilir.

Erişilebilirlik: tam tuş atama (klavye + gamepad), üç renk körü modu,
ayrıntılı zorluk, sarsıntı ve parlama sınırı, Türkçe ve İngilizce.

Yalnızca Windows. Zip'i aç, "Legend of Rey.exe"yi çalıştır — kurulum yok.
Windows "bilinmeyen yayıncı" derse: Ek bilgi → Yine de çalıştır.

Fantastik şiddet, kan, psikolojik korku ve bir karakterin ölümünü içerir.

Ardeko Studios.
```

---

## 5. ⚠ "No generative AI was used" — kaldırılmalı

Bu etiket şu an doğru değil, üç ayrı yerden:

1. **Sayfanın kendi görselleri** — banner 1024×1024, ekran görüntüsü
   1792×1024. İkisi de AI görsel üreticilerinin standart çıktı boyutu ve
   görünüşleri de öyle.
2. **Oyundaki portreler** — `assets/PROMPTLAR.md` portreler için yazılmış
   üretim promptlarını tutuyor; `assets/portraits/kaynak/` o promptların
   istediği boyutta beş asıl dosya tutuyor.
3. **Kod** bir AI kodlama asistanıyla yazıldı.

Yukarıdaki yeni görsellerin hepsi oyunun kendisinden, yani 1. madde
çözülüyor. 2. ve 3. madde oyunun içinde, sayfayı değiştirmek onları
değiştirmiyor.

**Öneri:** etiketi kaldır ve Edit game'deki AI beyan alanında *Graphics*
seç (portreler); istersen *Code* da. itch beyanı zorunlu tutuyor ve yanlış
etiket sayfanın işaretlenmesine yol açabilir. Müziğin kaynağını sen
biliyorsun — o da üretildiyse *Sound*.

---

## 6. İsteğe bağlı — çizim tarzında kapak için promptlar

**Önerim oyunun kendi görselleri** (§1): oyunu dürüstçe gösteriyorlar ve
AI beyanını büyütmüyorlar. Ama çizim tarzında bir kapak istersen, bu
promptlar en azından **oyunun gerçek karakterlerini ve dünyasını** tarif
ediyor — şu anki banner'ın yaptığının tersine.

Kısa ve sade tutuldular; üreticiler uzun promptta detayı kaybediyor.

**Ortak kuyruk** — her promptun sonuna:

```
Crisp pixel art, hard pixel edges, no anti-aliasing, no blur, no text,
no logo, no watermark. Limited palette: #06050B #100E1A #1E1B2C #183256
#285888 #6A34A0 #B47EEA #E4DECC #FFC660 #8A1A22.
```

**Kapak** — 1260 × 1000 üret, 630 × 500'e küçült:

```
Pixel art game cover. Deep stone dungeon, near-black and navy. A young
woman with long dark wavy hair, dark hooded cloak, blue tunic and a red
scarf stands back to back with a tall man with short dark hair, stubble
and dark leather armour. Between them a small violet flame burns on a
stone pedestal — the only light. Quiet, ominous, close. Empty dark space
at the top for a title.
```

**Banner** — 1920 × 480 üret, 960 × 240'a küçült:

```
Wide pixel art banner. A long underground stone corridor fading into
darkness. At the far right a violet flame on a pedestal, two small
figures beside it seen from the side. Left two thirds empty and dark for
a title. Near-black and navy, violet light only.
```

Üretilen görseller sayfaya konursa §5'teki *Graphics* beyanı zaten onları
da kapsıyor.

---

## 7. İsteğe bağlı — sürüm notu (Devlog)

```
Legend of Rey 1.0 is out

The full game is here: 18 chapters, four bosses, two playable characters
and an ending. This build replaces the old prototype entirely — if you
played that, everything is new.

Download the Windows zip, unpack, run. No installer.
```
