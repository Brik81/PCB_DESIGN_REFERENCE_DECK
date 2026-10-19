"""Card 09 - RF / ANTENNAS: U.FL + pi-match + via-fenced 50 ohm CPWG, wavelength gauges, tables."""
import math

from ..config import W, eq
from ..eng import (C0, cpwg, cpwg_gap, dim, dipole_len_m, microstrip, microstrip_width, monopole_len_m,
                   return_loss_db, wavelength_m)
from ..template import footer, new_card

H_DIEL, ER, T_CU = 0.91, 4.5, 0.035              # stack-up, FR-4 eps_r ASSUMED
CPW_W = 1.0
UFL = "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical"
C0402, L0402 = "Capacitor_SMD:C_0402_1005Metric", "Inductor_SMD:L_0402_1005Metric"
FREQS = [(433.92e6, "433 MHz"), (868e6, "868 MHz"), (915e6, "915 MHz"), (1575.42e6, "1.575 GHz"),
         (2.45e9, "2.45 GHz"), (5.0e9, "5.0 GHz"), (5.8e9, "5.8 GHz")]
GAUGES = [2.45e9, 5.8e9]
VSWRS = [1.1, 1.2, 1.5, 2.0, 3.0]
FENCE = 1.5
ZX2 = 50.0                                       # right end of the RF pour (front view)


def _ms_eeff():
    w50 = microstrip_width(50, H_DIEL, ER, T_CU)
    return w50, microstrip(w50, H_DIEL, ER, T_CU)[1]


def build(card):
    b, f, k = new_card(card, "U.FL feed, π match, λ gauges", "wavelengths, VSWR, RF formulas")
    footer(k)
    rf_feed(f)
    gauges(f)
    keepout(f)
    wl_table(k)
    vswr_table(k)
    return b


def rf_feed(f):
    s = round(cpwg_gap(50, CPW_W, H_DIEL, ER), 2)
    z0, ee = cpwg(CPW_W, s, H_DIEL, ER)
    pf, pk = f.through_panel("rf feed", 1.6, 11.8, 82.4, 16.6, "RF FEED  U.FL → π → 50 Ω CPWG", "RF FORMULAS")
    o = f.other()
    yc = pf.cy + 5.4
    x1, x2 = pf.x + 0.4, ZX2
    gnd, ra, rb = "GND_RF", f.b.net("RF_A"), f.b.net("RF_B")
    f.b.net(gnd)
    xu = x1 + 3.0                                            # U.FL centre; rotated: signal pin faces right
    f.lib_fp(UFL, xu, yc, 180, nets={"1": ra, "2": gnd})
    xl = xu + 13.0
    xa, xb = xl - 4.0, xl + 4.0
    f.lib_fp(L0402, xl, yc, 0, nets={"1": ra, "2": rb})
    f.lib_fp(C0402, xa, yc - 0.48, 90, nets={"1": ra, "2": gnd})
    f.lib_fp(C0402, xb, yc - 0.48, 90, nets={"1": rb, "2": gnd})
    f.track(xu + 1.75, yc, xl - 0.8, yc, CPW_W, ra)            # RF line under mask; clear of U.FL mask window;
    f.track(xl + 0.8, yc, x2 - 1.5, yc, CPW_W, rb)             # short of L1: 1.0 mm line > 0402 pad gap
    hw = 3.6
    zone = [(x1, yc - hw), (x2, yc - hw), (x2, yc + hw), (x1, yc + hw)]
    f.zone(zone, gnd, clearance=s, connect="solid", min_thick=0.2)
    for ya, yb in ((yc - hw, yc - CPW_W / 2 - s), (yc + CPW_W / 2 + s, yc + hw)):   # expose GND, not the gap
        f.rect(xu + 2.4, ya, x2, yb, "Mask", 0, True)            # U.FL area stays masked: own mask window
    plane = [(W - x2, yc - hw), (W - x1, yc - hw), (W - x1, yc + hw), (W - x2, yc + hw)]
    o.zone(plane, gnd, clearance=0.3, connect="solid")
    o.rect(W - x2, yc - hw, W - x1, yc + hw, "Mask", 0, True)
    n = 0
    x = xu + 3.0
    while x < x2 - 0.6:
        for dy in (1.45, 2.95):
            for sgn in (-1, 1):
                if dy > 2 and round((x - xu) / FENCE) % 2:
                    continue
                if sgn < 0 and dy < 2 and min(abs(x - xa), abs(x - xb)) < 1.0:
                    continue                                   # leave room for the shunt GND pad
                f.via(x, yc + sgn * dy, 0.6, 0.3, gnd, tent=False)
                n += 1
        x += FENCE
    yl = yc + hw + 1.0
    for t, xx in (("U.FL", xu), ("C1", xa), ("L1", xl), ("C2", xb), ("→ radio", x2 - 4.0)):
        pf.text(t, xx, yl, just="center")
    pf.lines([f"w {dim(CPW_W)} g {dim(s)} h {H_DIEL}", f"ε_{{r}} {ER} assumed", f"Z_{{0}} ≈ {z0:.0f} Ω (CPWG)",
              "π: C1-L1-C2 0402,", "values from VNA;", "0 Ω for L1 = thru"], x=x2 + 2.0, y=pf.cy + 0.8)
    lg20 = C0 / (2.45e9 * math.sqrt(ee)) / 20 * 1e3
    pk.lines(["half-wave dipole, total:", "  " + eq("dipole"), "λ/4 monopole:", "  " + eq("monopole"),
              "L-match: " + eq("lmatch_q"), "Wilkinson: " + eq("wilkinson").split(",")[0] + ",",
              "  " + eq("wilkinson").split(",")[1].strip(), f"fence {dim(FENCE)} ≤ λ_{{g}}/20 = {lg20:.1f} (rule)"],
             x=pk.x, y=pk.cy + 0.8, pitch=1.75)
    f.b.meta["rf_feed"] = dict(w=CPW_W, gap=s, z0=round(z0, 1), eeff=round(ee, 3), fence_vias=n)


