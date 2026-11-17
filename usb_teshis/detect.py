"""Find OS roots: already-mounted paths, or mount unmounted partitions READ-ONLY (live USB)."""
import json, os, subprocess, tempfile
from pathlib import Path


def classify(root):
    r = Path(root)
    if (r / "Windows/System32").is_dir() or (r / "WINDOWS/System32").is_dir():
        return "windows"
    if (r / "etc/os-release").is_file() and (r / "var").is_dir():
        return "linux"
    return None


def os_name(root, kind):
    if kind == "linux":
        try:
            for l in (Path(root) / "etc/os-release").read_text().splitlines():
                if l.startswith("PRETTY_NAME="):
                    return l.split("=", 1)[1].strip('"')
        except Exception:
            pass
        return "Linux"
    return "Windows"


def discover_mounted():
    out = []
    try:
        for l in Path("/proc/mounts").read_text().splitlines():
            mp = l.split()[1].replace("\\040", " ")
            if mp.startswith(("/proc", "/sys", "/dev", "/run", "/snap")):
                continue
            k = classify(mp)
            if k and mp != "/":
                out.append((mp, k))
    except Exception:
        pass
    return out


def mount_all_readonly():
    """Needs root. Returns list of (mountpoint, kind). BitLocker/LUKS volumes are skipped with a note."""
    found, notes = [], []
    if os.geteuid() != 0:
        return found, ["Salt-okunur bağlama için root gerekir (sudo)."]
    try:
        devs = json.loads(subprocess.run(["lsblk", "-J", "-p", "-o", "NAME,FSTYPE,MOUNTPOINT,TYPE"],
                                         capture_output=True, text=True).stdout)["blockdevices"]
    except Exception as e:
        return found, [f"lsblk okunamadı: {e}"]

    def walk(ds):
        for d in ds:
            yield d
            yield from walk(d.get("children", []) or [])
    for d in walk(devs):
        fs = d.get("fstype")
        if d.get("type") not in ("part", "lvm") or not fs or d.get("mountpoint"):
            continue
        if fs in ("BitLocker",) or fs == "crypto_LUKS":
            notes.append(f"{d['name']}: şifreli ({fs}); anahtar olmadan okunamaz.")
            continue
        mp = tempfile.mkdtemp(prefix="teshis_")
        opts = "ro,noexec,nosuid,nodev" + (",norecover" if fs in ("ext4", "ext3") else "")
        t = {"ntfs": "ntfs3"}.get(fs, fs)
        r = subprocess.run(["mount", "-t", t, "-o", opts, d["name"], mp], capture_output=True, text=True)
        if r.returncode != 0 and fs == "ntfs":
            r = subprocess.run(["mount", "-t", "ntfs-3g", "-o", "ro", d["name"], mp], capture_output=True, text=True)
        if r.returncode != 0:
            notes.append(f"{d['name']} ({fs}) bağlanamadı: {r.stderr.strip()[:120]} — dosya sistemi bozuk olabilir.")
            continue
        k = classify(mp)
        if k:
            found.append((mp, k))
    return found, notes
