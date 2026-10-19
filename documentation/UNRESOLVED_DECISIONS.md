# Unresolved decisions and known limitations

Read this before ordering or before relying on a printed value.

## Data that still needs verification

- **Values marked SECONDARY** (see `SOURCES.md`): pinouts (USB 2.0, DE-9/TIA-574, Qwiic, ARM 10-pin SWD), logic
  thresholds, colour/marking codes, ISO screw and washer tables, solder alloys. These match widely published
  tables, but the primary documents were not read during development. Check each against its primary document
  and set the status to VERIFIED.
- **UNVERIFIED entries**: resistor power ratings by chip size (only a secondary copy of the Yageo datasheet was
  available) and the SOT-223 body (the KiCad footprint cites no drawing).
- **Fab capabilities** are one manufacturer's published values on one date (JLCPCB, 2026-10-19).

## Engineering assumptions

- **εr = 4.5** for the FR-4 core. Real laminates are about 4.0–4.6 and frequency-dependent. The 50 Ω microstrip
  (w = 1.67 mm), the 90/100 Ω differential pairs, the CPWG and every λg value on cards 08 and 09 change with
  εr. They are closed-form estimates (formula registry, status MODEL), not field-solver results and not measured
  TDR values. Order a controlled-impedance build or measure before relying on them.
- **Card 09 RF feed** (U.FL → π network → CPWG) is a land-pattern and layout reference. It is **not tuned**: no
  matching values are given, and no antenna on the deck has been measured.
- The card 09 RF line is kept **under solder mask**. Mask slightly lowers the impedance (about 1–2 Ω, not
  calculated here); it was chosen so that the exposed ground bands cannot bridge to the RF copper.
- The IPC-2221 current values (card 07) use the IPC-2221 curve fit for external layers. It is conservative and
  does not replace a thermal measurement or IPC-2152.

## Design choices that could be revisited

- **Solder-mask bridges inside fine-pitch footprints are allowed** (see `MANUFACTURING_GUIDE.md`). The
  alternative would be custom footprints with wider webs, which would no longer be the stock KiCad patterns the
  cards are meant to show.
- **Card 10 decoupling example**: the GND connection is a B.Cu track rather than vias, to keep holes out of the
  front panels. It is a demonstration route, not a recommended production layout.
- **Glyphs**: the KiCad stroke font renders `½` and `ℓ` poorly, so formulas use `/2` and `L` instead. Subscripts
  need a line pitch of at least 1.7 mm.
- **3D previews** (`output/documentation/previews`) are KiCad raytraced renders. Faint shapes from the opposite
  face can show through near the header. This is a render artefact and does not appear in the Gerbers.
- **No combined panel** is provided. Panelising needs separate validation (tab-routing for the round corners).

## Not done

- No physical sample has been made, so no printed dimension has been measured on a fabricated card.
- Content review by a second engineer (every card has the validation status REVIEW "content technical review").
