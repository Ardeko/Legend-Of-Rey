"""Kaydedilmiş dövüş efektleri; özgün WAV dosyalarına dokunmaz.

SDL kaynak biçimini mixer biçimine çevirir (48 kHz/stereo/24-bit dahil).
Eksik veya okunamayan dosyada mevcut sentez sesi kullanılabilir.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pygame

from src.audio import synth

SFX_DIR = Path(__file__).resolve().parents[2] / "assets" / "audio" / "sfx"

RECORDINGS: dict[str, tuple[str, ...]] = {
    "dodge": ("dash.wav",),
    "dodge_perfect": ("dash perfect.wav",),
    "hit_light": ("Light Hit V1.wav", "Light Hit V2.wav", "Light Hit V3.wav"),
    "hit_kill": ("Light Hit Kill.wav", "Light Hit Kill V2.wav"),
    "swing_heavy": ("swing heavy.wav", "swing heavy v2.wav", "swing heavy v3.wav"),
}


def load(name: str, directory: Path = SFX_DIR) -> list[np.ndarray]:
    """Bir olayın mevcut kayıtlarını mixer üzerinden float mono olarak oku."""
    waves: list[np.ndarray] = []
    for filename in RECORDINGS.get(name, ()):
        path = directory / filename
        if not path.is_file():
            continue
        try:
            # Hatalı WAV'da SDL dosya tutamacını açık bırakabiliyor.
            # Sahiplik Python'da kalsın; hata yolunda da kapansın.
            with path.open("rb") as source:
                sound = pygame.mixer.Sound(file=source)
            raw = pygame.sndarray.array(sound)
        except (OSError, ValueError, pygame.error) as exc:
            logging.getLogger(__name__).warning("Ses okunamadı: %s (%s)", path, exc)
            continue
        if not raw.size:
            continue
        # Oyun -16 bit mixer kullanır; stereo aygıtta da aynı mono
        # perde/boğukluk hattına girsin. Kayıtların kuyrukları korunur.
        wave = raw.astype(np.float32) / 32768.0
        if wave.ndim == 2:
            wave = wave.mean(axis=1)
        waves.append(synth.normalize(wave))
    return waves
