"""Card 06 - ANALOG DESIGN: core op-amp / passive circuits, Kelvin sensing, guard ring, formulas."""
from ..config import eq
from ..graphics import Sch
from ..packages import info
from ..template import footer, new_card

CW, CH = 26.8, 20.0
COLS = [1.6, 29.4, 57.2]
ROWS = [11.8, 33.0]
R2512 = "Resistor_SMD:R_2512_6332Metric"          # Kelvin demo uses this land pattern's pad size / position


def build(card):
    b, f, k = new_card(card, "op-amp stages, passives, Kelvin", "formulas, noise, layout rules")
    footer(k)
    cells = [inverting, noninverting, tia, rc_lowpass, divider]
    for i, fn in enumerate(cells):
        x, y = COLS[i % 3], ROWS[i // 3]
        fn(f, f.panel(fn.__name__, x, y, CW, 19.6 if y == ROWS[0] else 19.38, fn.__doc__))
    kelvin(f)
    formulas(k)
    rules(k)
    guard(k)
    return b


def _eq(p, key):
    p.text(eq(key), p.x, p.y2 - 0.8)


def inverting(f, p):
    """INVERTING"""
    s = Sch(f)
    a, c = p.x + 9.5, p.cy + 8.2
    pin = s.opamp(a, c, 5.0)
    xn, xo = a - 2.0, a + 7.0
    s.res(p.x + 0.6, pin["inm"][1], xn, pin["inm"][1])
    s.wire((xn, pin["inm"][1]), pin["inm"])
    s.wire((xn, pin["inm"][1]), (xn, c - 4.6))
    s.res(xn, c - 4.6, xo, c - 4.6)
    s.wire((xo, c - 4.6), (xo, c))
    s.wire(pin["out"], (p.x2 - 0.6, c))
    s.dot(xn, pin["inm"][1])
    s.dot(xo, c)
    s.wire(pin["inp"], (xn, pin["inp"][1]))
    s.gnd(xn, pin["inp"][1])
    p.text("R_{in}", p.x + 2.2, pin["inm"][1] + 1.4)
    p.text("R_{f}", (xn + xo) / 2, c - 6.0, just="center")
    p.text("in", p.x, c - 2.6)
    p.text("out", p.x2, c - 1.2, just="right")
    _eq(p, "inv_amp")


def noninverting(f, p):
    """NON-INVERTING"""
    s = Sch(f)
    a, c = p.x + 9.5, p.cy + 7.0
    pin = s.opamp(a, c, 5.0, inv_top=False)
    xn, xo, yb = a - 2.0, a + 7.0, c + 4.6
    s.wire((p.x + 0.6, pin["inp"][1]), pin["inp"])
    s.wire(pin["inm"], (xn, pin["inm"][1]), (xn, yb))
    s.res(xn, yb, xo, yb)
    s.wire((xo, yb), (xo, c))
    s.wire(pin["out"], (p.x2 - 0.6, c))
    s.dot(xo, c)
    s.dot(xn, pin["inm"][1])
    s.wire((xn, pin["inm"][1]), (xn - 4.0, pin["inm"][1]))
    s.res(xn - 4.0, pin["inm"][1], xn - 4.0, yb + 0.2)
    s.gnd(xn - 4.0, yb + 0.2)
    p.text("in", p.x, c - 2.6)
    p.text("R_{g}", xn - 5.4, yb - 1.2, just="right")
    p.text("R_{f}", (xn + xo) / 2, yb + 1.4, just="center")
    p.text("out", p.x2, c - 1.2, just="right")
    _eq(p, "noninv_amp")


def tia(f, p):
    """TRANSIMPEDANCE"""
    s = Sch(f)
    a, c = p.x + 10.5, p.cy + 9.4
    pin = s.opamp(a, c, 5.0)
    xn, xo = a - 2.0, a + 7.0
    yr, yc = c - 3.6, c - 6.4
    s.wire(pin["inm"], (xn, pin["inm"][1]), (xn, yc))
    s.res(xn, yr, xo, yr)
    s.cap(xn, yc, xo, yc)
    s.wire((xo, yc), (xo, c))
    s.dot(xn, yr)
    s.dot(xo, yr)
    s.wire(pin["out"], (p.x2 - 0.6, c))
    s.dot(xo, c)
    s.dot(xn, pin["inm"][1])
    s.wire((xn, pin["inm"][1]), (p.x + 4.0, pin["inm"][1]))
    s.diode(p.x + 4.0, c + 4.2, p.x + 4.0, pin["inm"][1])
    s.gnd(p.x + 4.0, c + 4.2)
    s.wire(pin["inp"], (xn, pin["inp"][1]))
    s.gnd(xn, pin["inp"][1])
    p.text("PD", p.x, c + 1.2)
    p.text("R_{f}", xo + 0.6, yr)
    p.text("C_{f}", xo + 0.6, yc)
    _eq(p, "tia")


def rc_lowpass(f, p):
    """RC LOW-PASS"""
    s = Sch(f)
    y, xc = p.cy + 5.0, p.x + 13.0
    s.res(p.x + 0.6, y, xc, y)
    s.wire((xc, y), (p.x2 - 0.6, y))
    s.dot(xc, y)
    s.cap(xc, y, xc, y + 6.0)
    s.gnd(xc, y + 6.0)
    p.text("R", (p.x + xc) / 2, y - 1.4, just="center")
    p.text("C", xc + 1.4, y + 3.0)
    p.text("in", p.x, y - 1.4)
    p.text("out", p.x2, y - 1.4, just="right")
    p.text("−20 dB/dec above f_{c}", p.x, p.y2 - 2.4)
    _eq(p, "rc_fc")


def divider(f, p):
    """DIVIDER"""
    s = Sch(f)
    x, yt = p.x + 6.0, p.cy + 2.0
    s.rail(x, yt + 0.6, "")
    s.res(x, yt + 0.6, x, yt + 5.6)
    s.res(x, yt + 5.6, x, yt + 10.6)
    s.gnd(x, yt + 10.6)
    s.dot(x, yt + 5.6)
    s.wire((x, yt + 5.6), (x + 6.0, yt + 5.6))
    p.text("V_{in}", x + 1.2, yt)
    p.text("R1", x + 1.2, yt + 3.1)
    p.text("R2", x + 1.2, yt + 8.1)
    p.text("V_{out}", x + 6.6, yt + 5.6)
    p.lines(["load ≫ R2,", "else V_{out} drops"], x=p.x + 14.0, y=yt + 9.0)
    _eq(p, "divider")


def kelvin(f):
    """Real copper: 2512 land with separate force (wide) and sense (thin) connections."""
    p = f.panel("kelvin", COLS[2], ROWS[1], CW, 19.38, "KELVIN 4-WIRE")
    pads = info(R2512)["pads"]
    cx, cy = p.x + CW / 2, p.cy + 7.6
    for side, pd in zip((-1, 1), pads):
        n = f.b.net()
        px = cx + pd["x"]
        f.pad(px, cy, pd["w"], pd["h"], net=n)
        xo = px + side * pd["w"] / 2                            # outer edge: force (current)
        f.gold_track(px, cy, px + side * 5.0, cy, 1.0, n)
        f.gold_track(px - side * 0.35, cy - pd["h"] / 2 + 0.3, px - side * 0.35, cy - 4.4, 0.2, n)
        f.gold_track(px - side * 0.35, cy - 4.4, px - side * 0.35 + side * 3.0, cy - 4.4, 0.2, n)
        p.text("force", xo + side * 2.6, cy + 1.6, just="center")
    p.text("sense", cx, cy - 4.4, just="center")
    f.rect(cx - 1.9, cy - 1.0, cx + 1.9, cy + 1.0)              # resistor body outline (silk)
    p.text("2512 shunt", cx, cy + 3.4, just="center")
    p.lines(["sense taps at the pad inner", "edge: no I·R of force Cu"], y=p.y2 - 3.2)


def formulas(k):
    p = k.panel("formulas", 1.6, 11.8, 82.4, 19.0, "MORE ANALOG FORMULAS")
    rows = [("difference", "diff_amp"), ("summing", "sum_amp"), ("in-amp (3 op)", "ina"),
            ("integrator", "integrator"), ("TIA C_{f}, 45°", "tia_cf"), ("R noise", "noise_r"),
            ("noise, 1-pole", "noise_int"), ("full-power BW", "slew_fpbw"), ("ADC LSB", "adc_lsb"),
            ("ADC SNR", "adc_snr")]
    p.table([[a, eq(b)] for a, b in rows], [0, 16.0], header=False, pitch=1.7)   # sub/superscripts need 1.7


def rules(k):
    p = k.panel("rules", 1.6, 31.4, 46.0, 18.0, "ANALOG LAYOUT")
    p.lines(["decouple each supply pin: 100 nF", "  at the pin + bulk nearby", "keep feedback loops short;",
             "  R_{f}/C_{f} right at the inputs", "split nothing: one ground plane,", "  route returns, not islands",
             "Kelvin-sense shunts and refs", "e_{n}(1 kΩ) = 4.07 nV/√Hz at 25 °C"])


def guard(k):
    """Real copper on the back: driven guard ring around a high-impedance input pad."""
    p = k.panel("guard", 49.0, 31.4, 35.0, 18.0, "GUARD RING")
    cx, cy, r = p.x + 9.0, p.cy + 7.4, 4.0
    n_in, n_g = k.b.net(), k.b.net()
    k.pad(cx, cy, 1.2, 1.2, net=n_in)
    pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r), (cx - r, cy - r)]
    for a, b in zip(pts, pts[1:]):
        k.gold_track(*a, *b, 0.5, n_g)
    p.lines(["ring driven at the", "input's potential", "(buffer out or", "V_{CM}); leakage", "sees ~0 V"],
            x=p.x + 15.0, y=p.cy + 0.8)
    p.text("high-Z pad", cx, cy + r + 1.6, just="center")
