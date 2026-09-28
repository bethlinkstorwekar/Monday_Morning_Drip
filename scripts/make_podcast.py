#!/usr/bin/env python3
"""Turn an episode script into an MP3 and attach it to its issue.

Usage: python3 scripts/make_podcast.py content/podcast/<date>-issue-<n>.txt

Reads the script (one paragraph per blank-line-separated block), speaks it with
a Piper voice, writes docs/audio/<date>-issue-<n>.mp3, and records the file,
size and duration in content/issues/<date>-issue-<n>.json under "podcast".
Then run scripts/build_site.py to add the player and podcast feed.

Needs: pip install piper-tts lameenc, plus the voice model below
(scripts/get_voice.sh downloads it).
"""
import json
import os
import pathlib
import re
import sys

import lameenc
from piper import PiperVoice
from piper.config import SynthesisConfig

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOICE = os.environ.get("DRIP_VOICE", str(pathlib.Path.home() / "voices" / "en_US-lessac-high.onnx"))
PAUSE_S = 0.6       # silence between paragraphs
LENGTH_SCALE = 1.05  # >1 speaks a little slower
BITRATE = 64         # kbps, mono; ~0.5 MB per minute

# Spoken-only fixes for words the voice mispronounces. Add to this list when a
# new acronym comes out wrong (check with voice.phonemize("WORD")).
SAY = {
    "EPAs": "E P A's", "EPA": "E P A",
    "ACGME": "A-C-G-M-E", "APPD": "A-P-P-D", "APA": "A-P-A",
    "PAS": "P.A.S", "AAMC": "A-A-M-C", "NRMP": "N-R-M-P", "ABP": "A-B-P",
    "UME": "U-M-E", "JGME": "J-G-M-E", "MPPDA": "M-P-P-D-A", "DLLs": "D L L's",
}


def speakable(text):
    for word, spoken in SAY.items():
        text = re.sub(rf"\b{re.escape(word)}\b", spoken, text)
    return text


def main():
    script = pathlib.Path(sys.argv[1])
    slug = script.stem
    issue_json = ROOT / "content" / "issues" / f"{slug}.json"
    if not issue_json.exists():
        raise SystemExit(f"no issue file {issue_json}")

    voice = PiperVoice.load(VOICE)
    cfg = SynthesisConfig(length_scale=LENGTH_SCALE)
    rate = voice.config.sample_rate
    silence = b"\x00\x00" * int(rate * PAUSE_S)

    pcm = bytearray()
    for para in [p.strip() for p in script.read_text().split("\n\n") if p.strip()]:
        for chunk in voice.synthesize(speakable(" ".join(para.split())), cfg):
            pcm += chunk.audio_int16_bytes
        pcm += silence

    enc = lameenc.Encoder()
    enc.set_bit_rate(BITRATE)
    enc.set_in_sample_rate(rate)
    enc.set_channels(1)
    enc.set_quality(2)
    mp3 = enc.encode(bytes(pcm)) + enc.flush()

    out = ROOT / "docs" / "audio" / f"{slug}.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(mp3)

    seconds = round(len(pcm) / 2 / rate)
    data = json.loads(issue_json.read_text())
    data["podcast"] = {"file": f"audio/{slug}.mp3", "bytes": len(mp3), "seconds": seconds,
                       "voice": pathlib.Path(VOICE).stem}
    issue_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out.relative_to(ROOT)}: {seconds // 60}:{seconds % 60:02d}, {len(mp3) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
