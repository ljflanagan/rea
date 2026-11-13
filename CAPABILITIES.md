# CAPABILITIES — what to adopt for single-family residential design

Phase 2 of the architect pipeline. Features are in priority order.

## Where this knowledge comes from

Phase 1 (`REA-INVENTORY.md`) found that this repository contains **no**
research on architecture software. So the column "what the repository shows"
that Phase 2 asked for reads the same for every feature: **nothing**. It is
stated once here rather than repeated in every row.

What follows instead rests on two things:

1. **Open standards**, which are the actual basis of the build: IFC 4
   (ISO 16739, buildingSMART), the DXF reference (Autodesk publishes it),
   glTF 2.0 (Khronos), and the US National CAD Standard / AIA layer naming.
2. **Each program's publicly documented concepts**, recalled from general
   knowledge of their user documentation. These were *not* verified against the
   software in this work, and no program's code or content was examined or
   reproduced. Treat the "who does it best" column as informed opinion.

The last column records what `architect/housegen` actually does today.

## Capability map

| # | Feature | Who does it best, and the documented idea | Open-standard form | In `housegen` today |
|---|---|---|---|---|
| 1 | **One model, many views** | Revit and ArchiCAD. Plans, sections, 3D and schedules are live views of one building database; nothing is drawn twice. | IFC: one product has several representations (`Axis`, `Body`) of the same entity. | Built. `model.json` is the source; DXF, sheets, glTF, OBJ, IFC, renders and the report are all derived. A final step re-opens each export and compares it with the model. |
| 2 | **Parametric walls** (thickness, length, height, joins) | Revit: a wall is a location line plus a type (thickness) plus base/top constraints; joins are butt, mitre or square-off. ArchiCAD: reference line plus priority-based junctions. | `IfcWall` with an axis curve and an extruded rectangle. | Built. Centerline, thickness, height, kind. Butt joins resolved at every end (corner, tee, cross), so solids neither overlap nor gap. **Orthogonal walls only.** |
| 3 | **Doors and windows hosted in walls** | Revit: hosted families cut their host and move with it. ArchiCAD and AutoCAD Architecture anchor openings to the wall the same way. | `IfcOpeningElement` + `IfcRelVoidsElement` (cuts the wall), `IfcDoor`/`IfcWindow` + `IfcRelFillsElement`. | Built. An opening stores host wall id and position along it; it cannot exist unhosted. The hole appears in plan, mesh and IFC from that one record. |
| 4 | **Automatic room detection with areas** | Chief Architect: rooms appear as soon as walls close. Revit: rooms are bounded by walls and *room separation lines*, with a choice of where area is measured. ArchiCAD: zones. AutoCAD Architecture: associative spaces. | `IfcSpace` + `Qto_SpaceBaseQuantities.NetFloorArea`. | Built. Rooms are the closed faces of the centerline graph, named by a seed point; net area is the face minus wall solids. Separation lines give open-plan rooms. Gross = outside face of exterior walls. |
| 5 | **Dimension strings on plans** | Chief Architect auto-generates exterior dimension strings; AutoCAD Architecture has AEC dimensions; Revit dimensions are associative to wall faces or centers. | DXF `DIMENSION` entities with a dimension style. | Built for exterior: up to three tiers per side (openings, partitions, overall), to outside face of exterior walls and centerlines of partitions and openings. Real DXF dimension entities. **No interior dimension strings** (room labels carry clear sizes). |
| 6 | **Hip and gable roofs** | Chief Architect: automatic roofs from the wall layout, hip by default, mark a wall for a gable. Revit: roof by footprint, each edge slope-defining or not. | `IfcRoof` (`HIP_ROOF`, `GABLE_ROOF`). | Built for **rectangular footprints**: pitch, overhang, fascia; gable ends closed with wall infill. Non-rectangular footprints get a warning. |
| 7 | **Export: DXF, IFC, glTF/OBJ, sheets** | AutoCAD for DXF/DWG fidelity; ArchiCAD and Revit for IFC; SketchUp's LayOut for turning model views into sheets. | DXF R2010; IFC4; glTF 2.0 binary; SVG and PDF. | Built: DXF (inches, AIA layers), IFC4, GLB, OBJ, SVG + PDF sheets, PNG renders and elevations. |
| 8 | **Code and area validation** | No program does this for a local baseline out of the box; Revit schedules and Chief Architect's plan check come closest. | — | Built: area vs target, wall/opening sanity, circulation, IRC screening checks (room size, egress, light and air, hall width), setbacks, flood freeboard, windstorm flags. |
| 9 | **Multi-level stacking** | Revit levels; ArchiCAD stories. Walls are constrained to levels and the building stacks. | `IfcBuildingStorey` with elevation. | Built but lightly tested: levels with elevation and height, one plan sheet and DXF per level, stacked 3D. Roof sits on the top level. |
| 10 | **Stairs** | Revit stair-by-component and Chief Architect both compute risers from floor-to-floor height under rise/run rules. | `IfcStair`. | Partial: straight run only, riser count from the 7¾ in. maximum, plan symbol, 3D steps, IRC R311.7 check. **No floor opening is cut above, no landings, no winders.** |
| 11 | **Layout generation from a program** | Not a strength of any of them; Chief Architect's room-first workflow is the nearest. | — | One template (`split_ranch`: one storey, 2–3 bed, 2 bath, 1,100–1,900 sq ft). Anything else is authored as a layout program by Claude and run through the same model. |

## Not adopted, and why

| Feature | Reason |
|---|---|
| SketchUp-style free surface modelling | No wall or room semantics, so no areas, schedules or code checks can be derived. |
| Layered wall assemblies (studs, sheathing, finishes as separate layers) | Concept stage needs nominal thickness only. Worth adding when quantities are wanted. |
| Plumbing fixtures, cabinets, furniture | Not modelled yet. This is the largest gap in how the plan reads; bathrooms and kitchen are sized as rooms only. |
| Structural, energy, electrical and plumbing design | Out of scope for a concept tool; listed in every report as items for the licensed professional. |
| DWG, RVT, PLN, SKP output | Proprietary formats. DXF and IFC import into all five programs. |

## How route 3 (studying the programs with REA) would add to this

REA can inspect an installed program and its files. With Revit, ArchiCAD,
SketchUp or Chief Architect on a machine REA can reach, the useful, legitimate
questions are about *interchange behaviour*, answered by exporting from the
program and reading the open-format result:

- Export a small test house to IFC and DXF from each program and compare the
  entity choices, layer names and units with what `housegen` writes.
- Import `model.ifc` and `floor-plan.dxf` into each program and record what
  arrives intact (walls as walls, openings hosted, spaces with areas).

Findings would go into the "In `housegen` today" column and into exporter fixes.
Nothing from a program's own code or content belongs in this repository.
