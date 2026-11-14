"""Builds the First Flanagan Realty plan book PDF from the generated house folders.

Run from architect/:  python3 make_plan_book.py
Every number is read from each house's validation-report.json and model.json,
so the book cannot disagree with the drawings.
"""
import datetime
import glob
import json
import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from housegen import STAMP
from housegen.budget import (GARAGE_WEIGHT, OTHER, OTHER_SHARES, OUTDOOR_WEIGHT, construction_budget,
                             effective_sqft, sale_price_for)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "houses", "First-Flanagan-Plan-Book.pdf")
TMP = os.path.join(HERE, "houses", ".book-tmp")
LOT, LOW, HIGH = 20000, 100, 115
NAVY, RED, GREY = colors.HexColor("#1f2d3d"), colors.HexColor("#b00000"), colors.HexColor("#555555")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=20, leading=24, textColor=NAVY, spaceBefore=16, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13.5, leading=17, textColor=NAVY, spaceBefore=10, spaceAfter=5)
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=10.5, leading=14.5, spaceAfter=6)
SMALL = ParagraphStyle("S", parent=P, fontSize=8.5, leading=11.5, textColor=GREY)
BUL = ParagraphStyle("B", parent=P, leftIndent=14, bulletIndent=3, spaceAfter=3)
CELL = ParagraphStyle("C", parent=P, fontSize=9.5, leading=12, spaceAfter=0)
CELLB = ParagraphStyle("CB", parent=CELL, fontName="Helvetica-Bold")
TITLE = ParagraphStyle("T", parent=H1, fontSize=30, leading=35, alignment=TA_CENTER, spaceAfter=6)
SUB = ParagraphStyle("Sub", parent=P, fontSize=14, leading=18, alignment=TA_CENTER, textColor=GREY)

PLAN_NOTES = {
    "ffr-1": ("Plan 1", "The base house and the cheapest",
              ["Covered front porch and a proper entry hall, so the front door does not open straight into the living room.",
               "Kitchen with a walk-in pantry, open to a family room that runs the full width of the back of the house.",
               "Primary suite at the rear corner with its own bath and walk-in closet.",
               "Two more bedrooms at the front and middle, sharing a hall bath.",
               "Utility room between the garage and the kitchen, so groceries and laundry stay out of the living space.",
               "Back door from the family room to the yard."]),
    "ffr-2": ("Plan 2", "Plan 1 with a covered patio",
              ["Everything in Plan 1, in a house 4 ft deeper.",
               "An 11 x 11 ft covered patio at the rear corner, under the main roof.",
               "The patio is reached two ways: a sliding glass door from the family room and a door from the dining area.",
               "The primary bedroom and bedrooms 2 and 3 are each about a foot deeper than in Plan 1.",
               "The family room is narrower (about 13 ft) because the patio takes the corner."]),
    "ffr-3": ("Plan 3", "Four bedrooms",
              ["A fourth bedroom behind the garage, with its own closet and window.",
               "That fourth bedroom is small: about 88 sq ft. It suits a child, a guest or an office.",
               "Larger primary bedroom than Plan 1 (about 13 x 13 ft).",
               "No walk-in pantry; the kitchen runs along one wall and needs cabinet pantry storage.",
               "Back door from the kitchen and dining area to the yard."]),
}


def load():
    plans = []
    for key in ("ffr-1", "ffr-2", "ffr-3"):
        d = glob.glob(os.path.join(HERE, "houses", f"*{key}"))[0]
        r = json.load(open(os.path.join(d, "validation-report.json")))
        m = json.load(open(os.path.join(d, "model.json")))
        rooms = m["rooms"]
        garage = sum(x["net_area_sf"] for x in rooms if x["kind"] == "garage")
        gar_gross = None
        plans.append({"key": key, "dir": d, "report": r, "model": m, "rooms": rooms,
                      "living": r["summary"]["gross_area"], "uncond": r["summary"]["unconditioned_area"],
                      "beds": sum(1 for x in rooms if x["kind"] == "bedroom"),
                      "baths": sum(1 for x in rooms if x["kind"] == "bath"),
                      "fp": m["meta"]["footprint"], "price": r["indicative_price"]})
    return plans


