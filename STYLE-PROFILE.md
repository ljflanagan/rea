# STYLE-PROFILE — production "contemporary" homes, after Perry Homes

The owner named Perry Homes (perryhomes.com) as the style to design in. This
file is what was learned from their public Houston-area catalogue on
2026-11-13, and how the architect pipeline should use it.

## How this was gathered, and its limits

- **Source:** the plan pages listed in perryhomes.com's public sitemap for the
  Houston market: 326 unique designs, of which 278 parsed cleanly (size, beds,
  baths, stories, garage, base price, lot-width product line, feature text).
  Three floor plan drawings and three front elevations were looked at by eye.
- **Method:** plain page reads at a slow rate, respecting robots.txt. REA's
  reverse-engineering tools were not needed: the pages are ordinary
  server-rendered HTML, so there was no hidden application to take apart.
- **What is stored here:** aggregated statistics
  (`architect/styles/production-contemporary-stats.json`) and patterns
  described in my own words. No drawings, images or descriptive text from the
  site are kept in this repository.
- **Copyright boundary:** Perry Homes' plan sheets state that the designs are
  their property and may not be reproduced. House plans are protected as
  architectural works. So the pipeline designs **original plans that follow
  the same general patterns**; it must never trace, copy or closely imitate a
  specific Perry design, and must not label output with their design numbers
  or name.
- **About the word "contemporary":** the three exteriors looked at are brick
  with steep front gables over a hip roof and arched windows, which is closer
  to traditional or transitional than to contemporary (flat or low roofs,
  large plain glazing, mixed cladding). The *interiors* are contemporary:
  open plans, tall ceilings, large rear glazing. This profile covers the plan
  patterns; the owner should say which exterior direction they want.

## What the catalogue contains (278 designs)

| Measure | Finding |
|---|---|
| Size | 1,500 to 5,573 sq ft; median 2,987 |
| Stories | 57% one-storey, 43% two-storey |
| Bedrooms | 3 bed 12%, 4 bed 69%, 5 bed 19% |
| Full baths | 2 baths 13%, 3 baths 60%, 4 baths 24%, 5 baths 3% |
| Half bath | 47% have at least one |
| Garage | 2-car 38%, 3-car 60%, 4-car 3%; every design has one |

### By lot width (their product lines)

| Lot width | Designs | Sq ft (min / median / max) | One-storey | Usual beds | Garage |
|---:|---:|---|---:|---|---|
| 40 ft | 25 | 1,500 / 1,878 / 2,443 | 60% | 3 | 2-car |
| 45 ft | 34 | 1,653 / 2,174 / 2,712 | 64% | 4 | 2-car |
| 50 ft | 39 | 1,996 / 2,544 / 3,553 | 64% | 4 | 2-car, some 3 |
| 55 ft | 10 | 2,493 / 2,731 / 3,573 | 70% | 4 | 2 or 3 |
| 60 ft | 68 | 2,493 / 3,091 / 4,016 | 61% | 4 | 3-car |
| 70 ft | 55 | 2,896 / 3,658 / 5,240 | 52% | 4 or 5 | 3-car |
| 80 ft | 16 | 3,478 / 4,414 / 5,573 | 43% | 4 or 5 | 3 or 4 |

### By size

| Sq ft | Designs | Usual program | Stories | Median base price |
|---|---:|---|---|---:|
| 1,500–2,000 | 27 | 3 bed / 2 bath, 2-car | all one-storey | $395,900 |
| 2,000–2,500 | 43 | 4 bed / 3 bath, 2-car | two-thirds one-storey | $445,900 |
| 2,500–3,000 | 72 | 4 bed / 3 bath, 2 or 3-car | mostly one-storey | $535,900 |
| 3,000–3,500 | 56 | 4 bed / 3 bath, 3-car | 60% one-storey | $646,900 |
| 3,500+ | 77 | 4–5 bed / 4 bath, 3-car | mostly two-storey | $759,900 |

Base prices include the lot and the builder's margin in master-planned
communities, so they are not construction cost. They work out to a median of
about $196 per sq ft overall and about $220 per sq ft for homes under
2,000 sq ft. The cheapest design listed was 1,500 sq ft at $348,900.

### How often features appear in the descriptions

| Feature | Share of designs |
|---|---:|
| Kitchen island with seating | 99% |
| Dual vanities in the primary bath | 97% |
| Covered rear patio | 96% |
| "Wall of windows" in family room or primary bedroom | 94% |
| Garden tub with separate shower in the primary bath | 89% |
| Walk-in pantry | 87% |
| French doors to a flex room | 84% |
| Mud room at the garage entry | 80% |
| Home office | 79% |
| Game room | 71% |
| Guest suite with its own bath | 62% |
| Two walk-in closets in the primary suite | 59% |
| Formal dining room | 40% |
| Two-storey entry or family room | 37% |
| Morning (breakfast) area | 36% |
| Media room | 32% |
| Fireplace (often optional) | 24% |
| Butler's pantry | 23% |
| Curved staircase | 12% |

