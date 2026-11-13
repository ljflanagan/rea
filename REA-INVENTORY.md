# REA-INVENTORY — Phase 1 findings

Surveyed 2026-11-13 at commit `f3d6f45`, all 7,477 tracked files.

## Headline

**This repository contains no architecture-software research.** It is a fork of
`morluto/rea` ("REA: Reverse Engineer Anything"), a general-purpose
reverse-engineering toolkit (a CLI and MCP server written in TypeScript). It is
the *tool* one would use to study a program, not the results of studying Revit,
ArchiCAD, AutoCAD Architecture, SketchUp or Chief Architect.

The inventory below therefore records what was searched for and not found. It
does not describe how those programs model buildings, because nothing in the
repository supports any such statement.

## What was searched

| Looked for | Result |
|---|---|
| Sample or export files: `.ifc .dxf .dwg .rvt .rfa .skp .pln .gltf .glb .obj` | None |
| Mentions of Revit, ArchiCAD, SketchUp, Chief Architect, IFC | None |
| Mentions of AutoCAD | One, as a DXF version name ("AutoCAD R12") in a save dialog |
| Mentions of DXF | 11 lines in 5 files, all about one test fixture (below) |
| Floor plans, walls, rooms, roofs, stairs, dimensioning, BIM | None |
| Decompiled logic or format notes for any architecture program | None |
| `CLAUDE.md` | Does not exist (the repo has `AGENTS.md`, which is about developing REA itself) |

The two other repositories in the workspace (`awesome-claude-code`,
`videoediting-claude-skill`) were also searched; neither has architecture content.

## The only CAD-adjacent content

A desktop-automation test scenario in which LibreCAD (an open-source 2D
drafting program) adds four holes to `plate.dxf`, and a comparison run in
VariCAD:

- `docs/desktop-application-tasks.md:65`
- `docs/specs/desktop-app-environments/tasks/verification.md:51`
- `docs/specs/desktop-app-environments/vendor-deb-files/verification.md:115-152`
- `.agents/skills/reverse-engineer-anything/references/environments.md:326`
- `src/domain/desktop/appTaskDraft.test.ts:101-112`

The one transferable observation: saving rewrote the file from DXF R12 to DXF
2007, and VariCAD's default is DXF 2004 — so a DXF exporter should state its
target version explicitly. The `plate.dxf` file itself is not in the repository.

## What the repository actually is

| Area | Contents |
|---|---|
| `src/` (≈3,500 files) | Analysis adapters: native binaries via Ghidra, IDA, Hopper, Kuna; JavaScript and Electron; .NET; Android (APK, JADX, apktool, adb); firmware; WASM; EVM; Flutter; IL2CPP; pcap; SQLite; desktop-application capture |
| `tests/` (≈2,500 files) | Tests and fixtures for the above |
| `docs/` | Guides per analysis type, MCP contracts, specs |
| `bridge/`, `native/`, `scripts/`, `website/` | Analyzer bridges, Windows helpers, build tooling, the rea.tools site |

## By concept

| Concept | What the repository shows |
|---|---|
| Walls (thickness, joins, layers) | Nothing |
| Hosted openings (doors, windows) | Nothing |
| Rooms and area calculation | Nothing |
| Roofs | Nothing |
| Stairs | Nothing |
| Levels / multi-storey stacking | Nothing |
| Annotation and dimensioning | Nothing |
| Plan and 3D views from one model | Nothing |
| File formats | DXF version naming only (see above) |

## Consequence for Phases 2–4

Phase 2 asks, for each feature, "what the repository shows about how it works."
The truthful answer for every feature is "nothing", so the capability map
cannot be sourced from this repository. The pipeline in Phase 3 can still be
built; it would have to rest on the open standards themselves (IFC 4 schema,
the DXF reference, glTF 2.0) and on the programs' publicly documented concepts,
and say so.
