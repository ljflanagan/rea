"""Plan-view graphics derived from the model.

`plan_primitives` and `site_primitives` return neutral drawing primitives in
model coordinates (feet), each tagged with a CAD layer. The DXF exporter and
the sheet composer both draw from this one list, so the DXF and the printed
sheet always show the same walls, openings, labels and dimensions.

Primitive dictionaries:
  region  {layer, rings}                     filled area, first ring is the outside
  line    {layer, a, b}
  poly    {layer, pts, closed}
  arc     {layer, c, r, a0, a1}              degrees, counter-clockwise
  text    {layer, at, text, h, rot, bold}    h is paper inches; centred on `at`
  dim     {layer, axis, a, b, pos, out, text}   linear dimension; pos is the
          coordinate of the dimension line, out is which way is "away"
"""
import math

from .mesh import roof_geometry
from .units import ft_in, sf

# layer -> (ACI colour, linetype, stroke colour, stroke width pt, dash, fill)
LAYERS = {
    "A-WALL":       (7, "CONTINUOUS", "#111111", 0.9, None, "#4a4a4a"),
    "A-DOOR":       (3, "CONTINUOUS", "#1d1d1d", 0.6, None, None),
    "A-GLAZ":       (5, "CONTINUOUS", "#1558a6", 0.6, None, None),
    "A-FLOR-STRS":  (8, "CONTINUOUS", "#444444", 0.5, None, None),
    "A-ROOF-OTLN":  (8, "DASHED", "#777777", 0.5, (5, 3), None),
    "A-AREA":       (9, "CONTINUOUS", None, 0, None, None),          # room boundaries, not plotted
    "A-ANNO-TEXT":  (7, "CONTINUOUS", "#111111", 0, None, None),
    "A-ANNO-DIMS":  (2, "CONTINUOUS", "#333333", 0.45, None, None),
    "A-ANNO-NOTE":  (1, "CONTINUOUS", "#b00000", 0, None, None),
    "A-ANNO-TTLB":  (7, "CONTINUOUS", "#111111", 0.9, None, None),
    "A-BLDG-OTLN":  (7, "CONTINUOUS", "#111111", 0.9, None, "#c9c9c9"),
    "C-PROP":       (4, "PHANTOM", "#000000", 1.1, (14, 3, 2, 3, 2, 3), None),
    "C-PROP-SETB":  (1, "DASHED", "#b00000", 0.6, (6, 4), None),
}

TEXT_ROOM, TEXT_SMALL, TEXT_DIM, TEXT_TAG = 0.12, 0.08, 0.085, 0.065


def tag(o):
    """Width/height shorthand used on residential plans: 3'-0" x 6'-8" -> 3068."""
    def part(v):
        total = round(v * 12)
        return f"{total // 12}{total % 12}"
    return part(o.width) + part(o.height)


