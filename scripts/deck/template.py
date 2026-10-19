"""Master mechanical template shared by all 15 cards."""
import math

from .config import BOARDS, H, MECH, STYLE, W
from .layout import MARGIN, View, style
from .pcb import Board, pad, rounded_rect_outline

RH = MECH["ring_hole"]
LY = MECH["layout"]
REV = STYLE["revision"]["label"]
YEAR = STYLE["revision"]["year"]


def new_card(card, subtitle_front, subtitle_back):
    """Create a Board with outline, ring hole and headers. Returns (board, front_view, back_view)."""
    b = Board(card["dir"])
    rounded_rect_outline(b, W, H, MECH["card"]["corner_radius"])

    # Ring hole: plated, 1.5 mm exposed annulus both sides, rule-area keep-out.
    b.footprint("RING_HOLE", RH["x"], RH["y"],
                [pad("", "thru_hole", "circle", 0, 0, RH["pad_diameter"], drill=RH["finished_diameter"])],
                prefix="H")
    n = 32
    ko = [(RH["x"] + RH["keepout_radius"] * math.cos(2 * math.pi * i / n),
           RH["y"] + RH["keepout_radius"] * math.sin(2 * math.pi * i / n)) for i in range(n)]
    b.keepout(ko, name="RING_HOLE_KEEPOUT")

    f, k = View(b, True), View(b, False)
    num = f"{card['id']:02d}"
    hole_box = RH["x"] + RH["keepout_radius"]
    for v, sub in ((f, subtitle_front), (k, subtitle_back)):
        # seen from the back the ring hole is top-RIGHT, so the header swaps sides
        if v.front:
            v.reserve("ring hole", MARGIN, MARGIN, hole_box, hole_box)
            xl, xr = LY["header_left"], W - MARGIN
        else:
            v.reserve("ring hole", W - hole_box, MARGIN, W - MARGIN, hole_box)
            xl, xr = MARGIN, W - LY["header_left"]
        v.reserve("header", xl - 0.4 if v.front else xl, MARGIN, xr if v.front else xr + 0.4, LY["header_bottom"])
        nsize, _ = style("number")
        v.gold_text(num, xl, 4.6, "number")
        tx = xl + 2 * nsize * 0.98 + 1.2
        v.text(card["title"], tx, 3.9, "title")
        v.text(sub, tx, 7.3, "body")
        v.text(f"{'FRONT' if v.front else 'BACK'} {num}/15", xr, 7.3, "body", "right")
        v.gold_track(xl + 0.15, 9.7, xr - 0.15, 9.7, 0.3)
    return b, f, k


FOOTER_Y = H - MARGIN - 0.7   # footer text centre; content must end above FOOTER_Y - 0.8


def footer(v, text=f"PCB DESIGN REFERENCE DECK  |  dims mm unless stated  |  nominal values  |  {REV} {YEAR}"):
    v.reserve("footer", MARGIN, FOOTER_Y - 0.75, W - MARGIN, H - MARGIN)
    v.text(text, W / 2, FOOTER_Y, "body", "center")


def save(b, card):
    from .config import board_file
    b.save(board_file(card), f"{card['id']:02d} {card['title']}", REV, YEAR)
