"""Card 13 - TEST / DEBUG: SWD header + pinout, Tag-Connect land, solder jumpers, test-point grid."""
from ..config import W, data_table
from ..graphics import package_row
from ..packages import info
from ..template import footer, new_card

SWD = "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD"
TC = "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical"
JUMPERS = [("Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", "open", ["cut-free", "add solder"]),
           ("Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm", "bridged", ["cut trace", "to open"]),
           ("Jumper:SolderJumper-3_P1.3mm_Open_Pad1.0x1.5mm", "3-way", ["bridge 1-2", "or 2-3"])]
TP = "TestPoint:TestPoint_Pad_D1.5mm"
TP_PITCH = 2.54


def build(card):
    b, f, k = new_card(card, "SWD, Tag-Connect, jumpers, TPs", "bring-up, probing, JTAG")
    footer(k)
    tag_connect(f)
    swd(f)
    jumpers(f)
    tp_grid(f)
    bringup(k)
    probing(k)
    jtag(k)
    b.meta["packages"] = [SWD, TC, TP] + [j[0] for j in JUMPERS]
    return b


def tag_connect(f):
    pf, pk = f.through_panel("tc2030", 1.6, 11.8, 26.0, 19.0, "TAG-CONNECT", "TC2030 HOLES")
    placed = package_row(pf, [(TC, "TC2030-NL", ["6 pads, 1.27", "no-legs: hold", "or use a clip"])], pf.cy, 5.0)
    cx = placed[0][1]
    pk.lines(["3 NPTH Ø0.99", "locate the", "pogo cable;", "keep both", "sides clear"], x=pk.x, y=pk.cy + 0.8)
    f.b.meta["tc2030_x"] = cx


def swd(f):
    t = dict(data_table("interfaces")["swd10"]["rows"])
    p = f.panel("swd", 29.6, 11.8, 54.4, 19.0, "ARM 10-PIN SWD/JTAG 1.27")
    cx, cy = p.x + 27.0, p.cy + 7.6
    f.lib_fp(SWD, cx, cy)
    for pd in info(SWD)["pads"]:          # labels at 1.6 pitch (1.27 is too tight), leaders to the pads
        n, side = pd["num"], 1 if pd["x"] > 0 else -1
        yl = cy + pd["y"] / 1.27 * 1.6
        f.line(cx + side * 3.4, cy + pd["y"], cx + side * 4.4, yl, w=0.12)
        p.text(f"{n} {t[n]}" if side > 0 else f"{t[n]} {n}", cx + side * 4.8, yl,
               just="left" if side > 0 else "right")
    p.text("top view; pin 1 = marked corner", p.x, p.y2 - 0.8)


def jumpers(f):
    p = f.panel("jumpers", 1.6, 32.6, 40.0, 19.78, "SOLDER JUMPERS")
    package_row(p, JUMPERS, p.cy, 3.0, gap=0.6)
    p.lines(["no nets merged until", "you solder: config"], y=p.cy + 1.0)


def tp_grid(f):
    p = f.panel("tp", 43.6, 32.6, 40.4, 19.78, "TEST POINTS")
    x0, y0 = p.x + 2.4, p.cy + 2.4
    for i in range(3):
        for j in range(2):
            f.lib_fp(TP, x0 + i * TP_PITCH, y0 + j * TP_PITCH)
    p.lines([f"Ø1.5 at {TP_PITCH} pitch", "(100 mil probes)", "GND TP near each", "signal TP; label",
             "on silk; one side"], x=p.x + 10.8, y=p.cy + 0.8)
    p.lines(["for a fixture: TPs on", "the bottom, off-grid ok"], y=p.y2 - 2.4)


def bringup(k):
    p = k.panel("bringup", 1.6, 11.8, 55.0, 19.0, "BRING-UP ORDER")
    steps = ["1 inspect: shorts, polarity,", "  orientation, bridges", "2 R to GND per rail, unpowered",
             "3 current-limited supply,", "  watch I at power-on", "4 rails, then ripple", "5 clocks: crystal / PLL",
             "6 reset + boot pins", "7 debugger: read ID,", "  flash a blinky", "8 one peripheral at a time",
             "keep a log of every fix"]
    y0 = p.cy + 0.8
    p.lines(steps[:7], y=y0)
    p.lines(steps[7:], x=p.x + 29.0, y=y0)


def probing(k):
    p = k.panel("probing", 1.6, 32.4, 40.0, 17.0, "PROBING")
    p.lines(["10× probe, ground spring", "  (long clip lead rings)", "scope BW ≥ 3-5× f_{knee}",
             "DMM in series: burden V", "diode test: Si ≈ 0.5-0.7 V", "thermal camera / IPA spray", "  finds shorts fast"],
            pitch=1.6)


def jtag(k):
    p = k.panel("jtag", 43.6, 32.4, 40.4, 17.0, "SIGNALS")
    p.table([["SWDIO", "data, bidir."], ["SWCLK", "clock"], ["SWO", "trace out (opt.)"],
             ["TMS TCK", "JTAG mode, clock"], ["TDI TDO", "data in / out"], ["nRESET", "target reset"],
             ["VTref", "target I/O level"]], [0, 13.4], header=False)
