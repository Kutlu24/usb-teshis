import sys, datetime, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from usb_teshis.model import Report
from usb_teshis import windows, linux, hw

NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
def ev(prov, eid, data=""):
    return (f'<Event><System><Provider Name="{prov}"/><EventID>{eid}</EventID>'
            f'<TimeCreated SystemTime="{NOW}"/></System><EventData>{data}</EventData></Event>')

class T(unittest.TestCase):
    def test_windows_bugcheck_and_power(self):
        r = Report(); cutoff = datetime.datetime(2000,1,1,tzinfo=datetime.timezone.utc)
        windows._event(ev("Microsoft-Windows-Kernel-Power", 41), r, cutoff)
        windows._event(ev("Microsoft-Windows-WER-SystemErrorReporting".replace("WER-SystemErrorReporting","BugCheck"), 1001,
                          "<Data>0x0000007a</Data>"), r, cutoff)
        windows._event(ev("disk", 7), r, cutoff)
        titles = [f.title for f in r.findings]
        self.assertTrue(any("Kernel-Power 41" in t for t in titles))
        self.assertTrue(any("Mavi ekran" in t for t in titles))
        bc = next(f for f in r.findings if "Mavi ekran" in f.title)
        self.assertIn("KERNEL_DATA_INPAGE_ERROR", bc.explanation)
        self.assertTrue(any(f.severity == "kritik" and f.area == "Disk" for f in r.findings))
    def test_old_events_filtered(self):
        r = Report(); cutoff = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        windows._event(ev("Microsoft-Windows-Kernel-Power", 41), r, cutoff)
        self.assertEqual(r.findings, [])
    def test_linux_text(self):
        r = Report()
        linux.scan_text("kernel: Out of memory: Killed process 1 (python3)\nkernel: Buffer I/O error on dev sda1, logical block 5\n", "t", r)
        self.assertEqual({f.area for f in r.findings}, {"RAM", "Disk"})
    def test_smart_fail(self):
        r = Report()
        hw.evaluate_smart("sda", {"model_name": "X", "smart_status": {"passed": False},
            "ata_smart_attributes": {"table": [{"name": "Current_Pending_Sector", "raw": {"value": 12}}]}}, r)
        self.assertEqual(len([f for f in r.findings if f.severity == "kritik"]), 2)
    def test_missing_windows_files(self):
        import tempfile
        d = Path(tempfile.mkdtemp()); (d/"Windows/System32/config").mkdir(parents=True)
        r = Report(); windows._boot_checks(str(d), r)
        self.assertTrue(any("Eksik sistem dosyası" in f.title for f in r.findings))

class Esc(unittest.TestCase):
    def test_escape_stripped(self):
        from usb_teshis import report as rp
        r = Report(os_name="x\x1b[2Jy"); linux.scan_text("kernel: Out of memory: Killed process 1 (\x1b]0;pwn\x07)\n", "t", r)
        out = rp.to_text(r)
        self.assertNotIn("\x1b", out); self.assertNotIn("\x07", out)
        self.assertNotIn("\x1b", rp.to_html(r))

class Brief(unittest.TestCase):
    def test_brief_keeps_own_color_but_strips_log_escapes(self):
        from usb_teshis import report as rp
        r = Report(os_name="x\x1b[2J"); linux.scan_text("kernel: Out of memory: Killed process 1 (\x1b[31m?[evil)\n", "t", r)
        out = rp.to_brief(r)
        self.assertIn("\x1b[1;37;41m", out)              # our banner color is there
        self.assertNotIn("\x1b[2J", out); self.assertNotIn("\x1b[31m", out)   # log escapes are not

if __name__ == "__main__": unittest.main()
