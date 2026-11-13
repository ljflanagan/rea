"""3D geometry derived from the model.

Every element becomes an `Element` holding planar, outward-facing polygons in
feet (Z up). glTF, OBJ, the renders and the IFC roof all consume these same
polygons, so the 3D outputs cannot drift from each other or from the plan.
"""
import math
from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import box

MATERIALS = {
    "wall_ext": (0.90, 0.87, 0.80, 1.0),
    "wall_int": (0.96, 0.95, 0.93, 1.0),
    "slab": (0.72, 0.72, 0.70, 1.0),
    "floor": (0.80, 0.70, 0.56, 1.0),
    "roof": (0.36, 0.37, 0.40, 1.0),
    "door": (0.55, 0.36, 0.22, 1.0),
    "frame": (0.97, 0.97, 0.97, 1.0),
    "glass": (0.55, 0.75, 0.88, 0.45),
    "stair": (0.70, 0.58, 0.42, 1.0),
    "ground": (0.56, 0.68, 0.46, 1.0),
}


@dataclass
class Element:
    id: str
    name: str
    category: str      # wall | door | window | slab | roof | stair | site
    material: str
    polys: list = field(default_factory=list)   # each: list of (x, y, z)

    def add(self, pts, outward=None):
        pts = [tuple(map(float, p)) for p in pts]
        if outward is not None:
            n = _normal(pts)
            if n[0] * outward[0] + n[1] * outward[1] + n[2] * outward[2] < 0:
                pts = pts[::-1]
        self.polys.append(pts)

    def add_box(self, corners_fn, u0, u1, v0, v1, z0, z1):
        """Axis box in a local (u, v) frame; corners_fn maps (u, v) -> (x, y)."""
        P = lambda u, v, z: (*corners_fn(u, v), z)
        c = corners_fn((u0 + u1) / 2, (v0 + v1) / 2)
        cz = (z0 + z1) / 2

        def out(pts):
            m = np.mean(np.array(pts), axis=0)
            self.add(pts, (m[0] - c[0], m[1] - c[1], m[2] - cz))
        out([P(u0, v0, z0), P(u1, v0, z0), P(u1, v0, z1), P(u0, v0, z1)])
        out([P(u0, v1, z0), P(u1, v1, z0), P(u1, v1, z1), P(u0, v1, z1)])
        out([P(u0, v0, z0), P(u0, v1, z0), P(u0, v1, z1), P(u0, v0, z1)])
        out([P(u1, v0, z0), P(u1, v1, z0), P(u1, v1, z1), P(u1, v0, z1)])
        out([P(u0, v0, z0), P(u1, v0, z0), P(u1, v1, z0), P(u0, v1, z0)])
        out([P(u0, v0, z1), P(u1, v0, z1), P(u1, v1, z1), P(u0, v1, z1)])

    def triangles(self):
        tris = []
        for p in self.polys:
            for i in range(1, len(p) - 1):
                tris.append((p[0], p[i], p[i + 1]))
        return tris


def _normal(pts):
    a = np.array(pts)
    n = np.zeros(3)
    for i in range(len(a)):
        p, q = a[i], a[(i + 1) % len(a)]
        n += np.cross(p, q)
    return n


def rect_cells(poly):
    """Decompose a rectilinear polygon into axis-aligned rectangles."""
    xs = sorted({round(x, 6) for x, _ in poly.exterior.coords})
    ys = sorted({round(y, 6) for _, y in poly.exterior.coords})
    for ring in poly.interiors:
        xs = sorted(set(xs) | {round(x, 6) for x, _ in ring.coords})
        ys = sorted(set(ys) | {round(y, 6) for _, y in ring.coords})
    grown = poly.buffer(1e-7)
    cells = []
    for y0, y1 in zip(ys, ys[1:]):
        run = None
        for x0, x1 in zip(xs, xs[1:]):
            if grown.contains(box(x0, y0, x1, y1)):
                run = (run[0], x1) if run else (x0, x1)
            elif run:
                cells.append((run[0], y0, run[1], y1)); run = None
        if run:
            cells.append((run[0], y0, run[1], y1))
    return cells


