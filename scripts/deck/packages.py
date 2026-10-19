"""Package data extracted from the official KiCad footprint library.

Land patterns are used verbatim. Body size = extents of the F.Fab outline,
which the KiCad library generators draw at nominal body size from the source
named in the footprint description (IPC-SM-782, JEDEC, vendor drawings).
"""
import math
import re
from functools import lru_cache

from .config import KICAD_FP_DIR
from .sexpr import find, first, loads

_URL = re.compile(r"https?://[^\s,)]+")


@lru_cache(maxsize=None)
def info(lib_name):
    lib, name = lib_name.split(":")
    node = loads((KICAD_FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod").read_text(encoding="utf-8"))
    descr = str((first(node, "descr") or [None, ""])[1])
    fab, crt = _layer_pts(node, "F.Fab"), _layer_pts(node, "F.CrtYd")
    pads = []
    for p in find(node, "pad"):
        at, size, dr = first(p, "at"), first(p, "size"), first(p, "drill")
        pads.append({"num": str(p[1]), "x": float(at[1]), "y": float(at[2]), "w": float(size[1]),
                     "h": float(size[2]), "rot": float(at[3]) if len(at) > 3 else 0.0, "type": p[2],
                     "drill": float(dr[1]) if dr and dr[1] != "oval" else float(dr[2]) if dr else None})
    nums = {p["num"] for p in pads if p["num"]}
    xs, ys = [x for x, _ in fab], [y for _, y in fab]
    pext = [(p["x"] - p["w"] / 2, p["y"] - p["h"] / 2, p["x"] + p["w"] / 2, p["y"] + p["h"] / 2) for p in pads
            if p["rot"] % 180 == 0] + [(p["x"] - p["h"] / 2, p["y"] - p["w"] / 2, p["x"] + p["h"] / 2,
                                        p["y"] + p["w"] / 2) for p in pads if p["rot"] % 180 != 0]
    return {
        "footprint": lib_name,
        "descr": descr,
        "urls": _URL.findall(descr),
        "body": (round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)) if fab else None,
        "pads": pads,
        "pins": len(nums),
        "pitch": _pitch(pads),
        "crtyd": (min(x for x, _ in crt), min(y for _, y in crt), max(x for x, _ in crt), max(y for _, y in crt)),
        "extent": (min(e[0] for e in pext), min(e[1] for e in pext), max(e[2] for e in pext), max(e[3] for e in pext)),
    }


def _layer_pts(node, layer):
    pts = []
    for c in node:
        if isinstance(c, list) and c and c[0] in ("fp_line", "fp_rect", "fp_poly", "fp_arc", "fp_circle") \
                and first(c, "layer")[1] == layer:
            if c[0] == "fp_circle":
                (cx, cy), (ex, ey) = [(float(first(c, k)[1]), float(first(c, k)[2])) for k in ("center", "end")]
                r = math.hypot(ex - cx, ey - cy)
                pts += [(cx - r, cy - r), (cx + r, cy + r)]
                continue
            for sub in c:
                if isinstance(sub, list) and sub and sub[0] in ("start", "end", "mid", "center"):
                    pts.append((float(sub[1]), float(sub[2])))
                if isinstance(sub, list) and sub and sub[0] == "pts":
                    pts += [(float(p[1]), float(p[2])) for p in sub[1:]]
    return pts


def _pitch(pads):
    """Smallest centre distance between equal-size neighbouring pads in a row (None for 2-pad parts)."""
    best = None
    for i, a in enumerate(pads):
        for b in pads[i + 1:]:
            if (a["w"], a["h"]) != (b["w"], b["h"]) or not a["num"] or not b["num"]:
                continue
            if abs(a["x"] - b["x"]) < 1e-6 or abs(a["y"] - b["y"]) < 1e-6:
                d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
                if d > 1e-6 and (best is None or d < best - 1e-6):
                    best = d
    return round(best, 3) if best and len([p for p in pads if p["num"]]) > 2 else None


def pad_size(lib_name, num=None):
    """Pad (w, h) as placed; default = first numbered pad (BGA balls are named e.g. 'A1')."""
    p = next(p for p in info(lib_name)["pads"] if (p["num"] == num if num else p["num"]))
    return (p["h"], p["w"]) if p["rot"] % 180 else (p["w"], p["h"])


@lru_cache(maxsize=None)
def registry():
    import tomllib
    from .config import ROOT
    with open(ROOT / "data" / "package_dimensions" / "packages.toml", "rb") as fh:
        return tomllib.load(fh)


def pkg(key):
    return next(p for p in registry()["pkg"] if p["key"] == key)
