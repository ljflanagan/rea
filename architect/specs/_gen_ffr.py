"""Writes the First Flanagan Realty plan specs. Run: python3 specs/_gen_ffr.py
Coordinates are feet from the outside face of the front-left corner."""
import os
import yaml

H = 6.6667
def door(i, host, at, w=2.6667, into=None, hinge="low", **k):
    d = {"id": i, "host": host, "at": at, "kind": "door", "width": w, "height": H, "hinge": hinge}
    if into: d["swing_into"] = into
    d.update(k); return d
def bifold(i, host, at, into): return {"id": i, "host": host, "at": at, "kind": "door", "type": "bifold", "width": 4.0, "height": H, "swing_into": into}
def win(i, host, at, w=3.0, h=6.0, sill=1.0, t="single_hung"): return {"id": i, "host": host, "at": at, "kind": "window", "type": t, "width": w, "height": h, "sill": sill}
def sig(i, host, at, w=8.0): return win(i, host, at, w, 6.0, 1.5, "fixed")      # signature picture window
def small(i, host, at): return win(i, host, at, 2.0, 3.0, 4.0)
def sink(i, host, at): return win(i, host, at, 3.0, 3.0, 4.0)
def cased(i, host, at, w, h=8.0): return {"id": i, "host": host, "at": at, "kind": "cased", "width": w, "height": h}
def W(i, a, b, t=None):
    d = {"id": i, "from": list(a), "to": list(b)}
    if t: d["type"] = t
    return d
def R(name, typ, at): return {"name": name, "type": typ, "at": list(at)}
GD = {"id": "GD", "host": "ext-front", "at": 28, "kind": "door", "type": "overhead", "width": 16.0, "height": 7.0}

def wing(D, y1, y2, y3, y4, y5):
    """Left bedroom wing shared by all plans: Bedroom 2 | bath 2 | Bedroom 3 | primary bath + closet | Primary Bedroom."""
    walls = [W("WA1",(14,0),(14,y1)), W("WA2",(14,y2),(14,D)),
             W("L1",(0,y1),(14,y1)), W("L2",(0,y2),(14,y2)), W("L3",(10,y1),(10,y2)),
             W("C2a",(11.5,0),(11.5,6)), W("C2b",(11.5,6),(14,6)),
             W("C3a",(11.5,y3-6),(11.5,y3)), W("C3b",(11.5,y3-6),(14,y3-6)),
             W("L4",(0,y3),(14,y3)), W("L5",(0,y4),(14,y4)), W("L6",(8.5,y3),(8.5,y4)),
             W("P1",(14,4),(18.5,4)), W("G1",(18.5,0),(18.5,20.5))]
    rooms = [R("Bedroom 2","bedroom",(5.5,5)), R("Closet 2","closet",(12.75,3)), R("Bath 2","bath",(5,(y1+y2)/2)),
             R("Bedroom 3","bedroom",(5.5,(y2+y3)/2)), R("Closet 3","closet",(12.75,y3-3)),
             R("Primary Bath","bath",(4.25,(y3+y4)/2)), R("Primary Closet","closet",(11.25,(y3+y4)/2)),
             R("Primary Bedroom","bedroom",(7,(y4+D)/2)), R("Porch","porch",(16.25,2)), R("Entry Hall","hall",(16.25,12)),
             R("Garage","garage",(28,10))]
    ops = [cased("PO","ext-front",16.25,3.0), door("D01","P1",16.25,3.0,"Entry Hall"), dict(GD),
           door("D05","L1",12,into="Bedroom 2",hinge="high"), door("D06","L2",12,into="Bedroom 3",hinge="high"),
           door("D07","L3",(y1+y2)/2,2.5,"Bath 2"), bifold("D08","C2a",3,"Bedroom 2"), bifold("D09","C3a",y3-3,"Bedroom 3"),
           door("D10","WA2",y4+2.5,into="Primary Bedroom"), door("D11","L5",4.25,2.5,"Primary Bath"),
           door("D12","L5",11.25,2.3333,"Primary Closet"),
           win("N01","ext-front",5.75), win("N02","ext-left",(y2+y3-6)/2+0.5), small("N03","ext-left",(y1+y2)/2),
           small("N04","ext-left",(y3+y4)/2),
           sig("S01","ext-back",7), win("N06","ext-left",(y4+D)/2)]
    return walls, rooms, ops

PLANS = {}

# ---- Plan 1: the cheapest house that meets every standard -----------------------------------
D = 44
w, r, o = wing(D, 10.5, 16, 26, 32, D)
PLANS["ffr-1"] = dict(beds=3, baths=2, sqft=1250, name="First Flanagan Plan 1: 3 Bed / 2 Bath",
  layout={"footprint": {"width": 38, "depth": D},
  "walls": w + [W("G2",(18.5,20.5),(38,20.5)), W("U1",(31,20.5),(31,27)), W("U2",(31,27),(38,27)),
                W("PN1",(27,20.5),(27,24.5)), W("PN2",(27,24.5),(31,24.5)),
                W("S-EK",(14,20.5),(18.5,20.5),"sep"), W("S-KF",(14,32),(38,32),"sep")],
  "rooms": r + [R("Utility","utility",(34.5,23.75)), R("Pantry","closet",(29,22.5)),
                R("Kitchen + Dining","kitchen",(22,26)), R("Family Room","living",(26,38))],
  "openings": o + [door("D02","G2",34.5,into="Utility"), door("D03","U2",34.5,2.5,"Utility"),
                door("D04","PN2",29,2.0,"Kitchen + Dining"),
                sig("S02","ext-back",24), door("D13","ext-back",33,3.0,"Family Room"),
                win("N07","ext-right",34.5), win("N08","ext-right",39.5), sink("N09","ext-right",29.5)]})

