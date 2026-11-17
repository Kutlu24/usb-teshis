#!/bin/bash
# Bootable teşhis USB'si yapar: SystemRescue ISO'yu yazar + kalan alanda TESHIS bölümü açıp aracı kopyalar.
# KULLANIM: sudo bash scripts/make_usb.sh /dev/sdX /yol/systemrescue.iso
# DİKKAT: USB'nin TÜM içeriği silinir.
set -euo pipefail
DEV="${1:?cihaz ver, örn /dev/sda}"; ISO="${2:?iso yolu ver}"
[ "$(id -u)" = 0 ] || { echo "root gerekli (sudo)"; exit 1; }
[ -b "$DEV" ] || { echo "$DEV blok aygıt değil"; exit 1; }
N=$(basename "$DEV")
[ "$(cat /sys/block/$N/removable)" = 1 ] && [ "$(readlink -f /sys/block/$N/device | grep -c usb)" -ge 1 ] || { echo "$DEV çıkarılabilir USB görünmüyor — iptal"; exit 1; }
for m in $(lsblk -nr -o MOUNTPOINT "$DEV" | grep -v '^$'); do case "$m" in /|/boot*|/home*) echo "$DEV sistem diski gibi görünüyor — iptal"; exit 1;; esac; done
lsblk -o NAME,SIZE,MODEL,LABEL "$DEV"
[ "${TESHIS_YES:-}" = 1 ] || { read -r -p "$DEV tamamen silinecek. 'EVET' yaz: " a; [ "$a" = EVET ] || exit 1; }
SRC="$(cd "$(dirname "$0")/.." && pwd)"
umount "$DEV"?* 2>/dev/null || true; umount "$DEV" 2>/dev/null || true
echo ">> ISO yazılıyor"; dd if="$ISO" of="$DEV" bs=4M status=progress conv=fsync; sync
partprobe "$DEV"; sleep 2
echo ">> TESHIS bölümü ekleniyor"
echo ', , 7' | sfdisk --append "$DEV"; partprobe "$DEV"; sleep 2
P=$(lsblk -nrp -o NAME "$DEV" | tail -1)
mkfs.exfat -L TESHIS "$P"
M=$(mktemp -d); mount "$P" "$M"
mkdir -p "$M/usb-teshis"; tar -C "$SRC" --exclude=.git --exclude=__pycache__ -cf - . | tar -C "$M/usb-teshis" -xf -
sync; umount "$M"; rmdir "$M"
echo "Tamam. Arızalı PC'yi USB'den aç; SystemRescue'da:  mkdir /m && mount /dev/disk/by-label/TESHIS /m && sh /m/usb-teshis/teshis.sh"
