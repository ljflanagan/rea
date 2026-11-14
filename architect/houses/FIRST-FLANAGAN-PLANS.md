# First Flanagan Realty plans

> **CONCEPT — NOT FOR CONSTRUCTION — requires validation by a licensed Texas architect/PE.**

Three original one-storey plans that meet every First Flanagan standard at the lowest size I could reach. Plan 1 is the cheapest; Plans 2 and 3 add a covered patio or a fourth bedroom.

| Plan | Beds / baths | Footprint | Living area | Garage, porch, patio | Indicative sale price | Folder |
|---|---|---|---:|---:|---|---|
| First Flanagan Plan 1 | 3 / 2 | 38 x 44 ft | 1,241 sq ft | 431 sq ft | $209,835 to $237,473 | `3bd2ba-1250sqft-ffr-1/` |
| First Flanagan Plan 2 | 3 / 2 | 38 x 48 ft | 1,266 sq ft | 558 sq ft | $217,521 to $246,313 | `3bd2ba-1265sqft-ffr-2/` |
| First Flanagan Plan 3 | 4 / 2 | 38 x 46 ft | 1,317 sq ft | 431 sq ft | $219,553 to $248,650 | `4bd2ba-1320sqft-ffr-3/` |

Indicative sale price assumes a $20,000 lot, construction at $100 to $115 per sq ft of living area, a garage costed at half that rate and porch or patio at 30%, and 21.8% of the price for builder overhead, profit, sales and financing. None of those inputs is verified; see `BUDGET-MODEL.md`.

## Standards every plan meets

- At least 3 bedrooms and 2 baths.
- 2-car garage with a 16 ft door.
- Signature window in the primary bedroom facing the backyard: 8 ft wide by 6 ft tall.
- Signature window in the family room facing the backyard: 8 ft wide (7 ft in Plan 2).
- Each report checks these under "House standards".

## What is in each plan

- **Plan 1** is the base house: recessed front porch, entry hall, kitchen with walk-in pantry open to a 23 x 11 ft family room, primary suite at the rear corner with walk-in closet, two bedrooms sharing a bath, utility room between garage and kitchen.
- **Plan 2** is Plan 1 made 4 ft deeper with an 11 x 11 ft covered patio at the rear corner, reached from both the family room and the dining area. The primary bedroom and bedrooms 2 and 3 are each about a foot deeper.
- **Plan 3** adds a fourth bedroom behind the garage. That bedroom is small: 88 sq ft, 10'-10" x 8'-2". The pantry is dropped and the kitchen runs along the primary suite wall.

## Known weak points

- **Front wall bracing (all three):** garage door, porch and bedroom window take 58% of the front wall. This is normal for a front-garage house but an engineer must design that wall for wind.
- **Impact glass:** the signature windows are large fixed panes. In the windstorm area they need impact-rated glass or shutters. Price this early; it is the main cost risk of the signature feature.
- **Width:** all three are 38 ft wide, the most a 50 ft lot allows with 5 ft side setbacks and 1 ft eaves. A narrower lot will not take a 2-car front garage plus a front bedroom.
- **Not drawn:** fixtures, cabinets, kitchen island, exterior materials.

Regenerate with `python3 specs/_gen_ffr.py` then `python3 -m housegen design specs/ffr-1.yaml` from `architect/`.
