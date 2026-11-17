#!/bin/bash
# Hazır teshis.iso'yu USB'ye yazar + kalan alanda rapor için TESHIS (exFAT) bölümü açar. Araç ve autorun ISO'nun İÇİNDE.
# KULLANIM: sudo bash scripts/write_usb.sh /dev/sdX dist/teshis.iso
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
umount "$DEV"?* 2>/dev/null || true; umount "$DEV" 2>/dev/null || true
echo ">> ISO yazılıyor"; dd if="$ISO" of="$DEV" bs=4M status=progress conv=fsync; sync
partprobe "$DEV"; sleep 2
echo ">> TESHIS bölümü ekleniyor"
echo ', , 7' | sfdisk --append "$DEV"; partprobe "$DEV"; sleep 2
P=$(lsblk -nrp -o NAME "$DEV" | tail -1)
mkfs.exfat -L TESHIS "$P"
M=$(mktemp -d); mount "$P" "$M"; mkdir -p "$M/raporlar"; sync; umount "$M"; rmdir "$M"
echo "Tamam. Arızalı PC'yi USB'den aç (Secure Boot kapalı): araç kendiliğinden çalışır, raporlar USB'de TESHIS > raporlar/ altına yazılır."
