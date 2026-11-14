"""Validation: geometry sanity, area against target, and code flags.

Every check reads the same model the drawings come from. Statuses:
  PASS  checked and satisfied
  WARN  checked, marginal or advisory
  FAIL  checked and not satisfied
  INFO  cannot be decided from a concept model; listed for the design professional
Thresholds quoted from codes are concept-level screening values and must be
confirmed against the adopted code text by the licensed professional.
"""
from collections import defaultdict

from shapely.geometry import Point

from . import STAMP
from .mesh import roof_geometry
from .model import HABITABLE, UNCONDITIONED
from .units import ft_in, sf


def _clear_opening(o):
    """Estimated net clear opening (width ft, height ft). Conservative; the
    real figure comes from the window manufacturer."""
    if o.kind == "door":
        return (o.width - 2 / 12.0, o.height) if o.type == "swing" else (o.width / 2 - 3 / 12.0, o.height - 2 / 12.0)
    t = o.type
    if t == "single_hung":
        return o.width - 3 / 12.0, o.height / 2 - 6 / 12.0
    if t == "casement":
        return o.width - 4 / 12.0, o.height - 4 / 12.0
    if t == "slider":
        return o.width / 2 - 3 / 12.0, o.height - 4 / 12.0
    return 0.0, 0.0


def _glazing(o):
    """(glazed area, openable area) in sq ft."""
    a = o.width * o.height
    if o.kind == "window":
        return a, a * {"single_hung": 0.5, "slider": 0.5, "casement": 0.9}.get(o.type, 0.0)
    if o.kind == "door" and o.type == "slider":
        return a, a * 0.5
    return 0.0, 0.0


