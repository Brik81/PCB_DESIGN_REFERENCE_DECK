"""Native KiCad 10 board writer.

Everything is emitted as real PCB objects (Edge.Cuts graphics, tracks, vias,
pads inside footprints, zones, silkscreen text). No pcbnew dependency.
"""
import json
import math
import uuid
from pathlib import Path

from .config import FAB, KICAD_FP_DIR, MECH, RULES
from .sexpr import Q, dumps, find, first, loads

_NS = uuid.UUID("6f1d0c1e-3c1a-4c55-9a39-1b3c0dd0e5a1")

LAYERS = [
    (0, "F.Cu", "signal"), (2, "B.Cu", "signal"),
    (9, "F.Adhes", "user", "F.Adhesive"), (11, "B.Adhes", "user", "B.Adhesive"),
    (13, "F.Paste", "user"), (15, "B.Paste", "user"),
    (5, "F.SilkS", "user", "F.Silkscreen"), (7, "B.SilkS", "user", "B.Silkscreen"),
    (1, "F.Mask", "user"), (3, "B.Mask", "user"),
    (17, "Dwgs.User", "user", "User.Drawings"), (19, "Cmts.User", "user", "User.Comments"),
    (21, "Eco1.User", "user", "User.Eco1"), (23, "Eco2.User", "user", "User.Eco2"),
    (25, "Edge.Cuts", "user"), (27, "Margin", "user"),
    (31, "F.CrtYd", "user", "F.Courtyard"), (29, "B.CrtYd", "user", "B.Courtyard"),
    (35, "F.Fab", "user"), (33, "B.Fab", "user"),
]


def stroke(w):
    return ["stroke", ["width", w], ["type", "solid"]]


def font(size, thick):
    return ["font", ["size", size, size], ["thickness", thick]]


def pad(num, kind, shape, x, y, w, h=None, drill=None, layers=None, net=None,
        rratio=None, angle=0, mask_margin=None, extra=()):
    """Footprint pad (coordinates relative to the footprint)."""
    h = w if h is None else h
    if layers is None:
        layers = {"smd": ["F.Cu", "F.Mask"], "thru_hole": ["*.Cu", "*.Mask"],
                  "np_thru_hole": ["*.Cu", "*.Mask"]}[kind]
    p = ["pad", Q(num), kind, shape, ["at", x, y, angle] if angle else ["at", x, y], ["size", w, h]]
    if drill is not None:
        p.append(["drill", "oval", *drill] if isinstance(drill, tuple) else ["drill", drill])
    p.append(["layers", *[Q(l) for l in layers]])
    if rratio is not None:
        p.append(["roundrect_rratio", rratio])
    if mask_margin is not None:
        p.append(["solder_mask_margin", mask_margin])
    if net:
        p.append(["net", Q(net)])
    p.extend(extra)
    return p


def _flip_layer(name):
    s = str(name)
    return Q("B." + s[2:] if s.startswith("F.") else "F." + s[2:] if s.startswith("B.") else s)


def _flip(node):
    """Mirror a footprint child top<->bottom in footprint-local coordinates."""
    if not isinstance(node, list) or not node:
        return node
    head = node[0]
    out = [head]
    for e in node[1:]:
        out.append(_flip(e))
    if head in ("start", "end", "mid", "center", "xy") and len(out) >= 3:
        out[2] = -float(out[2])
    elif head == "at" and len(out) >= 3:      # pad/text angles in files are absolute
        out[2] = -float(out[2])
        a = (180 - (float(out[3]) if len(out) > 3 else 0.0)) % 360
        out[3:] = [a]
    elif head in ("layer", "layers"):
        out[1:] = [_flip_layer(l) for l in out[1:]]
    elif head == "effects" and not any(isinstance(e, list) and e[0] == "justify" for e in out):
        out.append(["justify", "mirror"])
    elif head == "justify" and "mirror" not in out:
        out.append("mirror")
    return out


CU_MM, MASK_MM = 0.035, 0.01   # stack-up: 1 oz outer copper, solder mask (KiCad stack-up / impedance only)


