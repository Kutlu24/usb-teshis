"""Offline Linux analysis: journald directory + classic text logs from a mounted root."""
import subprocess, shutil
from pathlib import Path
from .model import Finding
from .rules import TEXT_RULES

TEXT_LOGS = ["var/log/kern.log", "var/log/syslog", "var/log/messages", "var/log/dmesg", "var/log/boot.log"]
MAX_BYTES = 40 * 1024 * 1024


def scan_text(text, source, report):
    for rx, sev, area, title, expl, advice in TEXT_RULES:
        hits = [m for m in rx.finditer(text)]
        if not hits:
            continue
        ev = []
        for m in hits[:3]:
            a = text.rfind("\n", 0, m.start()) + 1
            b = text.find("\n", m.end()); b = len(text) if b < 0 else b
            ev.append(f"{source}: {text[a:b].strip()[:200]}")
        report.add(Finding(sev, area, title, expl, advice, ev, count=len(hits)))


def analyse(root, report, days=90, journal_dirs=None):
    root = Path(root)
    done = False
    jdirs = journal_dirs or [root / "var/log/journal", root / "run/log/journal"]
    jc = shutil.which("journalctl")
    if jc:
        for jd in jdirs:
            if Path(jd).is_dir():
                try:
                    out = subprocess.run([jc, "--directory", str(jd), "-p", "warning", "--since", f"-{days}d", "--no-pager", "-o", "short-iso"],
                                         capture_output=True, text=True, timeout=240).stdout
                    if out.strip():
                        scan_text(out[-MAX_BYTES:], "journal", report); done = True
                        _boots(jc, jd, report)
                except Exception as e:
                    report.notes.append(f"journalctl okunamadı: {e}")
    else:
        report.notes.append("journalctl yok: binary journal okunamadı.")
    for rel in TEXT_LOGS:
        p = root / rel
        if p.is_file():
            try:
                data = p.read_bytes()[-MAX_BYTES:].decode("utf-8", "replace")
                scan_text(data, rel, report); done = True
            except Exception as e:
                report.notes.append(f"{rel} okunamadı: {e}")
    if not done:
        report.notes.append("Linux günlüğü bulunamadı (var/log boş olabilir).")
    _fstab(root, report)


def _boots(jc, jd, report):
    try:
        out = subprocess.run([jc, "--directory", str(jd), "--list-boots", "--no-pager"], capture_output=True, text=True, timeout=60).stdout
        n = len([l for l in out.splitlines() if l.strip()])
        report.info["Kayıtlı açılış sayısı"] = str(n)
    except Exception:
        pass


def _fstab(root, report):
    p = root / "etc/fstab"
    if p.is_file():
        for line in p.read_text(errors="replace").splitlines():
            if line.strip().startswith("UUID=") and "noauto" not in line and "nofail" not in line:
                report.info.setdefault("fstab girdileri", "")
                break
