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

## USB hazırlama
1. USB'ye SystemRescue veya Ubuntu live ISO yaz (Ventoy ile ISO'yu kopyalamak yeterli).
2. Bu klasörü USB'nin veri bölümüne kopyala (`vendor/` içindeki python-evtx dahil, internet gerekmez).
3. Gerekli paketler canlı sistemde: python3, smartmontools, ntfs-3g (SystemRescue'da hazır).
4. Arızalı PC'yi USB'den aç → terminalde `sudo sh /yol/teshis.sh`.

## Testler
    python3 -m unittest tests.test_rules
