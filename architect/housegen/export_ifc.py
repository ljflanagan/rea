"""IFC4 export of the model (open BIM exchange, ISO 16739).

Semantic entities, not just triangles: storeys, walls as extrusions with an
axis, openings that void their host wall, doors and windows that fill those
openings, spaces carrying net floor area, a floor slab and a roof.
Lengths are metres.
"""
import uuid

import ifcopenshell
import ifcopenshell.guid

from . import STAMP
from .mesh import MATERIALS, roof_elements, stair_element
from .units import FT_TO_M as M

NS = uuid.UUID("6f1c2f0e-3b1d-4b7a-9d55-2a1f0c8e7a11")


class Writer:
    def __init__(self, b, spec):
        self.b, self.spec = b, spec
        self.f = ifcopenshell.file(schema="IFC4")
        self.styles = {}

    def guid(self, key):
        return ifcopenshell.guid.compress(uuid.uuid5(NS, self.b.name + "|" + key).hex)

    # ---- geometry helpers ---------------------------------------------
    def p3(self, x, y, z):
        return self.f.createIfcCartesianPoint((float(x) * M, float(y) * M, float(z) * M))

    def p2(self, x, y):
        return self.f.createIfcCartesianPoint((float(x) * M, float(y) * M))

    def axis(self, origin=(0, 0, 0), z=(0.0, 0.0, 1.0), x=(1.0, 0.0, 0.0)):
        f = self.f
        return f.createIfcAxis2Placement3D(self.p3(*origin), f.createIfcDirection(tuple(map(float, z))),
                                           f.createIfcDirection(tuple(map(float, x))))

    def place(self, rel, origin=(0, 0, 0), x=(1.0, 0.0, 0.0)):
        return self.f.createIfcLocalPlacement(rel, self.axis(origin, x=x))

    def extrude(self, profile, height, origin=(0, 0, 0)):
        f = self.f
        return f.createIfcExtrudedAreaSolid(profile, self.axis(origin), f.createIfcDirection((0.0, 0.0, 1.0)),
                                            float(height) * M)

    def rect_profile(self, cx, cy, xdim, ydim):
        f = self.f
        pos = f.createIfcAxis2Placement2D(self.p2(cx, cy), f.createIfcDirection((1.0, 0.0)))
        return f.createIfcRectangleProfileDef("AREA", None, pos, float(xdim) * M, float(ydim) * M)

    def poly_profile(self, pts):
        f = self.f
        loop = [self.p2(*p) for p in pts]
        return f.createIfcArbitraryClosedProfileDef("AREA", None, f.createIfcPolyline(loop + [loop[0]]))

    def brep(self, polys, dz=0.0):
        f = self.f
        cache, faces = {}, []

        def pt(p):
            k = (round(p[0], 5), round(p[1], 5), round(p[2] - dz, 5))
            if k not in cache:
                cache[k] = self.p3(*k)
            return cache[k]
        for poly in polys:
            loop = f.createIfcPolyLoop([pt(p) for p in poly])
            faces.append(f.createIfcFace([f.createIfcFaceOuterBound(loop, True)]))
        return f.createIfcFacetedBrep(f.createIfcClosedShell(faces))

    def shape(self, items, material, rep_type="SweptSolid"):
        f = self.f
        if material not in self.styles:
            r, g, b_, a = MATERIALS[material]
            shading = f.createIfcSurfaceStyleShading(f.createIfcColourRgb(None, r, g, b_), 1.0 - a)
            self.styles[material] = f.createIfcSurfaceStyle(material, "BOTH", [shading])
        for it in items:
            f.createIfcStyledItem(it, [self.styles[material]], None)
        rep = f.createIfcShapeRepresentation(self.body, "Body", rep_type, items)
        return rep

    def product_shape(self, reps):
        return self.f.createIfcProductDefinitionShape(None, None, reps)

    def pset(self, obj, name, props):
        f = self.f
        vals = []
        for k, v in props.items():
            if isinstance(v, bool):
                nv = f.create_entity("IfcBoolean", v)
            elif isinstance(v, (int, float)):
                nv = f.create_entity("IfcReal", float(v))
            else:
                nv = f.create_entity("IfcLabel", str(v))
            vals.append(f.createIfcPropertySingleValue(k, None, nv, None))
        ps = f.createIfcPropertySet(self.guid(f"pset|{obj.GlobalId}|{name}"), None, name, None, vals)
        f.createIfcRelDefinesByProperties(self.guid(f"relp|{obj.GlobalId}|{name}"), None, None, None, [obj], ps)

    # ---- build ----------------------------------------------------------
    def write(self, path):
        f, b, spec = self.f, self.b, self.spec
        units = f.createIfcUnitAssignment([
            f.createIfcSIUnit(None, "LENGTHUNIT", None, "METRE"),
            f.createIfcSIUnit(None, "AREAUNIT", None, "SQUARE_METRE"),
            f.createIfcSIUnit(None, "VOLUMEUNIT", None, "CUBIC_METRE"),
            f.createIfcSIUnit(None, "PLANEANGLEUNIT", None, "RADIAN")])
        ctx = f.createIfcGeometricRepresentationContext(None, "Model", 3, 1e-5, self.axis(), None)
        self.body = f.createIfcGeometricRepresentationSubContext("Body", "Model", None, None, None, None, ctx,
                                                                 None, "MODEL_VIEW", None)
        self.axis_ctx = f.createIfcGeometricRepresentationSubContext("Axis", "Model", None, None, None, None, ctx,
                                                                     None, "GRAPH_VIEW", None)
        project = f.createIfcProject(self.guid("project"), None, b.name, STAMP, None, None, None, [ctx], units)
        site_pl = self.place(None)
        site = f.createIfcSite(self.guid("site"), None, "Lot", spec["code"]["jurisdiction"], None, site_pl, None,
                               None, "ELEMENT", None, None, None, None, None)
        bld_pl = self.place(site_pl)
        building = f.createIfcBuilding(self.guid("building"), None, b.name, STAMP, None, bld_pl, None, None,
                                       "ELEMENT", None, None, None)
        f.createIfcRelAggregates(self.guid("agg-project"), None, None, None, project, [site])
        f.createIfcRelAggregates(self.guid("agg-site"), None, None, None, site, [building])
        if b.site:
            self.pset(site, "Housegen_Site", {
                "LotWidth_ft": b.site.lot_width, "LotDepth_ft": b.site.lot_depth,
                "SetbackFront_ft": b.site.setbacks["front"], "SetbackSide_ft": b.site.setbacks["side"],
                "SetbackRear_ft": b.site.setbacks["rear"],
                "FinishedFloorAboveGrade_ft": b.site.floor_above_grade, "Notice": STAMP})

        storeys = []
        fag = b.site.floor_above_grade if b.site else 1.0
        levels = sorted(b.levels, key=lambda l: l.elevation)
        for i, lv in enumerate(levels):
            st_pl = self.place(bld_pl, (0, 0, lv.elevation))
            storey = f.createIfcBuildingStorey(self.guid("storey" + lv.id), None, lv.name, None, None, st_pl, None,
                                               None, "ELEMENT", float(lv.elevation) * M)
            storeys.append(storey)
            contained, spaces = [], []

            # floor slab
            thick = fag if i == 0 else 1.0
            g = b.gross_polygon(lv.id)
            solid = self.extrude(self.poly_profile(list(g.exterior.coords)[:-1]), thick)
            slab = f.createIfcSlab(self.guid("slab" + lv.id), None, f"Floor {lv.name}", None, None,
                                   self.place(st_pl, (0, 0, -thick)),
                                   self.product_shape([self.shape([solid], "slab")]), None,
                                   "BASESLAB" if i == 0 else "FLOOR")
            contained.append(slab)

            for w in b.walls_on(lv.id):
                L = w.u1 - w.u0
                wpl = self.place(st_pl, (*w.pt(w.u0), 0), x=(w.dir[0], w.dir[1], 0.0))
                solid = self.extrude(self.rect_profile(L / 2, 0, L, w.thickness), w.height)
                axis = f.createIfcShapeRepresentation(self.axis_ctx, "Axis", "Curve2D",
                                                      [f.createIfcPolyline([self.p2(0, 0), self.p2(L, 0)])])
                mat = "wall_ext" if w.kind == "ext" else "wall_int"
                wall = f.createIfcWall(self.guid("wall" + w.id), None, w.id, None, None, wpl,
                                       self.product_shape([axis, self.shape([solid], mat)]), w.id,
                                       "STANDARD" if w.kind == "ext" else "PARTITIONING")
                self.pset(wall, "Pset_WallCommon", {"IsExternal": w.kind == "ext", "LoadBearing": w.kind == "ext",
                                                    "Reference": f"{w.thickness * 12:g} in. nominal"})
                contained.append(wall)
                for o in b.openings_in(w.id):
                    eps = 0.05
                    opl = self.place(wpl, (o.ua - w.u0, 0, o.sill))
                    void = self.extrude(self.rect_profile(o.width / 2, 0, o.width, w.thickness + 2 * eps),
                                        min(o.height, w.height - o.sill))
                    op = f.createIfcOpeningElement(self.guid("void" + o.id), None, f"Opening {o.id}", None, None,
                                                   opl, self.product_shape([self.shape([void], "frame")]), None,
                                                   "OPENING")
                    f.createIfcRelVoidsElement(self.guid("relvoid" + o.id), None, None, None, wall, op)
                    if o.kind == "cased":
                        continue
                    glazed = o.kind == "window" or o.type == "slider"
                    panel = self.extrude(self.rect_profile(o.width / 2, 0, o.width, 0.08 if glazed else 0.146),
                                         o.height)
                    shp = self.product_shape([self.shape([panel], "glass" if glazed else "door")])
                    fpl = self.place(opl)
                    if o.kind == "door":
                        el = f.create_entity("IfcDoor", GlobalId=self.guid("door" + o.id), Name=o.id,
                                             ObjectPlacement=fpl, Representation=shp, Tag=o.id,
                                             OverallHeight=o.height * M, OverallWidth=o.width * M,
                                             PredefinedType="DOOR",
                                             OperationType={"swing": "SINGLE_SWING_LEFT", "slider": "SLIDING_TO_LEFT",
                                                            "bifold": "FOLDING_TO_LEFT"}.get(o.type, "NOTDEFINED"))
                        self.pset(el, "Pset_DoorCommon", {"IsExternal": o.exterior, "Reference": o.type})
                    else:
                        el = f.create_entity("IfcWindow", GlobalId=self.guid("window" + o.id), Name=o.id,
                                             ObjectPlacement=fpl, Representation=shp, Tag=o.id,
                                             OverallHeight=o.height * M, OverallWidth=o.width * M,
                                             PredefinedType="WINDOW",
                                             PartitioningType={"single_hung": "DOUBLE_PANEL_HORIZONTAL",
                                                               "slider": "DOUBLE_PANEL_VERTICAL"}.get(o.type, "SINGLE_PANEL"))
                        self.pset(el, "Pset_WindowCommon", {"IsExternal": True, "Reference": o.type})
                    f.createIfcRelFillsElement(self.guid("relfill" + o.id), None, None, None, op, el)
                    contained.append(el)

            for n, r in enumerate(b.rooms_on(lv.id), 1):
                solid = self.extrude(self.poly_profile(list(r.net.exterior.coords)[:-1]), lv.height)
                sp = f.createIfcSpace(self.guid("space" + lv.id + r.name), None, f"{i + 1}{n:02d}", None, r.kind,
                                      self.place(st_pl), self.product_shape([self.shape([solid], "floor")]),
                                      r.name, "ELEMENT", "INTERNAL", None)
                q = [f.createIfcQuantityArea("NetFloorArea", None, None, r.area * M * M, None),
                     f.createIfcQuantityLength("Height", None, None, lv.height * M, None)]
                eq = f.createIfcElementQuantity(self.guid("qto" + lv.id + r.name), None, "Qto_SpaceBaseQuantities",
                                                None, None, q)
                f.createIfcRelDefinesByProperties(self.guid("relq" + lv.id + r.name), None, None, None, [sp], eq)
                self.pset(sp, "Housegen_Space", {"NetFloorArea_sqft": round(r.area, 2), "RoomType": r.kind})
                spaces.append(sp)

            for s in (s for s in b.stairs if s.level == lv.id):
                el = stair_element(b, s)
                boxes = [self.brep(el.polys[k:k + 6], dz=lv.elevation) for k in range(0, len(el.polys), 6)]
                stair = f.create_entity("IfcStair", GlobalId=self.guid("stair" + s.id), Name=s.id,
                                        ObjectPlacement=self.place(st_pl),
                                        Representation=self.product_shape([self.shape(boxes, "stair", "Brep")]),
                                        PredefinedType="STRAIGHT_RUN_STAIR")
                self.pset(stair, "Pset_StairCommon", {"NumberOfRiser": s.risers, "RiserHeight": s.riser_height * M,
                                                      "TreadLength": s.tread * M})
                contained.append(stair)

            if lv.id == b.top_level().id:
                for el in roof_elements(b):
                    body = self.brep(el.polys, dz=lv.elevation)
                    shp = self.product_shape([self.shape([body], el.material, "Brep")])
                    if el.category == "roof":
                        ent = f.create_entity("IfcRoof", GlobalId=self.guid("roof"), Name=el.name,
                                              ObjectPlacement=self.place(st_pl), Representation=shp,
                                              PredefinedType="HIP_ROOF" if b.roof.type == "hip" else "GABLE_ROOF")
                        self.pset(ent, "Housegen_Roof", {"Pitch_in_12": b.roof.pitch, "Overhang_ft": b.roof.overhang})
                    else:
                        ent = f.create_entity("IfcWall", GlobalId=self.guid("gable"), Name=el.name,
                                              ObjectPlacement=self.place(st_pl), Representation=shp,
                                              PredefinedType="STANDARD")
                    contained.append(ent)

            f.createIfcRelContainedInSpatialStructure(self.guid("contain" + lv.id), None, None, None, contained, storey)
            if spaces:
                f.createIfcRelAggregates(self.guid("agg-spaces" + lv.id), None, None, None, storey, spaces)
        f.createIfcRelAggregates(self.guid("agg-building"), None, None, None, building, storeys)
        hd = getattr(f, "header", None) or f.wrapped_data.header   # API differs across ifcopenshell versions
        try:
            hd.file_description.description = ("ViewDefinition [ReferenceView_V1.2]", STAMP)
            hd.file_name.name = str(path).split("/")[-1]
            hd.file_name.originating_system = "housegen"
        except Exception:
            pass
        f.write(str(path))
        return path


