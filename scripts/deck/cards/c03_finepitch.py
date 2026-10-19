"""Card 03 - QFP / BGA / FINE PITCH: real fine-pitch land patterns, pitch strips, BGA fan-out."""
import math

from ..config import RULES, W
from ..eng import dim, mm_to_mil
from ..graphics import package_row
from ..layout import PITCH
from ..packages import info, pkg
from ..template import footer, new_card

Y0 = 11.8
ROW = ["LQFP-48", "LQFP-32", "QFN-32", "BGA-49 0.8", "BGA-68 0.5", "WLCSP-49 0.4"]
STRIPS = [0.40, 0.50, 0.65, 0.80, 1.00]
LQFP = [(32, "LQFP-32_7x7mm_P0.8mm"), (48, "LQFP-48_7x7mm_P0.5mm"), (64, "LQFP-64_10x10mm_P0.5mm"),
        (100, "LQFP-100_14x14mm_P0.5mm"), (144, "LQFP-144_20x20mm_P0.5mm"), (176, "LQFP-176_24x24mm_P0.5mm")]
QFN = [(16, "3.0×3.0"), (20, "4.0×4.0"), (24, "4.0×4.0"), (32, "5.0×5.0"), (48, "7.0×7.0"), (64, "9.0×9.0")]
# pitch, ball, NSMD pad: taken from KiCad 10 library footprint names (vendor drawings)
BGA = [(1.0, 0.5, 0.4, "BGA-100_11.0x11.0mm_Layout10x10_P1.0mm_Ball0.5mm_Pad0.4mm_NSMD"),
       (0.8, 0.4, 0.35, "BGA-121_9.0x9.0mm_Layout11x11_P0.8mm_Ball0.4mm_Pad0.35mm_NSMD"),
       (0.5, 0.3, 0.25, "BGA-68_5.0x5.0mm_Layout9x9_P0.5mm_Ball0.3mm_Pad0.25mm_NSMD"),
       (0.4, 0.25, 0.2, "BGA-36_3.396x3.466mm_Layout6x6_P0.4mm_Ball0.25mm_Pad0.2mm_NSMD")]
FAN = dict(pitch=1.0, pad=0.40, via=(0.45, 0.20), trace=0.10)


def build(card):
    b, f, k = new_card(card, "QFP/QFN/BGA/WLCSP lands, pitch, fan-out", "pin counts, BGA rules, HDI")
    row(f)
    strips(f)
    numbering(f)
    fanout(f)
    footer(k)
    qfp_table(k)
    qfn_table(k)
    bga_table(k)
    hdi_notes(k)
    b.meta["packages"] = [pkg(n)["footprint"] for n in ROW]
    b.meta["pitch_strips_mm"] = STRIPS
    return b


def row(f):
    items = [(pkg(n)["footprint"], n.split()[0], [f"P {pkg(n)['pitch']}", "×".join(dim(x) for x in pkg(n)["body"])])
             for n in ROW]
    p = f.panel("row", 1.6, Y0, 82.4, 1.69 + 1.6 + 10.6 + 0.8 + PITCH + 0.8, "FINE-PITCH LAND PATTERNS (KiCad lib)")
    package_row(p, items, p.cy, 10.6, gap=0.6)


def strips(f):
    """Pitch comparison: 6 pads per strip, pad width = P/2 (illustrative, not a footprint)."""
    p = f.panel("strips", 1.6, 30.9, 52.0, 8.6, "PITCH  (pad w = P/2, illustrative)")
    cw = p.w / len(STRIPS)
    yt, yp, yb = p.cy + 0.75, p.cy + 2.75, p.cy + 4.75
    for i, P in enumerate(STRIPS):
        cx = p.x + cw * (i + 0.5)
        p.text(f"{P:.2f}", cx, yt, just="center")
        p.text(f"{mm_to_mil(P):.1f} mil", cx, yb, just="center")
        f.pad_group(cx, yp, [((j - 2.5) * P, 0, P / 2, 1.4) for j in range(6)], name=f"PITCH_{P:.2f}")
    f.b.meta["pitch_strip_pads"] = len(STRIPS) * 6


def numbering(f):
    p = f.panel("numbering", 1.6, 40.0, 52.0, 12.38, "PIN 1 & NUMBERING")
    s = 7.0
    x0, y0 = p.x + 2.0, p.cy + 0.5          # QFP outline with pin-1 dot, CCW arrow
    f.rect(x0, y0, x0 + s, y0 + s)
    f.circle(x0 + 1.1, y0 + 1.1, 0.45, fill=True)
    for i in range(5):
        f.line(x0 - 0.7, y0 + 1.2 + i * 1.15, x0, y0 + 1.2 + i * 1.15)
    f.text("1", x0 - 1.4, y0 + 1.2, "body", "center")
    f.arc((x0 + 2.8, y0 + 2.6), (x0 + 2.2, y0 + 4.2), (x0 + 3.6, y0 + 5.2))
    f.line(x0 + 3.6, y0 + 5.2, x0 + 3.0, y0 + 5.3)
    f.line(x0 + 3.6, y0 + 5.2, x0 + 3.4, y0 + 4.6)
    p.lines(["QFP/QFN: pin 1 at dot/bevel,", "count CCW seen from top",
             "BGA: A1 corner marked; rows A..", "skip I O Q S X Z; cols 1..n",
             "verify pin 1 vs tape orientation"], x=p.x + 10.5, y=p.cy + 0.8)


