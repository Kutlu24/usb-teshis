#!/bin/sh
# USB'den açılan Linux'ta çalıştır:  sudo sh teshis.sh
cd "$(dirname "$0")" || exit 1
OUT="${1:-$(pwd)/raporlar}"; mkdir -p "$OUT"
python3 -m usb_teshis --mount --this-machine --out "$OUT/rapor_$(date +%Y%m%d_%H%M)"
echo; echo "Raporlar: $OUT  (HTML dosyasını tarayıcıda aç)"