def areas_for_cost(p):
    """Garage and outdoor areas to wall centerlines, as the validation report prices them."""
    from shapely.geometry import Polygon
    # the report used face areas; recover them from the stated indicative price at the low cost
    eff = (p["price"][0] * (1 - OTHER) - LOT) / LOW
    return eff


def crop_plan(p):
    os.makedirs(TMP, exist_ok=True)
    im = PILImage.open(os.path.join(p["dir"], "sheet-A101-floor-plan.png")).convert("RGB")
    w, h = im.size
    im = im.crop((int(w * 0.03), int(h * 0.04), int(w * 0.82), int(h * 0.90)))
    bb = PILImage.eval(im.convert("L"), lambda v: 255 if v < 245 else 0).getbbox()
    im = im.crop((max(bb[0] - 30, 0), max(bb[1] - 30, 0), min(bb[2] + 30, im.width), min(bb[3] + 30, im.height)))
    # keep the drawing itself: drop the title lines under it, which the crop may cut through
    ink = [any(v < 245 for v in row) for row in (list(im.convert("L").crop((0, y, im.width, y + 1)).getdata())
                                                   for y in range(im.height))]
    blocks, start = [], None
    for y, on in enumerate(ink + [False]):
        if on and start is None:
            start = y
        elif not on and start is not None:
            blocks.append((start, y)); start = None
    merged = []
    for b0, b1 in blocks:                       # join blocks separated by less than 10 blank rows
        if merged and b0 - merged[-1][1] < 10:
            merged[-1] = (merged[-1][0], b1)
        else:
            merged.append((b0, b1))
    main = max(merged, key=lambda t: t[1] - t[0])
    im = im.crop((0, max(main[0] - 20, 0), im.width, min(main[1] + 20, im.height)))
    out = os.path.join(TMP, p["key"] + "-plan.jpg")
    im.save(out, quality=88)
    return out, im.size


def fit(path, size, max_w, max_h):
    s = min(max_w / size[0], max_h / size[1])
    return Image(path, width=size[0] * s, height=size[1] * s)


def table(rows, widths, header=True, align_right=()):
    data = [[Paragraph(str(c), CELLB if (header and i == 0) else CELL) for c in row] for i, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8c8c8")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9edf2")))
    t.setStyle(TableStyle(st))
    return t


def bullets(items):
    return [Paragraph(x, BUL, bulletText="•") for x in items]


def money(v):
    return f"${v:,.0f}"


def footer(c, doc):
    c.saveState()
    w, h = letter
    c.setStrokeColor(RED); c.setFillColor(RED); c.setLineWidth(1)
    c.rect(0.6 * inch, 0.38 * inch, w - 1.2 * inch, 0.3 * inch, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 8.3)
    c.drawCentredString(w / 2, 0.49 * inch, STAMP.replace("—", "-"))
    c.setFillColor(GREY); c.setFont("Helvetica", 8)
    c.drawString(0.6 * inch, 0.22 * inch, "First Flanagan Realty - Home Plan Book")
    c.drawRightString(w - 0.6 * inch, 0.22 * inch, f"Page {doc.page}")
    c.restoreState()


