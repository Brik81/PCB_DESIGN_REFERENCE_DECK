"""Deck Manager - offline front end for the whole pipeline (Python stdlib + kicad-cli only).

    python tools/deck_manager.py list                 # cards and their latest DRC / validation status
    python tools/deck_manager.py build [ids]          # generate boards, DRC, Gerbers, drills, previews, validate
    python tools/deck_manager.py docs                 # regenerate the data-driven documentation
    python tools/deck_manager.py package [ids]        # zip Gerbers + drills per card for upload to a fab
    python tools/deck_manager.py test                 # run the unit tests
"""
import argparse
import json
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from deck.config import BOARDS, board_by_id  # noqa: E402

REP = ROOT / "output" / "fabrication_reports"


def py(*args):
    print("$ python", *args, flush=True)
    return subprocess.run([sys.executable, *args], cwd=ROOT).returncode


def status(c):
    drc = REP / c["dir"] / "drc.json"
    val = REP / c["dir"] / "validation.json"
    d = "-"
    if drc.exists():
        j = json.loads(drc.read_text(encoding="utf-8"))
        d = f"{sum(v['severity'] == 'error' for v in j['violations'])}E/{len(j.get('unconnected_items', []))}U"
    v = dict(Counter(x["status"] for x in json.loads(val.read_text(encoding="utf-8")))) if val.exists() else "-"
    return d, v


def cards(ids):
    return [board_by_id(i) for i in ids] if ids else BOARDS


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["list", "build", "docs", "package", "test"])
    ap.add_argument("ids", nargs="*", type=int)
    a = ap.parse_args(argv)
    ids = [str(i) for i in a.ids]
    if a.cmd == "list":
        for c in cards(a.ids):
            d, v = status(c)
            print(f"{c['id']:02d}  {c['title']:<28} DRC {d:<7} {v}")
        return 0
    if a.cmd == "build":
        for step in (["scripts/generate_boards.py", *ids], ["scripts/generate_manufacturing_files.py", *ids],
                     ["scripts/validate_boards.py", *ids], ["scripts/generate_documentation.py"]):
            if py(*step):
                return 1
        return 0
    if a.cmd == "docs":
        return py("scripts/generate_documentation.py")
    if a.cmd == "test":
        return py("-m", "unittest", "discover", "tests")
    out = ROOT / "output" / "packages"
    out.mkdir(parents=True, exist_ok=True)
    for c in cards(a.ids):
        files = [p for sub in ("gerbers", "drill_files") for p in (ROOT / "output" / sub / c["dir"]).glob("*")
                 if p.suffix != ".pdf"]
        if not files:
            print(f"{c['dir']}: no fab files, run build first")
            continue
        z = out / f"{c['dir']}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
            for p in files:
                f.write(p, p.name)
        print(f"{z.relative_to(ROOT)}  ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
