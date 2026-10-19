"""Validate generated cards straight from the .kicad_pcb files (independent of the generator).

    python scripts/validate_boards.py            # all cards, uses existing DRC reports
    python scripts/validate_boards.py 1 --drc    # (re)run KiCad DRC first

Result per check: PASS | FAIL | REVIEW (needs a human) | FAB (needs manufacturer confirmation).
Writes output/fabrication_reports/<card>/validation.json and prints a summary.
"""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck.config import BOARDS, H, MECH, RULES, ROOT, W, board_by_id, board_dir, board_file  # noqa: E402
from deck.sexpr import find, first, loads  # noqa: E402

TOL = 1e-3
REQUIRED_LAYERS = ["F.Cu", "B.Cu", "F.Mask", "B.Mask", "F.SilkS", "B.SilkS", "Edge.Cuts"]


def xy(node, head):
    n = first(node, head)
    return (float(n[1]), float(n[2])) if n else None


def outline(tree):
    segs = []
    for it in tree:
        if isinstance(it, list) and it and it[0] in ("gr_line", "gr_arc") and first(it, "layer")[1] == "Edge.Cuts":
            segs.append((xy(it, "start"), xy(it, "end"), xy(it, "mid")))
    return segs


def check_outline(segs):
    """Closed single loop: every endpoint shared by exactly two segments, all segments in one chain."""
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    deg = Counter()
    for s, e, _ in segs:
        deg[key(s)] += 1
        deg[key(e)] += 1
    if not segs or any(v != 2 for v in deg.values()):
        return False, f"open/branching outline: {[k for k, v in deg.items() if v != 2][:4]}"
    adj = {}
    for s, e, _ in segs:
        adj.setdefault(key(s), []).append(key(e))
        adj.setdefault(key(e), []).append(key(s))
    start = next(iter(adj))
    seen, stack = {start}, [start]
    while stack:
        for n in adj[stack.pop()]:
            if n not in seen:
                seen.add(n)
                stack.append(n)
    ok = len(seen) == len(adj)
    return ok, f"{len(segs)} segments, closed single loop" if ok else "multiple loops"


def bbox(segs):
    pts = [p for s in segs for p in s if p]
    # arcs: include extreme points of quarter arcs (mid already lies on arc); corners are 90 deg arcs
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def footprints(tree):
    for it in tree:
        if isinstance(it, list) and it and it[0] == "footprint":
            yield it


