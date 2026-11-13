"""spec -> model -> every output. The only place outputs are orchestrated."""
import json
import os
import struct
import subprocess
from pathlib import Path

import ezdxf
from shapely.geometry import Polygon

from . import STAMP
from .export_dxf import write_dxf
from .export_gltf import write_glb, write_obj
from .export_ifc import verify_ifc, write_ifc
from .mesh import build_elements
from .model import build_model
from .plan2d import site_primitives
from .render import standard_views
from .sheets import plan_sheet, site_sheet, views_sheet, write_sheets
from .templates import generate_layout
from .units import FT_TO_M
from .validate import report_markdown, validate

HERE = Path(__file__).resolve().parent


def design(spec, out_root, quiet=False):
    say = (lambda *a: None) if quiet else print
    layout = spec.get("layout") or generate_layout(spec)
    b = build_model(spec, layout)
    out = Path(out_root) / spec["folder"]
    out.mkdir(parents=True, exist_ok=True)
    for old in out.iterdir():
        if old.is_file():
            old.unlink()
    report = validate(b, spec)
    say(f"model: {len(b.walls)} walls, {len(b.openings)} openings, {len(b.rooms)} rooms, "
        f"{b.gross_area():,.0f} sq ft gross")

    (out / "model.json").write_text(json.dumps(dict(b.to_dict(), notice=STAMP), indent=1))
    (out / "layout.json").write_text(json.dumps(layout, indent=1))

    # 2D: one sheet per level; the DXF is written from the same primitives
    sheets, plan_names = [], []
    multi = len(b.levels) > 1
    for i, lv in enumerate(sorted(b.levels, key=lambda l: l.elevation)):
        cv, prims, sc = plan_sheet(b, spec, lv.id, f"A-10{i + 1}")
        stem = f"floor-plan-{lv.id}" if multi else "floor-plan"
        extra = []
        if b.site and i == 0:
            extra = [p for p in site_primitives(b, sc) if p["layer"].startswith("C-") and p["type"] == "poly"]
        write_dxf(prims, out / f"{stem}.dxf", sc, f"{lv.name.upper()} PLAN" if multi else "FLOOR PLAN", extra)
        sheets.append((f"sheet-A10{i + 1}-{stem}", cv))
        plan_names.append(stem)

    # 3D
    elements = build_elements(b)
    stats = write_glb(elements, out / "model.glb", b.name)
    write_obj(elements, out / "model.obj", b.name)
    write_ifc(b, spec, out / "model.ifc")
    views = standard_views(b, elements, str(out))

    _consistency(b, out, plan_names, stats, report)
    report["counts"] = {k: sum(1 for c in report["checks"] if c["status"] == k)
                        for k in ("PASS", "WARN", "FAIL", "INFO")}

    if b.site:
        sheets.insert(0, ("sheet-A001-site", site_sheet(b, spec, report)))
    sheets.append(("sheet-A201-views", views_sheet(b, spec, views)))
    svgs = write_sheets(sheets, str(out))
    pngs = _rasterise(svgs)

    files = [("model.json", "The single source model: levels, walls, hosted openings, detected rooms, roof, site"),
             ("layout.json", "The layout program the model was built from; edit and re-run to revise the plan"),
             ("sheets.pdf", "All sheets, one per page")]
    files += [(Path(s).name, "Sheet (SVG)" + (", with a PNG copy" if pngs else "")) for s in svgs]
    files += [(f"{n}.dxf", "2D CAD plan, inches, AIA layers, DXF R2010") for n in plan_names]
    files += [("model.glb", "3D model, glTF 2.0 binary, metres"), ("model.obj / model.mtl", "3D model, Wavefront OBJ"),
              ("model.ifc", "BIM model, IFC4"), ("render-*.png", "Renders of model.glb: perspectives and elevations"),
              ("validation-report.md / .json", "This report")]
    (out / "validation-report.md").write_text(report_markdown(b, spec, report, files))
    (out / "validation-report.json").write_text(json.dumps(dict(report, notice=STAMP), indent=1))
    c = report["counts"]
    say(f"validation: {c['FAIL']} fail, {c['WARN']} warn, {c['PASS']} pass, {c['INFO']} info")
    say(f"outputs: {out}")
    return b, report, out


def _consistency(b, out, plan_names, stats, report):
    """Re-open each exported file and compare it with the model."""
    def add(status, msg):
        report["checks"].append({"category": "Outputs agree", "status": status, "message": msg, "ref": ""})
    net = sum(r.area for r in b.rooms)
    # DXF: room boundary polylines on A-AREA must enclose the same net area
    dxf_area = 0.0
    n_dims = 0
    for n in plan_names:
        doc = ezdxf.readfile(out / f"{n}.dxf")
        for e in doc.modelspace():
            if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "A-AREA":
                dxf_area += Polygon([(p[0] / 12, p[1] / 12) for p in e.get_points("xy")]).area
            elif e.dxftype() == "DIMENSION":
                n_dims += 1
    add("PASS" if abs(dxf_area - net) < 0.5 else "FAIL",
        f"DXF re-read: room boundaries enclose {dxf_area:,.1f} sq ft (model {net:,.1f}); "
        f"{n_dims} dimension entities.")
    # IFC
    v = verify_ifc(out / "model.ifc", b)
    ok = not v["mismatches"] and not v["schema_errors"] and abs(v["space_area_sqft"] - net) < 0.5 \
        and abs(v["wall_volume_cuft_ifc"] - v["wall_volume_cuft_model"]) < 1.0
    add("PASS" if ok else "FAIL",
        f"IFC re-read ({v['schema']}): {v['counts']['IfcWall']} walls, {v['counts']['IfcOpeningElement']} openings, "
        f"{v['counts']['IfcDoor']} doors, {v['counts']['IfcWindow']} windows, {v['counts']['IfcSpace']} spaces; "
        f"space areas total {v['space_area_sqft']:,.1f} sq ft (model {net:,.1f}); wall volume with openings cut "
        f"{v['wall_volume_cuft_ifc']:,.1f} cu ft (model {v['wall_volume_cuft_model']:,.1f})."
        + (" Problems: " + "; ".join(v["mismatches"] + v["schema_errors"]) if not ok else ""))
    # glTF: bounding box of the wall nodes must equal the footprint
    data = (out / "model.glb").read_bytes()
    jlen = struct.unpack("<I", data[12:16])[0]
    g = json.loads(data[20:20 + jlen])
    lo, hi = [1e9] * 3, [-1e9] * 3
    for node in g["nodes"]:
        if node["extras"]["category"] != "wall":
            continue
        acc = g["accessors"][g["meshes"][node["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
        lo = [min(a, c) for a, c in zip(lo, acc["min"])]
        hi = [max(a, c) for a, c in zip(hi, acc["max"])]
    x0, y0, x1, y1 = b.footprint().bounds
    gw, gd = (hi[0] - lo[0]) / FT_TO_M, (hi[2] - lo[2]) / FT_TO_M
    ok = abs(gw - (x1 - x0)) < 0.01 and abs(gd - (y1 - y0)) < 0.01
    add("PASS" if ok else "FAIL",
        f"glTF re-read: {stats['nodes']} nodes, {stats['triangles']:,} triangles; walls span "
        f"{gw:.2f} x {gd:.2f} ft (model {x1 - x0:.2f} x {y1 - y0:.2f}).")


def _rasterise(svgs):
    try:
        subprocess.run(["node", str(HERE / "svg2png.cjs"), "2400", *svgs], check=True, capture_output=True,
                       timeout=180, env=dict(os.environ))
        return [s[:-4] + ".png" for s in svgs]
    except Exception:
        return []
