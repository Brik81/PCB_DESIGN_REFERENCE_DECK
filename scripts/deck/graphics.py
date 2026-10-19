"""Reusable technical graphics: rulers and schematic symbols (silkscreen line art)."""
import math

from .config import H
from .eng import MIL

TICK_W = 0.15            # copper tick width, mm
EDGE_GAP = 0.8           # tick start distance from card edge; keeps end ticks 0.5 mm off the corner radii


def _ruler(v, name, x0, positions, unit, labels):
    """positions: [(offset_mm, tick_len_mm)], labels: [(offset_mm, text)]. Ticks are exposed copper."""
    y_edge = H - EDGE_GAP
    y_num = y_edge - max(l for _, l in positions) - 0.95
    x_end = x0 + max(p for p, _ in positions)
    v.reserve(name, x0 - 0.8, y_num - 0.7, x_end + 0.8, H, edge=True)
    for p, l in positions:
        v.gold_track(x0 + p, y_edge, x0 + p, y_edge - l, TICK_W)
    for p, t in [(0, "0")] + labels:
        v.text(t, x0 + p, y_num, "body", "center")
    v.text(unit, x0 + 1.6, y_num, "body", "left")
    v.b.meta.setdefault("rulers", []).append(
        {"side": v.p[0], "unit": unit, "x0": round(v.X(x0), 4), "positions": [round(p, 4) for p, _ in positions]})
    return y_num - 0.7


def metric_ruler(v, x0, length_mm=80):
    """1 mm ticks, 5/10 mm majors. Zero = first tick, not the card edge (edge tolerance +/-0.2 mm)."""
    pos = [(i, 2.2 if i % 10 == 0 else 1.5 if i % 5 == 0 else 0.9) for i in range(length_mm + 1)]
    return _ruler(v, "metric ruler", x0, pos, "mm", [(i, str(i)) for i in range(10, length_mm + 1, 10)])


def inch_ruler(v, x0, length_in=3.1):
    """50 mil ticks; 100 mil, 500 mil and 1 in majors."""
    pos = []
    for i in range(int(round(length_in * 20)) + 1):
        m = i * 50
        pos.append((m * MIL, 2.2 if m % 1000 == 0 else 1.8 if m % 500 == 0 else 1.3 if m % 100 == 0 else 0.8))
    return _ruler(v, "inch ruler", x0, pos, "in", [(k * 25.4, str(k)) for k in range(1, int(length_in) + 1)])


def package_row(p, items, y_top, band_h, gap=0.8, top_label=True):
    """Place library footprints side by side inside panel p.

    items: [(lib_name, top_text, [lines below][, angle 0|90])]. Footprints are centred (by courtyard)
    in a band of height band_h starting at y_top; returns y after the last text line.
    Raises LayoutError via the panel if text overflows; checks band/courtyard fit here.
    """
    from .layout import LayoutError, PITCH, text_width
    from .packages import info
    cells = []
    for lib, top, below, *ang in items:
        c = info(lib)["crtyd"]
        a = ang[0] if ang else 0
        if a == 90:          # KiCad +90 deg (CCW on screen, y down): (x, y) -> (y, -x)
            c = (c[1], -c[2], c[3], -c[0])
        tw = max([text_width(t, 1.0) for t in [top, *below]] + [c[2] - c[0]])
        if c[3] - c[1] > band_h + 1e-6:
            raise LayoutError(f"{p.name}: {lib} courtyard {c[3] - c[1]:.2f} > band {band_h}")
        cells.append((lib, top, below, c, tw, a))
    total = sum(c[4] for c in cells)
    spare = p.w - total
    if spare < gap * (len(cells) - 1) - 1e-6:
        raise LayoutError(f"{p.name}: package row needs {total + gap * (len(cells) - 1):.1f} mm > {p.w:.1f}")
    g = spare / (len(cells) - 1) if len(cells) > 1 else 0
    x = p.x
    yl = y_top + 0.8
    yb = y_top + (1.6 if top_label else 0) + band_h / 2
    ybelow = y_top + (1.6 if top_label else 0) + band_h + 0.8
    out = []
    for lib, top, below, c, tw, a in cells:
        cx = x + tw / 2
        p.v.lib_fp(lib, cx - (c[0] + c[2]) / 2, yb - (c[1] + c[3]) / 2, a)
        if top_label:
            p.text(top, cx, yl, just="center")
        for i, t in enumerate(below):
            if t:
                p.text(t, cx, ybelow + i * PITCH, just="center")
        out.append((lib, cx, yb))
        x += tw + g
    nlines = max(len(c[2]) for c in cells)
    p.cy = ybelow + (nlines - 1) * PITCH + 0.8
    return out


