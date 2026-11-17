"""Live hardware checks (run on the machine booted from the USB)."""
import json, shutil, subprocess, os, glob
from pathlib import Path
from .model import Finding


def _run(cmd, t=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=t).stdout
    except Exception:
        return ""


def analyse(report, live=True):
    if not live:
        return
    _blockdevs(report)
    _smart(report)
    _battery(report)
    _thermal(report)
    _meminfo(report)
    _dmi(report)


def _blockdevs(report):
    out = _run(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL"])
    try:
        devs = json.loads(out).get("blockdevices", [])
        report.info["Diskler"] = "; ".join(f"{d['name']} {d.get('size','')} {d.get('model') or ''}".strip() for d in devs if d.get("type") == "disk")
    except Exception:
        pass


def _smart(report):
    sm = shutil.which("smartctl")
    if not sm:
        report.notes.append("smartctl yok: disk SMART kontrolü yapılamadı (smartmontools kur).")
        return
    names = [n for n in os.listdir("/sys/block") if n.startswith(("sd", "nvme", "hd", "vd")) ]
    for n in names:
        raw = _run([sm, "-a", "-j", f"/dev/{n}"], 90)
        try:
            j = json.loads(raw)
        except Exception:
            continue
        evaluate_smart(n, j, report)


def evaluate_smart(name, j, report):
    model = j.get("model_name", name)
    passed = j.get("smart_status", {}).get("passed")
    if passed is False:
        report.add(Finding("kritik", "Disk", f"{name} ({model}): SMART SAĞLIK TESTİ BAŞARISIZ",
            "Disk kendi kendini 'arızalanıyor' olarak işaretledi.", "HEMEN YEDEK AL ve diski değiştir.", [f"smart_status.passed=false"]))
    tbl = {a.get("name"): a for a in j.get("ata_smart_attributes", {}).get("table", [])}
    for key, label in (("Reallocated_Sector_Ct", "Yeniden atanan sektör"), ("Current_Pending_Sector", "Bekleyen bozuk sektör"),
                       ("Offline_Uncorrectable", "Düzeltilemeyen sektör")):
        a = tbl.get(key)
        if a and a.get("raw", {}).get("value", 0) > 0:
            v = a["raw"]["value"]
            report.add(Finding("kritik" if v > 10 or key != "Reallocated_Sector_Ct" else "uyari", "Disk",
                f"{name}: {label} = {v}", "Disk yüzeyinde bozulma belirtisi.", "Yedek al; sayı artıyorsa diski değiştir.", [f"{key} raw={v}"]))
    nv = j.get("nvme_smart_health_information_log", {})
    if nv:
        if nv.get("critical_warning", 0):
            report.add(Finding("kritik", "Disk", f"{name}: NVMe kritik uyarı bayrağı", "SSD kritik uyarı bildiriyor.", "Yedek al.", [f"critical_warning={nv['critical_warning']}"]))
        if nv.get("percentage_used", 0) >= 90:
            report.add(Finding("uyari", "Disk", f"{name}: SSD ömrünün %{nv['percentage_used']}'i kullanıldı", "Yazma ömrü bitmek üzere.", "Yedek al, değişim planla.", []))
        if nv.get("media_errors", 0) > 0:
            report.add(Finding("kritik", "Disk", f"{name}: NVMe medya hataları = {nv['media_errors']}", "SSD veri hatası bildiriyor.", "Yedek al.", []))
    t = j.get("temperature", {}).get("current")
    if t and t >= 60:
        report.add(Finding("uyari", "Isı", f"{name} disk sıcaklığı yüksek: {t}°C", "Disk aşırı ısınıyor.", "Havalandırmayı iyileştir.", []))


def _battery(report):
    for b in glob.glob("/sys/class/power_supply/BAT*"):
        def rd(f):
            try: return int(Path(b, f).read_text())
            except Exception: return None
        full, design = rd("energy_full") or rd("charge_full"), rd("energy_full_design") or rd("charge_full_design")
        if full and design:
            pct = round(100 * full / design)
            report.info[f"Pil sağlığı ({Path(b).name})"] = f"%{pct}"
            if pct < 60:
                report.add(Finding("uyari", "Pil/Güç", f"Pil aşınmış: kapasite tasarımın %{pct}'i", "Pil ömrünü büyük ölçüde yitirmiş.", "Pili değiştir.", [f"{full}/{design}"]))


def _thermal(report):
    hot = []
    for z in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            t = int(Path(z).read_text()) / 1000
            if t >= 85:
                hot.append(f"{Path(z).parent.name}: {t:.0f}°C")
        except Exception:
            pass
    if hot:
        report.add(Finding("kritik", "Isı", "Yüksek sıcaklık", "Isı sensörü eşik üzerinde.", "Fan/soğutucu temizliği.", hot))


def _meminfo(report):
    try:
        m = {l.split(":")[0]: int(l.split()[1]) for l in Path("/proc/meminfo").read_text().splitlines()}
        report.info["RAM"] = f"{m['MemTotal']//1024} MB (kullanılabilir {m['MemAvailable']//1024} MB)"
    except Exception:
        pass


def _dmi(report):
    for k, f in (("Üretici", "sys_vendor"), ("Model", "product_name"), ("BIOS", "bios_version")):
        try:
            report.info[k] = Path(f"/sys/class/dmi/id/{f}").read_text().strip()
        except Exception:
            pass
