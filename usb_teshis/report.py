import html, datetime
LABEL = {"kritik": ("KRİTİK", "#c62828"), "uyari": ("UYARI", "#e68a00"), "bilgi": ("BİLGİ", "#1565c0")}


def summary(report):
    c = {"kritik": 0, "uyari": 0, "bilgi": 0}
    for f in report.findings:
        c[f.severity] += 1
    if c["kritik"]:
        return "SORUN VAR", "#c62828", f"{c['kritik']} kritik bulgu var. Önce en üstteki bulgudan başla."
    if c["uyari"]:
        return "DİKKAT", "#e68a00", f"{c['uyari']} uyarı var, acil kritik hata görünmüyor."
    return "TEMİZ", "#2e7d32", "Okunabilen günlüklerde bilinen bir sorun bulunamadı."


def to_text(report):
    t, _, s = summary(report)
    lines = [f"== {t} ==  {s}", f"Hedef: {report.target}  ({report.os_name})", ""]
    for f in report.sorted():
        lines += [f"[{LABEL[f.severity][0]}] {f.area}: {f.title}  (x{f.count})",
                  f"   Neden : {f.explanation}", f"   Öneri : {f.advice}"] + [f"   > {e}" for e in f.evidence] + [""]
    for n in report.notes:
        lines.append(f"(not) {n}")
    return "\n".join(lines)


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
    return f"""<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>USB Teşhis Raporu</title><style>
body{{font:16px system-ui,sans-serif;max-width:900px;margin:0 auto;padding:16px;background:#f6f7f9;color:#1b1f23}}
.top{{background:{col};color:#fff;padding:18px;border-radius:10px}} .top h1{{margin:0}}
.f{{background:#fff;margin:14px 0;padding:6px 16px;border-radius:8px}} .b{{color:#fff;padding:2px 8px;border-radius:4px;font-size:.7em}}
code{{font-size:.8em;word-break:break-all}} table{{border-collapse:collapse}} td{{padding:3px 12px 3px 0}}
</style><div class="top"><h1>{t}</h1><p>{e(s)}</p><p>{e(report.target)} · {e(report.os_name)} · {datetime.datetime.now():%Y-%m-%d %H:%M}</p></div>
{''.join(rows) or '<p>Bulgu yok.</p>'}
<h2>Sistem bilgisi</h2><table>{info}</table>
<h2>Kontrol EDİLEMEYENLER</h2><ul>{notes or '<li>—</li>'}</ul></html>"""