def extrude(el, poly, z0, z1):
    for x0, y0, x1, y1 in rect_cells(poly):
        el.add([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1))
        el.add([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], (0, 0, -1))
    ring = list(poly.exterior.coords)
    ccw = poly.exterior.is_ccw
    for (xa, ya), (xb, yb) in zip(ring, ring[1:]):
        dx, dy = xb - xa, yb - ya
        n = (dy, -dx, 0) if ccw else (-dy, dx, 0)
        el.add([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)], n)


def wall_element(b, w):
    lv = b.level(w.level)
    zb, H, h = lv.elevation, w.height, w.thickness / 2
    el = Element(w.id, f"Wall {w.id}", "wall", "wall_ext" if w.kind == "ext" else "wall_int")
    holes = [(o.ua, o.ub, o.sill, min(o.head, H)) for o in b.openings_in(w.id)]
    us = sorted({w.u0, w.u1} | {x for hh in holes for x in hh[:2]})
    zs = sorted({0.0, H} | {x for hh in holes for x in hh[2:]})

    def in_hole(u, z):
        return any(a < u < c and s < z < t for a, c, s, t in holes)

    n = w.normal
    for z0, z1 in zip(zs, zs[1:]):
        run = None
        spans = []
        for ua, ub in zip(us, us[1:]):
            if not in_hole((ua + ub) / 2, (z0 + z1) / 2):
                run = (run[0], ub) if run else (ua, ub)
            elif run:
                spans.append(run); run = None
        if run:
            spans.append(run)
        for ua, ub in spans:
            for side in (1, -1):
                v = side * h
                el.add([(*w.pt(ua, v), zb + z0), (*w.pt(ub, v), zb + z0),
                        (*w.pt(ub, v), zb + z1), (*w.pt(ua, v), zb + z1)],
                       (n[0] * side, n[1] * side, 0))
    # top and bottom, skipping the parts an opening removes
    for z, zdir, edge in ((H, 1, lambda hh: hh[3] >= H - 1e-9), (0.0, -1, lambda hh: hh[2] <= 1e-9)):
        for ua, ub in zip(us, us[1:]):
            m = (ua + ub) / 2
            if any(a < m < c and edge((a, c, s, t)) for a, c, s, t in holes):
                continue
            el.add([(*w.pt(ua, -h), zb + z), (*w.pt(ub, -h), zb + z),
                    (*w.pt(ub, h), zb + z), (*w.pt(ua, h), zb + z)], (0, 0, zdir))
    d = w.dir
    for u, s in ((w.u0, -1), (w.u1, 1)):
        el.add([(*w.pt(u, -h), zb), (*w.pt(u, h), zb), (*w.pt(u, h), zb + H), (*w.pt(u, -h), zb + H)],
               (d[0] * s, d[1] * s, 0))
    for a, c, s, t in holes:   # reveals
        for u, sgn in ((a, 1), (c, -1)):
            el.add([(*w.pt(u, -h), zb + s), (*w.pt(u, h), zb + s), (*w.pt(u, h), zb + t), (*w.pt(u, -h), zb + t)],
                   (d[0] * sgn, d[1] * sgn, 0))
        if t < H - 1e-9:
            el.add([(*w.pt(a, -h), zb + t), (*w.pt(c, -h), zb + t), (*w.pt(c, h), zb + t), (*w.pt(a, h), zb + t)],
                   (0, 0, -1))
        if s > 1e-9:
            el.add([(*w.pt(a, -h), zb + s), (*w.pt(c, -h), zb + s), (*w.pt(c, h), zb + s), (*w.pt(a, h), zb + s)],
                   (0, 0, 1))
    return el


