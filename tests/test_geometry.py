"""Tests for the board writer, mirroring, layout guards and outline validation."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from deck.config import H, W  # noqa: E402
from deck.layout import LayoutError, View, text_width  # noqa: E402
from deck.pcb import Board, _flip, rounded_rect_outline  # noqa: E402
from deck.sexpr import Q, dumps, loads  # noqa: E402
from validate_boards import bbox, check_outline, check_through, outline  # noqa: E402


class Sexpr(unittest.TestCase):
    def test_roundtrip(self):
        t = ["a", Q('x "q"'), ["b", 1, 2.5, -0.0], ["c", ["d", Q("")]]]
        back = loads(dumps(t))
        self.assertEqual(back[1], 'x "q"')
        self.assertEqual(back[2], ["b", "1", "2.5", "0"])


class Outline(unittest.TestCase):
    def test_card_outline_closed_and_sized(self):
        b = Board("t")
        rounded_rect_outline(b, W, H, 3.18)
        segs = outline(b.items)
        ok, _ = check_outline(segs)
        self.assertTrue(ok)
        x1, y1, x2, y2 = bbox(segs)
        self.assertAlmostEqual(x2 - x1, W)
        self.assertAlmostEqual(y2 - y1, H)

    def test_open_outline_detected(self):
        b = Board("t")
        rounded_rect_outline(b, W, H, 3.18)
        b.items.pop(0)
        self.assertFalse(check_outline(outline(b.items))[0])


class Mirroring(unittest.TestCase):
    def test_back_view_mirrors_x(self):
        b = Board("t")
        k = View(b, front=False)
        k.line(10, 5, 20, 5)
        item = b.items[-1]
        self.assertEqual(item[1], ["start", W - 10, 5])
        self.assertEqual(str(item[-2][1]), "B.SilkS")

    def test_back_text_is_mirrored(self):
        b = Board("t")
        View(b, front=False).text("x", 10, 10)
        self.assertIn("mirror", b.items[-1][4][2])

    def test_flip_footprint_child(self):
        pad = ["pad", Q("1"), "smd", "rect", ["at", "1.0", "2.0"], ["layers", Q("F.Cu"), Q("F.Mask")]]
        f = _flip(pad)
        self.assertEqual(f[4], ["at", "1.0", -2.0, 180.0])
        self.assertEqual([str(x) for x in f[5][1:]], ["B.Cu", "B.Mask"])


class LayoutGuards(unittest.TestCase):
    def test_overlap_rejected(self):
        v = View(Board("t"))
        v.panel("a", 10, 20, 10, 10)
        with self.assertRaises(LayoutError):
            v.panel("b", 15, 25, 10, 10)

    def test_margin_rejected(self):
        with self.assertRaises(LayoutError):
            View(Board("t")).panel("a", 0.5, 20, 10, 10)

    def test_text_overflow_rejected(self):
        p = View(Board("t")).panel("a", 10, 20, 5, 10)
        with self.assertRaises(LayoutError):
            p.text("THIS IS FAR TOO LONG", 10, 22)

    def test_text_width_markup(self):
        self.assertLess(text_width("V_{out}", 1.0), text_width("Vout", 1.0))  # subscripts render smaller
        self.assertAlmostEqual(text_width("AAAA", 2.0), 2 * text_width("AAAA", 1.0))


if __name__ == "__main__":
    unittest.main()


class Through(unittest.TestCase):
    def test_via_outside_through_region_fails(self):
        tree = loads('(kicad_pcb (via (at 10 10) (size 0.6) (drill 0.3)) (via (at 50 30) (size 0.6) (drill 0.3)))')
        rects = {"B": [["coupon (through)", 5, 5, 20, 20]]}
        status, detail = check_through(tree, rects)
        self.assertEqual(status, "FAIL")
        self.assertIn("(50.0, 30.0)", detail)
        rects["B"].append(["x (through)", 40, 20, 60, 40])
        self.assertEqual(check_through(tree, rects)[0], "PASS")