def validate(card, run_drc=False):
    res = []
    add = lambda name, status, detail="": res.append({"check": name, "status": status, "detail": detail})
    path = board_file(card)
    if not path.exists():
        add("board file exists", "FAIL", str(path))
        return res
    add("board file exists", "PASS", path.name)
    add("project file exists", "PASS" if path.with_suffix(".kicad_pro").exists() else "FAIL")
    tree = loads(path.read_text(encoding="utf-8"))

    # --- mechanical -----------------------------------------------------------
    segs = outline(tree)
    ok, msg = check_outline(segs)
    add("Edge.Cuts closed outline", "PASS" if ok else "FAIL", msg)
    x1, y1, x2, y2 = bbox(segs)
    add("width", "PASS" if abs((x2 - x1) - W) < TOL else "FAIL", f"{x2 - x1:.3f} mm (spec {W})")
    add("height", "PASS" if abs((y2 - y1) - H) < TOL else "FAIL", f"{y2 - y1:.3f} mm (spec {H})")
    add("origin at (0,0)", "PASS" if abs(x1) < TOL and abs(y1) < TOL else "FAIL", f"({x1:.3f},{y1:.3f})")
    th = float(first(first(tree, "general"), "thickness")[1])
    add("thickness", "PASS" if abs(th - MECH["card"]["thickness"]) < TOL else "FAIL", f"{th} mm")
    rh = MECH["ring_hole"]
    ring = [f for f in footprints(tree) if str(f[1]).endswith("RING_HOLE")]
    if len(ring) != 1:
        add("ring hole present", "FAIL", f"{len(ring)} found")
    else:
        f = ring[0]
        at = xy(f, "at")
        p = first(f, "pad")
        drill, size = float(first(p, "drill")[1]), float(first(p, "size")[1])
        add("ring hole position", "PASS" if math.dist(at, (rh["x"], rh["y"])) < TOL else "FAIL", f"{at}")
        add("ring hole diameter", "PASS" if abs(drill - rh["finished_diameter"]) < TOL else "FAIL",
            f"finished {drill} mm, {p[2]}")
        add("ring hole reinforcement pad", "PASS" if abs(size - rh["pad_diameter"]) < TOL and p[2] == "thru_hole"
            else "FAIL", f"plated annulus {(size - drill) / 2:.2f} mm")
        web = min(rh["x"], rh["y"]) - drill / 2
        add("ring hole edge web", "PASS" if web >= drill - TOL else "REVIEW", f"{web:.2f} mm laminate to edge")
    keep = [z for z in find(tree, "zone") if first(z, "keepout") and first(z, "name") and
            first(z, "name")[1] == "RING_HOLE_KEEPOUT"]
    add("ring hole keep-out", "PASS" if keep else "FAIL")

    # --- layers / content -----------------------------------------------------
    layers = {str(l[1]) for l in first(tree, "layers")[1:]}
    missing = [l for l in REQUIRED_LAYERS if l not in layers]
    add("required layers", "FAIL" if missing else "PASS", f"missing {missing}" if missing else "")
    texts = [t for t in find(tree, "gr_text")]
    per = Counter(str(first(t, "layer")[1]) for t in texts)
    add("front content", "PASS" if per["F.SilkS"] > 5 else "FAIL", f"{per['F.SilkS']} F.SilkS texts")
    add("back content", "PASS" if per["B.SilkS"] > 5 else "FAIL", f"{per['B.SilkS']} B.SilkS texts")
    small = []
    for t in texts:
        fnt = first(first(t, "effects"), "font")
        h, th_ = float(first(fnt, "size")[1]), float(first(fnt, "thickness")[1])
        if h < RULES["min_text_height"] - TOL or th_ < RULES["min_text_thickness"] - TOL:
            small.append(str(t[1])[:20])
    add("text height/stroke >= fab min", "FAIL" if small else "PASS",
        f"{len(texts)} texts, min {RULES['min_text_height']}/{RULES['min_text_thickness']} mm" +
        (f"; too small: {small[:5]}" if small else ""))
    back_mirror = [str(t[1])[:20] for t in texts if str(first(t, "layer")[1]).startswith("B.")
                   and "mirror" not in (first(first(t, "effects"), "justify") or [])]
    add("back text mirrored", "FAIL" if back_mirror else "PASS", ", ".join(back_mirror[:5]))

    # --- measurement features ---------------------------------------------------
    meta_p = board_dir(card) / "board_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    tracks = [(xy(s, "start"), xy(s, "end"), float(first(s, "width")[1]), str(first(s, "layer")[1]))
              for s in find(tree, "segment")]
    widths = Counter(round(w, 4) for *_, w, _ in tracks)
    if "trace_widths_mm" in meta:
        miss = [w for w in meta["trace_widths_mm"] if widths[round(w, 4)] == 0]
        add("trace-width samples present", "FAIL" if miss else "PASS", f"missing {miss}" if miss else
            f"{len(meta['trace_widths_mm'])} widths")
    if "spacings_mm" in meta:
        add("spacing samples geometry", *check_spacing(tracks, meta["spacings_mm"]))
    for r in meta.get("rulers", []):
        add(f"ruler {r['side']}.{r['unit']} tick positions", *check_ruler(tracks, r))
    if "vias_mm" in meta:
        have = {(round(float(first(v, "drill")[1]), 3), round(float(first(v, "size")[1]), 3)) for v in find(tree, "via")}
        miss = [v for v in meta["vias_mm"] if (round(v[0], 3), round(v[1], 3)) not in have]
        add("via samples present", "FAIL" if miss else "PASS", f"missing {miss}" if miss else f"{len(have)} sizes")
    if "drills_mm" in meta:
        add("drill samples present", *check_drills(tree, meta["drills_mm"]))
    if "reserved_rects" in meta:
        add("plated holes inside through regions", *check_through(tree, meta["reserved_rects"]))
    if "packages" in meta:
        placed = {str(f[1]) for f in footprints(tree)}
        miss = [p for p in meta["packages"] if p not in placed]
        add("library land patterns placed", "FAIL" if miss else "PASS", f"missing {miss}" if miss else
            f"{len(meta['packages'])} footprints")
    if meta.get("rulers") or meta.get("trace_widths_mm") or meta.get("drills_mm"):
        add("fabricated measurement accuracy", "FAB",
            "nominal geometry verified; etch (+/-~0.02-0.05 mm), drill (+0.13/-0.08) and outline (+/-0.2) "
            "tolerances apply - measure a sample card")

    # --- DRC ------------------------------------------------------------------
    rep = ROOT / "output" / "fabrication_reports" / card["dir"] / "drc.json"
    if run_drc:
        sys.path.insert(0, str(Path(__file__).parent))
        from generate_manufacturing_files import drc
        drc(card)
    if rep.exists():
        d = json.loads(rep.read_text(encoding="utf-8"))
        sev = Counter(v["severity"] for v in d["violations"])
        un = len(d.get("unconnected_items", []))
        st = "PASS" if not sev["error"] and not un else "FAIL"
        add("KiCad DRC", st, f"{sev['error']} errors, {sev['warning']} warnings, {un} unconnected "
                             f"(kicad {d.get('kicad_version', '?')}, {d.get('date', '')})")
        if sev["error"] or un:
            types = Counter(v["type"] for v in d["violations"] if v["severity"] == "error")
            res[-1]["detail"] += f"; {dict(types)}"
    else:
        add("KiCad DRC", "REVIEW", "not run yet (use --drc)")
    add("content technical review", "REVIEW", "DRC does not prove formulas, pinouts or footprints correct")
    return res


