"""Generate the native KiCad boards.

    python scripts/generate_boards.py            # all cards
    python scripts/generate_boards.py 1 2        # selected cards
    python scripts/generate_boards.py --no-fill  # skip kicad-cli zone refill
"""
import argparse
import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck.config import BOARDS, KICAD_CLI, W, board_by_id, board_dir, board_file  # noqa: E402
from deck.template import save  # noqa: E402


def refill_zones(path):
    """Let KiCad compute zone fills (and save) so Gerbers/previews contain the poured copper."""
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run([KICAD_CLI, "pcb", "drc", "--refill-zones", "--save-board", "-o",
                            str(Path(td) / "drc.rpt"), str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"zone refill failed for {path}:\n{r.stdout}\n{r.stderr}")


def build(card, fill=True):
    mod = importlib.import_module(f"deck.cards.{card['module']}")
    b = mod.build(card)
    save(b, card)
    meta = dict(b.meta)
    meta.pop("reserved", None)
    meta["reserved_panels"] = {s: [r[0] for r in rs] for s, rs in b.meta.get("reserved", {}).items()}
    # rectangles in BOARD coordinates (back view x mirrored back), used by validate_boards
    meta["reserved_rects"] = {s: [[n, *((x1, y1, x2, y2) if s == "F" else (W - x2, y1, W - x1, y2))]
                                  for n, x1, y1, x2, y2 in rs] for s, rs in b.meta.get("reserved", {}).items()}
    (board_dir(card) / "board_meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n",
                                                     encoding="utf-8")
    if fill:
        refill_zones(board_file(card))
    return board_file(card)


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", type=int)
    ap.add_argument("--no-fill", action="store_true")
    a = ap.parse_args(argv)
    cards = [board_by_id(i) for i in a.ids] if a.ids else BOARDS
    failed = 0
    for c in cards:
        try:
            print(f"[{c['id']:02d}] {build(c, not a.no_fill)}")
        except ModuleNotFoundError as e:
            print(f"[{c['id']:02d}] not implemented ({e.name})")
            failed += 1
        except Exception as e:  # report every card, fail at the end
            print(f"[{c['id']:02d}] FAILED: {e}")
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
