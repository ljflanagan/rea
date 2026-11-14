# Validation report: Plan 140-A: 2 Bed / 1 Bath Cottage

> **CONCEPT — NOT FOR CONSTRUCTION — requires validation by a licensed Texas architect/PE.**

Generated from `model.json`. Code baseline: Jefferson County / City of Beaumont, Texas: 2021 IRC, 2021 IPC, 2021 IECC, 2020 NEC, ICC 600-2020; TDI / TWIA windstorm certification (WPI-8).

## Result

**0 failures, 0 warnings, 23 checks passed.** 13 further items cannot be decided from a concept model and are listed for the design professional.

## Area against target

| Measure | Sq ft |
|---|---:|
| Target | 840 |
| Conditioned (living) area, to outside face of exterior walls | 840.0 |
| Difference from target | +0.0 (+0.0%) |
| Sum of net areas of conditioned rooms | 754.3 |
| Garage, porch and patio (excluded from living area) | 0.0 |
| Area occupied by walls | 85.7 |
| Total inside outside face of walls | 840.0 |

## Rooms

| Room | Type | Net area (sq ft) | Clear size |
|---|---|---:|---|
| Living | living | 238.1 | 15'-4" x 15'-6" |
| Kitchen + Dining | kitchen | 183.6 | 10'-4" x 13'-6" |
| Bedroom 1 | bedroom | 113.8 | 8'-10" x 11'-4" |
| Bedroom 2 | bedroom | 113.8 | 8'-10" x 11'-4" |
| Bath | bath | 41.1 | 7'-4" x 5'-8" |
| Hall | hall | 21.4 | 3'-10" x 5'-8" |
| Utility | utility | 19.9 | 4'-8" x 4'-4" |
| Closet 1 | closet | 11.3 | 2'-2" x 5'-4" |
| Closet 2 | closet | 11.3 | 2'-2" x 5'-4" |
| **Total, all rooms** | | **754.3** | |

Clear size is the largest rectangle that fits inside the room, so an L-shaped room has more area than its clear size implies.

## Site

| Item | Value |
|---|---|
| Lot | 50'-0" x 100'-0" = 5,000 SF |
| Setbacks (front / side / rear) | 25'-0" / 5'-0" / 25'-0" |
| Buildable area | 40'-0" x 50'-0" |
| House footprint | 28'-0" x 30'-0" |
| Yards: front / rear | 26'-0" / 44'-0" |
| Yards: left / right | 11'-0" / 11'-0" |
| Lot coverage | 16.8% |
| Finished floor above grade | 1'-0" |

## Checks

### Passed

| Area | Finding | Reference |
|---|---|---|
| Model | All 9 named rooms are enclosed and every enclosed space is named. |  |
| Area | Room areas reconcile: 754.3 sq ft of rooms + 85.7 sq ft of walls = 840.0 sq ft inside the outside face of the walls. |  |
| Area | Gross conditioned area 840 sq ft against the 840 sq ft target (+0.0%; tolerance 3%). Measured to the outside face of exterior walls. |  |
| Program | 2 bedrooms modelled, 2 requested. |  |
| Program | 1 bathrooms modelled, 1 requested. |  |
| Walls | Exterior walls form a closed loop; all 15 walls are joined at both ends with no overlaps. |  |
| Openings | All 15 openings sit inside their host wall, clear of wall junctions and of each other, with header room above. |  |
| Circulation | Every room can be reached from an exterior door. |  |
| IRC rooms | Every habitable room is at least 70 sq ft and 7 ft in its short direction. | 2021 IRC R304 |
| IRC rooms | Ceiling height 8'-0" meets the 7 ft minimum. | 2021 IRC R305.1 |
| IRC egress | Hall is 3'-9 3/4" clear (3 ft minimum). | 2021 IRC R311.6 |
| IRC egress | Egress door: D01, side-hinged, 3'-0" x 6'-8". | 2021 IRC R311.2 |
| IRC egress | Bedroom 1: N05 (3'-0" x 6'-0" single hung, sill 1'-0") gives an estimated 6.9 sq ft clear opening (33 x 30 in.); 5.7 sq ft, 20 in. wide, 24 in. high, sill 44 in. max required. | 2021 IRC R310.2 |
| IRC egress | Bedroom 2: N06 (3'-0" x 6'-0" single hung, sill 1'-0") gives an estimated 6.9 sq ft clear opening (33 x 30 in.); 5.7 sq ft, 20 in. wide, 24 in. high, sill 44 in. max required. | 2021 IRC R310.2 |
| IRC light and air | Bedroom 1: 18 sq ft glazing (15.8% of 114 sq ft floor; 8% required), 9 sq ft openable (7.9%; 4% required). | 2021 IRC R303.1 |
| IRC light and air | Bedroom 2: 18 sq ft glazing (15.8% of 114 sq ft floor; 8% required), 9 sq ft openable (7.9%; 4% required). | 2021 IRC R303.1 |
| IRC light and air | Living + Kitchen + Dining: 54 sq ft glazing (12.8% of 422 sq ft floor; 8% required), 27 sq ft openable (6.4%; 4% required). | 2021 IRC R303.1 |
| IRC light and air | Bath: 6 sq ft window (3 sq ft, half openable, required unless mechanically exhausted). | 2021 IRC R303.3 |
| Site | Walls are inside all setbacks: front 26'-0" (min 25'-0"), rear 44'-0" (min 25'-0"), left side 11'-0" (min 5'-0"), right side 11'-0" (min 5'-0"). |  |
| IRC fire separation | Walls are 11'-0" and eaves 10'-0" from the nearest side lot line; 5 ft or more needs no fire-resistance rating. | 2021 IRC R302.1 |
| Outputs agree | DXF re-read: room boundaries enclose 754.3 sq ft (model 754.3); 27 dimension entities. |  |
| Outputs agree | IFC re-read (IFC4): 15 walls, 15 openings, 8 doors, 7 windows, 9 spaces; space areas total 754.3 sq ft (model 754.3); wall volume with openings cut 571.9 cu ft (model 571.9). |  |
| Outputs agree | glTF re-read: 40 nodes, 1,202 triangles; walls span 28.00 x 30.00 ft (model 28.00 x 30.00). |  |

