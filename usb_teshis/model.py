from dataclasses import dataclass, field

SEV_ORDER = {"kritik": 0, "uyari": 1, "bilgi": 2}


@dataclass
class Finding:
    severity: str          # kritik | uyari | bilgi
    area: str              # Disk, RAM, Sistem, Önyükleme, Isı, Pil, Sürücü, Uygulama...
    title: str
    explanation: str
    advice: str
    evidence: list = field(default_factory=list)
    count: int = 1


@dataclass
class Report:
    target: str = ""
    os_name: str = ""
    findings: list = field(default_factory=list)
    notes: list = field(default_factory=list)   # what could NOT be checked
    info: dict = field(default_factory=dict)

    def add(self, f):
        # merge identical findings (same title) and keep a few evidence lines
        for g in self.findings:
            if g.title == f.title and g.area == f.area:
                g.count += f.count
                for e in f.evidence:
                    if len(g.evidence) < 5 and e not in g.evidence:
                        g.evidence.append(e)
                return
        f.evidence = f.evidence[:5]
        self.findings.append(f)

    def sorted(self):
        return sorted(self.findings, key=lambda f: (SEV_ORDER[f.severity], -f.count))
