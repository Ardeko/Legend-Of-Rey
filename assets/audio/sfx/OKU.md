# Kaydedilmiş dövüş sesleri

Dosyalar özgün adlarıyla bu klasörde kullanılır. Dönüştürme gerekmez:
48 kHz, stereo, 24-bit WAV dosyalarını oyun açılışta mixer biçimine çevirir.

| Dosya | Oyun olayı |
|---|---|
| `dash.wav` | Kaçınma |
| `dash perfect.wav` | Kusursuz kaçınma |
| `Light Hit V1.wav`, `V2.wav`, `V3.wav` | Hafif vuruşun üç varyantı |
| `Light Hit Kill.wav`, `Light Hit Kill V2.wav` | Öldürücü vuruşun iki varyantı |
| `swing heavy.wav`, `swing heavy v2.wav`, `swing heavy v3.wav` | Ağır savuruşun üç varyantı |

Her olayda kayıt ve ±%8 perde varyantı seçilir. Vuruşların Yankı açıkken
boğuk sürümleri aynı kayıtlardan hazırlanır. Kaynak dosyalar değiştirilmez;
çalma seviyesi mevcut efektlerle eşitlenir. Ağır savuruş isabetten bağımsızdır;
ağır isabet ve karşı vuruş kendi seslerini korur.

Eksik/okunamayan kaydın yerine mevcut sentez sesi çalışır. Dosya değişikliği
için oyunu yeniden aç. `oyna.bat` kaynak klasörü okur; paketli exe güncellemesi
için `Legend of Rey.spec` ile yeniden derle (ses klasörü pakete dahildir).