class Board:
    def __init__(self, name, thickness=MECH["card"]["thickness"]):
        self.name = name
        self.thickness = thickness
        self.items = []
        self.nets = set()
        self._n = 0
        self._fp = 0
        self.meta = {}   # free-form data recorded by card builders (used by validation/docs)

    # ---- bookkeeping -----------------------------------------------------
    def uid(self):
        self._n += 1
        return ["uuid", Q(str(uuid.uuid5(_NS, f"{self.name}/{self._n}")))]

    def net(self, name=None):
        if name is None:
            name = f"REF{len(self.nets) + 1}"
        self.nets.add(name)
        return name

    def add(self, item):
        item.append(self.uid())
        self.items.append(item)
        return item

    # ---- graphics --------------------------------------------------------
    def line(self, x1, y1, x2, y2, layer, w=0.15):
        return self.add(["gr_line", ["start", x1, y1], ["end", x2, y2], stroke(w), ["layer", Q(layer)]])

    def rect(self, x1, y1, x2, y2, layer, w=0.15, fill=False):
        return self.add(["gr_rect", ["start", x1, y1], ["end", x2, y2], stroke(w),
                         ["fill", "yes" if fill else "no"], ["layer", Q(layer)]])

    def circle(self, cx, cy, r, layer, w=0.15, fill=False):
        return self.add(["gr_circle", ["center", cx, cy], ["end", cx + r, cy], stroke(w),
                         ["fill", "yes" if fill else "no"], ["layer", Q(layer)]])

    def arc(self, start, mid, end, layer, w=0.15):
        return self.add(["gr_arc", ["start", *start], ["mid", *mid], ["end", *end], stroke(w), ["layer", Q(layer)]])

    def poly(self, pts, layer, w=0, fill=True):
        return self.add(["gr_poly", ["pts", *[["xy", x, y] for x, y in pts]], stroke(w),
                         ["fill", "yes" if fill else "no"], ["layer", Q(layer)]])

    def text(self, s, x, y, layer, size, thick, just="left", angle=0, mirror=False, valign=None):
        j = [k for k in (just if just != "center" else None, valign) if k]
        if mirror:
            j.append("mirror")
        eff = ["effects", font(size, thick)]
        if j:
            eff.append(["justify", *j])
        return self.add(["gr_text", Q(s), ["at", x, y, angle], ["layer", Q(layer)], eff])

    # ---- copper ----------------------------------------------------------
    def track(self, x1, y1, x2, y2, w, layer, net=None):
        t = ["segment", ["start", x1, y1], ["end", x2, y2], ["width", w], ["layer", Q(layer)]]
        if net:
            t.append(["net", Q(self.net(net))])
        return self.add(t)

    def arc_track(self, start, mid, end, w, layer, net=None):
        t = ["arc", ["start", *start], ["mid", *mid], ["end", *end], ["width", w], ["layer", Q(layer)]]
        if net:
            t.append(["net", Q(self.net(net))])
        return self.add(t)

    def via(self, x, y, size, drill, net=None, layers=("F.Cu", "B.Cu"), tent=True):
        v = ["via", ["at", x, y], ["size", size], ["drill", drill], ["layers", *[Q(l) for l in layers]]]
        if not tent:
            v.append(["tenting", ["front", "no"], ["back", "no"]])
        if net:
            v.append(["net", Q(self.net(net))])
        return self.add(v)

    def zone(self, pts, layer, net, clearance=0.25, min_thick=0.15, connect="thermal",
             thermal_gap=0.3, spoke=0.3, name=None):
        z = ["zone", ["net", Q(self.net(net))], ["layer", Q(layer)]]
        if name:
            z.append(["name", Q(name)])
        z += [["hatch", "edge", 0.5],
              ["connect_pads", *(["yes"] if connect == "solid" else ["no"] if connect == "none" else []),
               ["clearance", clearance]],
              ["min_thickness", min_thick],
              ["fill", "yes", ["thermal_gap", thermal_gap], ["thermal_bridge_width", spoke],
               ["island_removal_mode", 1]],
              ["polygon", ["pts", *[["xy", x, y] for x, y in pts]]]]
        return self.add(z)

    def keepout(self, pts, layers=("F.Cu", "B.Cu"), name="KEEPOUT"):
        return self.add(["zone", ["net", Q("")], ["layers", *[Q(l) for l in layers]], ["name", Q(name)],
                         ["hatch", "edge", 0.5], ["connect_pads", ["clearance", 0]], ["min_thickness", 0.25],
                         ["keepout", ["tracks", "not_allowed"], ["vias", "not_allowed"], ["pads", "allowed"],
                          ["copperpour", "not_allowed"], ["footprints", "allowed"]],
                         ["fill", ["thermal_gap", 0.5], ["thermal_bridge_width", 0.5]],
                         ["polygon", ["pts", *[["xy", x, y] for x, y in pts]]]])

    # ---- footprints ------------------------------------------------------
    def _ref(self, prefix):
        self._fp += 1
        return f"{prefix}{self._fp}"

    def footprint(self, name, x, y, pads, graphics=(), angle=0, prefix="X", layer="F.Cu"):
        """Board-only footprint built from pad() items (+ optional fp_* graphics)."""
        ref = self._ref(prefix)
        side = layer[0]
        props = [["property", Q(k), Q(v), ["at", 0, 0, 0], ["layer", Q(f"{side}.Fab")], ["hide", "yes"],
                  ["effects", font(1, 0.15)]] for k, v in (("Reference", ref), ("Value", name))]
        for p in pads:
            if p[0] == "pad":
                p.append(self.uid())
                net = first(p, "net")
                if net:
                    self.nets.add(str(net[1]))
        fp = ["footprint", Q(f"Deck:{name}"), ["layer", Q(layer)], ["at", x, y, angle] if angle else ["at", x, y],
              *props, ["attr", "board_only", "exclude_from_pos_files", "exclude_from_bom"],
              *graphics, *pads]
        return self.add(fp)

    def lib_footprint(self, lib_name, x, y, angle=0, ref_prefix="U", back=False, nets=None):
        """Place a footprint from the official KiCad library (land pattern source of truth).

        back=True mirrors it onto the bottom side exactly as KiCad's own Flip does
        (local Y negated, layers F<->B, footprint rotated 180 deg, pad angles 180-a).
        nets: {pad number: net name} for pads that connect to tracks / zones.
        """
        lib, fpname = lib_name.split(":")
        node = loads((KICAD_FP_DIR / f"{lib}.pretty" / f"{fpname}.kicad_mod").read_text(encoding="utf-8"))
        drop = {"version", "generator", "generator_version", "model", "tedit", "uuid", "embedded_fonts"}
        body = [c for c in node[2:] if not (isinstance(c, list) and c and c[0] in drop)]
        ref = self._ref(ref_prefix)
        for c in body:
            if isinstance(c, list):
                c[:] = [e for e in c if not (isinstance(e, list) and e and e[0] in ("uuid", "tstamp", "model"))]
            if isinstance(c, list) and c and c[0] == "pad":
                lay = first(c, "layers")   # no stencil is ordered: drop paste apertures
                lay[1:] = [l for l in lay[1:] if "Paste" not in l]
                if nets and str(c[1]) in nets:
                    c.append(["net", Q(self.net(nets[str(c[1])]))])
            if isinstance(c, list) and c and c[0] == "property":
                if c[1] == "Reference":
                    c[2] = Q(ref)
                if c[1] in ("Reference", "Value") and not find(c, "hide"):
                    c.insert(4, ["hide", "yes"])
            if isinstance(c, list) and c and c[0] in ("pad", "fp_text", "fp_line", "fp_rect", "fp_circle",
                                                        "fp_arc", "fp_poly", "property", "zone"):
                c.append(self.uid())
        body = [c for c in body if not (isinstance(c, list) and c[0] == "layer")]
        if back:
            body = [_flip(c) for c in body]
        if angle:   # pad / text angles in board files are absolute: add the footprint rotation
            for c in body:
                at = first(c, "at") if isinstance(c, list) and c[0] in ("pad", "property", "fp_text") else None
                if at:
                    at[3:] = [(float(at[3]) if len(at) > 3 else 0.0) + angle]
        if back:
            angle = (angle + 180) % 360
        fp = ["footprint", Q(lib_name), ["layer", Q("B.Cu" if back else "F.Cu")],
              ["at", x, y, angle] if angle else ["at", x, y], *body]
        self.items.append(fp + [self.uid()])
        return fp

    # ---- output ----------------------------------------------------------
    def setup(self):
        r = RULES
        cu, mask = CU_MM, MASK_MM
        core = round(self.thickness - 2 * cu - 2 * mask, 4)
        return ["setup",
                ["stackup",
                 ["layer", Q("F.SilkS"), ["type", Q("Top Silk Screen")], ["color", Q("White")]],
                 ["layer", Q("F.Paste"), ["type", Q("Top Solder Paste")]],
                 ["layer", Q("F.Mask"), ["type", Q("Top Solder Mask")], ["color", Q("Black")], ["thickness", mask]],
                 ["layer", Q("F.Cu"), ["type", Q("copper")], ["thickness", cu]],
                 ["layer", Q("dielectric 1"), ["type", Q("core")], ["color", Q("FR4 natural")],
                  ["thickness", core], ["material", Q("FR4")], ["epsilon_r", 4.5], ["loss_tangent", 0.02]],
                 ["layer", Q("B.Cu"), ["type", Q("copper")], ["thickness", cu]],
                 ["layer", Q("B.Mask"), ["type", Q("Bottom Solder Mask")], ["color", Q("Black")], ["thickness", mask]],
                 ["layer", Q("B.Paste"), ["type", Q("Bottom Solder Paste")]],
                 ["layer", Q("B.SilkS"), ["type", Q("Bottom Silk Screen")], ["color", Q("White")]],
                 ["copper_finish", Q(FAB["order"]["finish"])],
                 ["dielectric_constraints", "no"]],
                ["pad_to_mask_clearance", r["solder_mask_expansion"]],
                ["solder_mask_min_width", r["solder_mask_min_width"]],
                ["allow_soldermask_bridges_in_footprints", "yes"],   # fine-pitch webs < 0.13 mm are ganged by the fab
                ["tenting", ["front", "yes"], ["back", "yes"]],
                ["aux_axis_origin", 0, 0], ["grid_origin", 0, 0]]

    def tree(self, title, rev, date):
        return ["kicad_pcb", ["version", 20260206], ["generator", Q("pcb_deck_generator")],
                ["generator_version", Q("10.0")],
                ["general", ["thickness", self.thickness], ["legacy_teardrops", "no"]],
                ["paper", Q("A4")],
                ["title_block", ["title", Q(title)], ["date", Q(date)], ["rev", Q(rev)],
                 ["company", Q("PCB_DESIGN_REFERENCE_DECK")]],
                ["layers", *[[n, Q(name), t, *[Q(a) for a in rest]] for n, name, t, *rest in LAYERS]],
                self.setup(), *self.items, ["embedded_fonts", "no"]]

    def save(self, path, title, rev, date):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dumps(self.tree(title, rev, date)) + "\n", encoding="utf-8", newline="\n")
        write_project(path.with_suffix(".kicad_pro"))