def fanout(f):
    """5x5, 1.0 mm BGA: outer ring escapes on top, inner ring dog-bones to vias, bottom escapes."""
    P, pad_d, (vd, vh), tw = FAN["pitch"], FAN["pad"], FAN["via"], FAN["trace"]
    x, y, w, h = 55.4, 30.9, 28.6, 18.6
    pf, pk = f.through_panel("fanout", x, y, w, h, "BGA FAN-OUT 1.0 mm", "ESCAPE, BOTTOM LAYER")
    o = f.other()
    mx = lambda xx: W - xx
    ox, oy = x + 9.0, pf.cy + 4.4               # ball A1 centre
    ball = lambda c, r: (ox + c * P, oy + r * P)
    for r in range(5):
        for c in range(5):
            bx, by = ball(c, r)
            n = f.b.net()
            if (r, c) == (2, 2):                     # via-in-pad (must be filled + capped in production)
                f.pad(bx, by, pad_d, shape="circle", net=n)
                f.via(bx, by, vd, vh, n, tent=False)
                continue
            f.pad(bx, by, pad_d, shape="circle", net=n)
            if r in (0, 4) or c in (0, 4):           # outer ring: straight escape on top
                dx = -1 if c == 0 else 1 if c == 4 else 0
                dy = -1 if r == 0 else 1 if r == 4 else 0
                if dx and dy:
                    dx = 0
                f.gold_track(bx, by, bx + dx * 2.2, by + dy * 2.2, tw, n)
                continue
            # inner ring: dog-bone to the interstitial site facing outwards
            sx = -0.5 if c == 1 else 0.5 if c == 3 else (-0.5 if r == 1 else 0.5)
            sy = -0.5 if r == 1 else 0.5 if r == 3 else (-0.5 if c == 1 else 0.5)
            vx, vy = bx + sx * P, by + sy * P
            f.gold_track(bx, by, vx, vy, tw, n)
            f.via(vx, vy, vd, vh, n, tent=False)
            # bottom-layer escape: away from the array, between the rows of balls above
            dx, dy = (0, -1) if r == 1 else (0, 1) if r == 3 else ((-1, 0) if c == 1 else (1, 0))
            ex = ox - 0.5 * P - 2.2 if dx < 0 else ox + 4.5 * P + 2.2 if dx > 0 else vx
            ey = oy - 0.5 * P - 2.2 if dy < 0 else oy + 4.5 * P + 2.2 if dy > 0 else vy
            o.gold_track(mx(vx), vy, mx(ex), ey, tw, n)
    xl = x + 17.0
    pf.lines(["pad 0.40", "trace 0.10", "via 0.45/0.20", "dog-bone →", "via-in-pad:", "fill + cap"],
             x=xl, y=pf.cy + 0.8)
    pk.lines(["vias carry inner", "balls to the", "bottom layer;", "outer ring stays", "on top"],
             x=pk.x, y=pk.cy + 0.8)
    f.b.meta["fanout"] = FAN


def qfp_table(k):
    p = k.panel("qfp", 1.6, Y0, 44.0, 13.6, "LQFP  JEDEC MS-026 (mm)")
    rows = [["pins", "body", "pitch", "span"]]
    for n, fp in LQFP:
        i = info(f"Package_QFP:{fp}")
        b = i["body"][0]
        rows.append([str(n), f"{dim(b)}×{dim(b)}", dim(i["pitch"]), dim(b + 2.0)])
    p.table(rows, [-4.0, 7.0, -27.0, -38.0])


def qfn_table(k):
    p = k.panel("qfn", 47.0, Y0, 37.0, 13.6, "QFN  P 0.50 typ. (mm)")
    rows = [["pins", "body", "pins", "body"]]
    for (n1, b1), (n2, b2) in zip(QFN[:3], QFN[3:]):
        rows.append([str(n1), b1, str(n2), b2])
    p.table(rows, [-4.0, 7.0, -24.0, 27.0])
    p.lines(["many EP sizes per body:", "always use the datasheet"])


def bga_table(k):
    clr = trace = RULES["min_clearance"]
    p = k.panel("bga", 31.0, 25.6, 53.0, 12.9, f"BGA ESCAPE @ {trace:.2f}/{clr:.2f} trace/space")
    rows = [["pitch", "ball", "pad", "traces", "via max Ø"]]
    for P, ball, pd, _ in BGA:
        gap = P - pd
        n = max(0, math.floor((gap - clr) / (trace + clr)))
        vmax = P * math.sqrt(2) - pd - 2 * clr
        rows.append([dim(P), dim(ball), dim(pd), str(n), f"{vmax:.2f}" + ("" if vmax >= 0.45 else " VIP")])
    p.table(rows, [0, -15.0, -24.0, -36.0, -53.0])
    k.b.meta["bga_escape"] = rows[1:]


def hdi_notes(k):
    p = k.panel("hdi", 31.0, 38.8, 53.0, 10.6, "HDI CONCEPTS")
    p.lines(["NSMD pad: mask clears pad; SMD: mask defines it",
             "via-in-pad: filled + plated over (VIPPO) or solder wicks",
             "microvia: laser, ~0.1 mm, spans 1 layer; card 14",
             "traces = lines between adjacent pads (pad=NSMD Cu)"])
