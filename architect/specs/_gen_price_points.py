"""Writes the six price-point prototype specs. Run: python3 specs/_gen_price_points.py
Coordinates are feet from the outside face of the front-left corner."""
import yaml, os

H = 6.6667
def door(i, host, at, w=2.6667, into=None, hinge="low", **k):
    d = {"id": i, "host": host, "at": at, "kind": "door", "width": w, "height": H, "hinge": hinge}
    if into: d["swing_into"] = into
    d.update(k); return d
def bifold(i, host, at, into): return {"id": i, "host": host, "at": at, "kind": "door", "type": "bifold", "width": 4.0, "height": H, "swing_into": into}
def win(i, host, at, w=3.0, h=6.0, sill=1.0, t="single_hung"): return {"id": i, "host": host, "at": at, "kind": "window", "type": t, "width": w, "height": h, "sill": sill}
def small(i, host, at): return win(i, host, at, 2.0, 3.0, 4.0)
def sink(i, host, at): return win(i, host, at, 3.0, 3.0, 4.0)
def cased(i, host, at, w, h=8.0): return {"id": i, "host": host, "at": at, "kind": "cased", "width": w, "height": h}
def W(i, a, b, t=None):
    d = {"id": i, "from": list(a), "to": list(b)}
    if t: d["type"] = t
    return d
def R(name, typ, at): return {"name": name, "type": typ, "at": list(at)}

PLANS = {}

# ---------------------------------------------------------------- $140K, plan A
PLANS["140k-a"] = dict(price=140000, beds=2, baths=1, sqft=840, ceiling=8.0, name="Plan 140-A: 2 Bed / 1 Bath Cottage",
  layout={"footprint": {"width": 28, "depth": 30},
  "walls": [W("WB1",(16,0),(16,12)), W("S-HALL",(16,12),(16,18),"sep"), W("WB2",(16,18),(16,30)),
            W("R1",(16,12),(28,12)), W("R2",(16,18),(28,18)), W("R3",(20,12),(20,18)),
            W("C1a",(18.5,0),(18.5,6)), W("C1b",(16,6),(18.5,6)), W("C2a",(18.5,24),(18.5,30)), W("C2b",(16,24),(18.5,24)),
            W("U1",(11,25),(11,30)), W("U2",(11,25),(16,25)), W("S-LK",(0,16),(16,16),"sep")],
  "rooms": [R("Living","living",(8,8)), R("Kitchen + Dining","kitchen",(6,20)), R("Hall","hall",(18,15)), R("Bath","bath",(24,15)),
            R("Bedroom 1","bedroom",(23,6)), R("Closet 1","closet",(17.25,3)), R("Bedroom 2","bedroom",(23,22)),
            R("Closet 2","closet",(17.25,27)), R("Utility","utility",(13.5,27.5))],
  "openings": [door("D01","ext-front",4,3.0,"Living"), door("D02","ext-back",4,3.0,"Kitchen + Dining",hinge="high"),
            door("D03","R1",18,into="Bedroom 1"), door("D04","R2",18,into="Bedroom 2"), door("D05","R3",15,2.5,"Bath"),
            bifold("D06","C1a",3,"Bedroom 1"), bifold("D07","C2a",27,"Bedroom 2"), door("D08","U2",13.5,2.5,"Kitchen + Dining",hinge="high"),
            win("N01","ext-front",10.5), win("N02","ext-left",8), sink("N03","ext-left",22), sink("N04","ext-back",8),
            win("N05","ext-front",23.25), win("N06","ext-back",23.25), small("N07","ext-right",15)]})

