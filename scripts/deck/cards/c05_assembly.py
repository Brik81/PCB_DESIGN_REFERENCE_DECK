"""Card 05 - SOLDERING / ASSEMBLY: joint cross-sections, reflow profile, thermal relief, paste/mask."""
from ..config import RULES, W, data_table
from ..template import footer, new_card

Y0 = 11.8
RELIEF = [("solid", "solid", 0.3, 0.3), ("0.25/0.25", "thermal", 0.25, 0.25), ("0.5/0.5", "thermal", 0.5, 0.5)]
mx = lambda x: W - x


def build(card):
    b, f, k = new_card(card, "joints, reflow, relief, paste", "alloys, flux, classes, defects")
    footer(k)
    joints(f)
    reflow(f)
    relief(f)
    paste(f)
    alloys(k)
    hand(k)
    classes(k)
    defects(k)
    b.meta["thermal_relief"] = RELIEF
    return b


def _chip(f, x, y, kind):
    """Side view of a chip on two pads; x,y = left end of the board surface, 14 mm wide."""
    f.line(x, y, x + 14, y)                                # board surface
    for px in (x + 1.0, x + 10.0):                         # pads
        f.rect(px, y - 0.35, px + 3.0, y, fill=True)
    tilt = kind == "TOMBSTONE"
    if tilt:                                               # body stands on the right pad
        f.poly([(x + 10.6, y - 0.35), (x + 11.6, y - 0.35), (x + 11.6, y - 5.0), (x + 10.6, y - 5.0)], fill=False,
               w=0.15)
        f.arc((x + 12.9, y - 0.35), (x + 12.0, y - 1.0), (x + 11.6, y - 2.0))
        return
    bx1, bx2, by = x + 2.5, x + 11.5, y - 0.6
    f.rect(bx1, by - 1.8, bx2, by)                          # body
    f.line(bx1 + 1.0, by - 1.8, bx1 + 1.0, by)             # terminations
    f.line(bx2 - 1.0, by - 1.8, bx2 - 1.0, by)
    for side in (-1, 1):
        pe = x + 1.0 if side < 0 else x + 13.0              # pad outer edge
        be = bx1 if side < 0 else bx2                       # body end
        if kind == "GOOD":                                  # concave fillet, wets pad to ~1/2+ height
            f.arc((pe, y - 0.35), (be + side * 0.45, by - 0.55), (be, by - 1.2))
        elif kind == "INSUFF.":
            f.arc((be + side * 0.6, y - 0.35), (be + side * 0.2, by + 0.05), (be, by - 0.2))
        elif kind == "EXCESS":                              # convex, past the body top
            f.arc((pe, y - 0.35), (be + side * 1.1, by - 1.6), (be, by - 2.3))
        elif kind == "BRIDGE":
            pass
    if kind == "BRIDGE":                                    # solder under / between: end-to-end short
        f.rect(x + 4.0, y - 0.6, x + 10.0, y - 0.35, fill=True)