def _rings(geom):
    polys = getattr(geom, "geoms", [geom])
    out = []
    for p in polys:
        if p.is_empty or p.geom_type != "Polygon":
            continue
        out.append([list(p.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in p.interiors])
    return out


def plan_primitives(b, lid, scale):
    """scale: paper inches per foot (0.25 for 1/4" = 1'-0")."""
    P = []
    walls = b.walls_on(lid)
    poche = b.wall_union(lid)
    for o in b.openings_on(lid):
        w = b.wall(o.wall)
        poche = poche.difference(w.rect(o.ua, o.ub, grow=0.01))
    for rings in _rings(poche):
        P.append({"type": "region", "layer": "A-WALL", "rings": rings})

    for o in b.openings_on(lid):
        w = b.wall(o.wall)
        h = w.thickness / 2
        if o.kind == "window":
            for v in (-h, h, -h / 4, h / 4):
                P.append({"type": "line", "layer": "A-GLAZ", "a": w.pt(o.ua, v), "b": w.pt(o.ub, v)})
            out = -1 if o.rooms and o.rooms[1] == "exterior" else 1
            P.append({"type": "text", "layer": "A-ANNO-TEXT", "at": w.pt(o.center, out * (h + 0.14 / scale)),
                      "text": tag(o), "h": TEXT_TAG, "rot": 0 if w.horizontal else 90, "bold": False})
            continue
        if o.exterior or o.kind == "cased":
            for v in (-h, h):
                P.append({"type": "line", "layer": "A-DOOR", "a": w.pt(o.ua, v), "b": w.pt(o.ub, v)})
        s = o.swing_side
        if o.type == "overhead":
            out = -1 if o.rooms[1] == "exterior" else 1
            P.append({"type": "line", "layer": "A-ROOF-OTLN", "a": w.pt(o.ua, out * h * 0.5), "b": w.pt(o.ub, out * h * 0.5)})
        elif o.type == "slider":
            mid, lap = o.center, 0.15
            P.append({"type": "line", "layer": "A-GLAZ", "a": w.pt(o.ua, 0.07), "b": w.pt(mid + lap, 0.07)})
            P.append({"type": "line", "layer": "A-GLAZ", "a": w.pt(mid - lap, -0.07), "b": w.pt(o.ub, -0.07)})
        elif o.type == "bifold":
            p, ang = o.width / 4, math.radians(35)
            du, dv = p * math.sin(ang), p * math.cos(ang)
            for u0, sg in ((o.ua, 1), (o.ub, -1)):
                pts = [w.pt(u0, s * h), w.pt(u0 + sg * du, s * (h + dv)), w.pt(u0 + sg * 2 * du, s * h)]
                P.append({"type": "poly", "layer": "A-DOOR", "pts": pts, "closed": False})
        elif o.kind == "door":
            uh, ul = (o.ua, o.ub) if o.hinge == "a" else (o.ub, o.ua)
            hp = w.pt(uh, s * h)
            n = w.normal
            leaf = (hp[0] + n[0] * s * o.width, hp[1] + n[1] * s * o.width)
            latch = w.pt(ul, s * h)
            P.append({"type": "line", "layer": "A-DOOR", "a": hp, "b": leaf})
            a1 = math.degrees(math.atan2(leaf[1] - hp[1], leaf[0] - hp[0]))
            a2 = math.degrees(math.atan2(latch[1] - hp[1], latch[0] - hp[0]))
            if (a2 - a1) % 360 > 180:
                a1, a2 = a2, a1
            P.append({"type": "arc", "layer": "A-DOOR", "c": hp, "r": o.width, "a0": a1, "a1": a1 + (a2 - a1) % 360})
        if o.kind == "door":
            side = -s if o.type == "swing" else s
            if o.exterior:
                side = 1 if o.rooms[1] == "exterior" else -1      # tag on the inside
                if o.type == "swing":
                    side = -side                                    # ... unless the leaf is there
            P.append({"type": "text", "layer": "A-ANNO-TEXT", "at": w.pt(o.center, side * (h + 0.13 / scale)),
                      "text": tag(o), "h": TEXT_TAG, "rot": 0 if w.horizontal else 90, "bold": False})

    for s in (st for st in b.stairs if st.level == lid):
        dx, dy = s.direction
        nx, ny = -dy, dx
        hw = s.width / 2
        for i in range(s.risers):
            u = i * s.tread
            if u > s.run + 1e-9:
                break
            P.append({"type": "line", "layer": "A-FLOR-STRS",
                      "a": (s.origin[0] + u * dx - hw * nx, s.origin[1] + u * dy - hw * ny),
                      "b": (s.origin[0] + u * dx + hw * nx, s.origin[1] + u * dy + hw * ny)})
        for sg in (-1, 1):
            P.append({"type": "line", "layer": "A-FLOR-STRS",
                      "a": (s.origin[0] + sg * hw * nx, s.origin[1] + sg * hw * ny),
                      "b": (s.origin[0] + s.run * dx + sg * hw * nx, s.origin[1] + s.run * dy + sg * hw * ny)})
        P.append({"type": "text", "layer": "A-ANNO-TEXT",
                  "at": (s.origin[0] + s.run / 2 * dx, s.origin[1] + s.run / 2 * dy),
                  "text": f"UP {s.risers}R", "h": TEXT_SMALL, "rot": 0, "bold": True})

    if lid == b.top_level().id:
        ex0, ey0, ex1, ey1 = roof_geometry(b)["eave"]
        P.append({"type": "poly", "layer": "A-ROOF-OTLN", "closed": True,
                  "pts": [(ex0, ey0), (ex1, ey0), (ex1, ey1), (ex0, ey1)]})

    for r in b.rooms_on(lid):
        P.append({"type": "poly", "layer": "A-AREA", "pts": list(r.net.exterior.coords)[:-1], "closed": True})
        cw, cd = r.clear
        big = min(cw, cd) >= 8.0
        h1 = TEXT_ROOM if big else TEXT_SMALL
        name = r.name.upper()
        est = 0.85 * h1 * len(name) / scale          # label width in feet
        rot = 90 if (est > cw - 0.3 and cd > cw) else 0
        lines = [(name, h1, True), (sf(r.area), TEXT_SMALL, False)]
        if big:
            lines.append((f"{ft_in(cw, 1)} x {ft_in(cd, 1)}", TEXT_SMALL * 0.9, False))
        step = 0.17 / scale
        y0 = (len(lines) - 1) / 2 * step
        for i, (txt, hh, bold) in enumerate(lines):
            off = y0 - i * step
            at = (r.label[0] - off, r.label[1]) if rot else (r.label[0], r.label[1] + off)
            P.append({"type": "text", "layer": "A-ANNO-TEXT", "at": at, "text": txt, "h": hh,
                      "rot": rot, "bold": bold})

    P += _exterior_dims(b, lid, scale)
    return P


def _exterior_dims(b, lid, scale):
    """Three tiers per side, reading outward: openings, partitions, overall.
    Exterior walls are dimensioned to their outside face, partitions and
    openings to their centerlines."""
    x0, y0, x1, y1 = b.gross_polygon(lid).bounds
    ext = [w for w in b.walls_on(lid) if w.kind == "ext"]
    inner = [w for w in b.walls_on(lid) if w.kind == "int"]
    first, step = 0.62 / scale, 0.36 / scale
    out = []
    sides = [("h", y0, -1), ("h", y1, 1), ("v", x0, -1), ("v", x1, 1)]
    for axis, edge, sgn in sides:
        k = 0 if axis == "h" else 1          # coordinate that varies along the side
        lo, hi = (x0, x1) if axis == "h" else (y0, y1)
        on_side = [w for w in ext if w.horizontal == (axis == "h")
                   and abs(w.a[1 - k] - edge) < w.thickness]
        opens = sorted({round(w.pt(o.center)[k], 4) for w in on_side for o in b.openings_in(w.id)})
        parts = set()
        for w in inner:
            if w.horizontal == (axis == "h"):
                continue
            for p in (w.a, w.b):
                if abs(p[1 - k] - edge) < 1.0:
                    parts.add(round(p[k], 4))
        tiers = []
        if opens:
            tiers.append([lo] + opens + [hi])
        if parts:
            tiers.append([lo] + sorted(parts) + [hi])
        tiers.append([lo, hi])
        for t, pts in enumerate(tiers):
            pos = edge + sgn * (first + t * step)
            for a, c in zip(pts, pts[1:]):
                if c - a < 1e-6:
                    continue
                pa = (a, edge) if axis == "h" else (edge, a)
                pb = (c, edge) if axis == "h" else (edge, c)
                out.append({"type": "dim", "layer": "A-ANNO-DIMS", "axis": axis, "a": pa, "b": pb,
                            "pos": pos, "out": sgn, "text": ft_in(c - a)})
    return out


def plan_extent(prims, scale):
    """Bounding box of the primitives in feet, including dimension text."""
    xs, ys = [], []
    for p in prims:
        if p["type"] == "region":
            for ring in p["rings"]:
                xs += [q[0] for q in ring]; ys += [q[1] for q in ring]
        elif p["type"] in ("line",):
            xs += [p["a"][0], p["b"][0]]; ys += [p["a"][1], p["b"][1]]
        elif p["type"] == "poly":
            xs += [q[0] for q in p["pts"]]; ys += [q[1] for q in p["pts"]]
        elif p["type"] == "dim":
            pad = 0.3 / scale * p["out"]
            if p["axis"] == "h":
                xs += [p["a"][0], p["b"][0]]; ys += [p["pos"] + pad]
            else:
                ys += [p["a"][1], p["b"][1]]; xs += [p["pos"] + pad]
        elif p["type"] == "text":
            xs.append(p["at"][0]); ys.append(p["at"][1])
    return min(xs), min(ys), max(xs), max(ys)


def site_primitives(b, scale):
    P = []
    s = b.site
    lx0, ly0, lx1, ly1 = s.lot_polygon().bounds
    bx0, by0, bx1, by1 = s.buildable_polygon().bounds
    g = b.footprint()
    hx0, hy0, hx1, hy1 = g.bounds
    P.append({"type": "poly", "layer": "C-PROP", "closed": True,
              "pts": [(lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1)]})
    P.append({"type": "poly", "layer": "C-PROP-SETB", "closed": True,
              "pts": [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]})
    P.append({"type": "region", "layer": "A-BLDG-OTLN", "rings": [list(g.exterior.coords)[:-1]]})
    ex0, ey0, ex1, ey1 = roof_geometry(b)["eave"]
    P.append({"type": "poly", "layer": "A-ROOF-OTLN", "closed": True,
              "pts": [(ex0, ey0), (ex1, ey0), (ex1, ey1), (ex0, ey1)]})
    T = lambda at, txt, h=TEXT_SMALL, bold=False, rot=0, layer="A-ANNO-TEXT": P.append(
        {"type": "text", "layer": layer, "at": at, "text": txt, "h": h, "rot": rot, "bold": bold})
    cx = (hx0 + hx1) / 2
    T((cx, (hy0 + hy1) / 2 + 0.1 / scale), "HOUSE", TEXT_ROOM, True)
    T((cx, (hy0 + hy1) / 2 - 0.1 / scale), f"{sf(g.area)} footprint")
    T(((lx0 + lx1) / 2, ly0 - 0.95 / scale), "STREET (FRONT OF LOT)", TEXT_ROOM, True)
    T(((bx0 + bx1) / 2, by1 - 0.14 / scale), "building setback line", TEXT_TAG, layer="A-ANNO-NOTE")
    T(((lx0 + lx1) / 2, (hy1 + by1) / 2), "REAR YARD")
    D = lambda axis, a, c, pos, out: P.append(
        {"type": "dim", "layer": "A-ANNO-DIMS", "axis": axis, "a": a, "b": c, "pos": pos, "out": out,
         "text": ft_in(abs((c[0] - a[0]) if axis == "h" else (c[1] - a[1])))})
    D("h", (lx0, ly0), (lx1, ly0), ly0 - 0.5 / scale, -1)                 # lot width
    D("v", (lx0, ly0), (lx0, ly1), lx0 - 0.5 / scale, -1)                 # lot depth
    D("v", (cx, ly0), (cx, hy0), cx, 1)                                   # front yard
    D("v", (cx, hy1), (cx, ly1), cx, 1)                                   # rear yard
    my = (hy0 + hy1) / 2 - 0.45 / scale
    D("h", (lx0, my), (hx0, my), my, 1)                                   # side yards
    D("h", (hx1, my), (lx1, my), my, 1)
    D("h", (hx0, hy1), (hx1, hy1), hy1 + 0.3 / scale, 1)                  # house width
    D("v", (hx1, hy0), (hx1, hy1), lx1 + 0.5 / scale, 1)  # house depth
    return P