# ---------------------------------------------------------------- $140K, plan B
PLANS["140k-b"] = dict(price=140000, beds=2, baths=1, sqft=864, ceiling=8.0, name="Plan 140-B: 2 Bed / 1 Bath Narrow",
  layout={"footprint": {"width": 24, "depth": 36},
  "walls": [W("K1",(0,18),(8.5,18)), W("K2",(15.5,18),(24,18)), W("S-HALL",(8.5,18),(15.5,18),"sep"),
            W("H1",(8.5,18),(8.5,25)), W("H2",(15.5,18),(15.5,25)), W("B0",(0,25),(24,25)), W("BP",(12,25),(12,36)),
            W("C1a",(9.5,30),(9.5,36)), W("C1b",(9.5,30),(12,30)), W("C2a",(14.5,30),(14.5,36)), W("C2b",(12,30),(14.5,30)),
            W("S-LK",(0,10),(24,10),"sep")],
  "rooms": [R("Living","living",(12,5)), R("Kitchen + Dining","kitchen",(12,14)), R("Hall","hall",(12,21.5)), R("Bath","bath",(4,21.5)),
            R("Utility","utility",(20,21.5)), R("Bedroom 1","bedroom",(5,30)), R("Closet 1","closet",(10.75,33)),
            R("Bedroom 2","bedroom",(19,30)), R("Closet 2","closet",(13.25,33))],
  "openings": [door("D01","ext-front",5,3.0,"Living"), door("D02","ext-right",14,3.0,"Kitchen + Dining"),
            door("D03","B0",10.25,into="Bedroom 1",hinge="high"), door("D04","B0",13.75,into="Bedroom 2"),
            door("D05","H1",21.5,2.5,"Bath"), door("D06","H2",21.5,2.5,"Utility"),
            bifold("D07","C1a",33,"Bedroom 1"), bifold("D08","C2a",33,"Bedroom 2"),
            win("N01","ext-front",11.5), win("N02","ext-front",18), win("N03","ext-left",5), sink("N04","ext-left",14),
            small("N05","ext-left",21.5), win("N06","ext-back",5), win("N07","ext-back",19.5)]})

# ---------------------------------------------------------------- $200K, plan A (no garage)
PLANS["200k-a"] = dict(price=200000, beds=3, baths=2, sqft=1296, ceiling=9.0, name="Plan 200-A: 3 Bed / 2 Bath",
  layout={"footprint": {"width": 36, "depth": 36},
  "walls": [W("WA1",(14,0),(14,13)), W("S-HALL",(14,13),(14,19.5),"sep"), W("WA2",(14,19.5),(14,36)),
            W("L1",(0,13),(14,13)), W("L2",(0,19.5),(14,19.5)), W("L3",(10,13),(10,19.5)),
            W("C2a",(11.5,0),(11.5,7)), W("C2b",(11.5,7),(14,7)), W("L4",(0,31.5),(14,31.5)), W("L5",(7,31.5),(7,36)),
            W("S-LK",(14,14),(36,14),"sep"), W("R1",(14,24),(36,24)), W("R2",(14,28),(22,28)), W("R3",(22,24),(22,36))],
  "rooms": [R("Bedroom 2","bedroom",(5,6)), R("Closet 2","closet",(12.75,3.5)), R("Bath 2","bath",(5,16)), R("Hall","hall",(12,16)),
            R("Bedroom 3","bedroom",(6,25)), R("Closet 3","closet",(3.5,33.75)), R("Primary Closet","closet",(10.5,33.75)),
            R("Living","living",(25,7)), R("Kitchen + Dining","kitchen",(25,19)), R("Utility","utility",(18,26)),
            R("Primary Bath","bath",(18,32)), R("Primary Bedroom","bedroom",(29,30))],
  "openings": [door("D01","ext-front",17,3.0,"Living"), door("D02","ext-right",17,3.0,"Kitchen + Dining"),
            door("D03","L1",12,into="Bedroom 2",hinge="high"), door("D04","L2",12,into="Bedroom 3",hinge="high"),
            door("D05","L3",16.25,2.5,"Bath 2"), bifold("D06","C2a",3.5,"Bedroom 2"), bifold("D07","L4",3.5,"Bedroom 3"),
            door("D08","R1",24.2,into="Primary Bedroom"), door("D09","R1",18,2.5,"Kitchen + Dining"),
            door("D10","R3",32,2.5,"Primary Bath"), door("D11","WA2",33.75,2.3333,"Primary Closet"),
            win("N01","ext-front",24), win("N02","ext-front",31), win("N03","ext-right",7), sink("N04","ext-right",21.5),
            win("N05","ext-back",29), win("N06","ext-right",30), win("N07","ext-front",5.5), win("N08","ext-left",25.5),
            small("N09","ext-left",16.25)]})

