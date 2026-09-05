#!/usr/bin/env bash
# Render tools/og-image/template.html to ../../og-image.png at exactly 1200x630.
#
# Headless Chromium is used (not rsvg/ImageMagick) because the card relies on
# the Google-hosted brand fonts (Playfair Display, DM Mono, Outfit) that are
# not installed on the build host.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/../../og-image.png"
TEMPLATE="file://$HERE/template.html"

CHROME="$(command -v chromium || command -v chromium-browser || command -v google-chrome)"

"$CHROME" \
  --headless \
  --no-sandbox \
  --hide-scrollbars \
  --force-device-scale-factor=1 \
  --window-size=1200,630 \
  --default-background-color=00000000 \
  --virtual-time-budget=10000 \
  --screenshot="$OUT" \
  "$TEMPLATE"

# Fail loudly if the dimensions drifted from the spec LinkedIn/X expect.
python3 - "$OUT" <<'PY'
import sys
from PIL import Image
path = sys.argv[1]
size = Image.open(path).size
if size != (1200, 630):
    sys.exit(f"og-image.png is {size[0]}x{size[1]}, expected 1200x630")
print(f"wrote {path} ({size[0]}x{size[1]})")
PY
