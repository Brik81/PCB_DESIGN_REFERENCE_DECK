"""Side-aware drawing views and reserved-rectangle panels.

A View draws on one side of the card in *view coordinates*: what you see when
looking at that side (ring hole top-left on the front, top-right on the back).
Back-side X is mirrored automatically and text is mirrored so it reads
correctly from the back.

Panels reserve rectangles; overlapping panels or text estimated to overflow
its panel raise LayoutError at generation time.
"""
import math
import re

from .config import H, MECH, STYLE, W
from .pcb import pad

MARGIN = MECH["layout"]["margin"]
ADV = 0.98   # conservative glyph advance / size (caps, digits); measured 0.92-0.98
ADV_LOWER = 0.84
PITCH = STYLE["spacing"]["line_pitch"]


class LayoutError(Exception):
    pass


_MARKUP = re.compile(r"[_^~]\{([^}]*)\}")


def text_width(s, size):
    """Estimated rendered width (mm) of a KiCad stroke-font string incl. markup."""
    w = 0.0
    def run(t, scale):
        nonlocal w
        for ch in t:
            w += size * scale * (ADV_LOWER if ch.islower() else 0.62 if ch in " .,:;'|!il1()[]" else ADV)
    pos = 0
    for m in _MARKUP.finditer(s):
        run(s[pos:m.start()], 1.0)
        run(m.group(1), 1.0 if m.group(0)[0] == "~" else 0.78)
        pos = m.end()
    run(s[pos:], 1.0)
    return w


def style(name):
    st = STYLE["text"][name]
    return st["size"], st["thick"]


class View:
    def __init__(self, board, front=True):
        self.b = board
        self.front = front
        self.p = "F." if front else "B."
        self.reserved = board.meta.setdefault("reserved", {}).setdefault(self.p[0], [])

    # coordinate mapping
    def X(self, x):
        return x if self.front else W - x

    def L(self, name):
        return name if "." in name else self.p + name

    def pts(self, pts):
        return [(self.X(x), y) for x, y in pts]

    # reservation
    def reserve(self, name, x1, y1, x2, y2, edge=False):
        """edge=True: item (a ruler) may run to the bottom edge; copper-edge DRC still applies."""
        ymax = H if edge else H - MARGIN
        if x1 < MARGIN - 1e-6 or y1 < MARGIN - 1e-6 or x2 > W - MARGIN + 1e-6 or y2 > ymax + 1e-6:
            raise LayoutError(f"{self.b.name}/{self.p}{name}: ({x1:.2f},{y1:.2f},{x2:.2f},{y2:.2f}) outside margin")
        for n, a1, b1, a2, b2 in self.reserved:
            if x1 < a2 - 1e-6 and a1 < x2 - 1e-6 and y1 < b2 - 1e-6 and b1 < y2 - 1e-6:
                raise LayoutError(f"{self.b.name}/{self.p}: '{name}' overlaps '{n}'")
        self.reserved.append((name, x1, y1, x2, y2))

    # primitives (view coordinates)
    def text(self, s, x, y, st="body", just="left", layer="SilkS", angle=0, valign=None):
        size, thick = style(st) if isinstance(st, str) else st
        return self.b.text(s, self.X(x), y, self.L(layer), size, thick, just, angle if self.front else -angle,
                           mirror=not self.front, valign=valign)

    def line(self, x1, y1, x2, y2, layer="SilkS", w=0.15):
        return self.b.line(self.X(x1), y1, self.X(x2), y2, self.L(layer), w)

    def rect(self, x1, y1, x2, y2, layer="SilkS", w=0.15, fill=False):
        return self.b.rect(self.X(x1), y1, self.X(x2), y2, self.L(layer), w, fill)

    def circle(self, cx, cy, r, layer="SilkS", w=0.15, fill=False):
        return self.b.circle(self.X(cx), cy, r, self.L(layer), w, fill)

    def arc(self, s, m, e, layer="SilkS", w=0.15):
        f = lambda p: (self.X(p[0]), p[1])
        return self.b.arc(f(s), f(m), f(e), self.L(layer), w)

    def poly(self, pts, layer="SilkS", w=0, fill=True):
        return self.b.poly(self.pts(pts), self.L(layer), w, fill)

    def track(self, x1, y1, x2, y2, w, net=None, layer="Cu"):
        return self.b.track(self.X(x1), y1, self.X(x2), y2, w, self.L(layer), net)

    def arc_track(self, s, m, e, w, net=None, layer="Cu"):
        f = lambda p: (self.X(p[0]), p[1])
        return self.b.arc_track(f(s), f(m), f(e), w, self.L(layer), net)

    def via(self, x, y, size, drill, net=None, tent=True):
        return self.b.via(self.X(x), y, size, drill, net, tent=tent)

    def zone(self, pts, net, layer="Cu", **kw):
        return self.b.zone(self.pts(pts), self.L(layer), net, **kw)

    # exposed-copper ("gold") helpers: copper + identical solder-mask opening
    def gold_rect(self, x1, y1, x2, y2, net=None):
        self.rect(x1, y1, x2, y2, "Cu", 0, True)
        self.rect(x1, y1, x2, y2, "Mask", 0, True)

    def gold_text(self, s, x, y, st="number", just="left"):
        size, thick = style(st) if isinstance(st, str) else st
        self.text(s, x, y, (size, thick), just, "Cu")
        self.text(s, x, y, (size, thick), just, "Mask")

    def gold_track(self, x1, y1, x2, y2, w, net=None):
        self.track(x1, y1, x2, y2, w, net)
        self.line(x1, y1, x2, y2, "Mask", w)

    def pad(self, x, y, w, h=None, shape="rect", kind="smd", drill=None, net=None, rratio=None, angle=0,
            mask_margin=None, zone_connect=None, poly=None, paste=False, name="PAD", prefix="P"):
        """One pad in its own board-only footprint at view (x, y).

        kind: smd | thru_hole | np_thru_hole. poly: custom pad outline, view coords relative to (x, y).
        zone_connect: 1 = thermal relief, 2 = solid.
        """
        extra = []
        if zone_connect is not None:
            extra.append(["zone_connect", zone_connect])
        if poly:
            shape = "custom"
            pts = [["xy", px if self.front else -px, py] for px, py in poly]
            extra += [["options", ["clearance", "outline"], ["anchor", "rect"]],
                      ["primitives", ["gr_poly", ["pts", *pts], ["width", 0], ["fill", "yes"]]]]
        layers = None
        if kind == "smd":
            layers = [self.p + "Cu", self.p + "Mask"] + ([self.p + "Paste"] if paste else [])
        p = pad("1" if kind != "np_thru_hole" else "", kind, shape, 0, 0, w, h, drill=drill, layers=layers,
                net=net, rratio=rratio, angle=angle if self.front else -angle, mask_margin=mask_margin, extra=extra)
        return self.b.footprint(name, self.X(x), y, [p], layer=self.p + "Cu", prefix=prefix)

    def pad_group(self, x, y, pads, name="PADS"):
        """Several SMD pads in ONE footprint (mask webs between them may be ganged like a real part).

        pads: [(dx, dy, w, h)] relative to (x, y) in view coords; each pad gets its own net.
        """
        cu = [self.p + "Cu", self.p + "Mask"]
        items = [pad(str(i + 1), "smd", "rect", dx if self.front else -dx, dy, w, h, layers=cu, net=self.b.net())
                 for i, (dx, dy, w, h) in enumerate(pads)]
        return self.b.footprint(name, self.X(x), y, items, layer=self.p + "Cu", prefix="P")

    def lib_fp(self, lib_name, x, y, angle=0, nets=None):
        """Official KiCad library footprint at view (x, y); mirrored correctly on the back."""
        return self.b.lib_footprint(lib_name, self.X(x), y, angle if self.front else -angle, back=not self.front,
                                    nets=nets)

    def smd_pad(self, x, y, w, h, **kw):
        return self.pad(x, y, w, h, **kw)

    def panel(self, name, x, y, w, h, title=None):
        self.reserve(name, x, y, x + w, y + h)
        return Panel(self, name, x, y, w, h, title)

    def other(self):
        return View(self.b, not self.front)

    def through_panel(self, name, x, y, w, h, title=None, title_other=None):
        """Region holding plated-through features: reserved on BOTH sides (mirrored).

        Returns (panel_this_side, panel_other_side); the other side's panel is in its own view coords.
        """
        o = self.other()
        self.reserve(name, x, y, x + w, y + h)
        o.reserve(name + " (through)", W - x - w, y, W - x, y + h)
        return Panel(self, name, x, y, w, h, title), Panel(o, name, W - x - w, y, w, h, title_other)