class Sch:
    """Schematic line art on silkscreen (view coordinates, mm). Pins are axis-aligned."""

    def __init__(self, v, w=0.15):
        self.v, self.w = v, w

    # basic
    def wire(self, *pts):
        for a, b in zip(pts, pts[1:]):
            self.v.line(a[0], a[1], b[0], b[1], w=self.w)

    def dot(self, x, y, r=0.3):
        self.v.circle(x, y, r, w=0, fill=True)

    def text(self, s, x, y, just="left"):
        self.v.text(s, x, y, "body", just)

    @staticmethod
    def _axes(x1, y1, x2, y2):
        L = math.hypot(x2 - x1, y2 - y1)
        d = ((x2 - x1) / L, (y2 - y1) / L)
        return L, d, (-d[1], d[0])

    def _two(self, x1, y1, x2, y2, body):
        """Draw leads to a centred body of length `body`; returns (centre, dir, normal)."""
        L, d, n = self._axes(x1, y1, x2, y2)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        a = (cx - d[0] * body / 2, cy - d[1] * body / 2)
        b = (cx + d[0] * body / 2, cy + d[1] * body / 2)
        self.wire((x1, y1), a)
        self.wire(b, (x2, y2))
        return (cx, cy), d, n

    def _pt(self, c, d, n, u, t):
        return (c[0] + d[0] * u + n[0] * t, c[1] + d[1] * u + n[1] * t)

    # passives
    def res(self, x1, y1, x2, y2, body=2.0, h=0.8):
        c, d, n = self._two(x1, y1, x2, y2, body)
        p = lambda u, t: self._pt(c, d, n, u, t)
        self.wire(p(-body / 2, -h / 2), p(body / 2, -h / 2), p(body / 2, h / 2), p(-body / 2, h / 2), p(-body / 2, -h / 2))

    def cap(self, x1, y1, x2, y2, polar=False, gap=0.5, plate=1.6):
        c, d, n = self._two(x1, y1, x2, y2, gap)
        p = lambda u, t: self._pt(c, d, n, u, t)
        self.wire(p(-gap / 2, -plate / 2), p(-gap / 2, plate / 2))
        if polar:   # curved negative plate drawn as an arc; '+' at the positive (first) pin
            self.v.arc(p(gap / 2 + 0.25, -plate / 2), p(gap / 2, 0), p(gap / 2 + 0.25, plate / 2), w=self.w)
        else:
            self.wire(p(gap / 2, -plate / 2), p(gap / 2, plate / 2))

    def ind(self, x1, y1, x2, y2, n_turns=3, r=0.45):
        body = 2 * r * n_turns
        c, d, n = self._two(x1, y1, x2, y2, body)
        for i in range(n_turns):
            u0 = -body / 2 + 2 * r * i
            self.v.arc(self._pt(c, d, n, u0, 0), self._pt(c, d, n, u0 + r, -r), self._pt(c, d, n, u0 + 2 * r, 0),
                       w=self.w)

    def diode(self, x1, y1, x2, y2, kind="d", s=1.2):
        """Anode at (x1,y1), cathode at (x2,y2). kind: d, zener, schottky, led, tvs."""
        body = 2 * s if kind == "tvs" else s
        c, d, n = self._two(x1, y1, x2, y2, body)
        p = lambda u, t: self._pt(c, d, n, u, t)
        h = s * 0.55
        if kind == "tvs":
            self.wire(p(-s, -h), p(0, 0), p(-s, h), p(-s, -h))
            self.wire(p(s, -h), p(0, 0), p(s, h), p(s, -h))
            self.wire(p(-0.25, -h - 0.2), p(0, -h), p(0, h), p(0.25, h + 0.2))
            return
        self.wire(p(-s / 2, -h), p(s / 2, 0), p(-s / 2, h), p(-s / 2, -h))
        self.wire(p(s / 2, -h), p(s / 2, h))
        if kind == "zener":
            self.wire(p(s / 2 - 0.3, -h - 0.2), p(s / 2, -h))
            self.wire(p(s / 2, h), p(s / 2 + 0.3, h + 0.2))
        elif kind == "schottky":
            self.wire(p(s / 2 - 0.3, -h + 0.3), p(s / 2 - 0.3, -h), p(s / 2, -h))
            self.wire(p(s / 2, h), p(s / 2 + 0.3, h), p(s / 2 + 0.3, h - 0.3))
        elif kind == "led":
            for o in (-0.2, 0.4):
                a, b = p(o, -h - 0.2), p(o + 0.6, -h - 0.9)
                self.wire(a, b)
                self.wire(b, (b[0] - 0.3 * d[0] - 0.05, b[1] + 0.25))

    def gnd(self, x, y):
        self.wire((x, y), (x, y + 0.5))
        for i, hw in enumerate((0.8, 0.5, 0.2)):
            self.wire((x - hw, y + 0.5 + i * 0.3), (x + hw, y + 0.5 + i * 0.3))

    def rail(self, x, y, label):
        self.wire((x, y), (x, y - 0.6))
        self.wire((x - 0.7, y - 0.6), (x + 0.7, y - 0.6))
        self.text(label, x, y - 1.45, "center")

    # active
    def opamp(self, x, y, s=4.0, inv_top=True):
        """Triangle with left edge at x, centred on y. Returns pin coordinates."""
        self.wire((x, y - s / 2), (x + s, y), (x, y + s / 2), (x, y - s / 2))
        yi, yn = (y - s / 4, y + s / 4) if inv_top else (y + s / 4, y - s / 4)
        self.wire((x + 0.3, yi), (x + 0.9, yi))                          # minus
        self.wire((x + 0.3, yn), (x + 0.9, yn))                          # plus
        self.wire((x + 0.6, yn - 0.3), (x + 0.6, yn + 0.3))
        return {"inm": (x, yi), "inp": (x, yn), "out": (x + s, y)}

    def bjt(self, x, y, pnp=False, s=2.4):
        """Base bar at x. Returns pins b, c, e."""
        self.wire((x, y - s / 3), (x, y + s / 3))
        c, e = (x + s / 2, y - s / 2), (x + s / 2, y + s / 2)
        self.wire((x, y - s / 6), c)
        self.wire((x, y + s / 6), e)
        tip, tail = ((x, y + s / 6), e) if pnp else (e, (x, y + s / 6))
        L, d, n = self._axes(tail[0], tail[1], tip[0], tip[1])
        b1 = (tip[0] - d[0] * 0.6 + n[0] * 0.3, tip[1] - d[1] * 0.6 + n[1] * 0.3)
        b2 = (tip[0] - d[0] * 0.6 - n[0] * 0.3, tip[1] - d[1] * 0.6 - n[1] * 0.3)
        self.wire(b1, tip, b2)
        self.wire((x - 1.0, y), (x, y))
        return {"b": (x - 1.0, y), "c": c, "e": e}

    def mosfet(self, x, y, p_ch=False, s=2.4):
        """Gate plate at x. Enhancement mode, body diode omitted. Returns pins g, d, s."""
        self.wire((x, y - s / 3), (x, y + s / 3))
        xc = x + 0.4
        for yy in (-s / 3, 0, s / 3):
            self.wire((xc, y + yy - 0.25), (xc, y + yy + 0.25))
        d_, s_ = (x + s * 0.7, y - s / 2), (x + s * 0.7, y + s / 2)
        self.wire((xc, y - s / 3), (d_[0], y - s / 3), d_)
        self.wire((xc, y + s / 3), (s_[0], y + s / 3), s_)
        self.wire((xc, y), (s_[0], y), (s_[0], y + s / 3))
        if p_ch:
            self.wire((xc + 0.35, y - 0.25), (xc + 0.75, y), (xc + 0.35, y + 0.25))
        else:
            self.wire((xc + 0.4, y - 0.25), (xc, y), (xc + 0.4, y + 0.25))
        self.wire((x - 1.0, y + s / 3), (x, y + s / 3))   # gate lead into the gate plate (drawn at x)
        return {"g": (x - 1.0, y + s / 3), "d": d_, "s": s_}

    def gate(self, kind, x, y):
        """Distinctive-shape gate, body 4 x 4 mm, body left edge at x, centred on y.

        kind: BUF NOT AND NAND OR NOR XOR XNOR. Returns input pins [(x,y), ...] and output pin.
        """
        a = self.v.arc
        base = {"BUF": "BUF", "NOT": "BUF", "AND": "AND", "NAND": "AND"}.get(kind, "OR")
        tip = x + 4.0
        if base == "BUF":
            self.wire((x, y - 2), (tip, y), (x, y + 2), (x, y - 2))
            ins = [(x - 1.2, y)]
            self.wire(ins[0], (x, y))
        elif base == "AND":
            self.wire((x + 2, y - 2), (x, y - 2), (x, y + 2), (x + 2, y + 2))
            a((x + 2, y - 2), (tip, y), (x + 2, y + 2), w=self.w)
            ins = [(x - 1.2, y - 1), (x - 1.2, y + 1)]
            for p in ins:
                self.wire(p, (x, p[1]))
        else:                                   # OR family: concave back (circle r 2.9 through (x,+-2), (x+0.8,0))
            a((x, y - 2), (x + 0.8, y), (x, y + 2), w=self.w)
            a((x, y - 2), (x + 2.6, y - 1.45), (tip, y), w=self.w)
            a((x, y + 2), (x + 2.6, y + 1.45), (tip, y), w=self.w)
            ins = [(x - 1.2, y - 1), (x - 1.2, y + 1)]
            for p in ins:
                self.wire(p, (x + 0.62, p[1]))
            if kind.startswith("X"):
                a((x - 0.6, y - 2), (x + 0.2, y), (x - 0.6, y + 2), w=self.w)
        bubble = kind in ("NOT", "NAND", "NOR", "XNOR")
        if bubble:
            self.v.circle(tip + 0.35, y, 0.35, w=self.w)
        out = (tip + 1.6, y)
        self.wire((tip + (0.7 if bubble else 0), y), out)
        return ins, out
