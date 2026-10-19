"""Card 12 - COMPONENT IDENTIFICATION: colour code, SMD codes, polarity lands, dielectrics, refdes."""
from ..config import data_table
from ..eng import e_series
from ..graphics import package_row
from ..template import footer, new_card

POLARITY = [("Diode_SMD:D_SOD-123", "diode", ["band = K", "pad 1 = K"]),
            ("LED_SMD:LED_0805_2012Metric", "LED", ["mark = K", "pad 1 = K"]),
            ("Capacitor_Tantalum_SMD:CP_EIA-3216-18_Kemet-A", "tantalum", ["band = +", "pad 1 = +"]),
            ("Capacitor_SMD:CP_Elec_4x5.4", "electrolytic", ["stripe = −", "pad 1 = +"]),
            ("Package_TO_SOT_SMD:SOT-23", "SOT-23", ["pin 1 = dot", "check pinout"])]


def build(card):
    b, f, k = new_card(card, "colour code, SMD codes, polarity", "capacitors, dielectrics, refdes")
    footer(k)
    color_code(f)
    smd_codes(f)
    polarity(f)
    cap_codes(k)
    dielectrics(k)
    refdes(k)
    b.meta["packages"] = [p[0] for p in POLARITY]
    return b


def color_code(f):
    t = data_table("components")["color_code"]["rows"]
    p = f.panel("colors", 1.6, 11.8, 38.0, 23.4, "RESISTOR COLOUR CODE")
    rows = [["colour", "digit", "×10^{n}", "tol."]] + [[c, d, m, tol] for c, d, m, tol in t]
    p.table(rows, [0, -16.0, -24.0, -38.0], pitch=1.6)


def smd_codes(f):
    m = data_table("components")["eia96_multiplier"]["rows"]
    e96 = e_series(96)
    p = f.panel("smd codes", 41.6, 11.8, 42.4, 23.4, "SMD RESISTOR CODES")
    p.lines(["472 = 47·10^{2} = 4.7 kΩ  (3 digit)", "4702 = 470·10^{2} = 47.0 kΩ  (4 digit)",
             "4R7 = 4.7 Ω   R47 = 0.47 Ω   000 = 0 Ω",
             f"EIA-96: 01C = {e96[0] * 100:.0f}·100 = 10.0 kΩ", f"  68X = {e96[67] * 100:.0f}·0.1 = "
             f"{e96[67] * 10:.2f} Ω  (code nn = E96 no.)", "EIA-96 letter = multiplier:"], pitch=1.7)
    p.table([[a for a, _ in m[:5]], [b for _, b in m[:5]], [a for a, _ in m[5:]] + [""], [b for _, b in m[5:]] + [""]],
            [0, 8.4, 16.8, 25.2, 33.6], header=False, pitch=1.6)


def polarity(f):
    p = f.panel("polarity", 1.6, 35.8, 82.4, 16.58, "POLARITY ON KiCad LAND PATTERNS")
    package_row(p, [(fp, top, below) for fp, top, below in POLARITY], p.cy, 5.8, gap=0.6)


def cap_codes(k):
    t = data_table("components")["cap_tolerance"]["rows"]
    p = k.panel("cap codes", 1.6, 11.8, 40.0, 19.0, "CAPACITOR CODES (pF)")
    p.lines(["104 = 10·10^{4} pF = 100 nF", "475 = 4.7 µF   2R2 = 2.2 pF", "tolerance letter after code:"],
            pitch=1.7)
    p.table([[a, b] for a, b in t[:5]], [0, 3.0], header=False, y=p.cy + 0.8)
    p.table([[a, b] for a, b in t[5:]], [20.0, 23.0], header=False, y=p.cy - 5 * 1.6 + 0.8)


def dielectrics(k):
    t = data_table("components")["dielectrics"]["rows"]
    p = k.panel("dielectrics", 43.6, 11.8, 40.4, 19.0, "MLCC DIELECTRICS")
    p.table([["code", "ΔC", "range"]] + t, [0, 11.0, 24.0])
    p.lines(["class 2: C drops with DC bias,", "check the derating curve"])


def refdes(k):
    t = data_table("components")["refdes"]["rows"]
    p = k.panel("refdes", 1.6, 32.6, 82.4, 16.8, "REFERENCE DESIGNATORS")
    per = 5
    for c in range(0, len(t), per):
        x = p.x + (c // per) * 28.0
        p.table([[a, b] for a, b in t[c:c + per]], [0, 4.6], x=x, header=False, y=p.y + 1.69 + 0.8)
