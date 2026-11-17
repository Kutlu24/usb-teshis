"""Offline Windows analysis: read .evtx files and Minidump from a mounted Windows volume."""
import os, re, sys
from pathlib import Path
from .model import Finding
from .rules import WIN_RULES, BUGCHECK

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

MAX_EVENTS_PER_LOG = 60000
LOGS = ["System.evtx", "Application.evtx"]
RE_ID = re.compile(r"<EventID[^>]*>(\d+)</EventID>")
RE_PROV = re.compile(r'<Provider Name="([^"]+)"')
RE_TIME = re.compile(r'SystemTime="([^"]+)"')
RE_DATA = re.compile(r"<Data[^>]*>([^<]*)</Data>")


def find_logdir(root):
    for p in ("Windows/System32/winevt/Logs", "WINDOWS/System32/winevt/Logs", "windows/system32/winevt/logs"):
        d = Path(root) / p
        if d.is_dir():
            return d
    return None


def analyse(root, report, since_days=90):
    logdir = find_logdir(root)
    if not logdir:
        report.notes.append("Windows olay günlükleri bulunamadı (winevt/Logs).")
        return
    try:
        from Evtx.Evtx import Evtx
    except Exception as e:  # pragma: no cover
        report.notes.append(f"EVTX okuyucu yüklenemedi: {e}")
        return
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    stats = {}
    for name in LOGS:
        path = logdir / name
        if not path.exists():
            report.notes.append(f"{name} yok.")
            continue
        n = 0
        try:
            with Evtx(str(path)) as log:
                for rec in log.records():
                    n += 1
                    if n > MAX_EVENTS_PER_LOG:
                        report.notes.append(f"{name}: ilk {MAX_EVENTS_PER_LOG} kayıttan sonrası atlandı.")
                        break
                    try:
                        xml = rec.xml()
                    except Exception:
                        continue
                    _event(xml, report, cutoff)
        except Exception as e:
            report.notes.append(f"{name} okunamadı (bozuk/kilitli olabilir): {e}")
        stats[name] = n
    report.info["Windows olay sayısı"] = ", ".join(f"{k}: {v}" for k, v in stats.items())
    _minidumps(root, report)
    _boot_checks(root, report)


def _event(xml, report, cutoff):
    mid = RE_ID.search(xml); mp = RE_PROV.search(xml)
    if not (mid and mp):
        return
    eid, prov = int(mid.group(1)), mp.group(1)
    rule = None
    for (p, i), r in WIN_RULES.items():
        if i == eid and p.lower() in prov.lower():
            rule = r; break
    if not rule:
        return
    ts = RE_TIME.search(xml)
    when = ts.group(1)[:19] if ts else "?"
    if ts:
        from datetime import datetime, timezone
        try:
            t = datetime.fromisoformat(ts.group(1).replace("Z", "+00:00").split(".")[0] + "+00:00")
            if t < cutoff:
                return
        except Exception:
            pass
    data = [d for d in RE_DATA.findall(xml) if d.strip()]
    extra = " | ".join(data)[:160]
    sev, area, title, expl, advice = rule
    if eid == 1001 and "bugcheck" in prov.lower():
        code = next((d for d in data if d.lower().startswith("0x")), "")
        hint = BUGCHECK.get(code[:10].lower(), "")
        extra = f"kod {code} {hint}".strip()
        if hint:
            expl = f"{expl} Kod anlamı: {hint}."
    report.add(Finding(sev, area, title, expl, advice, [f"{when}  {prov}/{eid}  {extra}".strip()]))


def _minidumps(root, report):
    d = Path(root) / "Windows" / "Minidump"
    if d.is_dir():
        dumps = sorted(d.glob("*.dmp"))
        if dumps:
            report.add(Finding("kritik", "Sistem", f"{len(dumps)} mavi ekran döküm dosyası var",
                "Windows çökme dökümleri bırakmış: sistem gerçekten mavi ekran vermiş.",
                "Dökümleri WinDbg/BlueScreenView ile açıp 'sürücü' adına bak.",
                [f"{p.name} ({p.stat().st_size//1024} KB)" for p in dumps[-5:]]))
    if (Path(root) / "Windows" / "MEMORY.DMP").exists():
        report.add(Finding("uyari", "Sistem", "Tam bellek dökümü (MEMORY.DMP) mevcut",
            "Sistem çökmesi sonrası tam döküm alınmış.", "WinDbg ile analiz et.", ["Windows/MEMORY.DMP"]))


def _boot_checks(root, report):
    r = Path(root)
    need = [("Windows/System32/config/SYSTEM", "SYSTEM kayıt defteri kovanı"),
            ("Windows/System32/config/SOFTWARE", "SOFTWARE kayıt defteri kovanı"),
            ("Windows/System32/winload.efi", "winload.efi")]
    for rel, label in need:
        if not (r / rel).exists() and not (r / rel.replace("winload.efi", "winload.exe")).exists():
            report.add(Finding("kritik", "Önyükleme", f"Eksik sistem dosyası: {label}",
                "Windows önyüklemesi için gerekli dosya bulunamadı.",
                "Kurtarma ortamından 'sfc /scannow' ve 'bootrec /rebuildbcd' dene; olmazsa onarım kurulumu.", [rel]))
    c = r / "Windows/System32/config"
    for h in ("SYSTEM", "SOFTWARE"):
        p = c / h
        if p.exists() and p.stat().st_size == 0:
            report.add(Finding("kritik", "Önyükleme", f"{h} kayıt defteri kovanı boş/bozuk",
                "Kayıt defteri dosyası 0 bayt: Windows açılamaz.", "RegBack veya sistem geri yükleme noktasından geri yükle.", [str(p)]))
    if (r / "Windows/System32/config/RegBack").is_dir() is False:
        pass