def opening_elements(b, o):
    w = b.wall(o.wall)
    zb = b.level(w.level).elevation
    out = []
    if o.kind == "cased":
        return out
    glazed = o.kind == "window" or o.type == "slider"
    if glazed:
        fr = Element(o.id + "-frame", f"{o.kind.title()} {o.id} frame", o.kind, "frame")
        f, d = 0.17, min(0.17, w.thickness / 2)
        fr.add_box(w.pt, o.ua, o.ua + f, -d, d, zb + o.sill, zb + o.head)
        fr.add_box(w.pt, o.ub - f, o.ub, -d, d, zb + o.sill, zb + o.head)
        fr.add_box(w.pt, o.ua + f, o.ub - f, -d, d, zb + o.head - f, zb + o.head)
        fr.add_box(w.pt, o.ua + f, o.ub - f, -d, d, zb + o.sill, zb + o.sill + f)
        if o.type in ("single_hung", "slider"):
            if o.type == "single_hung":
                mid = zb + o.sill + o.height / 2
                fr.add_box(w.pt, o.ua + f, o.ub - f, -d * 0.6, d * 0.6, mid - 0.06, mid + 0.06)
            else:
                fr.add_box(w.pt, o.center - 0.06, o.center + 0.06, -d * 0.6, d * 0.6,
                           zb + o.sill + f, zb + o.head - f)
        gl = Element(o.id, f"{o.kind.title()} {o.id}", o.kind, "glass")
        gl.add_box(w.pt, o.ua + f, o.ub - f, -0.02, 0.02, zb + o.sill + f, zb + o.head - f)
        out += [fr, gl]
    else:
        el = Element(o.id, f"Door {o.id}", "door", "door")
        el.add_box(w.pt, o.ua + 0.02, o.ub - 0.02, -0.073, 0.073, zb + o.sill, zb + o.head - 0.02)
        out.append(el)
    return out


def roof_geometry(b):
    """Hip or gable roof over the bounding rectangle of the top level."""
    r = b.roof
    g = b.gross_polygon(b.top_level().id)
    x0, y0, x1, y1 = g.bounds
    o, p = r.overhang, r.pitch / 12.0
    plate = b.plate_height()
    ex0, ey0, ex1, ey1 = x0 - o, y0 - o, x1 + o, y1 + o
    along_x = (x1 - x0) >= (y1 - y0)
    span = (ey1 - ey0) if along_x else (ex1 - ex0)
    ze = plate - o * p
    zr = ze + span / 2 * p
    zf = ze - r.fascia
    faces = []   # (pts, kind)
    if along_x:
        ym = (ey0 + ey1) / 2
        inset = span / 2 if r.type == "hip" else 0.0
        ra, rb = (ex0 + inset, ym, zr), (ex1 - inset, ym, zr)
        faces.append(([(ex0, ey0, ze), (ex1, ey0, ze), rb, ra], "slope"))
        faces.append(([(ex1, ey1, ze), (ex0, ey1, ze), ra, rb], "slope"))
        kind = "slope" if r.type == "hip" else "gable"
        faces.append(([(ex0, ey1, ze), (ex0, ey0, ze), ra], kind))
        faces.append(([(ex1, ey0, ze), (ex1, ey1, ze), rb], kind))
    else:
        xm = (ex0 + ex1) / 2
        inset = span / 2 if r.type == "hip" else 0.0
        ra, rb = (xm, ey0 + inset, zr), (xm, ey1 - inset, zr)
        faces.append(([(ex1, ey0, ze), (ex1, ey1, ze), rb, ra], "slope"))
        faces.append(([(ex0, ey1, ze), (ex0, ey0, ze), ra, rb], "slope"))
        kind = "slope" if r.type == "hip" else "gable"
        faces.append(([(ex0, ey0, ze), (ex1, ey0, ze), ra], kind))
        faces.append(([(ex1, ey1, ze), (ex0, ey1, ze), rb], kind))
    area = 0.0
    for pts, kind in faces:
        if kind == "slope":
            area += 0.5 * float(np.linalg.norm(_normal(pts)))
    return {"faces": faces, "eave": (ex0, ey0, ex1, ey1), "ze": ze, "zr": zr, "zf": zf,
            "ridge": (ra, rb), "area": area, "along_x": along_x, "plate": plate,
            "rectangular": abs(g.area - (x1 - x0) * (y1 - y0)) < 1e-6, "bbox": (x0, y0, x1, y1)}


