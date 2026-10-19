"""Card 04 - DRILL / VIA / MECHANICAL: hole gauge, mounting holes, slots, headers, fiducials."""
from ..config import FAB, W, data_table
from ..eng import dim, mm_to_mil
from ..graphics import package_row
from ..layout import PITCH, text_width
from ..packages import info
from ..template import footer, new_card

Y0 = 11.8
GAUGE = [0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.80, 1.00, 1.20, 1.50, 2.00, 2.50, 3.00, 3.20]
NPTH_MIN = FAB["reference_fab"]["values"]["min_npth_mm"]
MOUNT = [("M2", "MountingHole:MountingHole_2.2mm_M2_Pad"), ("M2.5", "MountingHole:MountingHole_2.7mm_M2.5_Pad"),
         ("M3", "MountingHole:MountingHole_3.2mm_M3_Pad")]
HEADERS = [(2.54, "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"),
           (2.00, "Connector_PinHeader_2.00mm:PinHeader_1x04_P2.00mm_Vertical"),
           (1.27, "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical"),
           (1.00, "Connector_PinHeader_1.00mm:PinHeader_1x04_P1.00mm_Vertical")]
FIDS = ["Fiducial:Fiducial_0.75mm_Mask1.5mm", "Fiducial:Fiducial_1mm_Mask2mm", "Fiducial:Fiducial_1.5mm_Mask3mm"]
TPS = ["TestPoint:TestPoint_Pad_D1.0mm", "TestPoint:TestPoint_Pad_D1.5mm", "TestPoint:TestPoint_Pad_D2.0mm"]
mx = lambda x: W - x


def build(card):
    b, f, k = new_card(card, "hole gauge, mounting, slots, headers", "screw clearance, plating, tolerances")
    footer(k)
    gauge(f)
    mounting(f)
    pads_slots(f)
    headers(f)
    fiducials(f)
    testpads(f)
    front_notes(f)
    screw_table(k)
    hole_notes(k)
    b.meta["drills_mm"] = GAUGE
    b.meta["packages"] = [m[1] for m in MOUNT] + [h[1] for h in HEADERS] + FIDS + TPS
    return b


def gauge(f):
    pf, pk = f.through_panel("gauge", 1.6, Y0, 82.4, 8.6, "HOLE GAUGE Ø mm / mil",
                             "HOLE GAUGE Ø mm / mil")
    widths = [max(text_width(f"{d:.2f}", 1.0), d + 0.5) for d in GAUGE]
    g = (pf.w - sum(widths)) / (len(GAUGE) - 1)
    x, yt, yh, yb = pf.x, pf.cy + 0.75, pf.cy + 3.25, pf.cy + 5.75
    for d, wd in zip(GAUGE, widths):
        cx = x + wd / 2
        if d < NPTH_MIN:      # fab minimum NPTH: smaller holes are plated (via, 0.125 mm annulus)
            f.via(cx, yh, round(d + 0.25, 3), d, f.b.net(), tent=False)
        else:
            f.pad(cx, yh, d, shape="circle", kind="np_thru_hole", drill=d)
        for p, yy, t in ((pf, yt, f"{d:.2f}"), (pf, yb, f"{mm_to_mil(d):.0f}"), (pk, yt, f"{d:.2f}"),
                         (pk, yb, f"{mm_to_mil(d):.0f}")):
            p.text(t, cx if p is pf else mx(cx), yy, just="center")
        x += wd + g


def mounting(f):
    pf, pk = f.through_panel("mount", 1.6, 20.9, 26.6, 13.6, "MOUNTING", "MOUNTING")
    items = [(fp, m, [f"{dim(info(fp)['pads'][0]['drill'])}/{dim(info(fp)['pads'][0]['w'])}"]) for m, fp in MOUNT]
    placed = package_row(pf, items, pf.cy, 6.9, gap=0.6)
    for (fp, cx, yb), (m, _) in zip(placed, MOUNT):
        pk.text(m, mx(cx), pk.cy + 0.8, just="center")
    pk.text("hole/pad Ø, ISO 273 fine", pk.x, pk.y2 - 0.8)


