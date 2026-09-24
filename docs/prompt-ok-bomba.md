# Ok ve bomba — sanat üretim promptları

**Ardeko Studios · 25.09.2026** · Arda'nın isteği: *"Ok ve bomba spriteları için prompt yaz."*

Bugün ok ve bomba **kodla** çiziliyor (`src/art/projectiles.py`, dükkân ikonu `src/ui/shop.py::_draw_icon`, HUD ikonu `src/ui/hud.py::_draw_ammo_icon`). `DEVIR.md` §0.4 bunları "elle çizilmiş değil, sanat geçişine bırakıldı" diye listeliyor. Bu belge o geçiş için hazır promptları ve üretimden sonra yapılacakları topluyor.

> **Kural değişmiyor:** Kaynak ne olursa olsun her görsel `tools/quantize.py`'den geçer (`CLAUDE.md` §6). Aşağıdaki promptlar AI üreticisinden **temiz bir ızgara** istiyor; paleti yine boru hattı zorluyor.

---

## 1. Nasıl kullanılır

1. Aşağıdaki **ortak stil bloğunu** her promptun başına ekle.
2. Görseli **hedef boyutun tam 8 katında** iste (örn. 10×5 piksellik ok → 80×40). Üretici ızgarayı ne kadar net tutarsa küçültme o kadar temiz olur.
3. Çıktıyı içe aktar (kırp → alan ortalamasıyla küçült → 37 renge quantize):

   ```
   python tools/import_art.py indirilen.png --boyut 10x5 --cikti assets/sprites/arrow_player.png
   ```

4. Açıp bak: tek piksellik ayrıntılar (ok ucu, fitil) kaybolduysa kaynağı düzelt, küçültmeyi değil.
5. `python tools/silhouette.py` ile siluet testi: tek renk siyahta **ok ok gibi, bomba bomba gibi** okunmalı.
6. `assets/REGISTRY.md`'ye kaydet (`python tools/registry.py`), sonra koda bağla (bölüm 5).

## 2. Ortak stil bloğu (her promptun başına)

```
Pixel art game sprite, strict pixel grid, every source pixel drawn as an exact
8x8 block, no anti-aliasing, no blur, no gradients (only 2-colour checker
dithering allowed), no glow, no text, no border, no drop shadow.
Side-view dark fantasy platformer, 16-bit era readability.
Light source ALWAYS from the TOP-LEFT: top-left edges one tone lighter,
bottom-right edges one tone darker.
Outline colour #100E1A (never pure black). Background: solid flat #FF00FF
(magenta) for keying, nothing else in the image.
Use ONLY these colours:
#06050B #100E1A #1E1B2C #282C3C #3A4054 #565E74 #7E869E #0E1A30 #183256
#285888 #3A261C #68462C #5C2014 #B0461C #EC8230 #FFC660 #3E0E14 #8A1A22
#D43836 #623C2C #9A664A #CA9876 #163E4A #368E9A #82DEE4 #2E144A #6A34A0
#B47EEA #D84C22 #FF863C #E4DECC #FCFAF6 #12221C #223E2A #406C3A #6E9E52
#B0C86E
```

Negatif (destekleyen üreticiler için): `blurry, anti-aliased, smooth shading, gradient, 3d render, photorealistic, text, watermark, signature, frame, extra objects, soft edges, lens flare`

## 3. Promptlar

### 3.1 Oyuncunun oku — uçuşta (10×5, 1 kare, sağa bakan)

Oyunda sola uçan hali aynalanıyor; tek yön yeter.

```
[ORTAK STIL BLOGU]
A single wooden arrow flying horizontally to the RIGHT, drawn on a 10x5 pixel
grid (output 80x40). Shaft: 1 pixel tall, warm wood #9A664A with #CA9876 on its
upper edge. Arrowhead on the right: a small 3-pixel-tall iron point, #7E869E
with a single #FCFAF6 glint pixel at the very tip. Fletching on the left: two
bone-white feathers #E4DECC, one above and one below the shaft, 2 pixels each,
angled backwards. Outline #100E1A around the arrowhead and feathers only.
Centered, nothing else.
```

### 3.2 Düşman oku — uçuşta (10×5, 1 kare, sağa bakan)

`CLAUDE.md` §7/§10: tehlike **renk + şekil** ile anlatılır. Renk körü modunda palet değişir, şekil değişmez. Bu yüzden ucu çengelli.

```
[ORTAK STIL BLOGU]
A crude enemy arrow flying horizontally to the RIGHT, 10x5 pixel grid (output
80x40). Dark wood shaft #68462C. A BARBED hooked arrowhead in danger orange
#D84C22 with a bright core #FF863C: two backward-pointing barbs, one reaching
the top row and one the bottom row, so the silhouette reads as a hook even in
pure black. Ragged fletching in #D84C22. Outline #100E1A. Nothing else.
```

### 3.3 Bomba — uçuşta, dönüyor (8×10, 4 kare yatay şerit)

Oyunda 8 FPS (her kare ~7-8 oyun karesi). Fitilin kıvılcımı ayrı çiziliyor (parçacık); sprite'ta yalnızca fitilin ucu.

