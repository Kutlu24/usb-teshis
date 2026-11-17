# usb-teshis — bilgisayar için "OBD" teşhis aracı

USB'den açılan canlı Linux içinde çalışır; arızalı Windows/Linux diskini **salt-okunur** bağlar,
günlükleri okur ve Türkçe, öncelik sıralı bir rapor (HTML+TXT) üretir.

## Ne okur
- Windows: System/Application `.evtx` (Kernel-Power 41, BugCheck+kod anlamı, disk/Ntfs/WHEA, servis hataları), `Minidump`, eksik SYSTEM/SOFTWARE/winload
- Linux: journald (offline dizin), kern.log/syslog/messages (OOM, panic, I/O, FS, MCE, ısı, segfault, GPU, USB)
- Canlı donanım: SMART (smartctl), pil sağlığı, ısı, RAM/üretici bilgisi
- Şifreli (BitLocker/LUKS) diskleri atlar ve "kontrol edilemeyenler" listesine yazar

## Kullanım
    sudo sh teshis.sh                          # USB'den açılmış makinede: tüm diskleri bağla + tara
    python3 -m usb_teshis --root /mnt/windows  # elle bağlanmış bir sistem
    python3 -m usb_teshis --this-machine --days 7
Çıkış kodu: 0 temiz/uyarı, 1 kritik bulgu var, 2 çözümlenecek sistem yok.

## USB hazırlama (otomatik çalışan)
1. SystemRescue ISO'sunu indir ve doğrula (sha256). `sudo apt install xorriso` gerekir.
2. Aracı ISO'ya göm (root gerekmez, BIOS+UEFI önyüklemesi korunur):
   `bash scripts/build_iso.sh systemrescue-13.03-amd64.iso`  →  `dist/teshis.iso`
3. USB'ye yaz (USB TAMAMEN silinir; cihaz adını `lsblk` ile kontrol et):
   `sudo bash scripts/write_usb.sh /dev/sdX dist/teshis.iso`
4. Arızalı PC'yi USB'den aç (Secure Boot kapalı). Araç kendiliğinden başlar: diskleri salt-okunur bağlar, tarar,
   ekrana renkli özet (SORUN VAR / DİKKAT / TEMİZ) basar, ayrıntılı raporu USB'deki `TESHIS` bölümüne (`raporlar/`) yazar.

Sanal makinede doğrulandı (QEMU): BIOS ve UEFI açılışı, otomatik tarama, bozuk Linux diski bulma, rapor yazma.
Gerçek Windows diski ve gerçek donanımla henüz denenmedi.

## Testler
    python3 -m unittest tests.test_rules
