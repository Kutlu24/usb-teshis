#!/bin/bash
# SystemRescue ISO'suna aracı + autorun'u gömer (root gerekmez; xorriso lazım). Önyükleme düzeni (BIOS+UEFI) korunur.
# KULLANIM: bash scripts/build_iso.sh /yol/systemrescue-13.03-amd64.iso [cikis.iso]
set -euo pipefail
IN="${1:?SystemRescue ISO yolu}"; OUT="${2:-$(dirname "$0")/../dist/teshis.iso}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"; mkdir -p "$(dirname "$OUT")"; OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
mkdir -p "$W/autorun" "$W/usb-teshis"
cp "$SRC/autorun/autorun" "$W/autorun/autorun"; chmod +x "$W/autorun/autorun"
tar -C "$SRC" --exclude=.git --exclude=__pycache__ --exclude=autorun --exclude=tests --exclude=dist -cf - . | tar -C "$W/usb-teshis" -xf -
rm -f "$OUT"
xorriso -indev "$IN" -outdev "$OUT" -boot_image any replay -map "$W/autorun" /autorun -map "$W/usb-teshis" /usb-teshis -commit
echo "Hazır: $OUT"