# Checks that do not make sense on reference cards (unconnected sample copper,
# library-footprint parity) are lowered; everything else keeps KiCad's default.
SEVERITY_OVERRIDES = {
    "lib_footprint_issues": "ignore",     # footprints copied verbatim from the installed library
    "lib_footprint_mismatch": "ignore",
    "track_dangling": "ignore",           # trace-width samples are intentionally open-ended
    "via_dangling": "ignore",             # via samples are intentionally unconnected
    "isolated_copper": "ignore",          # copper-pour samples are intentionally not tied to pads
    "silk_overlap": "error",              # readability: overlapping text must fail
    "silk_edge_clearance": "error",
    "text_height": "error",
    "text_thickness": "error",
}


def write_project(path):
    r = RULES
    pro = {
        "board": {"design_settings": {
            "rules": {
                "min_clearance": r["min_clearance"], "min_track_width": r["min_track_width"],
                "min_via_diameter": r["min_via_diameter"], "min_through_hole_diameter": r["min_through_hole"],
                "min_via_annular_width": r["min_annular_ring"], "min_hole_to_hole": r["min_hole_to_hole"],
                "min_hole_clearance": 0.2, "min_copper_edge_clearance": r["min_copper_edge_clearance"],
                "min_silk_clearance": r["min_silk_clearance"], "min_text_height": r["min_text_height"],
                "min_text_thickness": r["min_text_thickness"], "min_microvia_diameter": 0.2,
                "min_microvia_drill": 0.1, "min_connection": 0.0, "max_error": 0.005,
                "solder_mask_to_copper_clearance": 0.0, "min_resolved_spokes": 1,
            },
            "rule_severities": SEVERITY_OVERRIDES,
        }},
        "net_settings": {"classes": [{"name": "Default", "clearance": r["min_clearance"], "track_width": 0.2,
                                      "via_diameter": 0.6, "via_drill": 0.3, "diff_pair_gap": 0.2,
                                      "diff_pair_width": 0.2, "priority": 2147483647}],
                         "meta": {"version": 5}},
        "meta": {"filename": path.name, "version": 3},
    }
    path.write_text(json.dumps(pro, indent=2) + "\n", encoding="utf-8", newline="\n")


def rounded_rect_outline(b, w, h, r, layer="Edge.Cuts", lw=0.05):
    """Closed outline of straight lines + 90 deg arcs."""
    k = r * (1 - math.sqrt(0.5))
    b.line(r, 0, w - r, 0, layer, lw)
    b.line(w, r, w, h - r, layer, lw)
    b.line(w - r, h, r, h, layer, lw)
    b.line(0, h - r, 0, r, layer, lw)
    b.arc((w - r, 0), (w - k, k), (w, r), layer, lw)
    b.arc((w, h - r), (w - k, h - k), (w - r, h), layer, lw)
    b.arc((r, h), (k, h - k), (0, h - r), layer, lw)
    b.arc((0, r), (k, k), (r, 0), layer, lw)
