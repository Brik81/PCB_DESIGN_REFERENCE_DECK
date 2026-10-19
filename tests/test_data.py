"""Cross-check the curated package registry against the installed KiCad library geometry."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from deck.packages import info, registry  # noqa: E402

TOL = 0.06   # mm; KiCad F.Fab outlines are nominal +/- drawing rounding


class ChipBodies(unittest.TestCase):
    def test_chip_bodies_match_kicad_fab(self):
        for eia, metric, fp, _, L, W in registry()["chip"]["codes"]:
            kb = sorted(info(fp)["body"])
            with self.subTest(eia=eia):
                self.assertAlmostEqual(kb[1], L, delta=TOL)
                self.assertAlmostEqual(kb[0], W, delta=TOL)

    def test_metric_code_consistent(self):
        for eia, metric, fp, *_ in registry()["chip"]["codes"]:
            self.assertIn(metric, fp)


class Packages(unittest.TestCase):
    def test_bodies(self):
        for p in registry()["pkg"]:
            if p["status"] == "UNVERIFIED":
                continue
            want = sorted(p.get("kicad_fab", p["body"]))
            with self.subTest(pkg=p["key"]):
                got = sorted(info(p["footprint"])["body"])
                self.assertAlmostEqual(got[0], want[0], delta=TOL)
                self.assertAlmostEqual(got[1], want[1], delta=TOL)

    def test_pitch(self):
        for p in registry()["pkg"]:
            i = info(p["footprint"])
            if p["pins"] <= 3 or i["pitch"] is None:
                continue
            with self.subTest(pkg=p["key"]):
                self.assertAlmostEqual(i["pitch"], float(p["pitch"].split("/")[0]), delta=0.001)

    def test_pin_count(self):
        for p in registry()["pkg"]:
            if p["key"].startswith("PowerPAK"):
                continue   # drain leads merged into the tab land
            with self.subTest(pkg=p["key"]):
                self.assertIn(info(p["footprint"])["pins"], (p["pins"], p["pins"] + 1))   # +1 = exposed pad

    def test_status_values(self):
        for p in registry()["pkg"]:
            self.assertIn(p["status"], ("VERIFIED", "CROSS-CHECKED", "UNVERIFIED"))
            self.assertTrue(p["source"])


if __name__ == "__main__":
    unittest.main()