def pads_slots(f):
    pf, pk = f.through_panel("pads", 29.2, 20.9, 20.8, 13.6, "PADS & SLOTS", "PADS & SLOTS")
    cells = [("round", "1.7/1.0", dict(w=1.7, shape="circle", kind="thru_hole", drill=1.0)),
             ("square", "1.7/1.0", dict(w=1.7, shape="rect", kind="thru_hole", drill=1.0)),
             ("slot", "0.8×1.7", dict(w=1.4, h=2.3, shape="oval", kind="thru_hole", drill=(0.8, 1.7))),
             ("NPTH", "1.0×2.5", dict(w=1.0, h=2.5, shape="oval", kind="np_thru_hole", drill=(1.0, 2.5)))]
    for i, (name, d, kw) in enumerate(cells):
        cx = pf.x + 1.3 + (i % 2) * 10.2
        cy = pf.cy + 2.6 + (i // 2) * 5.2
        w, h = kw.pop("w"), kw.pop("h", None)
        f.pad(cx, cy, w, h, net=f.b.net() if kw["kind"] == "thru_hole" else None, **kw)
        for p, x in ((pf, cx + 1.9), (pk, mx(cx) - 1.9)):
            p.text(name, x, cy - 0.8, just="left" if p is pf else "right")
            p.text(d, x, cy + 0.8, just="left" if p is pf else "right")


def headers(f):
    pf, pk = f.through_panel("headers", 1.6, 35.0, 48.4, 14.4, "HEADER PITCH (drill/pad)", "HEADER PITCH")
    items = []
    for P, fp in HEADERS:
        pd = info(fp)["pads"][0]
        items.append((fp, f"{P:.2f}", [f"{dim(pd['drill'])}/{dim(pd['w'])}"], 90))
    placed = package_row(pf, items, pf.cy, 3.6, gap=0.6)
    for (fp, cx, yb), (P, _) in zip(placed, HEADERS):
        pk.text(f"{P:.2f}", mx(cx), pk.cy + 0.8, just="center")
        pk.text(f"{mm_to_mil(P):.0f} mil", mx(cx), pk.cy + 0.8 + 1.6 + 3.6 + 0.8, just="center")
    pf.lines(["pin 1 = square pad"], y=pf.cy + 0.5)


def fiducials(f):
    p = f.panel("fiducials", 51.4, 20.9, 32.6, 9.8, "FIDUCIALS Cu/mask Ø")
    items = [(fp, None, [f"{fp.split('_')[1][:-2]}/{fp.split('Mask')[1][:-2]}"]) for fp in FIDS]
    package_row(p, [(a, "", b) for a, _, b in items], p.cy, 3.6, gap=0.6, top_label=False)


def testpads(f):
    p = f.panel("testpads", 51.4, 31.2, 32.6, 9.8, "SMD TEST PADS Ø")
    package_row(p, [(fp, "", [fp.split("_D")[1][:-2]]) for fp in TPS], p.cy, 3.0, gap=0.6, top_label=False)


def front_notes(f):
    v = FAB["reference_fab"]["values"]
    p = f.panel("notes", 51.4, 41.5, 32.6, 10.88, "HOLE NOTES")
    p.lines([f"PTH tol {v['pth_tolerance'].replace(' mm', '')}*", f"NPTH ≥ {v['min_npth_mm']:.2f}*, slot ±0.2*",
             f"gauge < {NPTH_MIN:.2f}: plated vias", "3 fiducials/side, not in line", "*JLCPCB 2026-10, confirm"])


def screw_table(k):
    iso, head, wsh = data_table("mechanical")["iso273"], data_table("mechanical")["iso4762_head"], \
        data_table("mechanical")["iso7089_washer"]
    p = k.panel("screws", 1.6, 20.9, 32.6, 13.6, "SCREW CLEARANCE ISO 273")
    rows = [["", "fine", "med", "crse", "head", "wshr"]]
    for (m, a, b_, c), (_, hd), (_, ws) in zip(iso["rows"], head["rows"], wsh["rows"]):
        rows.append([m, dim(a), dim(b_), dim(c), dim(hd), dim(ws)])
    p.table(rows, [0, -10.2, -15.6, -21.0, -26.6, -32.6])


def hole_notes(k):
    pl = data_table("mechanical")["plating"]["rows"]
    p = k.panel("drill notes", 1.6, 35.0, 32.6, 14.4, "DRILL vs FINISHED")
    p.lines(["specify FINISHED PTH Ø;", "fab drills larger to allow", "for wall plating:",
             f"≥{pl[0][1]} µm Cl.2 / ≥{pl[1][1]} µm Cl.3", "(IPC-6012 avg)", "aspect t/d 1.0/0.2 = 5:1"])
