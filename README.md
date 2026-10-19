# PCB_DESIGN_REFERENCE_DECK

A collection of 15 credit-card-sized PCB reference cards for hardware engineers. They feature component
footprints, trace dimensions, PCB design rules, RF and antenna geometries, impedance calculations, electronic
formulas, package references and practical engineering tools. They are designed in KiCad for everyday use at the
electronics design bench.

Each card is a real, double-sided 2-layer board (85.60 × 53.98 × 1.0 mm, black mask, white silk, ENIG) with a
plated Ø4 mm ring hole, so all 15 stack on one ring. Land patterns are stock KiCad 10 library footprints, and
measurement features (rulers, track/space samples, drill gauge, annular rings, impedance coupons) are real
copper.

| # | card | # | card |
|---|---|---|---|
| 01 | PCB layout master | 09 | RF & antennas |
| 02 | SMD footprint master | 10 | Digital logic |
| 03 | QFP / BGA / fine pitch | 11 | Communication interfaces |
| 04 | Drill / via / mechanical | 12 | Component identification |
| 05 | Soldering & assembly | 13 | Test / debug |
| 06 | Analog design | 14 | PCB manufacturing & stack-up |
| 07 | Power & thermal | 15 | Formula master |
| 08 | Impedance / high speed | | |

Previews and per-card details: [documentation/BOARD_CATALOG.md](documentation/BOARD_CATALOG.md).

## Requirements

- KiCad 10 (`kicad-cli`). The default path is `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`; override it
  with the env `KICAD_CLI`. Footprints come from the KiCad library (override with `KICAD10_FOOTPRINT_DIR`).
- Python ≥ 3.11 (standard library only; `tomllib`).

Nothing calls an online service or an AI model at runtime.

## Usage

```
python tools/deck_manager.py build          # all cards: generate, fill zones, DRC, Gerbers, drills, previews, validate, docs
python tools/deck_manager.py build 9        # one card
python tools/deck_manager.py list           # DRC / validation status per card
python tools/deck_manager.py package        # output/packages/<card>.zip ready to upload to a fab
python tools/deck_manager.py test           # unit tests
```

The individual steps are `scripts/generate_boards.py`, `generate_manufacturing_files.py`,
`validate_boards.py` and `generate_documentation.py`.

## Layout

| path | content |
|---|---|
| `project/` | mechanical spec, design rules, fab constraints, graphic style, card list |
| `data/` | formula registry, package dimensions, engineering tables. Every entry has a source and a status |
| `scripts/deck/` | shared library: board writer, layout guard, graphics, engineering calculations; `cards/c01…c15` |
| `boards/<card>/` | generated KiCad project (`.kicad_pcb`, `.kicad_pro`, `board_meta.json`) |
| `output/` | Gerbers, drill files, DRC / validation reports, previews |
| `documentation/` | catalog, formulas, sources, validation report, manufacturing guide, mechanical design, unresolved decisions |
| `tests/` | `python -m unittest discover tests` |

## Data integrity

Values are not invented. Every printed table comes from `data/` with a cited source and a status (VERIFIED,
CROSS-CHECKED, SECONDARY, UNVERIFIED); see [SOURCES.md](documentation/SOURCES.md). Computed values (impedance,
IPC-2221 current, wavelengths, VSWR, via resistance) come from `scripts/deck/eng.py`, which is unit-tested.
Standards are cited, not reproduced. Impedance and RF numbers are closed-form estimates for an **assumed**
εr = 4.5. Read [UNRESOLVED_DECISIONS.md](documentation/UNRESOLVED_DECISIONS.md) before relying on them or
ordering.
