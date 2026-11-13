"""The single building model.

Everything the pipeline emits (DXF, sheets, glTF/OBJ, IFC, renders, the
validation report) is derived from one `Building` instance. Nothing is drawn
twice: a wall is one object with a centerline, a thickness and a height, and
the plan, the 3D solid and the IFC entity are all views of it.

Conventions
-----------
* Units: decimal feet. X runs along the street frontage, Y runs from the
  front (street side, y=0) to the rear, Z is up with 0 at the finished floor
  of the lowest level.
* Walls are straight and axis-aligned, located by their centerline.
* Exterior walls run counter-clockwise, so a wall's left side is the interior.
* Openings (doors, windows, cased openings) are hosted: they store a host wall
  id and a position along that wall, and cannot exist without it.
* Rooms are not drawn. They are detected as the closed faces of the wall
  centerline graph and named by a seed point placed inside them.
* A wall of kind "sep" is a room separation line: it bounds rooms but has no
  thickness and no 3D solid (open-plan kitchen/dining/living).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union

TOL = 1e-6

HABITABLE = {"bedroom", "living", "dining", "kitchen", "study", "family"}
UNCONDITIONED = {"garage", "porch", "patio"}   # not counted as living area
OUTDOOR = {"porch", "patio"}                   # roofed but open: counts as outside for light, air, egress


class ModelError(Exception):
    pass


@dataclass
class Level:
    id: str
    name: str
    elevation: float  # finished floor, feet above the lowest finished floor
    height: float     # floor to top of wall plate


@dataclass
class Wall:
    id: str
    level: str
    a: tuple
    b: tuple
    thickness: float
    height: float
    kind: str               # "ext" | "int" | "sep"
    adj_a: float = 0.0      # join adjustment at a (+ extends, - trims)
    adj_b: float = 0.0
    join_a: str = "free"
    join_b: str = "free"

    @property
    def length(self):
        return math.hypot(self.b[0] - self.a[0], self.b[1] - self.a[1])

    @property
    def dir(self):
        L = self.length
        return ((self.b[0] - self.a[0]) / L, (self.b[1] - self.a[1]) / L)

    @property
    def normal(self):
        """Left-hand normal. For exterior walls this points indoors."""
        d = self.dir
        return (-d[1], d[0])

    @property
    def horizontal(self):
        return abs(self.dir[0]) > abs(self.dir[1])

    @property
    def u0(self):
        return -self.adj_a

    @property
    def u1(self):
        return self.length + self.adj_b

    def pt(self, u, v=0.0):
        d, n = self.dir, self.normal
        return (self.a[0] + u * d[0] + v * n[0], self.a[1] + u * d[1] + v * n[1])

    def rect(self, ua, ub, grow=0.0):
        h = self.thickness / 2 + grow
        return Polygon([self.pt(ua, -h), self.pt(ub, -h), self.pt(ub, h), self.pt(ua, h)])

    def solid(self):
        return self.rect(self.u0, self.u1)

    def line(self):
        return LineString([self.a, self.b])


@dataclass
class Opening:
    id: str
    wall: str
    kind: str            # "door" | "window" | "cased"
    center: float        # feet along host centerline from wall.a
    width: float
    height: float
    sill: float = 0.0
    type: str = "swing"  # door: swing|slider|bifold ; window: single_hung|casement|fixed|slider
    hinge: str = "a"     # jamb the leaf hangs from: "a" or "b" end of the host
    swing_side: int = 1  # +1 leaf opens to the host's left, -1 to its right
    swing_into: Optional[str] = None
    rooms: tuple = ()    # (left room name | "exterior", right room name | "exterior")
    outside: bool = False  # opens to the outdoors (directly, or onto a porch or patio)

    @property
    def ua(self):
        return self.center - self.width / 2

    @property
    def ub(self):
        return self.center + self.width / 2

    @property
    def head(self):
        return self.sill + self.height

    @property
    def exterior(self):
        return self.outside


@dataclass
class Room:
    name: str
    kind: str
    level: str
    face: Polygon        # centerline-bounded face
    net: Polygon         # clear floor area inside wall faces
    area: float
    label: tuple
    clear: tuple         # (x size, y size) of the largest clear rectangle


@dataclass
class Roof:
    type: str = "hip"    # "hip" | "gable"
    pitch: float = 5.0   # rise in 12
    overhang: float = 1.0
    fascia: float = 0.5


@dataclass
class Stair:
    id: str
    level: str           # level the stair starts on
    origin: tuple        # foot of the stair, centre of the bottom riser
    direction: tuple     # unit vector of travel in plan
    width: float
    rise: float          # total floor-to-floor rise
    risers: int = 0
    tread: float = 10.0 / 12

    @property
    def riser_height(self):
        return self.rise / self.risers

    @property
    def run(self):
        return (self.risers - 1) * self.tread


@dataclass
class Site:
    lot_width: float
    lot_depth: float
    setbacks: dict
    offset: tuple                 # house origin within the lot (lot origin = front-left corner)
    floor_above_grade: float = 1.0
    flood: dict = field(default_factory=dict)

    def lot_polygon(self):
        ox, oy = self.offset
        return box(-ox, -oy, self.lot_width - ox, self.lot_depth - oy)

    def buildable_polygon(self):
        ox, oy = self.offset
        s = self.setbacks
        return box(-ox + s["side"], -oy + s["front"],
                   self.lot_width - ox - s["side"], self.lot_depth - oy - s["rear"])


@dataclass
class Building:
    name: str
    levels: list
    walls: list
    openings: list
    seeds: list
    roof: Roof
    site: Optional[Site]
    stairs: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    rooms: list = field(default_factory=list)
    issues: list = field(default_factory=list)   # problems found while resolving the model
    _cache: dict = field(default_factory=dict, repr=False)

    # ---- lookups -------------------------------------------------------
    def level(self, lid):
        return next(l for l in self.levels if l.id == lid)

    def wall(self, wid):
        return next(w for w in self.walls if w.id == wid)

    def walls_on(self, lid, real=True):
        return [w for w in self.walls if w.level == lid and (w.kind != "sep" or not real)]

    def openings_in(self, wid):
        return sorted((o for o in self.openings if o.wall == wid), key=lambda o: o.center)

    def openings_on(self, lid):
        ids = {w.id for w in self.walls if w.level == lid}
        return [o for o in self.openings if o.wall in ids]

    def rooms_on(self, lid):
        return [r for r in self.rooms if r.level == lid]

    def room(self, name):
        return next((r for r in self.rooms if r.name == name), None)

    # ---- derived geometry ---------------------------------------------
    def wall_union(self, lid):
        key = ("wu", lid)
        if key not in self._cache:
            self._cache[key] = unary_union([w.solid() for w in self.walls_on(lid)])
        return self._cache[key]

    def gross_polygon(self, lid):
        """Outline to the outside face of the exterior walls."""
        key = ("gross", lid)
        if key not in self._cache:
            parts = [self.wall_union(lid)] + [r.face for r in self.rooms_on(lid)]
            g = unary_union(parts)
            if g.geom_type == "MultiPolygon":
                g = max(g.geoms, key=lambda p: p.area)
            self._cache[key] = Polygon(g.exterior)
        return self._cache[key]

    def gross_area(self, lid=None):
        lids = [lid] if lid else [l.id for l in self.levels]
        return sum(self.gross_polygon(l).area for l in lids)

    def unconditioned_area(self, lid=None):
        """Garage, porch and patio area, measured to the outside face of exterior walls."""
        total = 0.0
        for l in ([lid] if lid else [l.id for l in self.levels]):
            t = max((w.thickness for w in self.walls_on(l) if w.kind == "ext"), default=0.0)
            g = self.gross_polygon(l)
            for r in self.rooms_on(l):
                if r.kind in UNCONDITIONED:
                    total += r.face.buffer(t / 2, join_style=2).intersection(g).area
        return total

    def conditioned_area(self, lid=None):
        return self.gross_area(lid) - self.unconditioned_area(lid)

    def footprint(self):
        return self.gross_polygon(self.levels[0].id)

    def top_level(self):
        return max(self.levels, key=lambda l: l.elevation)

    def plate_height(self):
        t = self.top_level()
        return t.elevation + t.height

    # ---- resolution ----------------------------------------------------
    def resolve(self):
        """Compute everything that is derived: wall joins, rooms, opening sides."""
        self._cache.clear()
        self.issues = []
        for lv in self.levels:
            self._resolve_joins(lv.id)
        self.rooms = []
        for lv in self.levels:
            self._detect_rooms(lv.id)
        self._resolve_openings()
        return self

    def _arms(self, P, lid, skip):
        """Wall arms leaving point P: (direction, thickness, wall)."""
        arms = []
        for o in self.walls_on(lid):
            if o is skip:
                continue
            d = o.dir
            if _near(P, o.a):
                arms.append((d, o.thickness, o))
            elif _near(P, o.b):
                arms.append(((-d[0], -d[1]), o.thickness, o))
            elif o.line().distance(Point(P)) < TOL:
                arms.append((d, o.thickness, o))
                arms.append(((-d[0], -d[1]), o.thickness, o))
        return arms

    def _resolve_joins(self, lid):
        """Butt joins. At every wall end decide whether the wall runs through
        (extends to the far face of its neighbour) or stops at the neighbour's
        near face, so wall solids never overlap and never leave a gap."""
        def rank(w):
            return (w.kind == "ext", w.horizontal, w.id)

        for w in self.walls_on(lid):
            for end in ("a", "b"):
                P = w.a if end == "a" else w.b
                d = w.dir if end == "a" else (-w.dir[0], -w.dir[1])  # into the wall
                arms = self._arms(P, lid, w)
                perp = [a for a in arms if abs(a[0][0] * d[0] + a[0][1] * d[1]) < 0.5]
                col = [a for a in arms if (a[0][0] * d[0] + a[0][1] * d[1]) < -0.5]
                dup = [a for a in arms if (a[0][0] * d[0] + a[0][1] * d[1]) > 0.5]
                if dup:
                    self.issues.append(("FAIL", f"Wall {w.id} overlaps wall {dup[0][2].id}"))
                adj, kind = 0.0, "free"
                if perp:
                    tp = max(a[1] for a in perp)
                    signs = {round(a[0][0] * -d[1] + a[0][1] * d[0]) for a in perp}
                    through = len(signs) == 2
                    if through and not col:
                        adj, kind = -tp / 2, "tee"
                    elif through and col:
                        other = max((a[2] for a in perp), key=rank)
                        if rank(w) > rank(other):
                            adj, kind = 0.0, "cross-through"
                        else:
                            adj, kind = -tp / 2, "cross-butt"
                    elif col:
                        adj, kind = 0.0, "through"
                    else:
                        other = perp[0][2]
                        if rank(w) > rank(other):
                            adj, kind = tp / 2, "corner-through"
                        else:
                            adj, kind = -tp / 2, "corner-butt"
                elif col:
                    kind = "inline"
                if end == "a":
                    w.adj_a, w.join_a = adj, kind
                else:
                    w.adj_b, w.join_b = adj, kind

    def _detect_rooms(self, lid):
        lines = [w.line() for w in self.walls_on(lid, real=False)]
        if not lines:
            return
        faces = list(polygonize(unary_union(lines)))
        wu = self.wall_union(lid)
        seeds = [s for s in self.seeds if s["level"] == lid]
        used = set()
        for i, face in enumerate(sorted(faces, key=lambda f: (round(f.centroid.y, 3), round(f.centroid.x, 3)))):
            inside = [s for s in seeds if face.contains(Point(s["at"]))]
            if len(inside) > 1:
                self.issues.append(("FAIL", "Rooms " + ", ".join(s["name"] for s in inside)
                                    + " are not separated by any wall or separation line"))
            if inside:
                name, kind = inside[0]["name"], inside[0]["type"]
                used.add(inside[0]["name"])
            else:
                name, kind = f"Unnamed {i + 1}", "unnamed"
                self.issues.append(("WARN", f"Enclosed space at ({face.centroid.x:.1f}, "
                                    f"{face.centroid.y:.1f}) has no room name"))
            net = face.difference(wu)
            if net.geom_type == "MultiPolygon":
                net = max(net.geoms, key=lambda p: p.area)
            if net.is_empty:
                continue
            rect = _largest_rect(net)
            label = ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
            self.rooms.append(Room(name, kind, lid, face, net, net.area, label,
                                   (rect[2] - rect[0], rect[3] - rect[1])))
        for s in seeds:
            if s["name"] not in used:
                self.issues.append(("FAIL", f"Room '{s['name']}' is not enclosed by walls "
                                    f"(seed at {tuple(s['at'])})"))

    def room_at(self, pt, lid):
        p = Point(pt)
        for r in self.rooms_on(lid):
            if r.net.contains(p):
                return r.name
        if not self.gross_polygon(lid).contains(p):
            return "exterior"
        return None

    def _resolve_openings(self):
        for o in self.openings:
            w = self.wall(o.wall)
            probe = w.thickness / 2 + 0.3
            left = self.room_at(w.pt(o.center, probe), w.level)
            right = self.room_at(w.pt(o.center, -probe), w.level)
            o.rooms = (left, right)
            outdoor = {"exterior"} | {r.name for r in self.rooms if r.kind in OUTDOOR}
            o.outside = bool(outdoor & {left, right}) and not {left, right} <= outdoor
            if o.swing_into:
                if o.swing_into == left:
                    o.swing_side = 1
                elif o.swing_into == right:
                    o.swing_side = -1
                else:
                    self.issues.append(("FAIL", f"Opening {o.id}: swing_into '{o.swing_into}' is not "
                                        f"on either side of wall {w.id} (sides: {left}, {right})"))

    # ---- serialisation -------------------------------------------------
    def to_dict(self):
        def P(p):
            return [round(p[0], 4), round(p[1], 4)]
        return {
            "name": self.name,
            "units": "feet",
            "meta": self.meta,
            "levels": [vars(l) for l in self.levels],
            "walls": [{"id": w.id, "level": w.level, "kind": w.kind, "a": P(w.a), "b": P(w.b),
                       "thickness": w.thickness, "height": w.height,
                       "join_a": w.join_a, "join_b": w.join_b,
                       "adj_a": round(w.adj_a, 4), "adj_b": round(w.adj_b, 4)} for w in self.walls],
            "openings": [{"id": o.id, "wall": o.wall, "kind": o.kind, "type": o.type,
                          "center": round(o.center, 4), "width": o.width, "height": o.height,
                          "sill": o.sill, "hinge": o.hinge, "swing_side": o.swing_side,
                          "between": list(o.rooms)} for o in self.openings],
            "rooms": [{"name": r.name, "kind": r.kind, "level": r.level,
                       "net_area_sf": round(r.area, 2),
                       "clear_ft": [round(r.clear[0], 3), round(r.clear[1], 3)],
                       "boundary": [P(p) for p in r.net.exterior.coords[:-1]]} for r in self.rooms],
            "roof": vars(self.roof),
            "stairs": [dict(vars(s), riser_height=s.riser_height, run=s.run) for s in self.stairs],
            "site": None if not self.site else {
                "lot_width": self.site.lot_width, "lot_depth": self.site.lot_depth,
                "setbacks": self.site.setbacks, "house_offset": list(self.site.offset),
                "floor_above_grade": self.site.floor_above_grade, "flood": self.site.flood},
            "gross_area_sf": round(self.gross_area(), 2),
            "conditioned_area_sf": round(self.conditioned_area(), 2),
        }


def _near(p, q):
    return abs(p[0] - q[0]) < TOL and abs(p[1] - q[1]) < TOL


def _largest_rect(poly):
    """Largest axis-aligned rectangle inside a (rectilinear) polygon."""
    xs = sorted({round(x, 6) for x, _ in poly.exterior.coords})
    ys = sorted({round(y, 6) for _, y in poly.exterior.coords})
    best, best_a = poly.bounds, -1.0
    shrunk = poly.buffer(1e-7)
    for i, x0 in enumerate(xs):
        for x1 in xs[i + 1:]:
            for j, y0 in enumerate(ys):
                for y1 in ys[j + 1:]:
                    a = (x1 - x0) * (y1 - y0)
                    if a > best_a and shrunk.contains(box(x0, y0, x1, y1)):
                        best, best_a = (x0, y0, x1, y1), a
    return best


# ---------------------------------------------------------------------------
# Building a model from a layout program
# ---------------------------------------------------------------------------
EXT_NAMES = ("ext-front", "ext-right", "ext-back", "ext-left")


def build_model(spec, layout):
    """spec: normalised spec dict (see spec.py). layout: layout program dict.

    Layout coordinates are measured from the outside face of the front-left
    corner. Exterior walls are generated from the footprint; interior wall
    ends that reach the outside face are pulled back to the exterior wall
    centerline so they join it properly.
    """
    con = spec["construction"]
    t_ext = con["ext_wall_in"] / 12.0
    t_int = con["int_wall_in"] / 12.0
    W, D = float(layout["footprint"]["width"]), float(layout["footprint"]["depth"])
    h = t_ext / 2

    lv_defs = layout.get("levels") or [{
        "id": "L1", "name": "First Floor", "elevation": 0.0, "height": con["ceiling_ft"],
        "walls": layout.get("walls", []), "rooms": layout.get("rooms", []),
        "openings": layout.get("openings", [])}]

    levels, walls, openings, seeds = [], [], [], []
    for ld in lv_defs:
        lid = ld["id"]
        H = float(ld.get("height", con["ceiling_ft"]))
        levels.append(Level(lid, ld.get("name", lid), float(ld.get("elevation", 0.0)), H))
        pre = "" if len(lv_defs) == 1 else lid + ":"
        corners = [(h, h), (W - h, h), (W - h, D - h), (h, D - h)]
        for i, nm in enumerate(EXT_NAMES):
            walls.append(Wall(pre + nm, lid, corners[i], corners[(i + 1) % 4], t_ext, H, "ext"))

        def snap(p):
            return (min(max(float(p[0]), h), W - h), min(max(float(p[1]), h), D - h))

        for wd in ld.get("walls", []):
            a, b = snap(wd["from"]), snap(wd["to"])
            if _near(a, b):
                raise ModelError(f"Wall {wd['id']} has zero length")
            if abs(a[0] - b[0]) > TOL and abs(a[1] - b[1]) > TOL:
                raise ModelError(f"Wall {wd['id']} is not axis-aligned; only orthogonal walls are supported")
            kind = wd.get("type", "int")
            t = 0.0 if kind == "sep" else float(wd.get("thickness_in", con["int_wall_in"])) / 12.0
            walls.append(Wall(pre + wd["id"], lid, a, b, t, H, kind))

        for rd in ld.get("rooms", []):
            seeds.append({"name": rd["name"], "type": rd.get("type", "room"),
                          "at": tuple(rd["at"]), "level": lid})

        by_id = {w.id: w for w in walls if w.level == lid}
        for od in ld.get("openings", []):
            host = by_id.get(pre + od["host"])
            if host is None:
                raise ModelError(f"Opening {od['id']}: host wall '{od['host']}' does not exist")
            if host.kind == "sep":
                raise ModelError(f"Opening {od['id']}: a separation line cannot host an opening")
            at = float(od["at"])
            if host.horizontal:
                u = (at - host.a[0]) * (1 if host.dir[0] > 0 else -1)
                low_is_a = host.dir[0] > 0
            else:
                u = (at - host.a[1]) * (1 if host.dir[1] > 0 else -1)
                low_is_a = host.dir[1] > 0
            hinge = od.get("hinge", "low")
            hinge_end = "a" if (hinge == "low") == low_is_a else "b"
            kind = od["kind"]
            default_type = {"door": "swing", "window": "single_hung", "cased": "cased"}[kind]
            openings.append(Opening(
                id=pre + od["id"], wall=host.id, kind=kind, center=u,
                width=float(od["width"]), height=float(od["height"]),
                sill=float(od.get("sill", 0.0)), type=od.get("type", default_type),
                hinge=hinge_end, swing_into=od.get("swing_into")))

    rf = spec["roof"]
    roof = Roof(rf["type"], float(rf["pitch"]), float(rf["overhang_ft"]), 0.5)

    site = None
    lot = spec.get("lot")
    if lot:
        sb = lot["setbacks_ft"]
        ox = (lot["width_ft"] - W) / 2.0
        # keep the eave, not just the wall, behind the front setback line
        oy = float(sb["front"]) + float(spec["roof"]["overhang_ft"])
        site = Site(lot["width_ft"], lot["depth_ft"], dict(sb), (ox, oy),
                    float(spec["foundation"]["floor_above_grade_ft"]), dict(lot.get("flood") or {}))

    stairs = []
    for sd in layout.get("stairs", []):
        lv = next(l for l in levels if l.id == sd["level"])
        ups = sorted((l for l in levels if l.elevation > lv.elevation), key=lambda l: l.elevation)
        rise = (ups[0].elevation - lv.elevation) if ups else lv.height
        n = sd.get("risers") or math.ceil(rise * 12 / 7.75)
        stairs.append(Stair(sd["id"], lv.id, tuple(sd["origin"]), tuple(sd["direction"]),
                            float(sd.get("width", 3.0)), rise, n, float(sd.get("tread_in", 10.0)) / 12))

    b = Building(name=spec["project"]["name"], levels=levels, walls=walls, openings=openings,
                 seeds=seeds, roof=roof, site=site, stairs=stairs,
                 meta={"footprint": {"width": W, "depth": D},
                       "layout_source": layout.get("source", "explicit")})
    return b.resolve()
