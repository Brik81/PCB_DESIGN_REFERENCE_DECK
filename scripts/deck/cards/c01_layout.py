"""Card 01 - PCB LAYOUT MASTER: everyday layout rules with real copper samples."""
from .. import eng
from ..config import FAB, W
from ..graphics import inch_ruler, metric_ruler
from ..template import new_card

TRACE_MIL = [4, 5, 6, 8, 10, 12, 16, 20, 30, 40, 50, 100]
SPACE_MIL = [4, 5, 6, 8, 10, 12, 16, 20]
SPACE_TRACE = 0.20                       # mm, width of the tracks forming each spacing sample
VIAS = [(0.20, 0.45), (0.30, 0.60), (0.40, 0.80), (0.50, 1.00), (0.60, 1.20)]   # (finished hole, pad) mm
GCPW = dict(w=1.00, h=0.91, er=4.5)      # h = 1.0 mm card core (stack-up in pcb.py)
Y0 = 11.8


def build(card):
    b, f, k = new_card(card, "trace/space, vias, copper, rules", "conversions, rules, ruler")
    trace_widths(f)
    copper_weight(f)
    spacing(f)
    transitions(f)
    through_region(f)
    metric_ruler(f, 2.8, 80)
    mil_mm_table(k)
    rules_table(k)
    inch_ruler(k, 3.0, 3.1)
    return b


def trace_widths(f):
    p = f.panel("trace widths", 1.6, Y0, 27.4, 24.8, "TRACE WIDTH W")
    y = p.table([["mil", "mm", "1 oz, ENIG"]], [-4.2, -10.6, 12.0], header=True) + 0.15
    out = []
    for m in TRACE_MIL:
        w = eng.mil_to_mm(m)
        rh = max(1.6, w + 0.75)
        y += rh / 2
        p.text(str(m), p.x + 4.2, y, just="right")
        p.text(f"{w:.3f}", p.x + 10.6, y, just="right")
        f.gold_track(p.x + 12.0, y, p.x2 - 0.3, y, round(w, 4), net=f.b.net())
        out.append(round(w, 4))
        y += rh / 2
    f.b.meta["trace_widths_mm"] = out


def copper_weight(f):
    p = f.panel("copper weight", 1.6, 37.2, 27.4, 11.9, "COPPER (nominal)")
    rows = [["oz/ft²", "µm", "mil", "mΩ/sq"]]
    for oz, um in eng.OZ_UM.items():
        rows.append([f"{oz:g}", f"{um:g}", f"{um / 25.4:.2f}", f"{eng.sheet_resistance(um) * 1e3:.2f}"])
    p.table(rows, [0, -11.5, -18.5, -27.0])
    p.lines(["ρ_{Cu} 1.72e-8 Ωm @20°C; +0.39 %/K"])


def spacing(f):
    p = f.panel("spacing", 30.4, Y0, 26.6, 18.6, "SPACING S")
    y = p.table([["mil", "mm", f"W = {SPACE_TRACE:.2f} mm"]], [-4.2, -10.6, 12.0]) + 0.15
    x1, x2 = p.x + 12.0, p.x2 - 0.4
    out = []
    for m in SPACE_MIL:
        s = eng.mil_to_mm(m)
        rh = max(1.75, s + 2 * SPACE_TRACE + 0.95)
        y += rh / 2
        p.text(str(m), p.x + 4.2, y, just="right")
        p.text(f"{s:.3f}", p.x + 10.6, y, just="right")
        off = s / 2 + SPACE_TRACE / 2      # centre-line offset -> edge-to-edge gap = s
        net = f.b.net()
        for yy in (y - off, y + off):
            f.gold_track(x1, yy, x2, yy, SPACE_TRACE, net)
        f.gold_track(x2, y - off, x2, y + off, SPACE_TRACE, net)   # hairpin keeps both arms one net
        out.append(round(s, 4))
        y += rh / 2
    f.b.meta["spacings_mm"] = out