def check_spacing(tracks, spacings):
    """For each spacing value, find two parallel horizontal tracks whose edge gap equals it."""
    hz = [(s[1], w, min(s[0], e[0]), max(s[0], e[0])) for s, e, w, _ in tracks if abs(s[1] - e[1]) < TOL]
    found = []
    for want in spacings:
        ok = any(abs(abs(a[0] - b[0]) - (a[1] + b[1]) / 2 - want) < TOL and abs(a[2] - b[2]) < TOL
                 for i, a in enumerate(hz) for b in hz[i + 1:])
        found.append(ok)
    miss = [s for s, ok in zip(spacings, found) if not ok]
    return ("FAIL" if miss else "PASS", f"missing gaps {miss}" if miss else f"{len(spacings)} edge-to-edge gaps exact")


def check_ruler(tracks, r):
    layer = f"{r['side']}.Cu"
    xs = sorted({round(s[0], 4) for s, e, w, l in tracks if l == layer and abs(s[0] - e[0]) < TOL})
    sign = 1 if r["side"] == "F" else -1
    want = [round(r["x0"] + sign * p, 4) for p in r["positions"]]
    miss = [w for w in want if not any(abs(w - x) < TOL for x in xs)]
    span = abs(want[-1] - want[0])
    return ("FAIL" if miss else "PASS",
            f"{len(want)} ticks, span {span:.3f} mm" + (f", missing {miss[:4]}" if miss else ""))


def check_through(tree, rects):
    """Vias and drilled pads show on both faces, so each must sit in a region reserved on both faces."""
    thru = [r[1:] for side in ("F", "B") for r in rects.get(side, []) if "(through)" in r[0] or r[0] == "ring hole"]
    holes = [xy(v, "at") for v in find(tree, "via")]
    for f in footprints(tree):
        fx, fy = xy(f, "at")
        a = math.radians(float((first(f, "at") + [0])[3]) if len(first(f, "at")) > 3 else 0.0)
        for p in find(f, "pad"):
            if first(p, "drill"):
                px, py = xy(p, "at")          # pad offset rotates with the footprint (KiCad: clockwise y-down)
                holes.append((fx + px * math.cos(a) + py * math.sin(a), fy - px * math.sin(a) + py * math.cos(a)))
    out = [(round(x, 2), round(y, 2)) for x, y in holes
           if not any(x1 - TOL <= x <= x2 + TOL and y1 - TOL <= y <= y2 + TOL for x1, y1, x2, y2 in thru)]
    return ("FAIL" if out else "PASS", f"outside: {out[:4]}" if out else f"{len(holes)} holes in {len(thru)} regions")


def check_drills(tree, drills):
    have = set()
    for f in footprints(tree):
        for p in find(f, "pad"):
            d = first(p, "drill")
            if d:
                have.add(round(float(d[-1] if d[1] != "oval" else d[2]), 3))
    for v in find(tree, "via"):
        have.add(round(float(first(v, "drill")[1]), 3))
    miss = [d for d in drills if round(d, 3) not in have]
    return ("FAIL" if miss else "PASS", f"missing {miss}" if miss else f"{len(drills)} sizes present")


def consistency(cards):
    """All cards must share an identical outline and ring hole."""
    sigs = {}
    for c in cards:
        if board_file(c).exists():
            t = loads(board_file(c).read_text(encoding="utf-8"))
            ring = [xy(f, "at") for f in footprints(t) if str(f[1]).endswith("RING_HOLE")]
            sigs[c["dir"]] = (tuple(sorted((s, e, m) for s, e, m in outline(t))), tuple(ring))
    uniq = set(sigs.values())
    return {"check": "mechanical consistency across cards", "status": "PASS" if len(uniq) == 1 else "FAIL",
            "detail": f"{len(sigs)} boards, {len(uniq)} distinct outline/hole signature(s)"}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", type=int)
    ap.add_argument("--drc", action="store_true", help="run KiCad DRC before validating")
    a = ap.parse_args(argv)
    cards = [board_by_id(i) for i in a.ids] if a.ids else BOARDS
    total = Counter()
    for c in cards:
        res = validate(c, a.drc)
        out = ROOT / "output" / "fabrication_reports" / c["dir"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "validation.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        cnt = Counter(r["status"] for r in res)
        total.update(cnt)
        print(f"[{c['id']:02d}] {dict(cnt)}")
        for r in res:
            if r["status"] == "FAIL":
                print(f"      FAIL {r['check']}: {r['detail']}")
    cons = consistency(BOARDS)
    print(f"[all] {cons['check']}: {cons['status']} ({cons['detail']})")
    (ROOT / "output" / "fabrication_reports" / "consistency.json").write_text(json.dumps(cons, indent=1) + "\n")
    print(f"TOTAL {dict(total)}")
    return 1 if total["FAIL"] or cons["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
