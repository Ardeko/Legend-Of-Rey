"""Gerçek WAV ithali, varyantlar, Yankı filtresi ve eksik dosya yedeği."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pygame

from src.audio import recordings, sfx, synth
from src.audio.mixer import PITCH_VARIANTS, SoundBank


def main() -> None:
    pygame.mixer.init(frequency=synth.SAMPLE_RATE, size=-16, channels=1)
    bank = SoundBank()
    total = 0
    for name, filenames in recordings.RECORDINGS.items():
        existing = [p for p in filenames if (recordings.SFX_DIR / p).is_file()]
        if not existing:
            print(f"ATLA {name}: kayit dosyalari bu makinede yok")
            continue
        waves = recordings.load(name)
        assert len(waves) == len(existing), name
        # Dosyalar varken sentez fonksiyonu hiç çağrılmamalı.
        with patch.dict(sfx.SFX, {name: lambda: (_ for _ in ()).throw(
                AssertionError("kayit yerine sentez calisti"))}):
            pool = bank.variants(name)
            assert len(pool) == len(existing) * PITCH_VARIANTS, name
            assert bank.variants(name) is pool
            for index, wave in enumerate(waves):
                sound = pool[index * PITCH_VARIANTS + PITCH_VARIANTS // 2]
                actual = pygame.sndarray.array(sound)
                expected = (wave * 32767).astype(np.int16)
                assert np.array_equal(actual, expected), name
                assert np.max(np.abs(wave)) > 0.01, name
            if name in sfx.MUFFLED_KEYS:
                muffled = bank.variants(name, muffled=True)
                assert len(muffled) == len(pool)
                assert not np.array_equal(pygame.sndarray.array(muffled[2]),
                                          pygame.sndarray.array(pool[2]))
        total += len(existing)
        print(f"OK {name}: {len(existing)} kayit, {len(pool)} perde varyanti")
    with tempfile.TemporaryDirectory(prefix="lore_audio_") as directory:
        path = Path(directory)
        empty_bank = SoundBank(path)
        assert len(empty_bank.variants("hit_light")) == PITCH_VARIANTS
        (path / "Light Hit V1.wav").write_bytes(b"bozuk wav")
        assert len(SoundBank(path).variants("hit_light")) == PITCH_VARIANTS
        assert empty_bank.variants("olmayan_ses") == []
    pygame.mixer.quit()
    # Stereo mixer kullanılırsa da dosyalar ve varyantlar çalınabilir.
    pygame.mixer.init(frequency=synth.SAMPLE_RATE, size=-16, channels=2)
    stereo = SoundBank().variants("dodge")
    assert pygame.sndarray.array(stereo[0]).shape[1] == 2
    pygame.mixer.quit()
    print(f"OK {total} gercek kayit; eksik/bozuk dosya yedegi; stereo cikis")


if __name__ == "__main__":
    main()
