"""Card 10 - DIGITAL LOGIC: gates + truth tables, logic levels with noise margins, decoupling land."""
from ..config import data_table, eq
from ..graphics import Sch
from ..template import footer, new_card

GATES = [("NOT", lambda a: 1 - a), ("AND", lambda a, b: a & b), ("OR", lambda a, b: a | b),
         ("NAND", lambda a, b: 1 - (a & b)), ("NOR", lambda a, b: 1 - (a | b)), ("XOR", lambda a, b: a ^ b)]
GW, GH = 26.8, 11.6
SOIC = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
C0402 = "Capacitor_SMD:C_0402_1005Metric"


def build(card):
    b, f, k = new_card(card, "gates, truth tables, logic levels", "hex, Boolean, I/O practice")
    footer(k)
    for i, (name, fn) in enumerate(GATES):
        gate_cell(f, 1.6 + (i % 3) * 27.8, 11.8 + (i // 3) * 12.4, name, fn)
    levels(f)
    hex_table(k)
    boolean(k)
    practice(k)
    decoupling(k)
    b.meta["gates"] = [g for g, _ in GATES]
    return b


def gate_cell(f, x, y, name, fn):
    p = f.panel(name, x, y, GW, GH, name)
    ins, out = Sch(f).gate(name, p.x + 2.4, p.cy + 4.6)
    n = fn.__code__.co_argcount
    rows = [["A", "Y"]] if n == 1 else [["A", "B", "Y"]]
    combos = [(0,), (1,)] if n == 1 else [(0, 0), (0, 1), (1, 0), (1, 1)]
    rows += [[*map(str, c), str(fn(*c))] for c in combos]
    cols = [12.0, 16.0] if n == 1 else [12.0, 15.0, 19.0]
    p.table(rows, cols, y=p.y + 0.8, pitch=1.6)
    for t, (px, py) in zip("AB", ins):
        p.text(t, p.x, py)
    p.text("Y", out[0] + 0.4, out[1] - 1.2)


def levels(f):
    t = data_table("logic")["levels"]
    p = f.panel("levels", 1.6, 36.6, 82.4, 15.78, "LOGIC LEVELS (V) and noise margins")
    rows = [["family", "V_{IL}", "V_{IH}", "V_{OL}", "V_{OH}", "NM_{L}", "NM_{H}"]]
    for fam, vdd, vil, vih, vol, voh in t["rows"]:
        rows.append([fam, f"{vil:g}", f"{vih:g}", f"{vol:g}", f"{voh:g}", f"{vil - vol:.2f}", f"{voh - vih:.2f}"])
    p.table(rows, [0, -27.0, -36.0, -45.0, -54.0, -66.0, -78.0], pitch=1.65)
    f.b.meta["logic_levels"] = rows


def hex_table(k):
    p = k.panel("hex", 1.6, 11.8, 37.0, 16.4, "HEX / BINARY")
    left = [[f"{i:X}", f"{i:04b}", str(i)] for i in range(8)]
    right = [[f"{i:X}", f"{i:04b}", str(i)] for i in range(8, 16)]
    p.table([a + b for a, b in zip(left, right)], [0, 3.0, -15.0, 20.0, 23.0, -37.0], header=False, y=p.cy + 0.8)


def boolean(k):
    p = k.panel("boolean", 40.0, 11.8, 44.0, 16.4, "BOOLEAN")
    p.lines(["~{A·B} = ~{A} + ~{B}   (De Morgan)", "~{A+B} = ~{A} · ~{B}", "A + A·B = A   A·(A+B) = A",
             "A ⊕ B = A·~{B} + ~{A}·B", "NAND / NOR alone build any gate"], y=p.cy + 0.9, pitch=1.75)


def practice(k):
    p = k.panel("practice", 1.6, 29.6, 46.0, 19.8, "I/O PRACTICE")
    p.lines(["unused CMOS inputs: tie, never float", "slow edges: Schmitt-trigger input",
             "open-drain bus pull-up (I^{2}C):", *["  " + t for t in eq("i2c_rp").split(",  ")], "level shift: check V_{IH} vs V_{OH}",
             "series 22-33 Ω at fast drivers (typ.)", "reset: RC + supervisor, not RC alone"], pitch=1.75)


def decoupling(k):
    """Real copper: SOIC-8 with an 0402 at the supply pin, short loop to a GND via."""
    p = k.panel("decoupling", 49.6, 29.6, 34.4, 19.8, "DECOUPLING (example)")
    cx, cy = p.x + 9.0, p.cy + 8.4
    vcc, gnd = k.b.net("VCC_DEMO"), k.b.net("GND_DEMO")
    k.lib_fp(SOIC, cx, cy, 0, nets={"8": vcc, "4": gnd})
    # SOIC-8 pin 8 at (+2.475, -1.905), pin 4 at (-2.475, +1.905) (KiCad library footprint)
    p8, p4 = (cx + 2.475, cy - 1.905), (cx - 2.475, cy + 1.905)
    xc = p8[0] + 2.6
    k.lib_fp(C0402, xc, p8[1] - 1.6, 90, nets={"1": vcc, "2": gnd})
    k.gold_track(*p8, xc, p8[1], 0.3, vcc)
    k.gold_track(xc, p8[1], xc, p8[1] - 1.12, 0.3, vcc)
    k.gold_track(xc, p8[1] - 2.08, xc, p8[1] - 3.2, 0.3, gnd)
    k.gold_track(*p4, p4[0] - 1.2, p4[1] + 1.4, 0.3, gnd)
    route = [(xc, p8[1] - 3.2), (xc + 1.5, p8[1] - 3.2), (xc + 1.5, cy + 4.4), (p4[0] - 1.2, cy + 4.4),
             (p4[0] - 1.2, p4[1] + 1.4)]     # stands in for the GND plane; no vias: the front face is full
    for a, b_ in zip(route, route[1:]):
        k.gold_track(*a, *b_, 0.3, gnd)
    p.lines(["cap at the", "pin; real", "board: via", "to GND plane", "at the cap;", "loop area", "= ESL"],
            x=p.x + 21.6, y=p.cy + 0.8)
    p.text("pin 8 VCC / 4 GND: example", p.x, p.y2 - 0.8)
