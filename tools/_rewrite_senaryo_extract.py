"""Geçici: senaryo-akisi.md diyalog anahtarlarını çıkar."""
from __future__ import annotations

import re
from pathlib import Path

text = Path("docs/senaryo-akisi.md").read_text(encoding="utf-8")
pat = re.compile(
    r'^#### (.+)\n(?:\*\*[^\n]*\n)?(?:_[^\n]*\n)?- tr: "(.*)"\n- en: "(.*)"',
    re.M,
)
keys = pat.findall(text)
print(f"count={len(keys)}")
out = Path("build/senaryo_keys.txt")
out.parent.mkdir(parents=True, exist_ok=True)
lines = []
for k, tr, en in keys:
    lines.append(f"{k}\t{tr}\t{en}")
out.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out}")

# Yankı tekil şüphelileri (B14 öncesi)
pre_b14 = []
for k, tr, en in keys:
    if not (
        "echo" in k.lower()
        or k.startswith("prologue_echo")
        or k == "echo_alone_voice"
    ):
        continue
    # B14+ tekil serbest
    if k.startswith("ch14_") or k.startswith("ch15_echo") or k.startswith(
        "ch18_"
    ):
        if k.startswith("ch15_echo"):
            pass  # ch15 hâlâ çoğul olmalı
        elif not k.startswith("ch15_"):
            continue
    suspects = []
    for needle in (
        " bana ",
        " Bana ",
        " beni ",
        " Beni ",
        " ben ",
        " Ben ",
        "benim",
        "bilemezdim",
        "yanılmam",
        " I'm ",
        " I ",
        "I've",
        "I'll",
        " me ",
        " me.",
        "my ",
    ):
        if needle in f" {tr} " or needle in f" {en} ":
            suspects.append(needle.strip())
    if suspects:
        print(f"SUSPECT {k}: {suspects} | {tr[:70]}")
