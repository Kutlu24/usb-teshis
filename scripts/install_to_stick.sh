#!/bin/bash
# SystemRescue USB writer ile hazırlanmış (YAZILABİLİR FAT32) USB'ye aracı + autorun'u kopyalar. Root gerekmez.
# KULLANIM: bash scripts/install_to_stick.sh /run/media/$USER/RESCUE1303
set -euo pipefail
S="${1:?USB bağlama noktası ver (örn /run/media/kullanici/RESCUE1303)}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
[ -d "$S/sysresccd" ] && [ -d "$S/autorun" ] || { echo "$S bir SystemRescue USB'si gibi görünmüyor (sysresccd/ ve autorun/ yok) — iptal"; exit 1; }
touch "$S/.yazilabilir_test" 2>/dev/null && rm -f "$S/.yazilabilir_test" || { echo "$S yazılabilir değil (dd ile yazılmış, salt-okunur). USB writer ile yeniden hazırla."; exit 1; }
rm -rf "$S/usb-teshis"; mkdir -p "$S/usb-teshis"
tar -C "$SRC" --exclude=.git --exclude=__pycache__ --exclude=raporlar --exclude=autorun -cf - . | tar -C "$S/usb-teshis" -xf -
cp "$SRC/autorun/autorun" "$S/autorun/autorun"
sync
echo "Kuruldu: $S/usb-teshis ve $S/autorun/autorun"