def joints(f):
    p = f.panel("joints", 1.6, Y0, 52.0, 21.2, "CHIP JOINTS (side view)")
    kinds = ["GOOD", "INSUFF.", "EXCESS", "TOMBSTONE", "BRIDGE"]
    xs = [p.x + 0.4 + 17.4 * (i % 3) for i in range(6)]
    for i, kd in enumerate(kinds):
        x, y = xs[i], p.cy + 6.0 + (i // 3) * 9.4
        _chip(f, x, y, kd)
        p.text(kd, x + 7.0, y + 1.3, just="center")
    p.lines(["fillet: concave,", "wets pad + end", "termination"], x=xs[5], y=p.cy + 9.4 + 1.3)


def reflow(f):
    r = data_table("assembly")["reflow_sac305"]
    p = f.panel("reflow", 55.4, Y0, 28.6, 21.2, "REFLOW, SAC305 typ.")
    x0, y0, w, h = p.x + 3.2, p.y2 - 2.6, 24.4, 14.5           # axes origin (bottom-left)
    tmax, Tmax = 300.0, 260.0
    X = lambda t: x0 + t / tmax * w
    Y = lambda T: y0 - T / Tmax * h
    f.line(x0, y0, x0 + w, y0)
    f.line(x0, y0, x0, y0 - h)
    pts = [(X(t), Y(T)) for t, T in r["profile"]]
    for a, b_ in zip(pts, pts[1:]):
        f.line(*a, *b_, w=0.2)
    yl = Y(r["liquidus"])
    for i in range(12):                                         # dashed liquidus line
        f.line(X(i * 25), yl, X(i * 25 + 12), yl)
    p.text(f"{r['liquidus']}", x0 - 0.3, yl, just="right")
    p.text("°C", x0 - 0.3, y0 - h + 0.6, just="right")
    p.text("100", x0 - 0.3, Y(100), just="right")
    p.text("t →", x0 + w, y0 + 1.1, just="right")
    p.text("0", x0, y0 + 1.1, just="center")
    p.text("preheat", x0 + 0.6, Y(195))
    p.text(f"peak {r['peak']}", X(190), Y(253), just="right")
    p.text(f"TAL {r['tal']}", X(70), Y(55))


def relief(f):
    pf, pk = f.through_panel("relief", 1.6, 34.0, 36.0, 15.4, "THERMAL RELIEF spoke/gap", "THERMAL RELIEF")
    cw = pf.w / 3
    for i, (lab, conn, spoke, gap) in enumerate(RELIEF):
        x1, x2 = pf.x + i * cw + 0.6, pf.x + (i + 1) * cw - 0.6
        y1, y2 = pf.cy + 0.6, pf.cy + 9.4
        net = f.b.net()
        poly = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        f.zone(poly, net, clearance=gap, connect=conn, thermal_gap=gap, spoke=spoke, min_thick=0.2)
        f.rect(x1, y1, x2, y2, "Mask", 0, True)                 # expose the pour: relief gaps visible
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        f.pad(cx, cy, 2.0, shape="circle", kind="thru_hole", drill=1.0, net=net)
        pf.text(lab, cx, y2 + 1.2, just="center")
        pk.text(lab, mx(cx), y2 + 1.2, just="center")
    pk.lines(["relief: easier to hand-solder"], y=pk.cy + 0.8)
    pk.lines(["solid: lowest R/L, for power"], y=pk.y2 - 0.8)


def paste(f):
    s = data_table("assembly")["stencil"]
    p = f.panel("paste", 39.0, 34.0, 45.0, 18.38, "MASK & PASTE")
    p.lines([f"mask exp. {RULES['solder_mask_expansion']:.2f} here; web ≥ {RULES['solder_mask_min_width']:.2f}",
             "stencil t " + s["thickness_um"] + " µm",
             f"area ratio a·b/(2(a+b)·t) ≥ {s['area_ratio_min']}",
             f"aspect ratio a/t ≥ {s['aspect_ratio_min']}",
             "fine pitch: aperture −10 % typ.",
             "thermal pad: window-pane 50-80 %",
             "via in pad: plug or tent, no wicking",
             "IPC-7525 as summarised"])


def alloys(k):
    a = data_table("assembly")["alloys"]
    p = k.panel("alloys", 1.6, Y0, 50.0, 12.5, "SOLDER ALLOYS  sol/liq °C")
    rows = [["alloy", "sol.", "liq.", "note"]] + [[n, str(s), str(l), note] for n, s, l, note in a["rows"]]
    p.table(rows, [0, -14.0, -20.0, 22.0])


def hand(k):
    t = data_table("assembly")["iron"]["rows"]
    p = k.panel("hand", 53.0, Y0, 31.0, 12.5, "HAND SOLDERING")
    p.lines([f"tip {t[0][1]} °C leaded", f"tip {t[1][1]} °C SAC", "flux first, heat pad+lead,",
             "feed solder to joint,", "2-4 s, no movement", "while it solidifies"])


def classes(k):
    p = k.panel("classes", 53.0, 25.4, 31.0, 7.4, "")
    p.lines(["IPC-A-610 product classes:", "1 general  2 dedicated", "3 high-performance"], y=p.y + 0.8)


def defects(k):
    p = k.panel("defects", 1.6, 25.4, 50.0, 8.2, "FLUX  J-STD-004 type codes")
    p.lines(["RO rosin  RE resin  OR organic  IN inorganic", "activity L/M/H; 0 / 1 = halide-free / halide",
             "e.g. ROL0: rosin, low activity, no halide"])
    q = k.panel("defect causes", 1.6, 34.9, 45.4, 14.5, "DEFECT → LIKELY CAUSE")
    q.table([["tombstone", "uneven pad heat / size"], ["bridge", "excess paste, pitch"],
             ["insufficient", "small aperture, poor wetting"], ["voids", "outgassing, big EP print"],
             ["cold joint", "low temp, movement"], ["solder balls", "paste moisture/oxide"]],
            [0, 17.0], header=False)