def gauges(f):
    w50, ee = _ms_eeff()
    p = f.panel("gauges", 1.6, 30.0, 52.0, 22.38, "λ/4 LENGTH GAUGES (not antennas)")
    y = p.cy + 2.0
    rows = []
    for fr in GAUGES:
        l0 = wavelength_m(fr) / 4 * 1e3
        lg = wavelength_m(fr, ee) / 4 * 1e3
        for lab, L in ((f"{fr / 1e9:g} GHz λ_{{0}}/4", l0), (f"{fr / 1e9:g} GHz λ_{{g}}/4", lg)):
            x0 = p.x + 17.0
            f.gold_track(x0, y, x0 + L, y, 0.3, f.b.net())
            f.gold_track(x0, y - 0.6, x0, y + 0.6, 0.15)
            f.gold_track(x0 + L, y - 0.6, x0 + L, y + 0.6, 0.15)
            p.text(lab, p.x, y)
            p.text(f"{L:.1f}", x0 + L + 0.8, y)
            rows.append((lab, round(L, 2)))
            y += 2.4
    p.lines([f"λ_{{g}} on 50 Ω microstrip w {w50:.2f}:", f"ε_{{eff}} {ee:.2f} (H-J, ε_{{r}} {ER} assumed)",
             "real antennas: vendor layout + tune"], y=y + 0.2)
    f.b.meta["gauges_mm"] = rows


def keepout(f):
    p = f.panel("keepout", 55.4, 30.0, 28.6, 22.38, "CHIP ANTENNA")
    x0, y0 = p.x + 1.0, p.cy + 1.2                  # board corner drawn top-left
    bw, bh, kw = 26.0, 9.0, 11.0
    f.line(x0, y0, x0 + bw, y0)                      # board edge
    f.line(x0, y0, x0, y0 + bh)
    f.line(x0 + kw, y0, x0 + kw, y0 + bh)            # keep-out boundary
    f.line(x0, y0 + bh, x0 + kw, y0 + bh)
    for i in range(1, 9):                            # hatch
        a = i * 2.2
        f.line(x0 + max(0, a - bh), y0 + min(a, bh), x0 + min(a, kw), y0 + max(0, a - kw), w=0.1)
    f.rect(x0 + 2.0, y0 + 1.0, x0 + 8.0, y0 + 3.0, fill=False)
    p.text("GND pour", x0 + kw + 1.0, y0 + 4.5)
    p.lines(["hatched: no Cu on any", "layer; antenna at edge;", "copy vendor ref. design"], y=y0 + bh + 1.0)


def wl_table(k):
    _, ee = _ms_eeff()
    p = k.panel("wavelengths", 1.6, 30.0, 52.0, 19.4, "WAVELENGTH (mm)")
    rows = [["f", "λ0", "λ0/4", "dipole", "λg/4"]]      # no sub-scripts here: they hit the header rule
    for fr, lab in FREQS:
        mhz = fr / 1e6
        rows.append([lab, f"{wavelength_m(fr) * 1e3:.0f}", f"{wavelength_m(fr) * 250:.1f}",
                     f"{dipole_len_m(mhz) * 1e3:.0f}", f"{wavelength_m(fr, ee) * 250:.1f}"])
    p.table(rows, [0, -21.0, -30.0, -41.0, -52.0])
    k.b.meta["wavelength_table"] = rows
    k.b.meta["monopole_check_mm"] = round(monopole_len_m(2450) * 1e3, 2)


def vswr_table(k):
    p = k.panel("vswr", 55.4, 30.0, 28.6, 19.4, "VSWR")
    rows = [["VSWR", "|Γ|", "RL dB", "ML dB"]]
    for v in VSWRS:
        g = (v - 1) / (v + 1)
        rows.append([dim(v), f"{g:.3f}", f"{return_loss_db(g):.1f}", f"{-10 * math.log10(1 - g * g):.2f}"])
    p.table(rows, [0, -14.0, -21.0, -28.6])
    p.lines(["ML: mismatch loss"], y=p.cy + 1.0)