Ceiling heights mentioned most: 12 ft (entries, primary bedrooms), 13 ft, and
19–21 ft for two-storey volumes. Plans label main rooms at 10 ft.

## Layout patterns (from three plans, 1,653 / 2,513 / 3,399 sq ft)

These are the recurring moves, stated as rules the pipeline can follow.

1. **Narrow and deep.** The house fills the lot's buildable width and runs
   back. The footprint is close to a rectangle with small jogs.
2. **Front-loaded garage takes about half the frontage.** The rest of the
   front is one room (dining, office, game room or a bedroom) with a large
   window.
3. **Recessed porch between garage and front room**, about 5–6 ft wide,
   leading to a single entry door.
4. **Entry is a hall, not a room.** It runs back along the garage wall with a
   raised ceiling, passes the flex room (French doors) and opens into the
   living core.
5. **Rear living core in one open line:** kitchen with island, then dining or
   morning area, then family room at the back, all along one side of the
   house. The family room's rear wall is mostly glass.
6. **Covered patio at the rear**, recessed under the main roof beside the
   primary bedroom or family room, reached from the family or morning area.
7. **Primary suite at a rear corner** for privacy. Bedroom first, then a bath
   with two vanities, tub and separate shower, with the walk-in closet reached
   through the bath.
8. **Secondary bedrooms form a side wing** off a short hall, each with a
   walk-in closet, sharing a bath. Larger plans add a guest suite with its own
   bath near the front.
9. **Service rooms inside the plan:** utility room near the bedrooms, mud room
   between garage and house, pantry in a kitchen corner, linen closets on the
   bedroom hall.
10. **Two-storey versions** keep the primary suite and one more bedroom
    downstairs; upstairs has a game room, sometimes a media room, and the
    remaining bedrooms. Entry and family room are often open to above.

Drafting conventions on their plan sheets: each room shows its name, a nominal
size and its ceiling height; fixtures, cabinets and the island are drawn;
dashed lines mark ceiling changes and options.

## Using this profile in a design

When the owner asks for a house "in this style":

- Pick the program from the lot width and size tables unless the spec says
  otherwise, and say which row was used.
- Follow patterns 1–10. Author an original layout; do not start from, or
  check against, any single Perry plan.
- Always include: garage, recessed front porch, covered rear patio, kitchen
  island, walk-in pantry, utility room, walk-in closets.
- Ask the owner which exterior direction they want (brick traditional, as
  Perry builds, or a truly contemporary exterior).

## What the pipeline can and cannot yet do for this style

| Need | Status |
|---|---|
| Garage, porch and covered patio as rooms excluded from living area | **Built** this session (`type: garage / porch / patio`, door `type: overhead`) |
| Open sides of porch and patio | Built, as wide `cased` openings in the exterior wall |
| Windows onto a patio counted for light, air and egress | Built |
| Layout template for this style | **Not built.** Layouts are authored per spec. |
| Plumbing fixtures, cabinets, kitchen island drawn | Not built |
| Footprints with jogs, L or U shapes | Not built; footprint is one rectangle with recessed porch and patio |
| Front gables over a hip roof, multiple roof planes | Not built; one hip or gable roof |
| Different ceiling heights per room, two-storey volumes | Not built; one plate height per level |
| Curved stairs, stair openings in the floor above | Not built |
| Brick, stone or other cladding in the 3D model | Not built; one wall colour |

## Budget

The owner's standing budget (stated 2026-11-13): homes priced from **$140,000
to $250,000**. Whether that is construction cost or sale price, and whether it
includes the lot, is not yet settled; ask before sizing a house against it.

Perry's smallest Houston design is 1,500 sq ft at a $348,900 base price, lot
included, so their whole catalogue sits above this budget. Designs for this
owner therefore take Perry's layout patterns at a smaller size and with fewer
features. To hold cost: one storey, a plain rectangle, one simple roof, a
2-car garage at most, 3 bedrooms and 2 baths, 9 ft ceilings, and wet rooms
grouped together. Keep the island kitchen, covered patio and walk-in closets;
drop the home office, game room, guest suite, mud room and tall ceilings
first.

Unverified planning figures from general cost guides put basic Houston-area
construction at roughly $90 to $185 per sq ft excluding land. No Beaumont
figure was found. Size a house from a builder's quoted cost per sq ft, not
from these.
