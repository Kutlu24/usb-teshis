import argparse, sys, socket
from pathlib import Path
from .model import Report
from . import detect, windows, linux, hw, report as rp


def main(argv=None):
    ap = argparse.ArgumentParser(prog="usb_teshis", description="Bilgisayar teşhis aracı (OBD gibi)")
    ap.add_argument("--root", action="append", help="Çözümlenecek bağlı sistem kökü (birden fazla verilebilir)")
    ap.add_argument("--mount", action="store_true", help="Bağlı olmayan diskleri salt-okunur bağla (root gerekir)")
    ap.add_argument("--this-machine", action="store_true", help="Çalışan bu sistemi (/) ve donanımı tara")
    ap.add_argument("--out", default="teshis_raporu", help="Çıktı öneki (.html ve .txt yazılır)")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--brief", action="store_true", help="Renkli kısa özet göster (otomatik mod)")
    ap.add_argument("--live-dmesg", action="store_true", help="Bu açılışın çekirdek mesajlarını da tara (canlı USB)")
    a = ap.parse_args(argv)

    roots, notes = [], []
    for r in a.root or []:
        k = detect.classify(r)
        if not k:
            print(f"! {rp.clean(r)}: Windows ya da Linux kökü değil", file=sys.stderr); continue
        roots.append((r, k))
    if a.mount:
        f, n = detect.mount_all_readonly(); roots += f; notes += n
    if a.this_machine:
        roots.append(("/", "linux"))
    if not roots:
        roots = detect.discover_mounted()
    if not roots and not a.mount:
        print("Çözümlenecek sistem bulunamadı. --root, --mount ya da --this-machine kullan."); return 2

    # donanım + canlı dmesg bir kez toplanır, her sistem raporuna eklenir
    hwrep = Report()
    hw.analyse(hwrep, live=True)
    if a.live_dmesg:
        import subprocess
        try:
            out = subprocess.run(["dmesg", "--time-format", "iso"], capture_output=True, text=True, timeout=30).stdout
            linux.scan_text(out, "dmesg (bu açılış)", hwrep)
        except Exception as e:
            hwrep.notes.append(f"dmesg okunamadı: {e}")
    reports = []
    for root, kind in roots:
        rep = Report(target=root, os_name=detect.os_name(root, kind), notes=list(notes))
        (windows.analyse(root, rep, a.days) if kind == "windows" else linux.analyse(root, rep, a.days))
        reports.append(rep)
    if not reports:   # hiçbir işletim sistemi bulunamadı: yine de donanım raporu ver
        r = Report(target="(sistem bulunamadı)", os_name="—", notes=list(notes))
        r.notes.append("Windows/Linux kurulumu bulunamadı ya da bağlanamadı: disk bozuk, şifreli ya da boş olabilir.")
        reports.append(r)
    worst = 2
    for rep, slug in zip(reports, [(r[0].strip("/").replace("/", "_") or "root") for r in roots] or ["sistem"]):
        for f in hwrep.findings: rep.add(f)
        rep.notes += hwrep.notes; rep.info.update(hwrep.info)
        base = f"{a.out}_{slug}" if len(reports) > 1 else a.out
        Path(base + ".html").write_text(rp.to_html(rep)); Path(base + ".txt").write_text(rp.to_text(rep))
        print(rp.to_brief(rep) if a.brief else rp.to_text(rep)); print(f"\n-> {rp.clean(base)}.html")
        if any(f.severity == "kritik" for f in rep.findings): worst = 1
    return 0 if worst == 2 else 1


if __name__ == "__main__":
    sys.exit(main())