### For the design professional (not decidable from this model)

| Area | Finding | Reference |
|---|---|---|
| Area | The rooms alone sum to 754 sq ft net (90% of the target). The target is treated as gross area, which is how house size is normally quoted; say so if you meant net room area. |  |
| Site | Lot coverage 16.8% by walls, 19.2% under roof. No coverage limit was given in the spec; check the zoning district. |  |
| Flood | Spec states flood zone X, outside the special flood hazard area. Finished floor is modelled 1'-0" above grade. Confirm the zone on the current FEMA map and with the floodplain administrator before relying on this. | Jefferson County / City of Beaumont, Texas: BFE + 1 ft |
| Windstorm | Geometry for the engineer's ICC 600 applicability check: 1 storey, 28'-0" x 30'-0" plan, hip roof at 5:12, 1'-0" overhangs, mean roof height 11'-8" above grade. | ICC 600-2020 |
| Windstorm | 7 glazed openings totalling 96 sq ft (11% of exterior wall area), plus the exterior doors, need TDI-evaluated products rated for the site's design pressures, and impact protection if the lot is in the wind-borne debris region. The design wind speed and TDI zone for this address have not been established. | TDI / TWIA |
| Windstorm | A WPI-8 certificate depends on inspections by a TDI-appointed engineer or inspector during construction (foundation, framing, roofing, openings). It cannot be established from drawings; arrange the inspections before work starts. | TDI WPI-8 |
| Windstorm | Roof-to-wall and wall-to-foundation connections, sheathing nailing, braced wall lines and uplift load path are not modelled. | ICC 600-2020 |
| Code baseline | Code editions are the owner's standing baseline. A local news report says Beaumont City Council adopted the 2021 I-codes, 2020 NEC and ICC 600-2020 on April 4, 2023; local amendments were not reviewed, and unincorporated Jefferson County may differ from the City of Beaumont. | Jefferson County / City of Beaumont, Texas |
| Not modelled | Energy: insulation, window U-factor and SHGC, air sealing and duct design for climate zone 2A are not modelled. | 2021 IECC |
| Not modelled | Electrical: service, panel, receptacle spacing, GFCI and AFCI protection, smoke and carbon-monoxide alarms are not modelled. | 2020 NEC; 2021 IRC R314, R315 |
| Not modelled | Plumbing: fixture layout and clearances, water heater, drain-waste-vent and supply sizing are not modelled. Bathrooms are sized as rooms only. | 2021 IPC; 2021 IRC R307 |
| Not modelled | Structure: foundation, framing, headers, roof trusses and soils are not designed. Jefferson County clay soils normally call for an engineered slab. | 2021 IRC ch. 4-8 |
| Budget | Sale price $140,000 less the $20,000 lot and 21.8% for builder overhead, profit, sales and financing (NAHB 2024 national shares) leaves $89,480 to build with: $107 per sq ft of living area for this 840 sq ft house, with garage, porch, patio and site work paid from the same sum. No build cost per sq ft was given, so this is not judged. |  |

## Quantities for pricing

| Item | Quantity |
|---|---|
| Gross floor area | 840 SF |
| Slab / footprint area | 840 SF |
| Roof surface area | 1,040 SF |
| Exterior wall length | 114 ft |
| Interior partition length | 77 ft |
| Exterior doors | 2 |
| Interior doors | 6 |
| Windows | 7 (96 sq ft glazing incl. glazed doors) |
| Bathrooms / wet rooms | 1 baths + kitchen + laundry |

## Assumptions to confirm

- Prototype plan, not sited on a real lot. The 50 x 100 ft lot is the working minimum-lot assumption from BUDGET-MODEL.md; the minimum lot size has not been confirmed with the planning office.
- Setbacks of 25 ft front / 5 ft side / 25 ft rear are unconfirmed.
- Treated as outside the flood hazard area; a real lot needs its flood zone and elevations.
- Lot cost of $20,000 is a placeholder from a handful of Beaumont asking prices.

## Files

| File | What it is |
|---|---|
| `model.json` | The single source model: levels, walls, hosted openings, detected rooms, roof, site |
| `layout.json` | The layout program the model was built from; edit and re-run to revise the plan |
| `sheets.pdf` | All sheets, one per page |
| `sheet-A001-site.svg` | Sheet (SVG), with a PNG copy |
| `sheet-A101-floor-plan.svg` | Sheet (SVG), with a PNG copy |
| `sheet-A201-views.svg` | Sheet (SVG), with a PNG copy |
| `floor-plan.dxf` | 2D CAD plan, inches, AIA layers, DXF R2010 |
| `model.glb` | 3D model, glTF 2.0 binary, metres |
| `model.obj / model.mtl` | 3D model, Wavefront OBJ |
| `model.ifc` | BIM model, IFC4 |
| `render-*.png` | Renders of model.glb: perspectives and elevations |
| `validation-report.md / .json` | This report |

Code thresholds in this report are screening values applied to a concept model. They do not replace plan review or the judgement of a licensed architect or engineer.