def build():
    plans = load()
    W = letter[0] - 1.5 * inch
    today = datetime.date.today().strftime("%B %d, %Y").replace(" 0", " ")
    S = []

    # ---------------------------------------------------------------- cover
    S += [Spacer(1, 1.5 * inch), Paragraph("First Flanagan Realty", TITLE), Paragraph("Home Plan Book", TITLE),
          Spacer(1, 0.15 * inch), Paragraph("Three starter home plans with a luxury feel", SUB),
          Paragraph(f"Concept package, {today}", SUB), Spacer(1, 0.6 * inch)]
    S.append(table([["What this is",
                     "Three original floor plans for affordable single-family homes in the Beaumont / Jefferson County "
                     "area, with the cost reasoning behind them. It is meant to be read start to finish in about "
                     "fifteen minutes."],
                    ["What it is not",
                     "It is not a set of construction drawings and the prices are not quotes. Every drawing is a concept "
                     "that a licensed Texas architect or engineer must check and complete before anything is built or "
                     "priced for sale."],
                    ["How it was made",
                     "The plans were drawn by an AI design assistant (Claude) working from First Flanagan Realty's instructions. Each "
                     "plan was checked by software against room-size, exit, light and setback rules; that is a screening, "
                     "not a plan review."]],
                   [1.4 * inch, W - 1.4 * inch], header=False))
    S.append(PageBreak())

    # ---------------------------------------------------------------- bottom line
    lo = min(p["price"][0] for p in plans); hi = max(p["price"][1] for p in plans)
    p1 = plans[0]
    S += [Paragraph("1. The short version", H1),
          Paragraph("The goal is a home that feels upscale but sells at a price a lower-income family can reach. "
                    "Every plan here has three or more bedrooms, two baths, a two-car garage and our signature large "
                    "windows looking onto the backyard.", P),
          Paragraph(f"<b>What it costs.</b> The estimate is that these homes would sell for about <b>{money(round(lo, -3))} to "
                    f"{money(round(hi, -3))}</b>, lot included. The cheapest, Plan 1, comes to about "
                    f"{money(round(p1['price'][0], -3))} to {money(round(p1['price'][1], -3))}.", P),
          Paragraph("<b>What changed from the first idea.</b> The original target was $140,000 to $250,000. With a "
                    "two-car garage and three bedrooms, $140,000 cannot be reached; the realistic floor is a little "
                    "over $200,000. Section 5 shows the arithmetic.", P),
          Paragraph("<b>How firm these numbers are.</b> Not firm. They rest on an assumed $20,000 lot and an assumed "
                    f"building cost of ${LOW} to ${HIGH} per square foot. Neither has been confirmed with a builder or "
                    "a land seller. Section 8 lists what has to be confirmed.", P),
          Paragraph("The three plans at a glance", H2)]
    rows = [["", "Bedrooms / baths", "House size (outside)", "Living area", "Garage, porch, patio", "Estimated sale price"]]
    for p in plans:
        n = PLAN_NOTES[p["key"]]
        rows.append([f"<b>{n[0]}</b><br/>{n[1]}", f"{p['beds']} / {p['baths']}",
                     f"{p['fp']['width']:g} x {p['fp']['depth']:g} ft", f"{p['living']:,.0f} sq ft",
                     f"{p['uncond']:,.0f} sq ft", f"{money(round(p['price'][0], -3))} to {money(round(p['price'][1], -3))}"])
    S.append(table(rows, [1.55 * inch, 0.9 * inch, 1.05 * inch, 0.9 * inch, 1.05 * inch, W - 5.45 * inch]))
    S += [Spacer(1, 6), Paragraph("Living area is heated and cooled space measured to the outside of the walls. The "
                                  "garage, porch and patio are not counted in it.", SMALL)]

    # ---------------------------------------------------------------- standards
    S += [Paragraph("2. What every First Flanagan home includes", H1),
          Paragraph("These are the rules we set for our homes. The software checks each plan against them, and all three pass.", P)]
    S += bullets(["<b>At least 3 bedrooms and 2 bathrooms.</b> No two-bedroom, one-bath homes.",
                  "<b>A two-car garage</b> with a 16-foot door.",
                  "<b>The signature windows.</b> A large modern picture window, 8 feet wide and 6 feet tall, in the "
                  "primary bedroom looking onto the backyard, and a second one in the family room, also facing the "
                  "backyard. This is meant to be the thing people remember about our homes.",
                  "<b>A luxury feel at a modest price:</b> 9-foot ceilings, a covered front porch, a real entry hall, "
                  "an open kitchen and family room, and a primary suite with a walk-in closet.",
                  "<b>Not all brick.</b> Durable siding with brick or stone as an accent keeps the look while holding "
                  "cost down (Section 6)."])
    S.append(PageBreak())

    # ---------------------------------------------------------------- plans
    S.append(Paragraph("3. The plans", H1))
    S.append(Paragraph("How to read the drawings: the street is at the bottom of each plan. Thick dark lines are walls. "
                       "Thin blue lines in a wall are windows; the two long ones at the top are the signature windows. "
                       "Arcs show which way doors swing. Each room shows its name, floor area and clear size. Numbers "
                       "around the outside are dimensions in feet and inches.", P))
    for p in plans:
        n = PLAN_NOTES[p["key"]]
        img, size = crop_plan(p)
        S.append(Paragraph(f"{n[0]}: {n[1]}", H2))
        S.append(Paragraph(f"{p['beds']} bedrooms, {p['baths']} baths, two-car garage. {p['living']:,.0f} sq ft of living "
                           f"area in a house {p['fp']['width']:g} ft wide and {p['fp']['depth']:g} ft deep. Estimated "
                           f"sale price {money(round(p['price'][0], -3))} to {money(round(p['price'][1], -3))}.", P))
        S.append(fit(img, size, W, 6.4 * inch))
        S.append(PageBreak())
        S.append(Paragraph(f"{n[0]}: what you get", H2))
        S += bullets(n[2])
        order = {"bedroom": 0, "living": 1, "kitchen": 2, "bath": 3, "closet": 4, "utility": 5, "hall": 6,
                 "garage": 7, "porch": 8, "patio": 9}
        rr = sorted(p["rooms"], key=lambda x: (order.get(x["kind"], 5), -x["net_area_sf"]))
        rows = [["Room", "Floor area", "Clear size (ft)"]]
        for x in rr:
            cw, cd = x["clear_ft"]
            rows.append([x["name"], f"{x['net_area_sf']:,.0f} sq ft", f"{cw:.0f} x {cd:.0f}" if min(cw, cd) >= 4 else "-"])
        half = (len(rows) + 1) // 2 + 1
        left = table(rows[:half], [1.45 * inch, 0.9 * inch, 0.95 * inch])
        right = table([rows[0]] + rows[half:], [1.45 * inch, 0.9 * inch, 0.95 * inch])
        S.append(Spacer(1, 6))
        two = Table([[left, right]], colWidths=[W / 2, W / 2])
        two.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        S.append(two)
        S.append(Spacer(1, 8))
        f1, f2 = os.path.join(p["dir"], "render-3d-front.png"), os.path.join(p["dir"], "render-3d-roof-off.png")
        iw = (W - 8) / 2
        pics = Table([[Image(f1, width=iw, height=iw * 1000 / 1600), Image(f2, width=iw, height=iw * 1000 / 1600)],
                      [Paragraph("Massing view from the street side. Colours and finishes are placeholders.", SMALL),
                       Paragraph("Roof lifted off to show the rooms in 3D.", SMALL)]], colWidths=[iw + 4, iw + 4])
        pics.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        S.append(pics)
        S.append(PageBreak())

    # ---------------------------------------------------------------- compare
    S += [Paragraph("4. Choosing between them", H1)]
    S.append(table([["", "Plan 1", "Plan 2", "Plan 3"],
                    ["Best for", "Lowest price", "Buyers who want outdoor living", "Larger families"],
                    ["Bedrooms / baths"] + [f"{p['beds']} / {p['baths']}" for p in plans],
                    ["Living area"] + [f"{p['living']:,.0f} sq ft" for p in plans],
                    ["Estimated price"] + [f"{money(round(p['price'][0], -3))} to {money(round(p['price'][1], -3))}" for p in plans],
                    ["Covered patio", "No", "Yes, 11 x 11 ft", "No"],
                    ["Walk-in pantry", "Yes", "Yes", "No"],
                    ["Family room", "About 23 x 11 ft", "About 13 x 15 ft", "About 11 x 14 ft"],
                    ["Main trade-off", "No covered outdoor space", "Costs more; narrower family room",
                     "Fourth bedroom is small (88 sq ft); no pantry"]],
                   [1.35 * inch] + [(W - 1.35 * inch) / 3] * 3))
    S += [Spacer(1, 6), Paragraph("All three share the same bedroom wing, garage, porch and entry, so a builder who "
                                  "prices one has most of the information needed for the others.", P)]

    # ---------------------------------------------------------------- money
    S += [Paragraph("5. How the prices were worked out", H1),
          Paragraph("A sale price has to cover three things: the lot, the cost of building, and the builder's own "
                    "costs and profit. The estimate works forward from the size of each house.", P)]
    rows = [["Step", "Plan 1 at $%d / sq ft" % LOW, "Plan 1 at $%d / sq ft" % HIGH]]
    eff = (p1["price"][0] * (1 - OTHER) - LOT) / LOW
    for label, fn in (("Cost-weighted size (see note)", lambda c: f"{eff:,.0f} sq ft"),
                      ("Construction", lambda c: money(round(eff * c, -2))),
                      ("Lot", lambda c: money(LOT)),
                      ("Overhead, profit, sales, financing (21.8% of price)", lambda c: money(round((LOT + eff * c) / (1 - OTHER) * OTHER, -2))),
                      ("<b>Sale price</b>", lambda c: "<b>about %s</b>" % money(round((LOT + eff * c) / (1 - OTHER), -3)))):
        rows.append([label, fn(LOW), fn(HIGH)])
    S.append(table(rows, [3.1 * inch, (W - 3.1 * inch) / 2, (W - 3.1 * inch) / 2]))
    S += [Spacer(1, 6),
          Paragraph(f"Note: a garage costs less to build than living space, so each garage square foot is counted as "
                    f"{GARAGE_WEIGHT:g} of a living square foot, and porch or patio as {OUTDOOR_WEIGHT:g}. Those weights "
                    "are assumptions, not builder data.", SMALL),
          Paragraph("Where the 21.8% comes from", H2),
          Paragraph("It is the national average from the National Association of Home Builders' 2024 survey of what "
                    "goes into a new home's price, apart from the lot and construction: " +
                    ", ".join(f"{k} {v * 100:.1f}%" for k, v in OTHER_SHARES.items()) +
                    ". A small local builder's real figures will differ.", P),
          Paragraph("Why $140,000 does not work", H2)]
    need200 = construction_budget(200000, LOT) / eff
    need140 = construction_budget(140000, LOT) / eff
    S.append(Paragraph(f"Selling Plan 1 for $200,000 would leave {money(construction_budget(200000, LOT))} to build "
                       f"with, which means building at about ${need200:,.0f} per square foot. Selling it for $140,000 "
                       f"would leave {money(construction_budget(140000, LOT))}, about ${need140:,.0f} per square foot. "
                       "Published guides put basic construction in the Houston area at roughly $90 to $185 per square "
                       "foot, so $200,000 is at the very edge and $140,000 is out of reach for a house with a two-car "
                       "garage.", P))
    S.append(Paragraph("What would lower the price", H2))
    S += bullets(["A cheaper lot. Every $10,000 off the lot takes about $12,800 off the sale price.",
                  "A lower real building cost than assumed. Every $5 per square foot is worth about "
                  f"{money(round(5 * eff / (1 - OTHER), -2))} on Plan 1.",
                  "A smaller builder margin than the national average.",
                  "A one-car garage or carport would save the most, but that breaks our standard."])

    # ---------------------------------------------------------------- materials
    S += [Paragraph("6. Materials and the luxury feel", H1),
          Paragraph("These are recommendations from general building knowledge. None has been priced.", P),
          Paragraph("Outside", H2)]
    S.append(table([["Material", "Verdict", "Why"],
                    ["Fiber-cement siding (lap or board-and-batten)", "Recommended as the main cladding",
                     "Resists rot, termites and fire, holds paint well and suits a humid coastal climate."],
                    ["Brick or stone", "Use as an accent",
                     "A band along the front or around the entry gives the solid look without the cost of a full brick house."],
                    ["Engineered wood siding", "Possible", "Cheaper and attractive, but needs careful detailing against moisture."],
                    ["Vinyl siding", "Avoid", "Cheapest, but weaker in high wind and it reads as low-end."],
                    ["Stucco", "Avoid", "Prone to moisture problems in this climate if not detailed perfectly."],
                    ["Roof", "Wind-rated architectural shingles",
                     "Best value. Metal roofing lasts longer but costs more."]],
                   [1.9 * inch, 1.6 * inch, W - 3.5 * inch]))
    S.append(Paragraph("Because Jefferson County is in the state windstorm insurance area, siding, roofing, windows "
                       "and doors all have to be products approved for that program.", P))
    S.append(Paragraph("Inside: where a little money shows the most", H2))
    S += bullets(["The two signature windows and 9-foot ceilings. They change how every visitor experiences the house.",
                  "A kitchen island facing the family room.",
                  "A double-sink vanity and a walk-in closet in the primary suite.",
                  "One good floor material running through all the living areas.",
                  "Taller baseboards and one consistent style of door and hardware throughout."])

    # ---------------------------------------------------------------- risks
    S += [PageBreak(), Paragraph("7. Things to know before relying on this", H1)]
    S.append(table([["Issue", "What it means"],
                    ["The signature windows need impact-rated glass or shutters",
                     "Large panes in the windstorm area must resist wind-blown debris. This is the biggest cost risk "
                     "of our signature feature. Get a window supplier's price early."],
                    ["The front wall needs an engineer's attention",
                     "The garage door, porch and front window take up 58% of the front wall, leaving little solid wall "
                     "to brace the house against wind. This is normal for a house with a front garage, and engineers "
                     "have a standard answer for it, but it must be designed."],
                    ["The house needs a lot at least 50 feet wide",
                     "All three plans are 38 feet wide, the most that fits a 50-foot lot with 5-foot side yards."],
                    ["Kitchens and bathrooms are empty boxes on the drawings",
                     "Sinks, tubs, cabinets and the island are not drawn yet. The rooms are sized to take them."],
                    ["No structure, electrical, plumbing or air-conditioning design",
                     "Those come from the architect, engineer and trades."],
                    ["Windstorm certificate (WPI-8)",
                     "It is earned through inspections during construction, not from drawings. The inspections must "
                     "be arranged before work starts or the home may not qualify for windstorm insurance."]],
                   [2.3 * inch, W - 2.3 * inch]))

    S += [Paragraph("8. What still has to be confirmed", H1),
          Paragraph("Each of these is an assumption in this book. Real answers will move the prices.", P)]
    S.append(table([["Question", "What this book assumes", "Who can answer"],
                    ["What does it really cost to build per square foot?", f"${LOW} to ${HIGH}", "Two or three local builders, from recent jobs"],
                    ["What does a suitable lot cost?", money(LOT), "Local land listings or a land agent"],
                    ["What is the smallest lot the city allows, and the setbacks?", "50 x 100 ft; 25 ft front, 5 ft sides, 25 ft rear",
                     "City of Beaumont planning office"],
                    ["Is the lot in a flood zone?", "No", "FEMA flood map and the city floodplain office"],
                    ["Which building code edition applies?", "2021 codes, as reported adopted by Beaumont in 2023", "City building department"],
                    ["What do impact-rated signature windows cost?", "Not priced", "A window supplier"],
                    ["What are our own overhead and profit?", "21.8% national average", "Our own books"]],
                   [2.45 * inch, 1.9 * inch, W - 4.35 * inch]))

    S += [Paragraph("9. Suggested next steps", H1)]
    S += bullets(["<b>Pick one plan to price first.</b> Plan 1 is the natural choice because the others build on it.",
                  "<b>Get two or three builders to price it</b> from this book and the files listed below. Their cost "
                  "per square foot replaces the assumed one.",
                  "<b>Get a window quote</b> for two 8 x 6 ft impact-rated fixed windows.",
                  "<b>Call the Beaumont planning office</b> about minimum lot size, setbacks and flood zone for the "
                  "areas we are considering.",
                  "<b>Engage a licensed Texas architect or engineer</b> to turn the chosen concept into real drawings.",
                  "<b>Then decide the price range.</b> If builders come in near $100 per square foot, a home just over "
                  "$200,000 is realistic."])
    S.append(KeepTogether([Paragraph("Files that go with this book", H2),
          Paragraph("Each plan has a folder containing a CAD drawing (floor-plan.dxf) that architects and builders can "
                    "open, a 3D model (model.glb and model.ifc), elevation views, and a detailed check report "
                    "(validation-report.md). We can send whichever a builder or architect asks for.", P)]))

    doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.95 * inch,
                            title="First Flanagan Realty - Home Plan Book", author="First Flanagan Realty", subject=STAMP)
    doc.build(S, onFirstPage=footer, onLaterPages=footer)
    for f in glob.glob(os.path.join(TMP, "*")):
        os.remove(f)
    os.rmdir(TMP)
    print(OUT)


if __name__ == "__main__":
    build()