# ---------------------------------------------------------------- $200K, plan B (1-car garage, covered patio)
PLANS["200k-b"] = dict(price=200000, beds=3, baths=2, sqft=1100, ceiling=9.0, name="Plan 200-B: 3 Bed / 2 Bath with Garage",
  layout={"footprint": {"width": 34, "depth": 44},
  "walls": [W("WA1",(13,0),(13,10.5)), W("WA2",(13,16),(13,44)),
            W("L1",(0,10.5),(13,10.5)), W("L2",(0,16),(13,16)), W("L3",(9,10.5),(9,16)),
            W("C2a",(10.5,0),(10.5,6)), W("C2b",(10.5,6),(13,6)), W("C3a",(10.5,20.5),(10.5,26.5)), W("C3b",(10.5,20.5),(13,20.5)),
            W("L4",(0,26.5),(13,26.5)), W("L5",(0,32),(13,32)), W("L6",(8,26.5),(8,32)),
            W("G1",(22,0),(22,22)), W("G2",(18,22),(34,22)), W("E1",(18,0),(18,22)), W("E2",(18,12),(22,12)),
            W("S-EK",(13,22),(18,22),"sep"), W("S-KF",(13,32),(24,32),"sep"), W("PT1",(24,32),(34,32)), W("PT2",(24,32),(24,44))],
  "rooms": [R("Bedroom 2","bedroom",(5,5)), R("Closet 2","closet",(11.75,3)), R("Bath 2","bath",(4.5,13.25)),
            R("Bedroom 3","bedroom",(5,21)), R("Closet 3","closet",(11.75,23.5)), R("Primary Bath","bath",(4,29.25)),
            R("Primary Closet","closet",(10.5,29.25)), R("Primary Bedroom","bedroom",(6.5,38)), R("Entry Hall","hall",(15.5,8)),
            R("Mechanical","mech",(20,6)), R("Utility","utility",(20,17)), R("Garage","garage",(28,11)),
            R("Kitchen + Dining","kitchen",(24,27)), R("Family Room","living",(18.5,38)), R("Covered Patio","patio",(29,38))],
  "openings": [door("D01","ext-front",15.5,3.0,"Entry Hall"),
            {"id":"GD","host":"ext-front","at":27.75,"kind":"door","type":"overhead","width":8.0,"height":7.0},
            door("D02","G1",17,into="Garage"), door("D03","E1",19,into="Utility"), door("D04","G1",6,2.5,"Garage"),
            door("D05","L1",11,into="Bedroom 2",hinge="high"), door("D06","L2",11,into="Bedroom 3",hinge="high"),
            door("D07","L3",13.25,2.5,"Bath 2"), bifold("D08","C2a",3,"Bedroom 2"), bifold("D09","C3a",23.5,"Bedroom 3"),
            door("D10","WA2",34.5,into="Primary Bedroom"), door("D11","L5",4,2.5,"Primary Bath"), door("D12","L5",10.5,2.3333,"Primary Closet"),
            {"id":"D13","host":"PT2","at":38,"kind":"door","type":"slider","width":6.0,"height":H},
            cased("PA1","ext-back",28.25,6.5), cased("PA2","ext-right",38,7.0),
            win("N01","ext-back",16), win("N02","ext-back",21), win("N03","ext-back",6.5), win("N04","ext-left",38),
            sink("N05","ext-right",27), win("N06","ext-front",5.25), win("N07","ext-left",21.25),
            small("N08","ext-left",13.25), small("N09","ext-left",29.25)]})

