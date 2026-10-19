"""Card 11 - COMMUNICATION INTERFACES: UART frame, SPI modes, I2C bus, Qwiic land, pinouts."""
from ..config import data_table, eq
from ..graphics import Sch
from ..template import footer, new_card

QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
UART_BYTE = 0x41                                  # 'A', sent LSB first
BAUDS = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]


def build(card):
    b, f, k = new_card(card, "UART, SPI, I²C, CAN, RS-485", "pinouts, bauds, buses")
    footer(k)
    uart(f)
    spi(f)
    i2c(f)
    qwiic(f)
    diff_buses(f)
    de9(k)
    usb(k)
    bauds(k)
    reach(k)
    b.meta["packages"] = [QWIIC]
    return b


def uart(f):
    p = f.panel("uart", 1.6, 11.8, 52.0, 12.6, f"UART 8N1, 0x{UART_BYTE:02X} ('{chr(UART_BYTE)}')")
    bw, yh, yl = 4.2, p.cy + 1.6, p.cy + 4.0
    bits = [1] + [0] + [(UART_BYTE >> i) & 1 for i in range(8)] + [1, 1]
    labels = ["idle", "S"] + [str(i) for i in range(8)] + ["P", ""]
    x = p.x + 0.4
    lvl = None
    for bit, lab in zip(bits, labels):
        y = yh if bit else yl
        if lvl is not None and y != lvl:
            f.line(x, lvl, x, y, w=0.2)
        f.line(x, y, x + bw, y, w=0.2)
        if lab and lab != "idle":
            p.text(lab, x + bw / 2, yl + 1.3, just="center")
        lvl = y
        x += bw
    p.lines(["LSB first; S = start (0), P = stop (1)", "idle high (TTL level); RS-232 inverts"], y=yl + 2.9)


def spi(f):
    t = data_table("interfaces")["spi_modes"]
    p = f.panel("spi", 55.4, 11.8, 28.6, 12.6, "SPI MODES")
    p.table([["mode", "CPOL", "CPHA", "sample"]] + t["rows"], [0, -12.0, -18.6, -28.6])


def i2c(f):
    p = f.panel("i2c", 1.6, 26.0, 52.0, 13.4, "I²C: open drain + pull-ups")
    s = Sch(f)
    x0, ysda, yscl = p.x + 9.0, p.cy + 5.6, p.cy + 8.0
    for xr, y in ((x0, ysda), (x0 + 3.0, yscl)):
        s.res(xr, p.cy + 1.4, xr, y)
        s.dot(xr, y)
    s.wire((x0 - 1.0, p.cy + 1.4), (x0 + 4.0, p.cy + 1.4))
    p.text("V_{DD}", x0 - 1.4, p.cy + 1.4, just="right")
    p.text("R_{p}", x0 + 4.0, p.cy + 3.4)
    for y, lab in ((ysda, "SDA"), (yscl, "SCL")):
        s.wire((p.x + 0.4, y), (p.x + 32.0, y))
        p.text(lab, p.x, y - 1.0)
    for i, name in enumerate(("MCU", "dev 1", "dev 2")):
        bx = p.x + 13.4 + i * 6.6
        for y in (ysda, yscl):
            s.wire((bx + 1.0 + (y == yscl) * 2.0, y), (bx + 1.0 + (y == yscl) * 2.0, yscl + 1.2))
            s.dot(bx + 1.0 + (y == yscl) * 2.0, y)
        f.rect(bx, yscl + 1.2, bx + 5.8, yscl + 3.6)
        p.text(name, bx + 2.9, yscl + 2.4, just="center")
    sp = data_table("interfaces")["i2c_speeds"]["rows"]
    p.lines([f"{m} {v}" for m, v in sp], x=p.x + 34.0, y=p.cy + 0.8)


def qwiic(f):
    t = data_table("interfaces")["qwiic"]["rows"]
    p = f.panel("qwiic", 55.4, 26.0, 28.6, 13.4, "QWIIC / STEMMA QT")
    cx, cy = p.x + 6.8, p.cy + 5.6
    f.lib_fp(QWIIC, cx, cy)
    p.lines([f"{n} {s}" for n, s in t], x=p.x + 16.0, y=p.cy + 0.8)
    p.text("JST SH 1.0 mm", p.x, p.y2 - 0.8)


def diff_buses(f):
    p = f.panel("buses", 1.6, 41.0, 82.4, 11.38, "DIFFERENTIAL FIELD BUSES")
    p.table([["CAN", "CANH/CANL, 120 Ω at both ends; recessive ≈ 2.5 V both lines"],
             ["", "dominant: CANH ≈ 3.5 V, CANL ≈ 1.5 V (ISO 11898-2 typ.)"],
             ["RS-485", "A/B half duplex, 120 Ω at both ends, fail-safe bias"],
             ["", "daisy chain, short stubs; GND/common reference wire"]], [0, 13.0], header=False)


def de9(k):
    t = data_table("interfaces")["de9_rs232"]["rows"]
    p = k.panel("de9", 1.6, 11.8, 41.0, 17.0, "DE-9 male, face view (DTE)")
    x0, y0 = p.x + 1.0, p.cy + 1.0                 # trapezoid face, pins seen from the front
    k.poly([(x0, y0), (x0 + 16.0, y0), (x0 + 14.4, y0 + 6.6), (x0 + 1.6, y0 + 6.6)], fill=False, w=0.15)
    for i in range(5):
        cx = x0 + 2.4 + i * 2.8
        k.circle(cx, y0 + 2.0, 0.55)
        p.text(str(i + 1), cx, y0 + 3.6, just="center")
    for i in range(4):
        cx = x0 + 3.8 + i * 2.8
        k.circle(cx, y0 + 5.0, 0.55)
        p.text(str(i + 6), cx, y0 + 7.8, just="center")
    p.table([[a, b, c, d] for (a, b), (c, d) in zip(t[:5], t[5:] + [["", ""]])], [19.0, 21.6, 30.0, 32.6],
            header=False, y=p.cy + 0.8)


def usb(k):
    t = data_table("interfaces")["usb2_pins"]["rows"]
    p = k.panel("usb", 44.0, 11.8, 40.0, 17.0, "USB 2.0 PINS")
    p.table([["pin", "A / B", "micro-B"]] + t, [0, 8.0, 22.0])
    p.lines(["D+/D−: 90 Ω diff (card 08)"])


def bauds(k):
    p = k.panel("bauds", 1.6, 30.4, 41.0, 19.0, "COMMON BAUD RATES")
    rows = [[str(a), str(b)] for a, b in zip(BAUDS[:4], BAUDS[4:])]
    p.table(rows, [-12.0, -32.0], header=False)
    p.lines(["bit time = 1/baud", "115200: 8.68 µs/bit", "error: both ends add up;", "check clock divider"])
    assert abs(1e6 / 115200 - 8.68) < 0.005


def reach(k):
    p = k.panel("reach", 44.0, 30.4, 40.0, 19.0, "TOPOLOGY / REACH (typ.)")
    p.table([["I²C", "on-board, C_{b} ≤ 400 pF"], ["SPI", "on-board, 1 CS per dev"],
             ["UART", "point-to-point"], ["RS-485", "~1200 m at low rate"], ["CAN", "~40 m at 1 Mbit/s"],
             ["USB 2.0", "cable ≤ 5 m"]], [0, 12.0], header=False)
    p.lines([eq("i2c_rp").split(",  ")[1]], y=p.cy + 1.0)
