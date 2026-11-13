# CLAUDE.md

Rules for developing REA itself are in [AGENTS.md](AGENTS.md). This file adds
one workspace capability that is separate from REA.

## Architect pipeline: "design a house with [specs]"

When the owner asks to design a house from specifications, follow
[ARCHITECT.md](ARCHITECT.md) and run the pipeline end to end:

```bash
cd architect && pip install -r requirements.txt   # once per fresh machine
python3 -m housegen design specs/<name>.yaml
```

- Write the spec to `architect/specs/` in the format ARCHITECT.md gives.
- Outputs land in `architect/houses/<beds>bd<baths>ba-<sqft>sqft-<slug>/`:
  dimensioned floor plan (DXF, SVG, PDF, PNG), 3D model (GLB, OBJ, IFC),
  renders, and `validation-report.md`. All come from one `model.json`.
- **Ask, do not invent**: lot width and depth, setbacks, and flood data must
  come from the owner. The pipeline refuses to run without them.
- Standing code baseline unless a spec overrides it: Jefferson County /
  Beaumont, TX — 2021 IRC/IPC/IECC, 2020 NEC, ICC 600-2020, TDI/TWIA windstorm
  (WPI-8), finished floor 1 ft above base flood elevation. For a lot in
  unincorporated Harris County set `code.jurisdiction_id: harris`; ask which
  county and city the lot is in if the owner has not said.
- Style: the owner wants homes in the manner of Perry Homes. Follow
  [STYLE-PROFILE.md](STYLE-PROFILE.md): original layouts using its patterns,
  never a copy of one of their plans.
- Every sheet and file carries the stamp "CONCEPT — NOT FOR CONSTRUCTION —
  requires validation by a licensed Texas architect/PE." Never remove it.
- Fix validation failures by editing the spec or layout and re-running; never
  edit output files by hand.
- Background: [REA-INVENTORY.md](REA-INVENTORY.md) (this repository holds no
  architecture-software research) and [CAPABILITIES.md](CAPABILITIES.md)
  (feature map and what is built).
