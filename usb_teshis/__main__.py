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
    a = ap.parse_args(argv)

    roots, notes = [], []
    for r in a.root or []:
        k = detect.classify(r)
        if not k:
            print(f"! {r}: Windows ya da Linux kökü değil", file=sys.stderr); continue
        roots.append((r, k))
    if a.mount:
        f, n = detect.mount_all_readonly(); roots += f; notes += n
    if a.this_machine:
        roots.append(("/", "linux"))
    if not roots:
        roots = detect.discover_mounted()
    if not roots:
        print("Çözümlenecek sistem bulunamadı. --root, --mount ya da --this-machine kullan."); return 2

    worst = 2
    for root, kind in roots:
        rep = Report(target=root, os_name=detect.os_name(root, kind), notes=list(notes))
        (windows.analyse(root, rep, a.days) if kind == "windows" else linux.analyse(root, rep, a.days))
        hw.analyse(rep, live=True)
        slug = root.strip("/").replace("/", "_") or "root"
        base = f"{a.out}_{slug}" if len(roots) > 1 else a.out
        Path(base + ".html").write_text(rp.to_html(rep)); Path(base + ".txt").write_text(rp.to_text(rep))
        print(rp.to_text(rep)); print(f"\n-> {base}.html")
        if any(f.severity == "kritik" for f in rep.findings): worst = 1
    return 0 if worst == 2 else 1


if __name__ == "__main__":
    sys.exit(main())
