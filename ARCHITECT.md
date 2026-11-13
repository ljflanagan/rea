# ARCHITECT — house specs in, plan + 3D model + validation out

When the owner says **"design a house with [specs]"**, run this pipeline end to
end. Everything comes from one model, so the plan and the 3D model cannot
disagree.

> Every output is stamped: **CONCEPT — NOT FOR CONSTRUCTION — requires
> validation by a licensed Texas architect/PE.** Never remove the stamp.

## Run it

```bash
cd architect
pip install -r requirements.txt          # once per fresh machine
python3 -m housegen design specs/<name>.yaml
```

Exit status is 1 if any check fails. Outputs go to
`architect/houses/<beds>bd<baths>ba-<sqft>sqft-<slug>/`, for example
`architect/houses/3bd2ba-1350sqft-jefferson/`. The folder is rewritten on each
run.

PNG copies of the sheets need Node with Playwright's Chromium. Without it the
pipeline still writes SVG and PDF and skips the PNGs.

## Procedure for Claude

1. **Read the spec. Ask before inventing.** The pipeline refuses to run
   without: target sq ft, beds, baths, lot width and depth, and front, side and
   rear setbacks. If the lot is not stated to be outside the flood zone, it
   also needs the base flood elevation and the grade elevation. Ask the owner
   for anything missing or ambiguous. Do not guess dimensions.
2. **Write `architect/specs/<folder-name>.yaml`** in the format below. Record
   anything the owner chose without a source document under `assumptions`.
3. **Run the pipeline.** If it prints `NO TEMPLATE FITS`, author a `layout:`
   block in the spec (format below) and run again.
4. **Read `validation-report.md`.** Fix every FAIL and every avoidable WARN by
   editing the layout, then re-run. Do not hand over a design with failures
   unless the owner's own constraints cause them, and say so if they do.
5. **Look at the sheets** (`sheet-A101-floor-plan.png`) before showing them.
6. **Show the owner** the floor plan sheet, the 3D model file and the
   validation report, and state the warnings and open assumptions plainly.

## Spec format

```yaml
project:
  name: 3 Bed / 2 Bath Residence, Jefferson County   # optional
  slug: jefferson              # last part of the output folder name

program:
  target_sqft: 1350            # gross, to outside face of exterior walls
  beds: 3
  baths: 2
  stories: 1

lot:
  width_ft: 60                 # along the street
  depth_ft: 117
  setbacks_ft: {front: 25, side: 5, rear: 25}
  flood: {zone: X}             # or {zone: AE, bfe_ft: 12.0, grade_ft: 10.5}
                               # Harris: {zone: AE, flood_500yr_ft: 98.0, grade_ft: 97.5}

budget:                        # see BUDGET-MODEL.md
  sale_price_usd: 200000       # lot included
  lot_cost_usd: 20000
  build_cost_per_sqft: 110     # optional; with it the report judges the budget

preferences:
  template: split_ranch        # only template so far
  primary_side: left           # or right (mirrors the plan)

# Optional overrides; these are the defaults.
construction: {ext_wall_in: 6.0, int_wall_in: 4.5, ceiling_ft: 9.0}
roof: {type: hip, pitch: 5, overhang_ft: 1.0}       # type: hip | gable
foundation: {type: slab-on-grade, floor_above_grade_ft: 1.0}
sheet: {size_in: [24, 18]}
code: {jurisdiction_id: jefferson}   # or harris; see "Code baselines"
assumptions:
  - Setbacks were chosen by the owner and not checked against the zoning ordinance.
```

### Code baselines

Each house follows the baseline of the place its lot is in. Set
`code.jurisdiction_id`; Jefferson is the default. Baselines live in
`architect/housegen/spec.py` (`BASELINES`). Every report prints the baseline's
"to confirm" list, because none of this was checked against ordinance text.

| | `jefferson` (default) | `harris` |
|---|---|---|
| Jurisdiction | Jefferson County / City of Beaumont | Harris County, unincorporated only |
| Codes | 2021 IRC, IPC, IECC; 2020 NEC; ICC 600-2020 | 2021 IRC, 2021 IECC, 2020 NEC as placeholders; edition unconfirmed |
| Windstorm | TDI/TWIA WPI-8 | WPI-8 only if the lot is in the designated area east of SH 146 |
| Flood rule | Floor 1 ft above base flood elevation | Floor 2 ft above the 500-year flood elevation (reported; unconfirmed) |
| Flood fields needed | `bfe_ft`, `grade_ft` | `flood_500yr_ft`, `grade_ft` |

A lot inside a city in Harris County (Houston, Pasadena, Katy and others)
follows that city's codes, which no baseline here covers. Ask the owner which
city or unincorporated area the lot is in.

### Authoring a layout

For programs the template does not cover, add `layout:` to the spec.
Coordinates are feet from the **outside face of the front-left corner**; x runs
along the street, y runs from the front (y = 0) to the rear.

```yaml
layout:
  footprint: {width: 45, depth: 30}       # exterior walls are generated from this
  walls:
    - {id: W-A, from: [13.5, 0], to: [13.5, 30]}            # partition centerline
    - {id: S-1, from: [13.5, 16], to: [31, 16], type: sep}  # room separation line
  rooms:
    - {name: Living, type: living, at: [22, 8]}             # seed point inside the room
  openings:
    - {id: D01, host: ext-front, at: 16.5, kind: door, width: 3.0, height: 6.6667,
       hinge: low, swing_into: Living}
    - {id: N01, host: ext-front, at: 6.5, kind: window, type: single_hung,
       width: 3.0, height: 6.0, sill: 1.0}
```