def roof_elements(b):
    rg = roof_geometry(b)
    ex0, ey0, ex1, ey1 = rg["eave"]
    ze, zf = rg["ze"], rg["zf"]
    cx, cy = (ex0 + ex1) / 2, (ey0 + ey1) / 2
    el = Element("ROOF", f"{b.roof.type.title()} roof", "roof", "roof")
    for pts, kind in rg["faces"]:
        m = np.mean(np.array(pts), axis=0)
        el.add(pts, (m[0] - cx, m[1] - cy, 1.0) if kind == "slope" else (m[0] - cx, m[1] - cy, 0))
    el.add([(ex0, ey0, zf), (ex1, ey0, zf), (ex1, ey1, zf), (ex0, ey1, zf)], (0, 0, -1))
    ring = [(ex0, ey0), (ex1, ey0), (ex1, ey1), (ex0, ey1)]
    for (xa, ya), (xb, yb) in zip(ring, ring[1:] + ring[:1]):
        el.add([(xa, ya, zf), (xb, yb, zf), (xb, yb, ze), (xa, ya, ze)], (yb - ya, -(xb - xa), 0))
    out = [el]
    if b.roof.type == "gable":   # close the wall up to the roof at each gable end
        x0, y0, x1, y1 = rg["bbox"]
        t = max(w.thickness for w in b.walls if w.kind == "ext")
        p, plate = b.roof.pitch / 12.0, rg["plate"]
        ge = Element("GABLE", "Gable end walls", "wall", "wall_ext")

        def prism(tri_at):
            """Closed triangular prism between two parallel triangles."""
            A, B = tri_at(0), tri_at(1)
            c = np.mean(np.array(A + B), axis=0)
            for pts in (A, B, [A[0], A[1], B[1], B[0]], [A[1], A[2], B[2], B[1]], [A[2], A[0], B[0], B[2]]):
                m = np.mean(np.array(pts), axis=0)
                ge.add(pts, tuple(m - c))
        if rg["along_x"]:
            ym, top = (y0 + y1) / 2, plate + (y1 - y0) / 2 * p
            for xa, xb in ((x0, x0 + t), (x1 - t, x1)):
                prism(lambda i, xa=xa, xb=xb: [((xa, xb)[i], y0, plate), ((xa, xb)[i], y1, plate), ((xa, xb)[i], ym, top)])
        else:
            xm, top = (x0 + x1) / 2, plate + (x1 - x0) / 2 * p
            for ya, yb in ((y0, y0 + t), (y1 - t, y1)):
                prism(lambda i, ya=ya, yb=yb: [(x0, (ya, yb)[i], plate), (x1, (ya, yb)[i], plate), (xm, (ya, yb)[i], top)])
        out.append(ge)
    return out


def stair_element(b, s):
    lv = b.level(s.level)
    dx, dy = s.direction
    nx, ny = -dy, dx
    el = Element(s.id, f"Stair {s.id}", "stair", "stair")
    fn = lambda u, v: (s.origin[0] + u * dx + v * nx, s.origin[1] + u * dy + v * ny)
    for i in range(s.risers - 1):
        el.add_box(fn, i * s.tread, (i + 1) * s.tread, -s.width / 2, s.width / 2,
                   lv.elevation, lv.elevation + (i + 1) * s.riser_height)
    return el


def build_elements(b, include_site=True):
    els = []
    fag = b.site.floor_above_grade if b.site else 1.0
    for i, lv in enumerate(sorted(b.levels, key=lambda l: l.elevation)):
        slab = Element(f"SLAB-{lv.id}", f"Floor {lv.name}", "slab", "slab")
        extrude(slab, b.gross_polygon(lv.id), lv.elevation - (fag if i == 0 else 1.0), lv.elevation)
        els.append(slab)
    for w in b.walls:
        if w.kind != "sep":
            els.append(wall_element(b, w))
    for o in b.openings:
        els += opening_elements(b, o)
    for s in b.stairs:
        els.append(stair_element(b, s))
    els += roof_elements(b)
    if include_site and b.site:
        g = Element("SITE", "Lot", "site", "ground")
        x0, y0, x1, y1 = b.site.lot_polygon().bounds
        g.add([(x0, y0, -fag), (x1, y0, -fag), (x1, y1, -fag), (x0, y1, -fag)], (0, 0, 1))
        els.append(g)
    return els
