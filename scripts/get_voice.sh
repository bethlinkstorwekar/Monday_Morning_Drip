#!/bin/sh
# Install the podcast tools and download the Piper voice (needs huggingface.co
# and *.hf.co allowed in the environment's network settings).
set -e
pip install -q piper-tts lameenc
VOICE=${1:-lessac/high/en_US-lessac-high}
DIR="$HOME/voices"
NAME=$(basename "$VOICE")
mkdir -p "$DIR"
BASE=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US
for f in "$NAME.onnx" "$NAME.onnx.json"; do
  [ -s "$DIR/$f" ] && continue
  if ! curl -sfL -o "$DIR/$f" "$BASE/$(dirname "$VOICE")/$f"; then
    rm -f "$DIR/$f"
    echo "FAILED to download $f. Allow huggingface.co and *.hf.co in the environment's network settings." >&2
    exit 1
  fi
done
echo "voice ready: $DIR/$NAME.onnx"
