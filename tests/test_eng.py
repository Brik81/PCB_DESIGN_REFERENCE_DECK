"""Regression tests for unit conversions and analytical models against known reference values."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from deck import eng  # noqa: E402


class Conversions(unittest.TestCase):
    def test_mil(self):
        self.assertAlmostEqual(eng.mil_to_mm(1000), 25.4)
        self.assertAlmostEqual(eng.mm_to_mil(1.0), 39.3700787, places=6)
        self.assertAlmostEqual(eng.mil_to_mm(4), 0.1016)

    def test_temperature_db(self):
        self.assertAlmostEqual(eng.c_to_k(25), 298.15)
        self.assertAlmostEqual(eng.db20(10), 20.0)
        self.assertAlmostEqual(eng.db10(2), 3.0103, places=4)

    def test_fmt(self):
        self.assertEqual(eng.fmt(0.10160, 3), "0.102")
        self.assertEqual(eng.fmt(124.91, 3), "125")
        self.assertEqual(eng.fmt(1.0, 3), "1.00")


class Physics(unittest.TestCase):
    def test_constants(self):
        self.assertAlmostEqual(eng.ETA0, 376.73, places=2)

    def test_thermal_noise_1k(self):
        # 1 kohm at 300 K: 4.07 nV/rtHz (widely tabulated)
        self.assertAlmostEqual(eng.thermal_noise_density(1e3, 300) * 1e9, 4.07, places=2)

    def test_rc_lc(self):
        self.assertAlmostEqual(eng.rc_cutoff(1e3, 159.155e-9), 1000.0, delta=0.1)
        self.assertAlmostEqual(eng.lc_resonance(1e-6, 1e-9), 5.0329e6, delta=1e2)

    def test_diff_width_roundtrip(self):
        w = eng.diff_microstrip_width(90, 0.2, 0.91, 4.5, 0.035)
        self.assertAlmostEqual(eng.diff_microstrip(w, 0.2, 0.91, 4.5, 0.035), 90, places=6)

    def test_via(self):
        # 0.3 mm hole, 25 um plating, 1.6 mm board: barrel area = pi*0.025*0.325 = 0.02553 mm^2
        self.assertAlmostEqual(eng.via_barrel_area_mm2(0.3, 25), 0.025525, places=5)
        self.assertAlmostEqual(eng.via_resistance(0.3, 1.6, 25) * 1e3, 1.0807, places=3)
        self.assertAlmostEqual(eng.via_thermal_res(0.3, 1.0, 25), 100.45, places=1)

    def test_copper(self):
        # 1 oz (35 um) copper: ~0.49 mohm/sq at 20 degC
        self.assertAlmostEqual(eng.sheet_resistance(35) * 1e3, 0.4926, places=3)
        # 10 mil, 1 oz, dT=10 K external: ~0.88 A by the IPC-2221 fit
        self.assertAlmostEqual(eng.ipc2221_current(10, 1.378, 10), 0.88, delta=0.02)

    def test_e_series(self):
        e96 = eng.e_series(96)
        self.assertEqual(len(e96), 96)
        for v in (1.00, 1.02, 2.49, 4.99, 9.76):
            self.assertIn(v, e96)
        self.assertEqual(len(eng.E24), 24)


class RF(unittest.TestCase):
    def test_wavelength(self):
        self.assertAlmostEqual(eng.wavelength_m(2.4e9) * 1e3, 124.9, places=1)
        self.assertAlmostEqual(eng.wavelength_m(433e6), 0.6924, places=3)

    def test_gamma_vswr(self):
        g = eng.gamma(75, 50)
        self.assertAlmostEqual(g, 0.2)
        self.assertAlmostEqual(eng.vswr(g), 1.5)
        self.assertAlmostEqual(eng.return_loss_db(g), 13.98, places=2)

    def test_ellipk(self):
        self.assertAlmostEqual(eng.ellipk(0), math.pi / 2)
        self.assertAlmostEqual(eng.ellipk(math.sqrt(0.5)), 1.854075, places=6)

    def test_microstrip_reference(self):
        # w/h = 1, er = 1 (air): Hammerstad-Jensen gives ~126.5 ohm (Pozar tables ~126)
        z, ee = eng.microstrip(1, 1, 1.0)
        self.assertAlmostEqual(z, 126.5, delta=1.0)
        self.assertAlmostEqual(ee, 1.0, places=6)
        # 1.6 mm FR-4 (er 4.3), w = 3.0 mm, 35 um copper -> ~50 ohm
        z, _ = eng.microstrip(3.0, 1.6, 4.3, 0.035)
        self.assertAlmostEqual(z, 50.0, delta=2.0)
        w = eng.microstrip_width(50, 1.6, 4.3, 0.035)
        self.assertAlmostEqual(eng.microstrip(w, 1.6, 4.3, 0.035)[0], 50.0, places=3)

    def test_stripline_reference(self):
        # Pozar example 3.5: b = 0.32 cm, er = 2.20, 50 ohm -> W = 0.266 cm
        self.assertAlmostEqual(eng.stripline(0.266, 0.32, 2.20), 50.0, delta=1.0)

    def test_cpwg_monotonic(self):
        z1, _ = eng.cpwg(1.0, 0.15, 1.0, 4.5)
        z2, _ = eng.cpwg(1.0, 0.30, 1.0, 4.5)
        self.assertLess(z1, z2)
        s = eng.cpwg_gap(50, 1.0, 0.93, 4.5)
        self.assertAlmostEqual(eng.cpwg(1.0, s, 0.93, 4.5)[0], 50, places=3)


if __name__ == "__main__":
    unittest.main()
