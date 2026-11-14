"""Back a sale price out to a construction budget and a house size.

sale price = lot + construction + builder's other costs and profit
The "other" share comes from the NAHB 2024 Cost of Constructing a Home survey
(national averages): overhead 5.7%, profit 11.0%, sales commission 2.8%,
financing 1.5%, marketing 0.8% = 21.8% of the sale price. Lot cost and build
cost per sq ft are inputs, because they are local and were not verified.
"""
OTHER_SHARES = {"overhead and general": 0.057, "profit": 0.110, "sales commission": 0.028,
                "financing": 0.015, "marketing": 0.008}
OTHER = sum(OTHER_SHARES.values())


def construction_budget(sale_price, lot_cost, other_share=OTHER):
    return sale_price * (1 - other_share) - lot_cost


def affordable_sqft(sale_price, lot_cost, cost_per_sqft, other_share=OTHER):
    return max(construction_budget(sale_price, lot_cost, other_share), 0) / cost_per_sqft


def required_cost_per_sqft(sale_price, lot_cost, sqft, other_share=OTHER):
    return construction_budget(sale_price, lot_cost, other_share) / sqft


def table(prices, lot_cost, costs):
    rows = []
    for p in prices:
        b = construction_budget(p, lot_cost)
        rows.append((p, p * OTHER, lot_cost, b, [max(b, 0) / c for c in costs]))
    return rows


def print_table(prices, lot_cost, costs):
    print(f"Lot ${lot_cost:,.0f}; builder overhead, profit, sales and financing {OTHER * 100:.1f}% of price")
    print(f"{'Sale price':>11} {'Other':>9} {'Build budget':>13}  " + "  ".join(f"@${c:.0f}/sf" for c in costs))
    for p, other, lot, b, sizes in table(prices, lot_cost, costs):
        print(f"${p:>10,.0f} ${other:>8,.0f} ${b:>12,.0f}  " + "  ".join(f"{s:>7,.0f}" for s in sizes))


# Cost weights relative to a square foot of living area. Assumptions, not data:
# a garage has a slab, walls and roof but little finish; a porch or patio has
# slab and roof only.
GARAGE_WEIGHT, OUTDOOR_WEIGHT = 0.5, 0.3


def effective_sqft(living, garage=0.0, outdoor=0.0):
    return living + GARAGE_WEIGHT * garage + OUTDOOR_WEIGHT * outdoor


def sale_price_for(living, garage, outdoor, cost_per_sqft, lot_cost, other_share=OTHER):
    """Sale price needed to build this house at a given cost per sq ft of living area."""
    return (lot_cost + cost_per_sqft * effective_sqft(living, garage, outdoor)) / (1 - other_share)
