# Price-point prototype plans

> **CONCEPT — NOT FOR CONSTRUCTION — requires validation by a licensed Texas architect/PE.**

Six original plans, two at each sale price: $140,000, $200,000 and $250,000, lot included. All are one storey under one hip roof, on the working 50 x 100 ft lot with 25 / 5 / 25 ft setbacks, under the Jefferson County baseline. They follow the layout patterns in `STYLE-PROFILE.md` at a size the budget allows; none copies a Perry Homes plan.

| Plan | Sale price | Beds / baths | Footprint | Living area | Garage, porch, patio | Build budget | Needed cost per sq ft | Checks |
|---|---:|---|---|---:|---:|---:|---:|---|
| [Plan 140-A: 2 Bed / 1 Bath Cottage](2bd1ba-840sqft-jefferson-140k-a/sheet-A101-floor-plan.png) | $140,000 | 2 / 1 | 28 x 30 ft | 840 sq ft | 0 sq ft | $89,480 | $107 | 0 fail, 0 warn, 23 pass |
| [Plan 140-B: 2 Bed / 1 Bath Narrow](2bd1ba-864sqft-jefferson-140k-b/sheet-A101-floor-plan.png) | $140,000 | 2 / 1 | 24 x 36 ft | 864 sq ft | 0 sq ft | $89,480 | $104 | 0 fail, 0 warn, 23 pass |
| [Plan 200-A: 3 Bed / 2 Bath](3bd2ba-1296sqft-jefferson-200k-a/sheet-A101-floor-plan.png) | $200,000 | 3 / 2 | 36 x 36 ft | 1,296 sq ft | 0 sq ft | $136,400 | $105 | 0 fail, 0 warn, 25 pass |
| [Plan 200-B: 3 Bed / 2 Bath with Garage](3bd2ba-1100sqft-jefferson-200k-b/sheet-A101-floor-plan.png) | $200,000 | 3 / 2 | 34 x 44 ft | 1,098 sq ft | 398 sq ft | $136,400 | $124 | 0 fail, 0 warn, 27 pass |
| [Plan 250-A: 3 Bed / 2 Bath, 2-Car Garage](3bd2ba-1270sqft-jefferson-250k-a/sheet-A101-floor-plan.png) | $250,000 | 3 / 2 | 38 x 48 ft | 1,266 sq ft | 558 sq ft | $175,500 | $139 | 0 fail, 1 warn, 27 pass |
| [Plan 250-B: 4 Bed / 2 Bath](4bd2ba-1672sqft-jefferson-250k-b/sheet-A101-floor-plan.png) | $250,000 | 4 / 2 | 38 x 44 ft | 1,672 sq ft | 0 sq ft | $175,500 | $105 | 0 fail, 0 warn, 27 pass |

Build budget is the sale price less a $20,000 lot and 21.8% for builder overhead, profit, sales and financing (see `BUDGET-MODEL.md`). Needed cost per sq ft is that budget divided by living area; garage, porch, patio and site work come out of the same money, so plans with a garage need a lower true cost per sq ft than the figure shown.

## What differs within each price point

- **Plan 140-A: 2 Bed / 1 Bath Cottage** (`2bd1ba-840sqft-jefferson-140k-a/`): Bedrooms on one side sharing a bath off a short hall; living at the front, kitchen and dining at the rear with a back door. Widest and shallowest of the two.
- **Plan 140-B: 2 Bed / 1 Bath Narrow** (`2bd1ba-864sqft-jefferson-140k-b/`): Narrow 24 ft house for tight lots: open living and kitchen across the front, both bedrooms at the rear, bath and utility off a central hall. Side door from the kitchen.
- **Plan 200-A: 3 Bed / 2 Bath** (`3bd2ba-1296sqft-jefferson-200k-a/`): All 1,296 sq ft is living space, no garage. Big front living room open to the kitchen, primary suite at the rear corner, two bedrooms in a side wing.
- **Plan 200-B: 3 Bed / 2 Bath with Garage** (`3bd2ba-1100sqft-jefferson-200k-b/`): Trades about 200 sq ft of living space for a 1-car garage and a covered rear patio. Entry hall along the garage, kitchen open to a rear family room, primary suite at the rear.
- **Plan 250-A: 3 Bed / 2 Bath, 2-Car Garage** (`3bd2ba-1270sqft-jefferson-250k-a/`): Closest to the Perry pattern: 2-car garage across half the front, recessed porch, entry hall, kitchen with pantry open to a rear family room, covered patio, primary suite at the rear corner.
  - Warning: Openings take 58% of exterior wall ext-front; little length is left for braced or shear wall panels.
- **Plan 250-B: 4 Bed / 2 Bath** (`4bd2ba-1672sqft-jefferson-250k-b/`): Maximum bedrooms for the money: 4 bedrooms off a central hall, no garage, living and kitchen across the front, rear door at the end of the hall.

## Each folder holds

Floor plan sheet (`sheet-A101-floor-plan.png`, also SVG and in `sheets.pdf`), `floor-plan.dxf`, the 3D model (`model.glb`, `model.obj`, `model.ifc`), renders and elevations, and `validation-report.md`.

## Not yet settled

- Minimum lot size, setbacks and lot cost are unconfirmed placeholders.
- No builder cost per sq ft has been supplied, so no plan is passed or failed on budget.
- Fixtures, cabinets and the kitchen layout are not drawn.
- Interior baths without a window need an exhaust fan (noted in each report).
- Regenerate with `python3 specs/_gen_price_points.py` then `python3 -m housegen design specs/<file>.yaml`.