def validate(b, spec):
    checks = []

    def add(cat, status, message, ref=""):
        checks.append({"category": cat, "status": status, "message": message, "ref": ref})

    pr = spec["program"]
    code = spec["code"]
    # ------------------------------------------------------------- model
    for status, msg in b.issues:
        add("Model", status, msg)
    if not b.issues:
        add("Model", "PASS", f"All {len(b.seeds)} named rooms are enclosed and every enclosed space is named.")

    net_all = sum(r.area for r in b.rooms)
    net = sum(r.area for r in b.rooms if r.kind not in UNCONDITIONED)
    walls = sum(b.wall_union(l.id).area for l in b.levels)
    total = b.gross_area()
    uncond = b.unconditioned_area()
    gross = total - uncond                 # conditioned (living) area
    target = float(pr["target_sqft"])
    if abs(net_all + walls - total) < 0.5:
        add("Area", "PASS", f"Room areas reconcile: {net_all:,.1f} sq ft of rooms + {walls:,.1f} sq ft of walls "
            f"= {total:,.1f} sq ft inside the outside face of the walls.")
    else:
        add("Area", "FAIL", f"Rooms ({net_all:,.1f}) plus walls ({walls:,.1f}) do not equal the total area "
            f"({total:,.1f} sq ft); some floor area is unassigned.")
    if uncond:
        parts = ", ".join(f"{r.name} {r.area:,.0f}" for r in b.rooms if r.kind in UNCONDITIONED)
        add("Area", "INFO", f"{uncond:,.0f} sq ft of garage, porch and patio is excluded from living area "
            f"(net: {parts}).")
    d = (gross - target) / target * 100
    st = "PASS" if abs(d) <= 3 else "WARN" if abs(d) <= 5 else "FAIL"
    add("Area", st, f"Gross conditioned area {gross:,.0f} sq ft against the {target:,.0f} sq ft target "
        f"({d:+.1f}%; tolerance 3%). Measured to the outside face of exterior walls"
        + (", excluding garage, porch and patio." if uncond else "."))
    add("Area", "INFO", f"The rooms alone sum to {net:,.0f} sq ft net ({net / target * 100:.0f}% of the target). "
        "The target is treated as gross area, which is how house size is normally quoted; "
        "say so if you meant net room area.")

    n_bed = sum(1 for r in b.rooms if r.kind == "bedroom")
    n_bath = sum(1 for r in b.rooms if r.kind == "bath")
    add("Program", "PASS" if n_bed == int(pr["beds"]) else "FAIL",
        f"{n_bed} bedrooms modelled, {pr['beds']} requested.")
    add("Program", "PASS" if n_bath == float(pr["baths"]) else "FAIL",
        f"{n_bath} bathrooms modelled, {pr['baths']:g} requested.")

    # ---------------------------------------------------- walls / openings
    dangling = [w.id for w in b.walls if w.kind != "sep" and "free" in (w.join_a, w.join_b)]
    if dangling:
        add("Walls", "WARN", "Walls with an unjoined end: " + ", ".join(dangling))
    ext_open = [w.id for w in b.walls if w.kind == "ext" and not (w.join_a.startswith("corner")
                                                                  and w.join_b.startswith("corner"))]
    add("Walls", "FAIL" if ext_open else "PASS",
        "Exterior walls do not form a closed loop: " + ", ".join(ext_open) if ext_open else
        f"Exterior walls form a closed loop; all {sum(1 for w in b.walls if w.kind != 'sep')} walls are joined "
        "at both ends with no overlaps.")

    bad = 0
    for w in b.walls:
        ops = b.openings_in(w.id)
        for o in ops:
            lo, hi = o.ua - w.u0, w.u1 - o.ub
            if lo < 0 or hi < 0:
                add("Openings", "FAIL", f"{o.id} runs past the end of its host wall {w.id}."); bad += 1
            elif min(lo, hi) < 4 / 12.0 - 1e-6:
                add("Openings", "WARN", f"{o.id} is {ft_in(min(lo, hi))} from the end of wall {w.id}; "
                    "less than 4 in. leaves no room for framing at the jamb."); bad += 1
            if o.head > w.height - 0.5 + 1e-6:
                add("Openings", "WARN", f"{o.id} head at {ft_in(o.head)} leaves under 6 in. below the "
                    f"{ft_in(w.height)} plate for a header."); bad += 1
            for other in b.walls_on(w.level):
                if other is w:
                    continue
                for p in (other.a, other.b):
                    if w.line().distance(Point(p)) < 1e-6:
                        u = (p[0] - w.a[0]) * w.dir[0] + (p[1] - w.a[1]) * w.dir[1]
                        if o.ua - other.thickness / 2 < u < o.ub + other.thickness / 2:
                            add("Openings", "FAIL", f"{o.id} in wall {w.id} collides with wall {other.id} "
                                "joining at that point."); bad += 1
            if None in o.rooms:
                add("Openings", "FAIL", f"{o.id} opens onto a space that is not a room."); bad += 1
            if o.kind == "window" and not o.outside:
                add("Openings", "WARN", f"Window {o.id} is in an interior wall."); bad += 1
            if o.kind == "door" and o.rooms[0] == o.rooms[1]:
                add("Openings", "FAIL", f"Door {o.id} has the same room on both sides."); bad += 1
        for p, q in zip(ops, ops[1:]):
            if q.ua - p.ub < 0:
                add("Openings", "FAIL", f"{p.id} and {q.id} overlap in wall {w.id}."); bad += 1
            elif q.ua - p.ub < 0.5:
                add("Openings", "WARN", f"{p.id} and {q.id} are only {ft_in(q.ua - p.ub)} apart in wall {w.id}.")
                bad += 1
    if not bad:
        add("Openings", "PASS", f"All {len(b.openings)} openings sit inside their host wall, clear of wall "
            "junctions and of each other, with header room above.")

    # reachability: every room must be reachable from an exterior door
    adj = defaultdict(set)
    for o in b.openings:
        if o.kind in ("door", "cased") and None not in o.rooms:
            a, c = o.rooms
            adj[a].add(c); adj[c].add(a)
    groups = []           # rooms joined by separation lines (one open space)
    for w in b.walls:
        if w.kind == "sep":
            m = w.length / 2
            a, c = b.room_at(w.pt(m, 0.3), w.level), b.room_at(w.pt(m, -0.3), w.level)
            if a and c:
                adj[a].add(c); adj[c].add(a)
                groups.append({a, c})
    levels = sorted(b.levels, key=lambda l: l.elevation)
    for s_ in b.stairs:           # a stair joins the room at its foot to the room at its head
        up = [l for l in levels if l.elevation > b.level(s_.level).elevation]
        if up:
            head = (s_.origin[0] + (s_.run + 0.5) * s_.direction[0], s_.origin[1] + (s_.run + 0.5) * s_.direction[1])
            a, c = b.room_at(s_.origin, s_.level), b.room_at(head, up[0].id)
            if a and c:
                adj[a].add(c); adj[c].add(a)
    seen, todo = set(), ["exterior"]
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n); todo += list(adj[n])
    lost = [r.name for r in b.rooms if r.name not in seen]
    add("Circulation", "FAIL" if lost else "PASS",
        "No door path from outside reaches: " + ", ".join(lost) if lost else
        "Every room can be reached from an exterior door.")

    spaces = _merge_groups(groups, [r.name for r in b.rooms])

    # ------------------------------------------------------------ IRC
    small = []
    for r in b.rooms:
        if r.kind in HABITABLE:
            if r.area < 70:
                small.append(f"{r.name} is {r.area:.0f} sq ft (70 minimum)")
            if r.kind != "kitchen" and min(r.clear) < 7:
                small.append(f"{r.name} is {ft_in(min(r.clear))} in its short direction (7 ft minimum)")
    add("IRC rooms", "FAIL" if small else "PASS", "; ".join(small) if small else
        "Every habitable room is at least 70 sq ft and 7 ft in its short direction.", "2021 IRC R304")
    low = [l.name for l in b.levels if l.height < 7]
    add("IRC rooms", "FAIL" if low else "PASS",
        f"Ceiling below 7 ft on: {', '.join(low)}" if low else
        f"Ceiling height {ft_in(min(l.height for l in b.levels))} meets the 7 ft minimum.", "2021 IRC R305.1")
    for r in b.rooms:
        if r.kind == "hall":
            add("IRC egress", "PASS" if min(r.clear) >= 3 - 1e-6 else "FAIL",
                f"{r.name} is {ft_in(min(r.clear))} clear (3 ft minimum).", "2021 IRC R311.6")

    egress_doors = [o for o in b.openings if o.kind == "door" and o.exterior and o.type == "swing"
                    and o.width >= 3.0 - 1e-6 and o.height >= 6.6666]
    add("IRC egress", "PASS" if egress_doors else "FAIL",
        f"Egress door: {egress_doors[0].id}, side-hinged, {ft_in(egress_doors[0].width)} x "
        f"{ft_in(egress_doors[0].height)}." if egress_doors else
        "No side-hinged exterior door at least 3'-0\" x 6'-8\".", "2021 IRC R311.2")

    for r in b.rooms:
        if r.kind != "bedroom":
            continue
        best = None
        for o in b.openings:
            if r.name in o.rooms and o.exterior:
                cw, ch = _clear_opening(o)
                ok = cw * ch >= 5.7 and cw >= 20 / 12.0 and ch >= 24 / 12.0 and o.sill <= 44 / 12.0
                if ok and (best is None or cw * ch > best[1]):
                    best = (o, cw * ch, cw, ch)
        if best:
            o, a, cw, ch = best
            add("IRC egress", "PASS", f"{r.name}: {o.id} ({ft_in(o.width)} x {ft_in(o.height)} {o.type.replace('_', ' ')}, "
                f"sill {ft_in(o.sill)}) gives an estimated {a:.1f} sq ft clear opening "
                f"({cw * 12:.0f} x {ch * 12:.0f} in.); 5.7 sq ft, 20 in. wide, 24 in. high, sill 44 in. max required.",
                "2021 IRC R310.2")
        else:
            add("IRC egress", "FAIL", f"{r.name} has no exterior opening that meets emergency escape size "
                "(5.7 sq ft clear, 20 in. wide, 24 in. high, sill no higher than 44 in.).", "2021 IRC R310")

    for names in spaces:
        rs = [b.room(n) for n in names]
        if not any(r.kind in HABITABLE for r in rs):
            continue
        rs = [r for r in rs if r.kind in HABITABLE]
        area = sum(r.area for r in rs)
        gl = op = 0.0
        for o in b.openings:
            if o.exterior and any(r.name in o.rooms for r in rs):
                g_, o_ = _glazing(o)
                gl += g_; op += o_
        label = " + ".join(r.name for r in rs)
        ok_l, ok_v = gl >= 0.08 * area, op >= 0.04 * area
        add("IRC light and air", "PASS" if ok_l and ok_v else "FAIL",
            f"{label}: {gl:.0f} sq ft glazing ({gl / area * 100:.1f}% of {area:.0f} sq ft floor; 8% required), "
            f"{op:.0f} sq ft openable ({op / area * 100:.1f}%; 4% required).", "2021 IRC R303.1")
    for r in b.rooms:
        if r.kind == "bath":
            gl = sum(_glazing(o)[0] for o in b.openings if o.exterior and r.name in o.rooms)
            if gl >= 3:
                add("IRC light and air", "PASS", f"{r.name}: {gl:.0f} sq ft window (3 sq ft, half openable, required "
                    "unless mechanically exhausted).", "2021 IRC R303.3")
            else:
                add("IRC light and air", "INFO", f"{r.name} has no window, so it needs a mechanical exhaust fan "
                    "ducted outdoors is required.", "2021 IRC R303.3")
    for s in b.stairs:
        ok = s.riser_height * 12 <= 7.75 + 1e-6 and s.tread * 12 >= 10 - 1e-6 and s.width >= 3 - 1e-6
        add("IRC egress", "PASS" if ok else "FAIL",
            f"Stair {s.id}: {s.risers} risers at {s.riser_height * 12:.2f} in., {s.tread * 12:.1f} in. treads, "
            f"{ft_in(s.width)} wide (7-3/4 in. max riser, 10 in. min tread, 36 in. min width).", "2021 IRC R311.7")

    # ------------------------------------------------------------ site
    site_rows = []
    rg = roof_geometry(b)
    if b.site:
        s = b.site
        lot = s.lot_polygon()
        fp = b.footprint()
        buildable = s.buildable_polygon()
        lx0, ly0, lx1, ly1 = lot.bounds
        hx0, hy0, hx1, hy1 = fp.bounds
        yards = {"front": hy0 - ly0, "rear": ly1 - hy1, "left side": hx0 - lx0, "right side": lx1 - hx1}
        req = {"front": s.setbacks["front"], "rear": s.setbacks["rear"],
               "left side": s.setbacks["side"], "right side": s.setbacks["side"]}
        inside = buildable.buffer(1e-6).contains(fp)
        add("Site", "PASS" if inside else "FAIL",
            "Walls are inside all setbacks: " + ", ".join(f"{k} {ft_in(v)} (min {ft_in(req[k])})"
                                                          for k, v in yards.items()) + "."
            if inside else "The house crosses a setback line: " +
            ", ".join(f"{k} {ft_in(v)} (min {ft_in(req[k])})" for k, v in yards.items() if v < req[k] - 1e-6))
        ex0, ey0, ex1, ey1 = rg["eave"]
        eaves = {"front": ey0 - ly0, "rear": ly1 - ey1, "left side": ex0 - lx0, "right side": lx1 - ex1}
        over = [k for k in eaves if eaves[k] < req[k] - 1e-6]
        if over:
            add("Site", "WARN", f"The roof overhang projects into the {', '.join(over)} setback; confirm the "
                "zoning ordinance allows eave projections into required yards.")
        min_side = min(yards["left side"], yards["right side"])
        min_eave = min(eaves["left side"], eaves["right side"])
        add("IRC fire separation", "PASS" if min_side >= 5 and min_eave >= 5 else "WARN",
            f"Walls are {ft_in(min_side)} and eaves {ft_in(min_eave)} from the nearest side lot line; "
            "5 ft or more needs no fire-resistance rating.", "2021 IRC R302.1")
        cov = fp.area / lot.area * 100
        add("Site", "INFO", f"Lot coverage {cov:.1f}% by walls, {(ex1 - ex0) * (ey1 - ey0) / lot.area * 100:.1f}% "
            "under roof. No coverage limit was given in the spec; check the zoning district.")
        fl = s.flood or {}
        zone = str(fl.get("zone", "")).upper()
        fb = code["flood_freeboard_ft"]
        basis = code.get("flood_basis", "bfe")
        key, label = ("flood_500yr_ft", "0.2% (500-year) flood elevation") if basis == "500yr" else ("bfe_ft", "BFE")
        rule = f"{code['jurisdiction']}: {label} + {fb:g} ft"
        if fl.get(key) is not None and fl.get("grade_ft") is not None:
            ffe = fl["grade_ft"] + s.floor_above_grade
            need = fl[key] + fb
            add("Flood", "PASS" if ffe >= need - 1e-6 else "FAIL",
                f"Finished floor at elevation {ffe:.2f} ft; required {need:.2f} ft ({label} {fl[key]:.2f} + "
                f"{fb:g} ft).", rule)
        elif zone in ("X", "C", "B"):
            add("Flood", "INFO", f"Spec states flood zone {zone}, outside the special flood hazard area. Finished floor "
                f"is modelled {ft_in(s.floor_above_grade)} above grade. Confirm the zone on the current FEMA map "
                "and with the floodplain administrator before relying on this.", rule)
        else:
            add("Flood", "FAIL", f"The lot is not stated to be outside the flood zone, and the spec lacks "
                f"lot.flood.{key} and lot.flood.grade_ft; the finished-floor height cannot be set.", rule)
        site_rows = [("Lot", f"{ft_in(s.lot_width, 1)} x {ft_in(s.lot_depth, 1)} = {sf(lot.area)}"),
                     ("Setbacks (front / side / rear)", " / ".join(ft_in(s.setbacks[k], 1) for k in ("front", "side", "rear"))),
                     ("Buildable area", f"{ft_in(buildable.bounds[2] - buildable.bounds[0], 1)} x "
                                        f"{ft_in(buildable.bounds[3] - buildable.bounds[1], 1)}"),
                     ("House footprint", f"{ft_in(hx1 - hx0, 1)} x {ft_in(hy1 - hy0, 1)}"),
                     ("Yards: front / rear", f"{ft_in(yards['front'], 1)} / {ft_in(yards['rear'], 1)}"),
                     ("Yards: left / right", f"{ft_in(yards['left side'], 1)} / {ft_in(yards['right side'], 1)}"),
                     ("Lot coverage", f"{cov:.1f}%"),
                     ("Finished floor above grade", ft_in(s.floor_above_grade))]

    # ------------------------------------------------------------ wind
    if not rg["rectangular"]:
        add("Roof", "WARN", "The footprint is not a rectangle; the roof generator covers only its bounding "
            "rectangle. Model this roof by hand.")
    fag = b.site.floor_above_grade if b.site else 0
    mean_roof = (rg["ze"] + rg["zr"]) / 2 + fag
    x0, y0, x1, y1 = b.footprint().bounds
    add("Windstorm", "INFO", f"Geometry for the engineer's ICC 600 applicability check: {len(b.levels)} storey, "
        f"{ft_in(x1 - x0, 1)} x {ft_in(y1 - y0, 1)} plan, {b.roof.type} roof at {b.roof.pitch:g}:12, "
        f"{ft_in(b.roof.overhang)} overhangs, mean roof height {ft_in(mean_roof, 1)} above grade.", "ICC 600-2020")
    for w in b.walls:
        if w.kind != "ext":
            continue
        ops = b.openings_in(w.id)
        ratio = sum(o.width for o in ops) / (w.u1 - w.u0)
        if ratio > 0.5:
            add("Windstorm", "WARN", f"Openings take {ratio * 100:.0f}% of exterior wall {w.id}; little length is "
                "left for braced or shear wall panels.", "ICC 600-2020 (engineer to design)")
        for o in ops:
            edge = min(o.ua - w.u0, w.u1 - o.ub)
            if edge < 2.0:
                add("Windstorm", "WARN", f"{o.id} is {ft_in(edge)} from the corner of wall {w.id}; corners normally "
                    "need a full-height braced panel.", "ICC 600-2020 (engineer to design)")
    glazed = [o for o in b.openings if o.exterior and _glazing(o)[0] > 0]
    ga = sum(_glazing(o)[0] for o in glazed)
    wall_face = sum((w.u1 - w.u0) * w.height for w in b.walls if w.kind == "ext")
    add("Windstorm", "INFO", f"{len(glazed)} glazed openings totalling {ga:.0f} sq ft ({ga / wall_face * 100:.0f}% of "
        "exterior wall area), plus the exterior doors, need TDI-evaluated products rated for the site's design "
        "pressures, and impact protection if the lot is in the wind-borne debris region. The design wind speed "
        "and TDI zone for this address have not been established.", "TDI / TWIA")
    if code.get("windstorm_applies") == "check":
        add("Windstorm", "INFO", "Windstorm certification applies only if the lot is inside the TDI designated "
            "catastrophe area. Confirm the address with TDI before deciding; the items below assume it may apply.",
            "TDI / TWIA")
    add("Windstorm", "INFO", "A WPI-8 certificate depends on inspections by a TDI-appointed engineer or inspector "
        "during construction (foundation, framing, roofing, openings). It cannot be established from drawings; "
        "arrange the inspections before work starts.", "TDI WPI-8")
    add("Windstorm", "INFO", "Roof-to-wall and wall-to-foundation connections, sheathing nailing, braced wall "
        "lines and uplift load path are not modelled.", "ICC 600-2020")

    garages = [r.name for r in b.rooms if r.kind == "garage"]
    if garages:
        beds = {r.name for r in b.rooms if r.kind == "bedroom"}
        bad_doors = [o.id for o in b.openings if o.kind == "door" and set(o.rooms) & set(garages) and set(o.rooms) & beds]
        add("IRC garage", "FAIL" if bad_doors else "PASS",
            f"Door {', '.join(bad_doors)} opens from the garage directly into a bedroom." if bad_doors else
            "No door opens from the garage directly into a bedroom.", "2021 IRC R302.5.1")
        add("IRC garage", "INFO", "The door between garage and house must be solid or 20-minute rated, and the "
            "garage side of shared walls and ceilings needs gypsum board separation. Not modelled.",
            "2021 IRC R302.5, R302.6")
    for item in code.get("to_confirm", []):
        add("Code baseline", "INFO", item, code["jurisdiction"])

    # ------------------------------------------- not modelled, by code
    add("Not modelled", "INFO", "Energy: insulation, window U-factor and SHGC, air sealing and duct design for "
        "climate zone 2A are not modelled.", "2021 IECC")
    add("Not modelled", "INFO", "Electrical: service, panel, receptacle spacing, GFCI and AFCI protection, smoke "
        "and carbon-monoxide alarms are not modelled.", "2020 NEC; 2021 IRC R314, R315")
    add("Not modelled", "INFO", "Plumbing: fixture layout and clearances, water heater, drain-waste-vent and "
        "supply sizing are not modelled. Bathrooms are sized as rooms only.", "2021 IPC; 2021 IRC R307")
    add("Not modelled", "INFO", "Structure: foundation, framing, headers, roof trusses and soils are not "
        "designed. Jefferson County clay soils normally call for an engineered slab.", "2021 IRC ch. 4-8")

    # ---------------------------------------------------------- budget
    ext_len = sum(w.u1 - w.u0 for w in b.walls if w.kind == "ext")
    int_len = sum(w.u1 - w.u0 for w in b.walls if w.kind == "int")
    qty = [("Gross floor area", sf(gross)), ("Slab / footprint area", sf(b.footprint().area)),
           ("Roof surface area", sf(rg["area"])), ("Exterior wall length", f"{ext_len:,.0f} ft"),
           ("Interior partition length", f"{int_len:,.0f} ft"),
           ("Exterior doors", str(sum(1 for o in b.openings if o.kind == "door" and o.exterior))),
           ("Interior doors", str(sum(1 for o in b.openings if o.kind == "door" and not o.exterior))),
           ("Windows", f"{sum(1 for o in b.openings if o.kind == 'window')} ({ga:.0f} sq ft glazing incl. glazed doors)"),
           ("Bathrooms / wet rooms", f"{n_bath} baths + kitchen + laundry")]
    bd = spec.get("budget") or {}
    if bd.get("sale_price_usd") and bd.get("lot_cost_usd") is not None:
        from .budget import OTHER, construction_budget
        cb = construction_budget(bd["sale_price_usd"], bd["lot_cost_usd"])
        need = cb / gross
        msg = (f"Sale price ${bd['sale_price_usd']:,.0f} less the ${bd['lot_cost_usd']:,.0f} lot and {OTHER * 100:.1f}% for "
               f"builder overhead, profit, sales and financing (NAHB 2024 national shares) leaves ${cb:,.0f} to "
               f"build with: ${need:,.0f} per sq ft of living area for this {gross:,.0f} sq ft house, with garage, "
               "porch, patio and site work paid from the same sum.")
        cps = bd.get("build_cost_per_sqft")
        if cps:
            st_ = "PASS" if need >= cps else "FAIL"
            msg += f" The spec's build cost is ${cps:,.0f} per sq ft, so the budget supports {cb / cps:,.0f} sq ft."
        else:
            st_ = "INFO"
            msg += " No build cost per sq ft was given, so this is not judged."
        add("Budget", st_, msg)
    budget = bd.get("total_usd")
    if budget:
        add("Budget", "INFO", f"${budget:,.0f} over {gross:,.0f} sq ft is ${budget / gross:,.0f} per sq ft if the "
            "whole budget goes to the building. The pipeline does not price construction: no current local cost "
            "data was provided, and the spec does not say whether the budget includes land, site work, utility "
            "connections, fees, and windstorm-rated products. Use the quantities below to get builder pricing.")
        add("Budget", "INFO", "Cost-conscious choices already in this concept: a plain rectangle, one roof form, "
            "no hallway beyond a 4 ft vestibule, kitchen, laundry and primary bath plumbing grouped on one side, "
            "and a modest window count.")

    counts = {k: sum(1 for c in checks if c["status"] == k) for k in ("PASS", "WARN", "FAIL", "INFO")}
    return {
        "summary": {"net_area": net, "wall_area": walls, "gross_area": gross, "target": target, "delta_pct": d,
                    "unconditioned_area": uncond, "total_area": total, "net_all": net_all},
        "site_rows": site_rows, "counts": counts, "checks": checks, "quantities": qty,
        "rooms": [{"name": r.name, "kind": r.kind, "level": r.level, "area": round(r.area, 1),
                   "clear": [round(r.clear[0], 2), round(r.clear[1], 2)]} for r in b.rooms],
    }


