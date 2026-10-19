"""Card 07 - POWER / THERMAL: power traces with IPC-2221 estimates, thermal via array, buck layout."""
from ..config import MECH, W, eq
from ..eng import OZ_UM, dim, ipc2221_current, mm_to_mil, trace_resistance, via_resistance, via_thermal_res
from ..graphics import Sch
from ..template import footer, new_card

Y0 = 11.8
WIDTHS = [0.5, 1.0, 2.0, 3.0]
T_MIL = mm_to_mil(OZ_UM[1] / 1000)            # 1 oz outer copper, nominal (plating adds thickness)
VIA = dict(drill=0.30, dia=0.60, pitch=1.2, n=3, plating_um=25.0)
BOARD = MECH["card"]["thickness"]


def build(card):
    b, f, k = new_card(card, "trace current, thermal vias, buck", "converter formulas, losses, Tj")
    footer(k)
    traces(f)
    thermal_vias(f)
    buck(f)
    fet_checks(f)
    formulas(k)
    thermal_notes(k)
    b.meta["power_traces_mm"] = WIDTHS
    b.meta["thermal_vias"] = VIA
    return b


def traces(f):
    p = f.panel("traces", 1.6, Y0, 52.0, 19.6, "POWER TRACES 1 oz, ext.")
    p.text("w mm", p.x, p.cy + 0.8)
    p.text("I @ ΔT 10 / 20 °C", p.x2, p.cy + 0.8, just="right")
    y = p.cy + 3.0
    for w in WIDTHS:
        i10, i20 = (ipc2221_current(mm_to_mil(w), T_MIL, dT) for dT in (10, 20))
        f.gold_track(p.x + 6.0, y, p.x + 30.0, y, w, f.b.net())
        p.text(dim(w), p.x, y)
        p.text(f"{i10:.1f} / {i20:.1f} A", p.x2, y, just="right")
        y += max(w, 1.0) + 1.9
    p.text("IPC-2221 fit: estimate only", p.x, p.y2 - 0.8)
    f.b.meta["power_trace_currents"] = {w: [round(ipc2221_current(mm_to_mil(w), T_MIL, d), 2) for d in (10, 20)]
                                        for w in WIDTHS}


def thermal_vias(f):
    pf, pk = f.through_panel("thermal vias", 55.4, Y0, 28.6, 19.6, "THERMAL VIAS", "THERMAL VIAS (bottom)")
    o = f.other()
    n = f.b.net()
    P, m = VIA["pitch"], VIA["n"]
    cx, cy = pf.x + 6.0, pf.cy + 7.6
    f.pad(cx, cy, P * m + 0.6, net=n)                       # top: exposed thermal pad
    o.pad(W - cx, cy, P * m + 2.4, net=n)                   # bottom: larger exposed spreading pad
    for i in range(m):
        for j in range(m):
            f.via(cx + (i - 1) * P, cy + (j - 1) * P, VIA["dia"], VIA["drill"], n, tent=False)
    rv = via_thermal_res(VIA["drill"], BOARD, VIA["plating_um"])
    pf.lines([f"{m}×{m} vias {dim(VIA['drill'])}/{dim(VIA['dia'])}", f"pitch {dim(P)}",
              f"1 via ≈ {rv:.0f} K/W", f"{m * m} vias ≈ {rv / m / m:.0f} K/W"], x=pf.x + 12.6, y=pf.cy + 2.6)
    pf.text("barrel only, 25 µm, unfilled", pf.x, pf.y2 - 0.8)
    pk.lines(["bottom copper", "spreads heat;", "more area,", "lower θ"], x=pk.x, y=pk.cy + 2.6)


def buck(f):
    p = f.panel("buck", 1.6, 32.6, 52.0, 19.78, "SYNC BUCK: HOT LOOP")
    s = Sch(f)
    x0, yt = p.x, p.cy + 3.4
    s.rail(x0 + 2.0, yt, "")
    p.text("V_{in}", x0 + 2.8, yt - 1.2)
    s.wire((x0 + 2.0, yt), (x0 + 11.7, yt))
    s.dot(x0 + 4.0, yt)
    s.cap(x0 + 4.0, yt, x0 + 4.0, yt + 8.8)
    s.gnd(x0 + 4.0, yt + 8.8)
    hs = s.mosfet(x0 + 10.0, yt + 3.0)
    ls = s.mosfet(x0 + 10.0, yt + 7.6)
    xs = hs["d"][0]
    s.wire((xs, yt), hs["d"])
    s.wire(hs["s"], ls["d"])
    s.gnd(xs, ls["s"][1])
    ysw = (hs["s"][1] + ls["d"][1]) / 2
    s.dot(xs, ysw)
    s.ind(xs, ysw, x0 + 22.0, ysw)
    s.wire((x0 + 22.0, ysw), (x0 + 26.0, ysw))
    s.dot(x0 + 24.0, ysw)
    s.cap(x0 + 24.0, ysw, x0 + 24.0, ls["s"][1])
    s.gnd(x0 + 24.0, ls["s"][1])
    p.text("C_{in}", x0 + 5.4, yt + 6.6)
    p.text("V_{out}", x0 + 26.2, ysw - 1.2, just="right")
    p.text("SW", (xs + x0 + 22.0) / 2, ysw + 1.4, just="center")
    p.lines(["hot loop C_{in}-HS-LS:", "smallest area, same", "layer, solid GND below", "SW node: small Cu",
             "FB trace away from L"], x=x0 + 29.0, y=p.cy + 0.8)
    p.text("dI/dt loop sets EMI, ringing", x0, p.y2 - 0.8)


def fet_checks(f):
    p = f.panel("fet", 55.4, 32.6, 28.6, 19.78, "MOSFET CHECKS")
    p.lines(["V_{DS} margin over V_{in,max}", "R_{DS(on)} at your V_{GS}", "  and hot T_{j} (×1.5-2)",
             "Q_{g} → driver current", "SOA for linear use", "body diode / dead time", "θ_{JA} is board-specific"])


def formulas(k):
    p = k.panel("formulas", 31.6, Y0, 52.4, 21.0, "FORMULAS (ideal, CCM)")
    rows = [("buck D", "buck_d"), ("buck ripple", "buck_ripple"), ("boost D", "boost_d"),
            ("inv. buck-boost", "buckboost_d"), ("LDO dissipation", "ldo_pd"), ("conduction", "mos_cond"),
            ("switching", "mos_sw"), ("junction temp", "tj"), ("efficiency", "efficiency"),
            ("trace R", "cu_r")]
    p.table([[a, eq(b)] for a, b in rows], [0, 15.4], header=False, pitch=1.8)


def thermal_notes(k):
    p = k.panel("thermal", 1.6, 33.4, 82.4, 16.0, "NUMBERS FOR THIS 1.0 mm BOARD")
    rv = via_resistance(VIA["drill"], BOARD, VIA["plating_um"])
    r10 = trace_resistance(10.0, 1.0, OZ_UM[1])
    p.lines([f"via {dim(VIA['drill'])} mm, 25 µm: {rv * 1e3:.2f} mΩ, {via_thermal_res(VIA['drill'], BOARD):.0f} K/W",
             f"1 mm × 10 mm, 1 oz: {r10 * 1e3:.1f} mΩ at 20 °C",
             "Cu +0.39 %/K; 1 oz = 35 µm nominal",
             "IPC-2152 supersedes IPC-2221 charts",
             "planes, airflow change ΔT a lot"], y=p.cy + 0.8)
    k.b.meta["via_resistance_mohm"] = round(rv * 1e3, 3)
