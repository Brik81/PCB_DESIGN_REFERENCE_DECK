"""DRC, Gerbers, drill files and previews for each card (kicad-cli).

    python scripts/generate_manufacturing_files.py              # everything, all cards
    python scripts/generate_manufacturing_files.py 1 2 --steps drc,preview

Outputs (one directory per card, never mixed):
    output/fabrication_reports/<card>/drc.json
    output/gerbers/<card>/*.gbr + job file
    output/drill_files/<card>/*.drl + map
    output/documentation/previews/<card>_{top,bottom}.png
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck.config import BOARDS, KICAD_CLI, ROOT, board_by_id, board_file  # noqa: E402

OUT = ROOT / "output"
LAYERS = "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts"
STEPS = ("drc", "gerbers", "drill", "preview")


def run(args):
    r = subprocess.run([KICAD_CLI, *map(str, args)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"kicad-cli {' '.join(map(str, args[:3]))} failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout


def drc(card):
    d = OUT / "fabrication_reports" / card["dir"]
    d.mkdir(parents=True, exist_ok=True)
    run(["pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", d / "drc.json",
         board_file(card)])
    rep = json.loads((d / "drc.json").read_text(encoding="utf-8"))
    n = {s: sum(1 for v in rep["violations"] if v["severity"] == s) for s in ("error", "warning")}
    n["unconnected"] = len(rep.get("unconnected_items", []))
    return n


def gerbers(card):
    d = OUT / "gerbers" / card["dir"]
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    run(["pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "-o", d, board_file(card)])
    return len(list(d.iterdir()))


def drill(card):
    d = OUT / "drill_files" / card["dir"]
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    run(["pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map",
         "--map-format", "pdf", "--excellon-units", "mm", "-o", str(d) + "/", board_file(card)])
    return len(list(d.iterdir()))


def preview(card):
    d = OUT / "documentation" / "previews"
    d.mkdir(parents=True, exist_ok=True)
    for side in ("top", "bottom"):
        run(["pcb", "render", "--side", side, "--quality", "high", "--use-board-stackup-colors",
             "--background", "opaque", "-w", 2400, "-h", 1560, "--zoom", 1.35,
             "-o", d / f"{card['dir']}_{side}.png", board_file(card)])
    return 2


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", type=int)
    ap.add_argument("--steps", default=",".join(STEPS))
    a = ap.parse_args(argv)
    steps = a.steps.split(",")
    cards = [board_by_id(i) for i in a.ids] if a.ids else BOARDS
    bad = 0
    for c in cards:
        if not board_file(c).exists():
            print(f"[{c['id']:02d}] missing board file")
            bad += 1
            continue
        res = {}
        for s in STEPS:
            if s in steps:
                try:
                    res[s] = globals()[s](c)
                except RuntimeError as e:
                    res[s] = f"FAILED {e}"
                    bad += 1
        if isinstance(res.get("drc"), dict) and (res["drc"]["error"] or res["drc"]["unconnected"]):
            bad += 1
        print(f"[{c['id']:02d}] {res}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