def write_ifc(b, spec, path):
    return Writer(b, spec).write(path)


def verify_ifc(path, b):
    """Re-open the file and compare it with the model it came from."""
    import ifcopenshell.geom
    import ifcopenshell.validate
    f = ifcopenshell.open(str(path))
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(f, logger)
    counts = {k: len(f.by_type(k)) for k in ("IfcBuildingStorey", "IfcWall", "IfcOpeningElement", "IfcDoor",
                                             "IfcWindow", "IfcSpace", "IfcSlab", "IfcRoof", "IfcStair")}
    area_m2 = sum(q.AreaValue for q in f.by_type("IfcQuantityArea") if q.Name == "NetFloorArea")
    expect = {"IfcWall": sum(1 for w in b.walls if w.kind != "sep") + (1 if b.roof.type == "gable" else 0),
              "IfcOpeningElement": len(b.openings),
              "IfcDoor": sum(1 for o in b.openings if o.kind == "door"),
              "IfcWindow": sum(1 for o in b.openings if o.kind == "window"),
              "IfcSpace": len(b.rooms), "IfcBuildingStorey": len(b.levels)}
    mismatches = [f"{k}: file {counts[k]}, model {v}" for k, v in expect.items() if counts[k] != v]
    # wall volume with the openings actually cut, from the IFC geometry kernel
    settings = ifcopenshell.geom.settings()
    vol = 0.0
    import numpy as np
    for w in f.by_type("IfcWall"):
        shp = ifcopenshell.geom.create_shape(settings, w)
        v = np.array(shp.geometry.verts).reshape(-1, 3)
        t = np.array(shp.geometry.faces).reshape(-1, 3)
        a, c, d = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
        vol += abs(np.einsum("ij,ij->i", a, np.cross(c, d)).sum() / 6.0)
    model_vol = 0.0
    for w in b.walls:
        if w.kind == "sep":
            continue
        cut = sum(o.width * min(o.height, w.height - o.sill) for o in b.openings_in(w.id))
        model_vol += ((w.u1 - w.u0) * w.height - cut) * w.thickness
    if b.roof.type == "gable":
        from .mesh import roof_geometry
        rg = roof_geometry(b)
        x0, y0, x1, y1 = rg["bbox"]
        span = (y1 - y0) if rg["along_x"] else (x1 - x0)
        t = max(w.thickness for w in b.walls if w.kind == "ext")
        model_vol += 2 * 0.5 * span * (span / 2 * b.roof.pitch / 12.0) * t
    return {"schema": f.schema, "counts": counts, "mismatches": mismatches,
            "schema_errors": [s["message"] if isinstance(s, dict) else str(s) for s in logger.statements][:10],
            "space_area_sqft": area_m2 / (M * M),
            "wall_volume_cuft_ifc": vol / M ** 3, "wall_volume_cuft_model": model_vol}
