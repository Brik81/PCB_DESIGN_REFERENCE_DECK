"""Card 08 - IMPEDANCE / HIGH SPEED: computed controlled-impedance coupons, length matching, rules."""
from ..config import W, data_table, eq
from ..eng import diff_microstrip, diff_microstrip_width, dim, microstrip, microstrip_width, prop_delay_ps_per_mm
from ..template import footer, new_card

H_DIEL, ER, T_CU = 0.91, 4.5, 0.035          # this card's stack-up: core 0.91 mm, FR-4 eps_r 4.5 ASSUMED
GAP = 0.20
X1, X2 = 22.6, 62.6                          # coupon track span (front view)
SERP = dict(w=0.2, amp=1.0, pitch=2.0, n=4)


def _coupons():
    w50 = round(microstrip_width(50, H_DIEL, ER, T_CU), 2)
    rows = [("50 Ω single", w50, None, microstrip(w50, H_DIEL, ER, T_CU)[0])]
    for zd in (90, 100):
        w = round(diff_microstrip_width(zd, GAP, H_DIEL, ER, T_CU), 2)
        rows.append((f"{zd} Ω diff", w, GAP, diff_microstrip(w, GAP, H_DIEL, ER, T_CU)))
    return rows


def build(card):
    b, f, k = new_card(card, "impedance coupons, length match", "interfaces, rise time, reflections")
    footer(k)
    coupons(f)
    length_match(f)
    rules(f)
    interfaces(k)
    formulas(k)
    b.meta["impedance_coupons"] = [dict(name=n, w=w, s=s, z=round(z, 1)) for n, w, s, z in _coupons()]
    b.meta["stackup_assumed"] = dict(h=H_DIEL, er=ER, t=T_CU)
    return b


def coupons(f):
    pf, pk = f.through_panel("coupons", 1.6, 11.8, 82.4, 19.6, f"CONTROLLED IMPEDANCE  h {H_DIEL}, ε_{{r}} {ER} assumed",
                             "REFERENCE PLANE")
    o = f.other()
    y = pf.cy + 3.0
    for name, w, s, z in _coupons():
        pf.text(name, pf.x, y)
        geo = f"w {dim(w)}" + (f" s {dim(s)}" if s else "")
        pf.text(geo, pf.x2, y - 0.8, just="right")
        pf.text(f"≈{z:.0f} Ω", pf.x2, y + 0.8, just="right")
        offs = [0] if s is None else [-(w + s) / 2, (w + s) / 2]
        for dy in offs:
            n = f.b.net()
            f.gold_track(X1, y + dy, X2, y + dy, w, n)
        y += 5.0
    gnd = f.b.net("GND_REF")                                  # bottom reference plane, exposed (gold)
    zx1, zx2, zy1, zy2 = W - X2 - 2.4, W - X1 + 2.4, pk.cy + 0.4, pk.y2 - 0.4
    poly = [(zx1, zy1), (zx2, zy1), (zx2, zy2), (zx1, zy2)]
    o.zone(poly, gnd, connect="solid", min_thick=0.25)
    o.rect(zx1, zy1, zx2, zy2, "Mask", 0, True)
    y0 = pk.cy + 0.8
    pk.lines(["solid GND", "under the", "coupons:", "the return", "current path"], x=pk.x, y=y0)
    pk.lines(["Z: H-J +", "IPC-2141", "≈ ±10 %;", "mask lowers", "Z a few %"], x=zx2 + 0.8, y=y0)


def length_match(f):
    _, ee = microstrip(SERP["w"], H_DIEL, ER, T_CU)
    tpd = prop_delay_ps_per_mm(ee)
    p = f.panel("length", 1.6, 33.0, 40.0, 19.38, "LENGTH MATCHING")
    w, a, pi, n = SERP["w"], SERP["amp"], SERP["pitch"], SERP["n"]
    xa, xb = p.x + 1.0, p.x2 - 1.0
    y1, y2 = p.cy + 2.0, p.cy + 6.4
    n1, n2 = f.b.net(), f.b.net()
    f.gold_track(xa, y1, xb, y1, w, n1)
    pts = [(xa, y2)]
    x = (xa + xb) / 2 - n * pi / 2
    pts.append((x, y2))
    for _ in range(n):
        pts += [(x, y2 - a), (x + pi / 2, y2 - a), (x + pi / 2, y2), (x + pi, y2)]
        x += pi
    pts.append((xb, y2))
    for p1, p2 in zip(pts, pts[1:]):
        f.gold_track(*p1, *p2, w, n2)
    dl = 2 * a * n
    p.lines([f"ΔL = {dim(dl)} mm → {dl * tpd:.0f} ps", f"({tpd:.2f} ps/mm, ε_{{eff}} {ee:.2f})",
             "gap ≥ 3-4 w, few long bumps;", "match at the mismatch source"], y=y2 + 1.4)
    f.b.meta["serpentine"] = dict(SERP, extra_mm=dl, ps=round(dl * tpd, 1))


def rules(f):
    p = f.panel("rules", 43.4, 33.0, 40.6, 19.38, "SIGNAL INTEGRITY")
    p.lines(["no plane splits under fast nets", "GND via next to every signal", "  via changing reference",
             "pairs: match within the pair", "  first, keep coupling constant",
             "AC caps: same land both legs", "3W to aggressors (rule)", "series R at the driver: Z_{0}"])


def interfaces(k):
    t = data_table("interfaces")["diff_impedance"]
    p = k.panel("interfaces", 1.6, 33.0, 46.0, 16.4, "DIFF. IMPEDANCE")
    p.table([["interface", "Ω", "note"]] + [[a, str(z), n] for a, z, n in t["rows"]], [0, -24.0, 26.0])


def formulas(k):
    p = k.panel("formulas", 49.4, 33.0, 34.6, 16.4, "EDGES & REFLECTIONS")
    p.lines([eq("knee"), eq("tpd"), eq("gamma"), eq("return_loss"), eq("vswr"),
             "long line: delay > t_{r}/6 (rule)", f"stripline ε_{{r}} {ER}: {prop_delay_ps_per_mm(ER):.2f} ps/mm"], pitch=1.7)
