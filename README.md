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
1. **SystemRescue USB writer** ile ISO'yu yaz (yazılabilir FAT32 oluşturur; `dd` ile yazılan USB salt-okunur olur ve autorun eklenemez):
   `sudo ./sysrescueusbwriter-x86_64.AppImage systemrescue-13.03-amd64.iso` (cihaz seç; USB TAMAMEN silinir).
2. Aracı ve autorun'u kopyala (root gerekmez): `bash scripts/install_to_stick.sh /run/media/$USER/RESCUE1303`
3. Arızalı PC'yi USB'den aç (Secure Boot kapalı). Araç kendiliğinden başlar: diskleri salt-okunur bağlar, tarar,
   ekrana renkli özet (SORUN VAR / DİKKAT / TEMİZ) basar, ayrıntılı raporu USB'de `raporlar/` altına yazar.

## Testler
    python3 -m unittest tests.test_rules
