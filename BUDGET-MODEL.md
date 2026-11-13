# BUDGET-MODEL — from sale price to house size

The owner sells homes for **$140,000 to $250,000, lot included** (stated
2026-11-13). This file turns that into a construction budget and a house size.

A build cost per square foot cannot be derived from the sale price: it is set
by local labour and material prices. What *can* be derived is how much is left
to build with, and therefore the cost per sq ft the builder has to hit for a
given size. That is what this model gives.

## The arithmetic

```
construction budget = sale price x (1 - 21.8%) - lot cost
```

The 21.8% is the builder's non-construction share from the NAHB 2024 Cost of
Constructing a Home survey (national averages): overhead and general expenses
5.7%, profit 11.0%, sales commission 2.8%, financing 1.5%, marketing 0.8%.
A small builder's real shares will differ; replace them when known.

The construction budget has to cover everything on the lot: house, garage,
porch, patio, slab, driveway, utility connections, permits and impact fees.

Run it for any lot cost:

```bash
cd architect && python3 -m housegen budget --lot 20000
```

## Minimum lot size: not confirmed

The ordinance text could not be read (the code host blocks automated access),
so these are unverified and must be checked with each planning office.

| Place | Minimum lot, as best known | Confidence |
|---|---|---|
| City of Beaumont, R-S single-family district | Set by the table in zoning §28.03.024; 5,000 sq ft and 50 ft wide is my recollection | Low: recalled, not read |
| City of Houston and its ETJ (most of unincorporated Harris County) | Chapter 42: 5,000 sq ft suburban, 3,500 sq ft urban, smaller with conditions | Medium: the city's own FAQ states the 5,000 and 3,500 figures |
| Unincorporated Harris County outside any ETJ | No zoning; plat rules and deed restrictions govern | Low |
| Unincorporated Jefferson County | No zoning; plat and septic rules govern | Low |

Working assumption until confirmed: a **50 x 100 ft, 5,000 sq ft lot**. With
25 ft front, 5 ft side and 25 ft rear setbacks (also unconfirmed) that leaves
a 40 x 50 ft buildable area, 2,000 sq ft on one storey.

## Lot cost: weak data

| Place | Figure found | Source quality |
|---|---|---|
| Beaumont infill lots | Asking prices of about $10,000 to $25,000 for small city lots | A handful of current listings; asking, not sold; utilities and condition unknown |
| Houston outlying suburbs and unincorporated areas | About $40,000 to $80,000 | One contractor's article; unverified |

The tables below use $20,000 for Jefferson County and $60,000 for Harris
County as placeholders.

## What the price range buys

Living area in sq ft at four assumed construction costs. General cost guides
put basic Houston-area construction at roughly $90 to $185 per sq ft; no
Beaumont figure was found.

**Jefferson County, $20,000 lot**

| Sale price | Build budget | $100/sf | $115/sf | $130/sf | $150/sf |
|---:|---:|---:|---:|---:|---:|
| $140,000 | $89,480 | 895 | 778 | 688 | 597 |
| $170,000 | $112,940 | 1,129 | 982 | 869 | 753 |
| $200,000 | $136,400 | 1,364 | 1,186 | 1,049 | 909 |
| $225,000 | $155,950 | 1,560 | 1,356 | 1,200 | 1,040 |
| $250,000 | $175,500 | 1,755 | 1,526 | 1,350 | 1,170 |

**Harris County, $60,000 lot**

| Sale price | Build budget | $100/sf | $115/sf | $130/sf | $150/sf |
|---:|---:|---:|---:|---:|---:|
| $140,000 | $49,480 | 495 | 430 | 381 | 330 |
| $170,000 | $72,940 | 729 | 634 | 561 | 486 |
| $200,000 | $96,400 | 964 | 838 | 742 | 643 |
| $225,000 | $115,950 | 1,160 | 1,008 | 892 | 773 |
| $250,000 | $135,500 | 1,355 | 1,178 | 1,042 | 903 |

## What follows from this

- **The target to build at is about $100 to $115 per sq ft of living area**,
  all site costs included. That is the bottom of the published range for basic
  construction, so it needs the plainest house: one storey, a rectangle, one
  simple roof, standard finishes, plumbing grouped.
- **Jefferson County works across the range.** Roughly 800–900 sq ft at
  $140,000, 1,200–1,350 sq ft at $200,000, and 1,500–1,750 sq ft at $250,000.
- **Harris County works only near the top**, unless lots are found well under
  $60,000. At $140,000 the lot and the builder's share leave under $50,000 to
  build with.
- **A garage comes out of the same budget.** At $140,000–$170,000 a carport
  or no covered parking is the realistic choice.
- **The 5,000 sq ft lot is not the constraint.** Its buildable area holds
  every house in these tables on one storey.

## Suggested product ladder (to refine with real costs)

| Sale price | Where | Living area | Program |
|---:|---|---:|---|
| $140,000–$160,000 | Jefferson | 850–1,000 sq ft | 2 bed / 1 bath, no garage |
| $170,000–$200,000 | Jefferson | 1,100–1,350 sq ft | 3 bed / 2 bath, carport or 1-car |
| $210,000–$250,000 | Jefferson | 1,400–1,700 sq ft | 3 bed / 2 bath, 2-car garage, covered patio |
| $225,000–$250,000 | Harris | 1,000–1,300 sq ft | 3 bed / 2 bath, 1-car or carport |

## In a spec

```yaml
budget:
  sale_price_usd: 200000
  lot_cost_usd: 20000
  build_cost_per_sqft: 110     # optional; with it the report passes or fails the budget
```

The validation report then states the construction budget and the cost per
sq ft the design has to be built for.

## What would make this real

1. The builder's actual cost per sq ft from recent jobs or bids.
2. Actual lot prices for the subdivisions or streets being considered.
3. The minimum lot size and setbacks from each planning office.
4. The builder's own overhead, profit and sales percentages.