- Exterior hosts are `ext-front`, `ext-right`, `ext-back`, `ext-left`.
- `at` is the opening's centre: an x value on walls that run left-right, a y
  value on walls that run front-back.
- `hinge: low | high` is the jamb at the lower or higher coordinate.
- Room `type`: `bedroom`, `living`, `dining`, `kitchen`, `study`, `bath`,
  `closet`, `hall`, `utility`, `mech`, and the unconditioned types `garage`,
  `porch`, `patio`. Types drive the code checks. Garage, porch and patio sit
  inside the footprint but are excluded from living area; `target_sqft` is
  living area. Give a porch or patio its open side as a wide `cased` opening
  in the exterior wall.
- Door `type`: `swing`, `slider`, `bifold`, `overhead` (garage door). Window `type`: `single_hung`,
  `casement`, `slider`, `fixed`. `kind: cased` is a doorless opening.
- Multi-storey: use `layout.levels: [{id, name, elevation, height, walls,
  rooms, openings}, ...]` and `layout.stairs: [{id, level, origin, direction,
  width}]`.
- A generated layout is saved as `layout.json` in the output folder; copy it
  into a spec as the starting point for edits.

## Outputs

| File | Contents |
|---|---|
| `model.json` | The single source model: levels, walls with joins, hosted openings, detected rooms with areas, roof, site |
| `layout.json` | The layout program the model was built from |
| `sheets.pdf` | All sheets: A-001 site plan and schedules, A-101 floor plan, A-201 views and elevations |
| `sheet-*.svg`, `sheet-*.png` | The same sheets individually |
| `floor-plan.dxf` | 2D CAD plan: inches, AIA layer names, real dimension entities, DXF R2010 |
| `model.glb` | 3D model, glTF 2.0 binary, metres, Y up |
| `model.obj`, `model.mtl` | 3D model, Wavefront OBJ |
| `model.ifc` | BIM model, IFC4: storeys, walls, openings voiding walls, doors, windows, spaces with areas, slab, roof |
| `render-*.png` | Perspectives, a roof-off view, four elevations, all rendered from the same mesh as `model.glb` |
| `validation-report.md`, `.json` | Area vs target, geometry checks, code flags, quantities, assumptions |

## Conventions

From `REA-INVENTORY.md` and `CAPABILITIES.md`:

- **The REA repository holds no architecture research.** The pipeline is built
  on open standards (IFC 4, DXF, glTF 2.0, AIA layer names), not on any
  program's code. Do not claim otherwise.
- **One model, many views.** Never edit an output file by hand; change the spec
  or layout and re-run. New outputs must be derived from `Building`.
- **Walls** are axis-aligned centerlines with thickness and height. Exterior
  walls run counter-clockwise, so their left side is indoors.
- **Openings are hosted**: host wall id plus position along it.
- **Rooms are detected**, not drawn: closed faces of the wall graph, named by a
  seed point. `sep` walls bound rooms without building anything.
- **Area**: the target is gross area to the outside face of exterior walls.
  Room areas are net, inside finished wall faces.
- **Dimensions** run to the outside face of exterior walls and to centerlines
  of partitions and openings.
- **Units**: feet in the model, inches in DXF, metres in glTF, OBJ and IFC.
- **DXF** states its version explicitly (R2010), since programs differ in their
  defaults.
- **Validation statuses**: PASS, WARN, FAIL, and INFO for things a concept
  model cannot decide. Code thresholds are screening values, not plan review.

## Style

The owner wants production "contemporary" homes in the manner of Perry Homes.
[STYLE-PROFILE.md](STYLE-PROFILE.md) holds the program tables by lot width and
size, the ten layout patterns to follow, and the copyright boundary: design
original plans in the style, never copy one of their designs. No template
exists for this style yet, so author the layout for each spec.

## Known limits

- Orthogonal walls only; the roof generator needs a rectangular footprint.
- One layout template. Other programs need an authored layout.
- No plumbing fixtures, cabinets, furniture, structure, or MEP.
- Stairs are straight runs with no floor opening above; multi-storey is
  lightly tested.
- No interior dimension strings; no construction pricing.
- Window clear-opening sizes for egress are conservative estimates, not
  manufacturer data.
- The design wind speed and TDI zone for an address are not looked up.

## Route 3: studying the commercial programs with REA

Not done yet: it needs Revit, ArchiCAD, SketchUp or Chief Architect installed
on a machine REA can reach (share a folder from that computer through Remote
Control in the Claude desktop app). When available, export a test house from
each program to IFC and DXF, import this pipeline's `model.ifc` and
`floor-plan.dxf` into each, and record what survives in `CAPABILITIES.md`.
Study open-format behaviour only; do not copy any program's code or content.

## Code map

| File in `architect/housegen/` | Role |
|---|---|
| `spec.py` | Spec loading, defaults, required fields, code baseline |
| `templates.py` | Layout templates (`split_ranch`) |
| `model.py` | The building model: joins, room detection, opening sides |
| `plan2d.py` | Plan and site graphics, labels, dimension strings |
| `sheets.py` | Sheet composition, SVG and PDF writers |
| `export_dxf.py`, `export_gltf.py`, `export_ifc.py` | Exporters |
| `mesh.py`, `render.py` | 3D geometry and PNG renderer |
| `validate.py` | Checks and the report |
| `pipeline.py` | Orchestration and the outputs-agree checks |