# ---------------------------------------------------------------- $250K, plan A (2-car garage, porch, patio)
PLANS["250k-a"] = dict(price=250000, beds=3, baths=2, sqft=1270, ceiling=9.0, name="Plan 250-A: 3 Bed / 2 Bath, 2-Car Garage",
  layout={"footprint": {"width": 38, "depth": 48},
  "walls": [W("WA1",(14,0),(14,11.5)), W("WA2",(14,17.5),(14,48)),
            W("L1",(0,11.5),(14,11.5)), W("L2",(0,17.5),(14,17.5)), W("L3",(10,11.5),(10,17.5)),
            W("C2a",(11.5,0),(11.5,6.5)), W("C2b",(11.5,6.5),(14,6.5)), W("C3a",(11.5,22.5),(11.5,29)), W("C3b",(11.5,22.5),(14,22.5)),
            W("L4",(0,29),(14,29)), W("L5",(0,36),(14,36)), W("L6",(8.5,29),(8.5,36)),
            W("P1",(14,4),(18.5,4)), W("G1",(18.5,0),(18.5,20.5)), W("G2",(18.5,20.5),(38,20.5)),
            W("U1",(31,20.5),(31,27)), W("U2",(31,27),(38,27)), W("PN1",(27,20.5),(27,24.5)), W("PN2",(27,24.5),(31,24.5)),
            W("PT1",(27,37),(38,37)), W("PT2",(27,37),(27,48)),
            W("S-EK",(14,20.5),(18.5,20.5),"sep"), W("S-KF1",(14,33),(27,33),"sep"), W("S-KF2",(27,33),(27,37),"sep")],
  "rooms": [R("Bedroom 2","bedroom",(5.5,5.5)), R("Closet 2","closet",(12.75,3.25)), R("Bath 2","bath",(5,14.5)),
            R("Bedroom 3","bedroom",(5.5,23)), R("Closet 3","closet",(12.75,25.75)), R("Primary Bath","bath",(4.25,32.5)),
            R("Primary Closet","closet",(11.25,32.5)), R("Primary Bedroom","bedroom",(7,42)), R("Porch","porch",(16.25,2)),
            R("Entry Hall","hall",(16.25,12)), R("Garage","garage",(28,10)), R("Utility","utility",(34.5,23.75)),
            R("Pantry","closet",(29,22.5)), R("Kitchen + Dining","kitchen",(22,27)), R("Family Room","living",(20.5,41)),
            R("Covered Patio","patio",(32.5,42.5))],
  "openings": [cased("PO","ext-front",16.25,3.0), door("D01","P1",16.25,3.0,"Entry Hall"),
            {"id":"GD","host":"ext-front","at":28,"kind":"door","type":"overhead","width":16.0,"height":7.0},
            door("D02","G2",34.5,into="Utility"), door("D03","U2",34.5,2.5,"Utility"), door("D04","PN2",29,2.0,"Kitchen + Dining"),
            door("D05","L1",12,into="Bedroom 2",hinge="high"), door("D06","L2",12,into="Bedroom 3",hinge="high"),
            door("D07","L3",14.5,2.5,"Bath 2"), bifold("D08","C2a",3.25,"Bedroom 2"), bifold("D09","C3a",25.75,"Bedroom 3"),
            door("D10","WA2",38.5,into="Primary Bedroom"), door("D11","L5",4.25,2.5,"Primary Bath"), door("D12","L5",11.25,2.3333,"Primary Closet"),
            {"id":"D13","host":"PT2","at":42.5,"kind":"door","type":"slider","width":6.0,"height":H},
            door("D14","PT1",32.5,3.0,"Kitchen + Dining"), cased("PA1","ext-back",32.25,6.5), cased("PA2","ext-right",42.25,6.0),
            win("N01","ext-front",5.75), win("N02","ext-left",23.25), small("N03","ext-left",14.5), small("N04","ext-left",32.5),
            win("N05","ext-back",7), win("N06","ext-left",42), win("N07","ext-back",17.5), win("N08","ext-back",23),
            sink("N09","ext-right",32)]})

