"""Card 14 - PCB MANUFACTURING: this card's stack-up, annular-ring coupon, finishes, outputs, order."""
from ..config import FAB, MECH, RULES, W, data_table
from ..eng import dim
from ..pcb import CU_MM, MASK_MM
from ..template import footer, new_card

THK = MECH["card"]["thickness"]
CORE = round(THK - 2 * CU_MM - 2 * MASK_MM, 4)
RINGS = [0.125, 0.15, 0.20, 0.25]               # annular ring samples, via drill 0.30
DRILL = 0.30
GERBERS = [("F_Cu", "gtl", "top copper"), ("B_Cu", "gbl", "bottom copper"), ("F_Mask", "gts", "top mask"),
           ("B_Mask", "gbs", "bottom mask"), ("F_Silkscreen", "gto", "top silk"),
           ("B_Silkscreen", "gbo", "bottom silk"), ("Edge_Cuts", "gm1", "outline"), ("PTH / NPTH", "drl", "drills")]


def build(card):
    b, f, k = new_card(card, "stack-up, annular ring, finishes", "Gerbers, order settings, DFM")
    footer(k)
    stackup(f)
    rings(f)
    finishes(f)
    order(k)
    gerbers(k)
    dfm(k)
    b.meta["stackup_mm"] = dict(cu=CU_MM, mask=MASK_MM, core=CORE, total=THK)
    b.meta["annular_rings_mm"] = RINGS
    return b


def stackup(f):
    p = f.panel("stackup", 1.6, 11.8, 52.0, 24.0, f"THIS CARD: 2 LAYERS, {THK} mm")
    layers = [("silkscreen", "ink", 1.3, "silk"), ("solder mask", f"{MASK_MM * 1000:.0f} µm", 1.3, "mask"),
              ("F.Cu 1 oz", f"{CU_MM * 1000:.0f} µm", 1.6, "cu"), ("FR-4 core", f"{CORE} mm", 5.0, "core"),
              ("B.Cu 1 oz", f"{CU_MM * 1000:.0f} µm", 1.6, "cu"), ("solder mask", f"{MASK_MM * 1000:.0f} µm", 1.3, "mask"),
              ("silkscreen", "ink", 1.3, "silk")]
    x1, x2 = p.x + 0.4, p.x + 20.0
    y = p.cy + 1.0
    for name, t, h, kind in layers:                     # drawn height NOT to scale (labelled)
        if kind == "cu":
            f.gold_rect(x1, y, x2, y + h)
        elif kind == "core":
            f.rect(x1, y, x2, y + h)
            for i in range(1, 9):
                f.line(x1 + i * 2.2 - 1.6, y + h - 0.3, x1 + i * 2.2, y + 0.3, w=0.1)
        elif kind == "mask":
            f.rect(x1, y, x2, y + h)
        else:
            f.rect(x1 + 3.0, y, x1 + 8.0, y + h, fill=True)
            f.rect(x1 + 12.0, y, x1 + 15.0, y + h, fill=True)
        p.text(name, x2 + 1.2, y + h / 2)
        p.text(t, p.x2, y + h / 2, just="right")
        y += h + 0.3
    p.text("(heights not to scale)", p.x, p.y2 - 0.8)


def rings(f):
    pf, pk = f.through_panel("rings", 55.4, 11.8, 28.6, 24.0, "ANNULAR RING", "ANNULAR RING")
    for i, ar in enumerate(RINGS):
        y = pf.cy + 2.0 + i * 4.0
        d = round(DRILL + 2 * ar, 3)
        f.via(pf.x + 3.0, y, d, DRILL, f.b.net(), tent=False)
        pf.text(f"{dim(ar)}  Ø{dim(d)}/{dim(DRILL)}", pf.x + 6.0, y)
        pk.text(f"AR {dim(ar)}", W - (pf.x + 6.0), y, just="right")
    v = FAB["reference_fab"]["values"]
    pf.text(f"rule here ≥ {RULES['min_annular_ring']}", pf.x, pf.y2 - 2.4)
    pf.text("AR = (pad − drill)/2", pf.x, pf.y2 - 0.8)
    pk.lines(["PTH AR:", *[t.replace("recommended", "rec.").replace("absolute", "abs.")
                          for t in v["annular_ring_2layer_mm"].split(", ")], "(JLCPCB, confirm)"],
             x=pk.x, y=pk.cy + 0.8)


def finishes(f):
    t = data_table("manufacturing")["finishes"]["rows"]
    p = f.panel("finishes", 1.6, 37.4, 82.4, 14.98, "SURFACE FINISH (this deck: ENIG)")
    p.table([["finish", "flat", "note"]] + t, [0, 20.0, 28.0], pitch=1.6)


def order(k):
    o = FAB["order"]
    p = k.panel("order", 31.6, 11.8, 52.4, 24.0, "ORDER SETTINGS (each card)")
    p.table([["layers", str(o["layers"])], ["thickness", f"{o['thickness_mm']} mm"], ["copper", f"{o['copper_oz']} oz"],
             ["mask / silk", f"{o['mask']} / White"], ["finish", o["finish"]],
             ["size", f"{MECH['card']['width']} × {MECH['card']['height']} mm"], ["order no.", "no / hidden"],
             ["outline tol.", "±0.2 mm typ."]], [0, 17.0], header=False, y=p.cy + 1.0)


def gerbers(k):
    p = k.panel("gerbers", 1.6, 37.4, 46.0, 12.0, "OUTPUT FILES <card>-<layer>.<ext>")
    half = (len(GERBERS) + 1) // 2
    y0 = p.cy + 0.8
    for c, rows in enumerate((GERBERS[:half], GERBERS[half:])):
        p.table([[e, d] for _, e, d in rows], [0, 4.0], x=p.x + c * 23.0, y=y0, header=False)


def dfm(k):
    p = k.panel("dfm", 49.6, 37.4, 34.4, 12.0, "BEFORE ORDERING")
    p.lines(["DRC with fab rules", "view Gerbers in a viewer", "check drill map + outline", "silk off pads; text ≥ 1 mm"])
