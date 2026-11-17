import html, datetime, re
_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


def clean(s):
    """Strip C0/C1 control chars (incl. ESC): log lines come from an untrusted disk."""
    return _CTRL.sub("?", str(s))

LABEL = {"kritik": ("KRİTİK", "#c62828"), "uyari": ("UYARI", "#e68a00"), "bilgi": ("BİLGİ", "#1565c0")}


def summary(report):
    c = {"kritik": 0, "uyari": 0, "bilgi": 0}
    for f in report.findings:
        c[f.severity] += 1
    if c["kritik"]:
        return "SORUN VAR", "#c62828", f"{c['kritik']} kritik bulgu var. Önce en üstteki bulgudan başla."
    if c["uyari"]:
        return "DİKKAT", "#e68a00", f"{c['uyari']} uyarı var, acil kritik hata görünmüyor."
    if report.target.startswith("(sistem"):
        return "KONTROL EDİLEMEDİ", "#616161", "Hiçbir işletim sistemi okunamadı; yalnızca donanım bilgisine bakıldı. Notlara bak."
    return "TEMİZ", "#2e7d32", "Okunabilen günlüklerde bilinen bir sorun bulunamadı."


def to_text(report):
    t, _, s = summary(report)
    lines = [f"== {t} ==  {s}", f"Hedef: {report.target}  ({report.os_name})", ""]
    for f in report.sorted():
        lines += [f"[{LABEL[f.severity][0]}] {f.area}: {f.title}  (x{f.count})",
                  f"   Neden : {f.explanation}", f"   Öneri : {f.advice}"] + [f"   > {e}" for e in f.evidence] + [""]
    for n in report.notes:
        lines.append(f"(not) {n}")
    return clean("\n".join(lines))


def to_html(report):
    e = html.escape
    t, col, s = summary(report)
    rows = []
    for f in report.sorted():
        lab, c = LABEL[f.severity]
        ev = "".join(f"<li><code>{e(x)}</code></li>" for x in f.evidence)
        rows.append(f"""<section class="f" style="border-left:6px solid {c}">
<h3><span class="b" style="background:{c}">{lab}</span> {e(f.area)} · {e(f.title)} <small>×{f.count}</small></h3>
<p><b>Neden:</b> {e(f.explanation)}</p><p><b>Ne yapmalı:</b> {e(f.advice)}</p>
<details><summary>Kanıt</summary><ul>{ev}</ul></details></section>""")
    info = "".join(f"<tr><td>{e(k)}</td><td>{e(v)}</td></tr>" for k, v in report.info.items())
    notes = "".join(f"<li>{e(n)}</li>" for n in report.notes)
    return clean(f"""<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>USB Teşhis Raporu</title><style>
body{{font:16px system-ui,sans-serif;max-width:900px;margin:0 auto;padding:16px;background:#f6f7f9;color:#1b1f23}}
.top{{background:{col};color:#fff;padding:18px;border-radius:10px}} .top h1{{margin:0}}
.f{{background:#fff;margin:14px 0;padding:6px 16px;border-radius:8px}} .b{{color:#fff;padding:2px 8px;border-radius:4px;font-size:.7em}}
code{{font-size:.8em;word-break:break-all}} table{{border-collapse:collapse}} td{{padding:3px 12px 3px 0}}
</style><div class="top"><h1>{t}</h1><p>{e(s)}</p><p>{e(report.target)} · {e(report.os_name)} · {datetime.datetime.now():%Y-%m-%d %H:%M}</p></div>
{''.join(rows) or '<p>Bulgu yok.</p>'}
<h2>Sistem bilgisi</h2><table>{info}</table>
<h2>Kontrol EDİLEMEYENLER</h2><ul>{notes or '<li>—</li>'}</ul></html>""")


ANSI = {"kritik": "\033[1;37;41m", "uyari": "\033[1;30;43m", "bilgi": "\033[1;37;44m", "ok": "\033[1;37;42m"}


def to_brief(report, top=5):
    """Large colored banner + top findings, for the live-USB console.
    Untrusted text (from the inspected disk) is cleaned BEFORE our own ANSI codes are added."""
    t, _, s = summary(report)
    key = "kritik" if t == "SORUN VAR" else "uyari" if t in ("DİKKAT", "KONTROL EDİLEMEDİ") else "ok"
    R = "\033[0m"
    out = ["", f"{ANSI[key]}{'':52s}{R}", f"{ANSI[key]}   {t:^46s}   {R}", f"{ANSI[key]}{'':52s}{R}",
           f"  {s}", f"  Sistem: {clean(report.os_name)}  ({clean(report.target)})", ""]
    for f in report.sorted()[:top]:
        lab = LABEL[f.severity][0]
        out += [f"{ANSI[f.severity]} {lab:^7s} {R} {clean(f.area)}: {clean(f.title)}  (x{f.count})",
                f"          -> {clean(f.advice)}"]
    extra = len(report.findings) - top
    if extra > 0:
        out.append(f"  ... ve {extra} bulgu daha (tam rapor dosyada)")
    for n in report.notes[:4]:
        out.append(f"  (kontrol edilemedi) {clean(n)}")
    return "\n".join(out)