# ---------------------------------------------------------------- $250K, plan B (4 bedrooms, no garage)
PLANS["250k-b"] = dict(price=250000, beds=4, baths=2, sqft=1672, ceiling=9.0, name="Plan 250-B: 4 Bed / 2 Bath",
  layout={"footprint": {"width": 38, "depth": 44},
  "walls": [W("Y16a",(0,16),(17,16)), W("Y16b",(21,16),(38,16)), W("S-HALL",(17,16),(21,16),"sep"), W("S-LK",(21,0),(21,16),"sep"),
            W("HW",(17,16),(17,44)), W("HE",(21,16),(21,44)),
            W("L27",(0,27),(17,27)), W("L33",(0,33),(17,33)), W("LX7",(7,27),(7,33)), W("L30",(0,30),(7,30)),
            W("R27",(21,27),(38,27)), W("R33",(21,33),(38,33)), W("RX29",(29,27),(29,33)),
            W("UE",(26,16),(26,21.5)), W("US",(21,21.5),(26,21.5)), W("CLS",(26,18.5),(31.5,18.5)), W("CLE",(31.5,16),(31.5,18.5))],
  "rooms": [R("Living","living",(10,8)), R("Kitchen + Dining","kitchen",(30,8)), R("Hall","hall",(19,30)),
            R("Bedroom 2","bedroom",(8,21)), R("Closet 2","closet",(3.5,28.5)), R("Closet 3","closet",(3.5,31.5)),
            R("Bath 2","bath",(12,30)), R("Bedroom 3","bedroom",(8,39)), R("Utility","utility",(23.5,18.75)),
            R("Closet 4","closet",(28.5,17.25)), R("Bedroom 4","bedroom",(32,23)), R("Primary Closet","closet",(25,30)),
            R("Primary Bath","bath",(33.5,30)), R("Primary Bedroom","bedroom",(29.5,38.5))],
  "openings": [door("D01","ext-front",18,3.0,"Living",hinge="high"), door("D02","ext-right",12,3.0,"Kitchen + Dining"),
            door("D03","ext-back",19,3.0,"Hall"),
            door("D04","HW",24.5,into="Bedroom 2",hinge="high"), door("D05","HW",35.5,into="Bedroom 3"),
            door("D06","HW",30,2.5,"Bath 2"), door("D07","L27",3.5,2.3333,"Bedroom 2"), door("D08","L33",3.5,2.3333,"Bedroom 3"),
            door("D09","HE",24.25,into="Bedroom 4",hinge="high"), door("D10","HE",35.5,into="Primary Bedroom"),
            door("D11","Y16b",23.5,2.5,"Utility"), bifold("D12","CLS",28.75,"Bedroom 4"),
            door("D13","R33",25,2.3333,"Primary Closet"), door("D14","R33",33.5,2.5,"Primary Bath"),
            win("N01","ext-front",6), win("N02","ext-front",12), win("N03","ext-left",8), sink("N04","ext-front",26),
            win("N05","ext-front",33), win("N06","ext-right",5), win("N07","ext-left",21.5), win("N08","ext-left",38.5),
            win("N09","ext-right",22), win("N10","ext-back",29.5), win("N11","ext-right",38.5), small("N12","ext-right",30)]})

ASSUME = [
    "Prototype plan, not sited on a real lot. The 50 x 100 ft lot is the working minimum-lot assumption from BUDGET-MODEL.md; the minimum lot size has not been confirmed with the planning office.",
    "Setbacks of 25 ft front / 5 ft side / 25 ft rear are unconfirmed.",
    "Treated as outside the flood hazard area; a real lot needs its flood zone and elevations.",
    "Lot cost of $20,000 is a placeholder from a handful of Beaumont asking prices.",
]
here = os.path.dirname(os.path.abspath(__file__))
for key, p in PLANS.items():
    spec = {"project": {"name": p["name"], "slug": f"jefferson-{key}"},
            "program": {"target_sqft": p["sqft"], "beds": p["beds"], "baths": p["baths"], "stories": 1},
            "lot": {"width_ft": 50, "depth_ft": 100, "setbacks_ft": {"front": 25, "side": 5, "rear": 25}, "flood": {"zone": "X"}},
            "budget": {"sale_price_usd": p["price"], "lot_cost_usd": 20000},
            "construction": {"ceiling_ft": p["ceiling"]},
            "roof": {"type": "hip", "pitch": 5, "overhang_ft": 1.0},
            "assumptions": ASSUME, "layout": p["layout"]}
    fn = os.path.join(here, f"{p['beds']}bd{p['baths']}ba-{p['sqft']}sqft-jefferson-{key}.yaml")
    with open(fn, "w") as f:
        f.write(f"# {p['name']} - ${p['price']:,} price point. Generated by specs/_gen_price_points.py; edit that file.\n")
        yaml.safe_dump(spec, f, sort_keys=False, default_flow_style=None, width=140)
    print(fn)
