# Manufacturing guide

Each card is a separate 2-layer board. Order them as 15 separate designs (or validate a panel first, see
"Panelisation"). Fabricator values below are from JLCPCB's published capabilities
(`project/manufacturing_constraints.toml`, read 2026-10-19). Other fabs differ, so re-confirm everything
before ordering.

## Files per card

| path | content |
|---|---|
| `output/gerbers/<card>/` | `<card>-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `job.gbrjob` |
| `output/drill_files/<card>/` | `<card>-PTH.drl`, `<card>-NPTH.drl` (Excellon, mm) and PDF drill maps |
| `output/fabrication_reports/<card>/` | `drc.json` (KiCad DRC), `validation.json` |

Zip the Gerber folder and the drill folder of one card together for upload.

## Order settings (every card)

| setting | value | why |
|---|---|---|
| layers | 2 | |
| thickness | 1.0 mm | stiff enough for a wallet card; stack-up assumed by the impedance numbers on cards 08 and 09 |
| copper | 1 oz outer | |
| solder mask | black | |
| silkscreen | white | |
| surface finish | **ENIG** | flat pads for the fine-pitch samples; it gives the gold accent. HASL works but makes the fine-pitch pads uneven |
| order number | none / specify location | the cards have no free space for one |
| mask bridges between pins | allowed / fab default | see "Solder-mask bridges" |

## Rules the boards were checked against

The rules in `project/design_rules.toml` are written into every `.kicad_pro` and are at or above the reference
fab's minimums. Track and space are 0.10 mm, the smallest via is 0.45/0.20 mm, and copper-to-edge clearance is
0.5 mm (the fab minimum is 0.2). Text is at least 1.0 mm high with a 0.15 mm stroke. Every card passes KiCad 10
DRC with these rules; the results are in `VALIDATION_REPORT.md`.

## Solder-mask bridges

The KiCad library footprints for fine-pitch parts (0.4–0.5 mm pitch QFN/QFP/WLCSP) have mask webs narrower than
the black-mask minimum of 0.13 mm. The project sets `allow_soldermask_bridges_in_footprints`, so KiCad accepts a
single ganged opening inside such a footprint. This is the normal fab behaviour: webs below the minimum are
removed. Outside footprints, no exposed (gold) opening ever touches copper of two different nets, and DRC
enforces this.

## Measurement features

The rulers, track-width and spacing samples and drill gauges are drawn at nominal size. After fabrication they
are subject to the fab's tolerances: etch about ±0.02–0.05 mm, PTH +0.13/−0.08 mm, outline ±0.2 mm. Measure a
sample card before trusting it for measurement.

## Panelisation

No combined panel is supplied. If you panelise (V-score or tab-route), validate the panel separately: the 3.18 mm
corner radius needs tab-routing, and V-score only gives square corners.

## Before ordering checklist

1. `python tools/deck_manager.py build` (or the individual scripts) finishes with 0 DRC errors.
2. Open each Gerber set in a viewer (KiCad GerbView or the fab's online viewer). Check the outline, the drill
   hits and that the back silk is mirrored.
3. Re-confirm the fab capabilities against the current fab website.
4. Read `UNRESOLVED_DECISIONS.md`.