class Panel:
    """Reserved rectangle with an optional section title. Coordinates are absolute view mm."""

    def __init__(self, v, name, x, y, w, h, title):
        self.v, self.name, self.x, self.y, self.w, self.h = v, name, x, y, w, h
        self.cy = y
        if title:
            size, _ = style("section")
            self.text(title, x, y + size * 0.6, "section")
            self.cy = y + size * 1.35

    @property
    def x2(self):
        return self.x + self.w

    @property
    def y2(self):
        return self.y + self.h

    def _check(self, s, x, y, size, just):
        tw = text_width(s, size)
        x1 = {"left": x, "right": x - tw, "center": x - tw / 2}[just]
        if x1 < self.x - 0.05 or x1 + tw > self.x2 + 0.05 or y - size * 0.6 < self.y - 0.05 or y + size * 0.6 > self.y2 + 0.05:
            raise LayoutError(f"{self.v.b.name}/{self.v.p}{self.name}: text '{s}' ({tw:.1f} mm) overflows panel")

    def text(self, s, x, y, st="body", just="left", layer="SilkS"):
        size, thick = style(st) if isinstance(st, str) else st
        self._check(s, x, y, size, just)
        return self.v.text(s, x, y, (size, thick), just, layer)

    def lines(self, rows, x=None, y=None, st="body", pitch=PITCH):
        """Stack text lines; returns y after the last line."""
        x = self.x if x is None else x
        y = self.cy + pitch * 0.5 if y is None else y
        for r in rows:
            self.text(r, x, y, st)
            y += pitch
        self.cy = y - pitch * 0.5
        return self.cy

    def table(self, rows, cols, x=None, y=None, st="body", pitch=PITCH, header=True):
        """cols = list of x offsets; prefix offset with '>' string? use negative to right-align at |offset|."""
        x = self.x if x is None else x
        y = self.cy + pitch * 0.5 if y is None else y
        for i, r in enumerate(rows):
            for c, cell in zip(cols, r):
                if cell == "":
                    continue
                if c < 0:
                    self.text(str(cell), x - c, y, st, "right")
                else:
                    self.text(str(cell), x + c, y, st)
            if header and i == 0:
                self.v.line(self.x, y + 0.95, self.x2, y + 0.95, w=0.15)
                y += 0.5
            y += pitch
        self.cy = y - pitch * 0.5
        return self.cy

    def rule(self, y=None):
        y = self.cy + 0.3 if y is None else y
        self.v.line(self.x, y, self.x2, y)
        self.cy = y + 0.3
        return self.cy