```
[ORTAK STIL BLOGU]
Sprite strip of 4 frames side by side, each frame 8x10 pixels (whole strip
output 256x80). A round iron bomb, 7 pixels wide, body #3A4054, top-left
highlight #7E869E (2-3 pixels), bottom-right shade #282C3C, outline #100E1A.
A short twisted fuse rising from the upper right, #68462C, 2 pixels, ending in
a single #FFC660 ember pixel. A darker iron band #1E1B2C wraps the bomb; across
the 4 frames the band ROTATES (horizontal, diagonal, vertical, other diagonal)
so the bomb reads as spinning. Highlight stays fixed at top-left in every
frame (light does not rotate). Frames aligned on the same baseline.
```

### 3.4 Bomba — patlamak üzere (8×10, 2 kare)

Son 30 karede gövde tehlike renginde yanıp sönüyor (`BOMB_WARN_FRAMES`). Şekil kanalı: kıvılcım büyüyor.

```
[ORTAK STIL BLOGU]
Sprite strip of 2 frames, each 8x10 pixels (output 128x80). Same round iron
bomb as before, but its body glows danger orange: frame 1 body #D84C22 with
#FF863C highlight at top-left; frame 2 body #B0461C. The fuse is almost burnt
down: 1 pixel of #68462C with a LARGER 2x2 spark #FFC660 / #FCFAF6 on top.
Outline #100E1A. Nothing else.
```

### 3.5 Patlama (32×32, 6 kare) — isteğe bağlı

Bugün patlama parçacık ve sarsıntıyla anlatılıyor (`juice.explosion`). Sprite eklenirse üçlü senkron bozulmamalı: kare `on_hit()` ile aynı anda başlar (`CLAUDE.md` §7).

```
[ORTAK STIL BLOGU]
Sprite strip of 6 frames, each 32x32 pixels (output 1536x256). A pixel art
bomb explosion read from the side: frame 1 a small white-hot core #FCFAF6
with #FFC660 ring; frame 2 expanding fireball #EC8230 / #B0461C with jagged
edges; frame 3 largest, orange outer, dark smoke #3A4054 starting on the
upper-left; frames 4-5 fire shrinking into rolling smoke #565E74 / #282C3C,
embers #FFC660 flying outward; frame 6 thin smoke wisps only. Use 2-colour
checker dithering between smoke tones. Radial, no ground.
```

### 3.6 Envanter / dükkân / HUD ikonları (9×9, her biri 1 kare)

Dükkân satırı ve HUD cephane göstergesi 9×9 kutu kullanıyor. İkon ok ve bombayı **siluetiyle** ayırmalı; harf yok (`CLAUDE.md` §9, diyegetik tercih).

```
[ORTAK STIL BLOGU]
Two separate 9x9 pixel inventory icons side by side with 1 empty column
between them (output 152x72).
Left: a small bundle of THREE arrows standing upright, tips up, iron tips
#7E869E, wooden shafts #9A664A, bone fletching #E4DECC at the bottom, tied with
a 1-pixel leather band #68462C.
Right: the same round iron bomb (#3A4054 body, #7E869E top-left highlight,
#100E1A outline) with a short fuse and one #FFC660 ember pixel.
Both centred in their 9x9 cells, readable as silhouettes.
```

## 4. Kontrol listesi — içe aktarmadan sonra

- [ ] Palet dışı renk yok (`tools/quantize.py` zaten zorluyor — yine de `tools/preview.py` ile kontak sayfasında bak)
- [ ] Işık sol üstten; dönen bombada ışık **dönmüyor**
- [ ] Kontur #100E1A, saf siyah yok
- [ ] Düşman oku siluette çengelli — renk körü modunda da oyuncunun okundan ayırt ediliyor (`tools/colorblind.py`)
- [ ] 8 FPS: bomba dönüşü 4 kare
- [ ] Siluet testi geçti (`tools/silhouette.py`)
- [ ] `assets/REGISTRY.md` güncel

## 5. Koda bağlama — sanat gelince yapılacak iş

Bu belge yalnızca promptları veriyor; bağlama kodu **yazılmadı**. Sanat geldiğinde:

1. `src/art/projectiles.py`: `_PLAYER_ARROW` / `_ENEMY_ARROW` ASCII tablolarının yerine PNG yükleyen bir yol. **Yedek olarak ASCII kalsın:** dosya yoksa oyun çökmesin (portrelerdeki `staging._draw_closeup` deseni).
2. `_draw_bomb`: 4 karelik şerit 8 FPS ile dönsün; uyarı şeridi son `BOMB_WARN_FRAMES` karede.
3. `src/ui/shop.py::_draw_icon` ve `src/ui/hud.py::_draw_ammo_icon`: 9×9 ikonlar.
4. `Legend of Rey.spec`: `assets/sprites/*.png` paketleniyor mu? (`tests/test_build.py` spec'i ölçüyor.)
5. `tests/test_sprites.py`'ye ölçü: ok 10×5, bomba 8×10, ikon 9×9.
