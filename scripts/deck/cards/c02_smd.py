"""Card 02 - SMD FOOTPRINT MASTER: real KiCad land patterns + 1:1 body silhouettes."""
from ..eng import dim
from ..graphics import package_row
from ..layout import PITCH
from ..packages import info, pad_size, pkg, registry
from ..template import footer, new_card

Y0 = 11.8
FRONT_PKGS = ["SOT-23", "SOT-323", "SOT-363", "SOT-89", "SOT-223", "SOIC-8", "MSOP-8"]
BACK_PKGS = ["SOIC-14", "SSOP-16", "TSSOP-14", "TSSOP-16", "TSSOP-20", "TSSOP-24", "DFN-8", "QFN-16",
             "PowerPAK SO-8"]
SHORT = {"PowerPAK SO-8": "PPAK SO8"}


def build(card):
    b, f, k = new_card(card, "chip & SOT/SO land patterns, 1:1", "fine-pitch SO, DFN/QFN, data")
    chips(f)
    pkg_row(f, "sot", FRONT_PKGS, 27.6, 7.4, "SOT / SO FAMILY")
    legend(f)
    footer(k)
    pkg_row(k, "so", BACK_PKGS, Y0, 9.4, "SO / TSSOP / DFN / QFN")
    chip_table(k)
    notes(k)
    b.meta["packages"] = [c[2] for c in registry()["chip"]["codes"]] + \
        [pkg(n)["footprint"] for n in FRONT_PKGS + BACK_PKGS]
    return b


def chips(f):
    p = f.panel("chips", 1.6, Y0, 82.4, 15.3, "CHIP SIZES  land pattern + body 1:1")
    codes = registry()["chip"]["codes"]
    items = []
    for eia, metric, fp, _, L, Wd in codes:
        items.append((fp, eia, ["", "", "", metric, f"{dim(L)}×{dim(Wd)}"]))
    placed = package_row(p, items, p.cy, 4.0, gap=0.6)
    for (fp, cx, yb), (eia, metric, _, _, L, Wd) in zip(placed, codes):
        yc = yb + 2.0 + 0.8 + PITCH          # centre of the three blank lines
        f.rect(cx - L / 2, yc - Wd / 2, cx + L / 2, yc + Wd / 2, "SilkS", 0, True)
    f.b.meta["chip_bodies_mm"] = {c[0]: [c[4], c[5]] for c in codes}


def pkg_row(v, name, keys, y, band, title):
    items = []
    for key in keys:
        d = pkg(key)
        items.append((d["footprint"], SHORT.get(key, key),
                      [f"P {d['pitch']}", "×".join(dim(x) for x in d["body"])]))
    p = v.panel(name, 1.6, y, 82.4, 1.69 + 1.6 + band + 0.8 + PITCH + 0.8, title)
    package_row(p, items, p.cy, band, gap=0.6)


def legend(f):
    p = f.panel("legend", 1.6, 42.2, 82.4, 10.1, "READING THIS CARD")
    p.table([["gold pads", "KiCad 10 library land pattern, IPC-7351 nominal (N) density"],
             ["white body", "nominal body at 1:1; metric code is rounded: 2012 = 2.0×1.25"],
             ["P", "lead pitch, mm  (SOT: lead pitch / outer-lead spacing)"],
             ["L×W", "nominal body, mm; vendors differ - use the exact datasheet variant"],
             ["", "same package name ≠ same size or pinout (e.g. SOT-23-3 vs -5/-6)"]],
            [0, 15.0], header=False)


def chip_table(k):
    p = k.panel("chip table", 1.6, 28.4, 55.0, 21.3, "CHIP DATA (mm)")
    rows = [["EIA", "metric", "body", "land w×h", "C-C", "P_{70}*"]]
    for eia, metric, fp, pw, L, Wd in registry()["chip"]["codes"]:
        w, h = pad_size(fp)
        cc = 2 * abs(info(fp)["pads"][0]["x"])
        rows.append([eia, metric, f"{dim(L)}×{dim(Wd)}", f"{w:.2f}×{h:.2f}",
                     f"{cc:.2f}", f"{pw} W" if pw != "-" else "-"])
    p.table(rows, [0, 7.0, 13.4, 23.6, -42.0, -55.0])


def notes(k):
    p = k.panel("notes", 58.2, 28.4, 25.8, 21.3, "NOTES")
    p.lines(["land = pads on card", "C-C = pad centre dist.", "body = nominal L×W",
             "EP = exposed pad: tie", "as datasheet says, often", "GND; split paste window",
             "*Yageo RC_L thick film", "@70 °C, unverified copy", "- = no Yageo 1812"])