def transitions(f):
    p = f.panel("transitions", 30.4, 31.0, 26.6, 18.1, "TRANSITIONS")
    x0 = p.x + 0.4
    # 1. neck-down: 0.60 mm route narrows to 0.20 mm over 0.6 mm before a fine-pitch pad
    y = p.cy + 0.9
    p.text("neck-down 0.60 → 0.20", p.x, y)
    y += 1.8
    n = f.b.net()
    f.gold_track(x0, y, x0 + 12, y, 0.60, n)
    f.pad(x0 + 12, y, 0.2, 0.2, poly=[(0, -0.3), (0.6, -0.1), (0.6, 0.1), (0, 0.3)], net=n)
    f.gold_track(x0 + 12.6, y, x0 + 17.5, y, 0.20, n)
    f.pad(x0 + 18.0, y, 1.0, 0.25, net=n)                    # 0.25 mm wide pad, 0.5 mm pitch style
    # 2. step vs taper into a pad
    y += 2.3
    p.text("abrupt step", p.x, y)
    p.text("taper (teardrop)", p.x + 13.2, y)
    y += 2.0
    n = f.b.net()
    f.gold_track(x0, y, x0 + 8.5, y, 0.25, n)
    f.pad(x0 + 8.5, y, 1.6, 1.6, shape="circle", net=n)
    n = f.b.net()
    f.gold_track(x0 + 13.0, y, x0 + 19.0, y, 0.25, n)
    f.pad(x0 + 19.0, y, 0.25, 0.25, poly=[(0, -0.125), (2.4, -0.75), (2.4, 0.75), (0, 0.125)], net=n)
    f.pad(x0 + 22.0, y, 1.6, 1.6, shape="circle", net=n)
    # 3. bends: 45 deg chamfer and arc; never 90 deg or acute
    y += 2.4
    p.text("45° chamfer", p.x, y)
    p.text("arc", p.x + 13.2, y)
    y += 1.2
    n = f.b.net()
    f.gold_track(x0, y, x0 + 6, y, 0.3, n)
    f.gold_track(x0 + 6, y, x0 + 8.5, y + 2.5, 0.3, n)
    n = f.b.net()
    f.gold_track(x0 + 13.0, y, x0 + 18.0, y, 0.3, n)
    f.arc_track((x0 + 18.0, y), (x0 + 18.0 + 2.5 * 0.7071, y + 2.5 * 0.2929), (x0 + 20.5, y + 2.5), 0.3, n)
    f.arc((x0 + 18.0, y), (x0 + 18.0 + 2.5 * 0.7071, y + 2.5 * 0.2929), (x0 + 20.5, y + 2.5), "Mask", 0.3)
    p.cy = y + 2.8
    p.lines(["W and S are independent rules"], st="body")


def through_region(f):
    """Vias, thermal relief and a via-fenced GCPW. Plated, so visible on both faces."""
    mx = lambda x: W - x
    x, w = 58.0, 26.0
    # --- vias -------------------------------------------------------------
    pf, pk = f.through_panel("vias", x, Y0, w, 8.4, "VIA d / D (mm)", "VIAS, BOTTOM")
    xs = [x + 3.8 + 4.6 * i for i in range(len(VIAS))]
    yd, yv, yD = pf.cy + 0.8, pf.cy + 2.4, pf.cy + 4.0
    pf.text("d", x, yd)
    pf.text("D", x, yD)
    for xi, (d, D) in zip(xs, VIAS):
        pf.text(f"{d:.2f}", xi, yd, just="center")
        pf.text(f"{D:.2f}", xi, yD, just="center")
        f.via(xi, yv, D, d, net=f.b.net(), tent=False)
        pk.text(f"{(D - d) / 2:.3g}", mx(xi), yD, just="center")
    pk.text("annular ring AR = (D − d)/2", pk.x, yd)
    f.b.meta["vias_mm"] = VIAS
    # --- thermal relief vs solid --------------------------------------------
    pf, pk = f.through_panel("thermal", x, 20.8, w, 9.2, "THERMAL vs SOLID", "PLANE TIE, BOTTOM")
    zy1, zy2 = pf.cy + 0.3, pf.cy + 5.6
    net = f.b.net("PLANE_A")
    pts = [(x + 0.5, zy1), (x + w - 0.5, zy1), (x + w - 0.5, zy2), (x + 0.5, zy2)]
    for v in (f, f.other()):
        vp = pts if v is f else [(mx(a), b_) for a, b_ in pts]
        v.zone(vp, net, clearance=0.3, thermal_gap=0.35, spoke=0.3)
        v.rect(vp[0][0], zy1, vp[2][0], zy2, "Mask", 0, True)
    ym = (zy1 + zy2) / 2
    f.pad(x + 6.5, ym, 1.8, kind="thru_hole", shape="circle", drill=1.0, net=net, zone_connect=1)
    f.pad(x + w - 6.5, ym, 1.8, kind="thru_hole", shape="circle", drill=1.0, net=net, zone_connect=2)
    pf.text("4 spokes 0.30", x + 6.5, zy2 + 1.0, just="center")
    pf.text("solid", x + w - 6.5, zy2 + 1.0, just="center")
    pk.text("thermal", mx(x + 6.5), zy2 + 1.0, just="center")
    pk.text("solid", mx(x + w - 6.5), zy2 + 1.0, just="center")
    # --- GCPW with via fence --------------------------------------------------
    s = eng.cpwg_gap(50, GCPW["w"], GCPW["h"], GCPW["er"])
    s = round(s, 2)
    z0, ee = eng.cpwg(GCPW["w"], s, GCPW["h"], GCPW["er"])
    pf, pk = f.through_panel("gcpw", x, 30.6, w, 18.6, "VIA FENCE / GCPW", "PLANE + STITCHING")
    yc = pf.cy + 5.0
    gnd, sig = f.b.net("GND_FENCE"), f.b.net("RF_DEMO")
    x1, x2 = x + 0.5, x + w - 0.5
    f.gold_track(x1, yc, x2, yc, GCPW["w"], sig)
    hw = GCPW["w"] / 2 + s
    top = [(x1, yc - hw - 3.6), (x2, yc - hw - 3.6), (x2, yc - hw), (x1, yc - hw)]
    bot = [(x1, yc + hw), (x2, yc + hw), (x2, yc + hw + 3.6), (x1, yc + hw + 3.6)]
    for z in (top, bot):
        f.zone(z, gnd, clearance=s, connect="solid")
        f.rect(z[0][0], z[0][1], z[2][0], z[2][1], "Mask", 0, True)
    o = f.other()
    plane = [(mx(x1), yc - hw - 3.6), (mx(x2), yc - hw - 3.6), (mx(x2), yc + hw + 3.6), (mx(x1), yc + hw + 3.6)]
    o.zone(plane, gnd, clearance=0.3, connect="solid")
    o.rect(plane[0][0], plane[0][1], plane[2][0], plane[2][1], "Mask", 0, True)
    for i in range(16):
        vx = x1 + 0.8 + i * 1.5
        for vy in (yc - hw - 0.75, yc + hw + 0.75, yc - hw - 2.6, yc + hw + 2.6):
            if vy in (yc - hw - 2.6, yc + hw + 2.6) and i % 2:
                continue        # outer row = sparser stitching
            f.via(vx, vy, 0.6, 0.3, gnd, tent=False)
    lines = [f"W {GCPW['w']:.2f}  G {s:.2f}  h {GCPW['h']:.2f}  εr {GCPW['er']}",
             f"Z_{{0}} ≈ {z0:.0f} Ω  ε_{{eff}} {ee:.2f} (CPWG)",
             f"pitch 1.5 ≤ λ/20 to {eng.C0 / (1.5e-3 * 20 * ee ** 0.5) / 1e9:.1f} GHz",
             "illustrative: verify w/ solver"]
    pf.cy = yc + hw + 3.6 + 0.2
    pf.lines(lines)
    pk.cy = yc + hw + 3.6 + 0.2
    pk.lines(["solid plane = return path", "under the signal; stitch", "pours at ≤ λ/20 pitch"])
    f.b.meta["gcpw"] = {"w": GCPW["w"], "gap": s, "z0": round(z0, 1)}