# ---- Plan 2: adds a covered patio ---------------------------------------------------------------
D = 48
w, r, o = wing(D, 11.5, 17.5, 29, 36, D)
PLANS["ffr-2"] = dict(beds=3, baths=2, sqft=1265, name="First Flanagan Plan 2: 3 Bed / 2 Bath with Covered Patio",
  layout={"footprint": {"width": 38, "depth": D},
  "walls": w + [W("G2",(18.5,20.5),(38,20.5)), W("U1",(31,20.5),(31,27)), W("U2",(31,27),(38,27)),
                W("PN1",(27,20.5),(27,24.5)), W("PN2",(27,24.5),(31,24.5)),
                W("PT1",(27,37),(38,37)), W("PT2",(27,37),(27,D)),
                W("S-EK",(14,20.5),(18.5,20.5),"sep"), W("S-KF1",(14,33),(27,33),"sep"), W("S-KF2",(27,33),(27,37),"sep")],
  "rooms": r + [R("Utility","utility",(34.5,23.75)), R("Pantry","closet",(29,22.5)),
                R("Kitchen + Dining","kitchen",(22,27)), R("Family Room","living",(20.5,41)),
                R("Covered Patio","patio",(32.5,42.5))],
  "openings": o + [door("D02","G2",34.5,into="Utility"), door("D03","U2",34.5,2.5,"Utility"),
                door("D04","PN2",29,2.0,"Kitchen + Dining"),
                sig("S02","ext-back",20.5,7.0),
                {"id":"D13","host":"PT2","at":42.5,"kind":"door","type":"slider","width":6.0,"height":H},
                door("D14","PT1",32.5,3.0,"Kitchen + Dining"),
                cased("PA1","ext-back",32.25,4.0), cased("PA2","ext-right",42.25,6.0), sink("N09","ext-right",32)]})

# ---- Plan 3: four bedrooms ------------------------------------------------------------------------
D = 46
w, r, o = wing(D, 10.5, 16, 26, 32, D)
PLANS["ffr-3"] = dict(beds=4, baths=2, sqft=1320, name="First Flanagan Plan 3: 4 Bed / 2 Bath",
  layout={"footprint": {"width": 38, "depth": D},
  "walls": w + [W("G2",(18.5,20.5),(38,20.5)), W("UX",(26.5,20.5),(26.5,31.5)), W("UY",(18.5,26),(26.5,26)), W("UW",(18.5,20.5),(18.5,26)),
                W("CL4",(26.5,23),(38,23)), W("B4S",(26.5,31.5),(38,31.5)),
                W("S-EK",(14,20.5),(18.5,20.5),"sep"), W("S-KF",(26.5,31.5),(26.5,D),"sep")],
  "rooms": r + [R("Utility","utility",(22.5,23.25)), R("Closet 4","closet",(32,21.75)), R("Bedroom 4","bedroom",(32,27)),
                R("Kitchen + Dining","kitchen",(20,38)), R("Family Room","living",(32,39))],
  "openings": o + [door("D02","G2",22.5,into="Utility"), door("D03","UY",22.5,2.5,"Kitchen + Dining"),
                door("D15","UX",29,into="Bedroom 4"), bifold("D16","CL4",32,"Bedroom 4"),
                sig("S02","ext-back",31), door("D13","ext-back",20,3.0,"Kitchen + Dining"),
                win("N07","ext-right",35), win("N08","ext-right",41.5), win("N10","ext-right",27.5)]})

ASSUME = [
    "Prototype plan, not sited on a real lot. The 50 x 100 ft lot is a working assumption; the minimum lot size has not been confirmed with the planning office.",
    "Setbacks of 25 ft front / 5 ft side / 25 ft rear are unconfirmed.",
    "Treated as outside the flood hazard area; a real lot needs its flood zone and elevations.",
    "Lot cost of $20,000 is a placeholder from a handful of Beaumont asking prices.",
    "Signature windows are drawn as fixed picture windows. In the windstorm area they need impact-rated glass or shutters, which is a real cost; get that price early.",
]
STANDARDS = {"min_beds": 3, "min_baths": 2, "min_garage_cars": 2, "signature_window_min_width_ft": 6}
here = os.path.dirname(os.path.abspath(__file__))
for key, p in PLANS.items():
    spec = {"project": {"name": p["name"], "slug": key},
            "program": {"target_sqft": p["sqft"], "beds": p["beds"], "baths": p["baths"], "stories": 1},
            "lot": {"width_ft": 50, "depth_ft": 100, "setbacks_ft": {"front": 25, "side": 5, "rear": 25}, "flood": {"zone": "X"}},
            "budget": {"lot_cost_usd": 20000, "build_cost_range_per_sqft": [100, 115]},
            "standards": STANDARDS,
            "construction": {"ceiling_ft": 9.0},
            "roof": {"type": "hip", "pitch": 5, "overhang_ft": 1.0},
            "assumptions": ASSUME, "layout": p["layout"]}
    fn = os.path.join(here, f"{key}.yaml")
    with open(fn, "w") as f:
        f.write(f"# {p['name']}. Generated by specs/_gen_ffr.py; edit that file.\n")
        yaml.safe_dump(spec, f, sort_keys=False, default_flow_style=None, width=140)
