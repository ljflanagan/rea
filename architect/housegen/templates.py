"""Layout templates: turn a program (beds, baths, area, lot) into a layout
program (footprint, interior walls, room seeds, hosted openings).

A template only decides *where things go*. It emits the same layout-program
dictionary a designer can write by hand under `layout:` in a spec, and from
there on the model, not the template, is the source of truth.
"""
from .units import r05


class TemplateError(Exception):
    """The template cannot honour the spec; a hand-authored layout is needed."""


def generate_layout(spec):
    name = spec["preferences"].get("template", "split_ranch")
    if name not in TEMPLATES:
        raise TemplateError(f"Unknown template '{name}'. Available: {', '.join(TEMPLATES)}")
    return TEMPLATES[name](spec)


def split_ranch(spec):
    """One-storey rectangle, three bays across the frontage:
    primary suite | living over kitchen+dining | two bedrooms sharing a bath.
    A rectangle under one simple roof is the cheapest shape to frame and the
    easiest to tie down for wind."""
    pr, lot = spec["program"], spec["lot"]
    beds, baths, area = int(pr["beds"]), float(pr["baths"]), float(pr["target_sqft"])
    if int(pr.get("stories", 1)) != 1:
        raise TemplateError("split_ranch is single-storey; author a layout for multi-storey programs")
    if beds not in (2, 3) or baths != 2:
        raise TemplateError(f"split_ranch covers 2-3 bedrooms with 2 baths, not {beds} bed / {baths:g} bath; "
                            "author a layout for this program")
    if not 1100 <= area <= 1900:
        raise TemplateError(f"split_ranch is proportioned for 1,100-1,900 sq ft, not {area:,.0f}; "
                            "author a layout for this program")

    sb = lot["setbacks_ft"]
    max_w = lot["width_ft"] - 2 * sb["side"]
    max_d = lot["depth_ft"] - sb["front"] - sb["rear"]
    W = min(r05((1.5 * area) ** 0.5), r05(max_w - 0.25))
    D = r05(area / W)
    if D > max_d or W < 40:
        raise TemplateError(f"A {area:,.0f} sq ft split_ranch needs about {W:g} x {D:g} ft but the buildable "
                            f"area is {max_w:g} x {max_d:g} ft; author a layout for this lot")

    xl = r05(0.30 * W)                    # primary suite | public
    xr = W - min(max(r05(0.31 * W), 13.0), 15.5)   # public | secondary bedrooms
    y_pb = r05(0.483 * D)                 # primary bedroom | bath + closet
    y_ut = r05(0.767 * D)                 # bath + closet | utility
    x_pb = r05(0.63 * xl)                 # primary bath | walk-in closet
    x_me = r05(0.41 * xl)                 # mechanical | laundry
    y_lv = r05(0.533 * D)                 # living | kitchen + dining
    x_kd = r05(xl + 0.515 * (xr - xl))    # kitchen | dining
    y_b2 = r05(0.40 * D)                  # bedroom 2 | hall + bath 2
    y_b3 = y_b2 + 6.0                     # hall + bath 2 | bedroom 3
    x_hl = xr + 4.0                       # hall | bath 2
    x_cl = xr + 2.5                       # closet depth
    y_c2 = r05(0.54 * y_b2)               # bedroom 2 closet length
    y_c3 = D - r05(0.54 * (D - y_b3))

    third = "Bedroom 3" if beds == 3 else "Study"
    walls = [
        {"id": "W-A", "from": [xl, 0], "to": [xl, D]},
        {"id": "W-B1", "from": [xr, 0], "to": [xr, y_b2]},
        {"id": "W-B2", "from": [xr, y_b3], "to": [xr, D]},
        {"id": "S-HALL", "from": [xr, y_b2], "to": [xr, y_b3], "type": "sep"},
        {"id": "W-P1", "from": [0, y_pb], "to": [xl, y_pb]},
        {"id": "W-P2", "from": [x_pb, y_pb], "to": [x_pb, y_ut]},
        {"id": "W-P3", "from": [0, y_ut], "to": [xl, y_ut]},
        {"id": "W-P4", "from": [x_me, y_ut], "to": [x_me, D]},
        {"id": "S-LIV", "from": [xl, y_lv], "to": [xr, y_lv], "type": "sep"},
        {"id": "S-KD", "from": [x_kd, y_lv], "to": [x_kd, D], "type": "sep"},
        {"id": "W-R1", "from": [xr, y_b2], "to": [W, y_b2]},
        {"id": "W-R2", "from": [xr, y_b3], "to": [W, y_b3]},
        {"id": "W-R3", "from": [x_hl, y_b2], "to": [x_hl, y_b3]},
        {"id": "W-C2a", "from": [x_cl, 0], "to": [x_cl, y_c2]},
        {"id": "W-C2b", "from": [xr, y_c2], "to": [x_cl, y_c2]},
    ]
    rooms = [
        {"name": "Primary Bedroom", "type": "bedroom", "at": [xl / 2, y_pb / 2]},
        {"name": "Primary Bath", "type": "bath", "at": [x_pb / 2, (y_pb + y_ut) / 2]},
        {"name": "Primary Closet", "type": "closet", "at": [(x_pb + xl) / 2, (y_pb + y_ut) / 2]},
        {"name": "Mechanical", "type": "mech", "at": [x_me / 2, (y_ut + D) / 2]},
        {"name": "Laundry", "type": "utility", "at": [(x_me + xl) / 2, (y_ut + D) / 2]},
        {"name": "Living", "type": "living", "at": [(xl + xr) / 2, y_lv / 2]},
        {"name": "Kitchen", "type": "kitchen", "at": [(xl + x_kd) / 2, (y_lv + D) / 2]},
        {"name": "Dining", "type": "dining", "at": [(x_kd + xr) / 2, (y_lv + D) / 2]},
        {"name": "Bedroom 2", "type": "bedroom", "at": [(x_cl + W) / 2, y_b2 / 2]},
        {"name": "Closet 2", "type": "closet", "at": [(xr + x_cl) / 2, y_c2 / 2]},
        {"name": "Hall", "type": "hall", "at": [(xr + x_hl) / 2, (y_b2 + y_b3) / 2]},
        {"name": "Bath 2", "type": "bath", "at": [(x_hl + W) / 2, (y_b2 + y_b3) / 2]},
        {"name": third, "type": "bedroom" if beds == 3 else "study", "at": [(x_cl + W) / 2, (y_b3 + D) / 2]},
    ]
    EG = {"kind": "window", "type": "single_hung", "width": 3.0, "height": 6.0, "sill": 1.0}
    SM = {"kind": "window", "type": "single_hung", "width": 2.0, "height": 3.0, "sill": 4.0}
    hall_c = (xr + x_hl) / 2
    live_w = xr - xl
    openings = [
        # exterior doors
        {"id": "D01", "host": "ext-front", "at": xl + 3.0, "kind": "door", "width": 3.0, "height": 6.6667,
         "hinge": "low", "swing_into": "Living"},
        {"id": "D02", "host": "ext-back", "at": (x_kd + xr) / 2, "kind": "door", "type": "slider",
         "width": 6.0, "height": 6.6667},
        # interior doors
        {"id": "D03", "host": "W-A", "at": y_pb - 2.0, "kind": "door", "width": 2.6667, "height": 6.6667,
         "hinge": "high", "swing_into": "Primary Bedroom"},
        {"id": "D04", "host": "W-P1", "at": x_pb - 2.0, "kind": "door", "width": 2.5, "height": 6.6667,
         "hinge": "high", "swing_into": "Primary Bath"},
        {"id": "D05", "host": "W-P1", "at": (x_pb + xl) / 2, "kind": "door", "width": 2.3333, "height": 6.6667,
         "hinge": "low", "swing_into": "Primary Closet"},
        {"id": "D06", "host": "W-A", "at": y_ut + 3.0, "kind": "door", "width": 2.6667, "height": 6.6667,
         "hinge": "low", "swing_into": "Laundry"},
        {"id": "D07", "host": "W-P4", "at": y_ut + 3.5, "kind": "door", "width": 2.5, "height": 6.6667,
         "hinge": "high", "swing_into": "Mechanical"},
        {"id": "D08", "host": "W-R1", "at": hall_c, "kind": "door", "width": 2.6667, "height": 6.6667,
         "hinge": "low", "swing_into": "Bedroom 2"},
        {"id": "D09", "host": "W-R2", "at": hall_c, "kind": "door", "width": 2.6667, "height": 6.6667,
         "hinge": "low", "swing_into": third},
        {"id": "D10", "host": "W-R3", "at": (y_b2 + y_b3) / 2, "kind": "door", "width": 2.5, "height": 6.6667,
         "hinge": "low", "swing_into": "Bath 2"},
        {"id": "D11", "host": "W-C2a", "at": y_c2 / 2, "kind": "door", "type": "bifold",
         "width": 4.0, "height": 6.6667, "swing_into": "Bedroom 2"},
        # windows
        dict(EG, id="N01", host="ext-front", at=xl / 2),
        dict(EG, id="N02", host="ext-left", at=y_pb / 2),
        dict(EG, id="N03", host="ext-front", at=r05(xl + 0.49 * live_w)),
        dict(EG, id="N04", host="ext-front", at=r05(xl + 0.77 * live_w)),
        dict(EG, id="N05", host="ext-front", at=(x_cl + W) / 2),
        dict(EG, id="N06", host="ext-back", at=(x_cl + W) / 2),
        dict(SM, id="N07", host="ext-left", at=(y_pb + y_ut) / 2),
        dict(SM, id="N08", host="ext-right", at=(y_b2 + y_b3) / 2),
        {"id": "N09", "host": "ext-back", "at": (xl + x_kd) / 2, "kind": "window", "type": "single_hung",
         "width": 3.0, "height": 3.0, "sill": 4.0},
    ]
    if beds == 3:
        walls += [
            {"id": "W-C3a", "from": [x_cl, y_c3], "to": [x_cl, D]},
            {"id": "W-C3b", "from": [xr, y_c3], "to": [x_cl, y_c3]},
        ]
        rooms.append({"name": "Closet 3", "type": "closet", "at": [(xr + x_cl) / 2, (y_c3 + D) / 2]})
        openings.append({"id": "D12", "host": "W-C3a", "at": (y_c3 + D) / 2, "kind": "door", "type": "bifold",
                         "width": 4.0, "height": 6.6667, "swing_into": third})

    layout = {"source": "template:split_ranch", "footprint": {"width": W, "depth": D},
              "walls": walls, "rooms": rooms, "openings": openings}
    if spec["preferences"].get("primary_side", "left") == "right":
        layout = mirror_x(layout)
    return layout


def mirror_x(layout):
    """Mirror a layout left-to-right about the footprint centre."""
    W = layout["footprint"]["width"]
    swap = {"ext-left": "ext-right", "ext-right": "ext-left"}
    flip = {"low": "high", "high": "low"}
    out = dict(layout, walls=[], rooms=[], openings=[])
    vertical = set()
    for w in layout["walls"]:
        if w["from"][0] == w["to"][0]:
            vertical.add(w["id"])
        out["walls"].append(dict(w, **{"from": [W - w["from"][0], w["from"][1]],
                                       "to": [W - w["to"][0], w["to"][1]]}))
    for r in layout["rooms"]:
        out["rooms"].append(dict(r, at=[W - r["at"][0], r["at"][1]]))
    for o in layout["openings"]:
        host = swap.get(o["host"], o["host"])
        runs_x = o["host"] in ("ext-front", "ext-back") or (o["host"] not in swap and o["host"] not in vertical)
        n = dict(o, host=host)
        if runs_x:
            n["at"] = W - o["at"]
            if "hinge" in o:
                n["hinge"] = flip[o["hinge"]]
        out["openings"].append(n)
    return out


TEMPLATES = {"split_ranch": split_ranch}