def mil_mm_table(k):
    p = k.panel("conversions", 29.0, Y0, 24.2, 37.4, "MIL ↔ MM")
    mils = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100]
    mms = ["0.05", "0.10", "0.127", "0.15", "0.20", "0.25", "0.30", "0.40", "0.50", "0.80", "1.00", "1.60", "2.54", "25.4"]
    rows = [["mil", "mm", "mm", "mil"]]
    rows += [[str(a), f"{eng.mil_to_mm(a):.3f}", c, f"{eng.mm_to_mil(float(c)):.1f}"] for a, c in zip(mils, mms)]
    p.table(rows, [-3.6, -10.4, -16.8, -24.0])
    p.lines(["1 mil = 0.0254 mm exact", "1 mm = 39.37 mil", "1 in = 25.4 mm", "1 oz Cu ≈ 35 µm ≈ 1.4 mil"])


def rules_table(k):
    v = FAB["reference_fab"]["values"]
    p = k.panel("rules", 54.6, Y0, 29.4, 18.4, "FAB RULES (mm)")
    rows = [["item", "fab min*", "typ."],
            ["track/space", "0.10", "0.15"],
            ["via d/D", f"{v['min_via_hole_mm']:.2f}/{v['min_via_diameter_mm']:.2f}", "0.3/0.6"],
            ["PTH ring", "0.18", "0.25"],
            ["Cu to edge", f"{v['copper_to_routed_edge_mm']:.2f}", "0.50"],
            ["silk line/h", "0.15/1.0", "≥ min"],
            ["silk to pad", "0.15", "0.20"],
            ["mask dam blk", "0.13", "0.15"],
            ["NPTH min", f"{v['min_npth_mm']:.2f}", "-"]]
    p.table(rows, [0, -21.0, -29.4])
    p.lines(["*JLCPCB 2L 1oz, 2026-10"])
    p = k.panel("practice", 54.6, 30.8, 29.4, 18.4, "LAYOUT PRACTICE")
    p.lines(["W sets R & Z; S sets coupling", "and voltage; both are rules",
             "keep solid ref. plane under", "fast signals - no splits",
             "courtyard excess (IPC-7351B)", "  0.10 / 0.25 / 0.50 L/N/M",
             "45° or arcs; no acute angles", "neck down only at pad entry",
             "ampacity ≠ width alone: card 07"])
