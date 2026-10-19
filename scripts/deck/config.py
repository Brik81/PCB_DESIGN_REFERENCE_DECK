"""Shared configuration loaded from project/*.toml."""
import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "project"


def _load(name):
    with open(PROJECT / name, "rb") as fh:
        return tomllib.load(fh)


MECH = _load("mechanical_spec.toml")
STYLE = _load("graphic_style.toml")
RULES = _load("design_rules.toml")
FAB = _load("manufacturing_constraints.toml")
PROJECT_CFG = _load("project_config.toml")
BOARDS = PROJECT_CFG["board"]

W = MECH["card"]["width"]
H = MECH["card"]["height"]
KICAD_FP_DIR = Path(os.environ.get("KICAD10_FOOTPRINT_DIR", PROJECT_CFG["project"]["footprint_library"]))
KICAD_CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")


def board_dir(b):
    return ROOT / "boards" / b["dir"]


def board_file(b):
    return board_dir(b) / f"{b['dir']}.kicad_pcb"


def board_by_id(i):
    return next(b for b in BOARDS if b["id"] == int(i))


def data_table(name):
    """data/engineering_tables/<name>.toml"""
    with open(ROOT / "data" / "engineering_tables" / f"{name}.toml", "rb") as fh:
        return tomllib.load(fh)


with open(ROOT / "data" / "formulas" / "formulas.toml", "rb") as _fh:
    FORMULAS = tomllib.load(_fh)


def eq(key):
    """Printed equation text from the formula registry (single source for cards and docs)."""
    return FORMULAS[key]["eq"]
