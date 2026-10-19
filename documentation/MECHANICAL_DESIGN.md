# Mechanical design

All values come from `project/mechanical_spec.toml`.

| item | value | basis |
|---|---|---|
| outline | 85.60 × 53.98 mm, corner radius 3.18 mm | ISO/IEC 7810 ID-1 nominal |
| thickness | 1.0 mm FR-4 | standard fab option (±10 %) |
| ring hole | Ø4.0 mm finished, plated, centred at (6.0, 6.0) from the front top-left | a copper barrel resists ring abrasion |
| ring pad | Ø7.0 mm, exposed ENIG on both sides | 1.5 mm annulus |
| hole-to-edge web | 4.0 mm (= 1 × hole diameter) | checked by `validate_boards.py` |
| ring keep-out | R 5.5 mm rule area | no other copper or text |
| margin | 1.6 mm from the edge for all text and graphics | |
| copper to edge | 0.5 mm (fab minimum 0.2) | |

The outline and ring hole are identical on all 15 cards. `validate_boards.py` checks this ("mechanical
consistency across cards"), so the deck stacks on one ring.

## Coordinate system

The origin is the top-left corner seen from the front; x runs right and y runs down (the KiCad convention). From
the back the ring hole is top-right. Back-side content is authored in a mirrored "view" (view x = 85.6 − board x)
and written with mirrored back silk, so it reads correctly when the card is turned over.

## Two-sided layout discipline

Each face is divided into reserved rectangles (panels). The generator fails with a `LayoutError` if two panels
overlap or any text overflows its panel. Anything with a hole (vias, PTH pads, NPTH) is visible on both faces,
so it must sit inside a *through region*: a panel reserved at the mirrored position on the other face as well.
`validate_boards.py` checks every hole against these regions ("plated holes inside through regions").

## Stack-up (assumed for all calculations)

| layer | thickness |
|---|---|
| solder mask | 0.01 mm |
| F.Cu | 0.035 mm (1 oz) |
| FR-4 core | 0.91 mm, εr = 4.5 **assumed**, tan δ = 0.02 |
| B.Cu | 0.035 mm |
| solder mask | 0.01 mm |

The impedance and wavelength numbers on cards 08 and 09 depend on εr. The fab's actual laminate value is not
known (see `UNRESOLVED_DECISIONS.md`).