def _merge_groups(pairs, names):
    groups = [{n} for n in names]
    for pair in pairs:
        hit = [g for g in groups if g & pair]
        merged = set().union(*hit) if hit else set(pair)
        groups = [g for g in groups if not (g & pair)] + [merged]
    return [sorted(g, key=names.index) for g in groups]


def report_markdown(b, spec, report, files):
    s, c = report["summary"], report["counts"]
    L = [f"# Validation report: {spec['project']['name']}", "",
         f"> **{STAMP}**", "",
         f"Generated from `model.json`. Code baseline: {spec['code']['jurisdiction']}: "
         f"{', '.join(spec['code']['codes'])}; {spec['code']['windstorm']}.", "",
         "## Result", "",
         f"**{c['FAIL']} failures, {c['WARN']} warnings, {c['PASS']} checks passed.** "
         f"{c['INFO']} further items cannot be decided from a concept model and are listed for the design professional.", "",
         "## Area against target", "",
         "| Measure | Sq ft |", "|---|---:|",
         f"| Target | {s['target']:,.0f} |",
         f"| Conditioned (living) area, to outside face of exterior walls | {s['gross_area']:,.1f} |",
         f"| Difference from target | {s['gross_area'] - s['target']:+,.1f} ({s['delta_pct']:+.1f}%) |",
         f"| Sum of net areas of conditioned rooms | {s['net_area']:,.1f} |",
         f"| Garage, porch and patio (excluded from living area) | {s['unconditioned_area']:,.1f} |",
         f"| Area occupied by walls | {s['wall_area']:,.1f} |",
         f"| Total inside outside face of walls | {s['total_area']:,.1f} |", "",
         "## Rooms", "", "| Room | Type | Net area (sq ft) | Clear size |", "|---|---|---:|---|"]
    for r in sorted(b.rooms, key=lambda r: -r.area):
        L.append(f"| {r.name} | {r.kind} | {r.area:,.1f} | {ft_in(r.clear[0], 1)} x {ft_in(r.clear[1], 1)} |")
    L.append(f"| **Total, all rooms** | | **{s['net_all']:,.1f}** | |")
    L += ["", "Clear size is the largest rectangle that fits inside the room, so an L-shaped room has more "
              "area than its clear size implies.", ""]
    if report["site_rows"]:
        L += ["## Site", "", "| Item | Value |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in report["site_rows"]]
        L.append("")
    L += ["## Checks", ""]
    order = ["FAIL", "WARN", "PASS", "INFO"]
    title = {"FAIL": "Failures", "WARN": "Warnings", "PASS": "Passed",
             "INFO": "For the design professional (not decidable from this model)"}
    for st in order:
        rows = [k for k in report["checks"] if k["status"] == st]
        if not rows:
            continue
        L += [f"### {title[st]}", "", "| Area | Finding | Reference |", "|---|---|---|"]
        L += [f"| {k['category']} | {k['message']} | {k['ref']} |" for k in rows]
        L.append("")
    L += ["## Quantities for pricing", "", "| Item | Quantity |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in report["quantities"]]
    L.append("")
    if spec.get("assumptions"):
        L += ["## Assumptions to confirm", ""] + [f"- {a}" for a in spec["assumptions"]] + [""]
    L += ["## Files", "", "| File | What it is |", "|---|---|"]
    L += [f"| `{k}` | {v} |" for k, v in files]
    L += ["", "Code thresholds in this report are screening values applied to a concept model. "
              "They do not replace plan review or the judgement of a licensed architect or engineer.", ""]
    return "\n".join(L)
