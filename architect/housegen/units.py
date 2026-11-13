"""Feet-and-inches formatting. The model stores decimal feet everywhere."""
import math
from fractions import Fraction

FT_TO_M = 0.3048


def ft_in(feet, denom=4):
    """12.5 -> 12'-6"   (rounded to the nearest 1/denom inch)."""
    neg = feet < 0
    total = round(abs(feet) * 12 * denom)
    whole_in, frac = divmod(total, denom)
    ft, inch = divmod(whole_in, 12)
    s = f"{ft}'-{inch}"
    if frac:
        f = Fraction(frac, denom)
        s += f" {f.numerator}/{f.denominator}"
    return ("-" if neg else "") + s + '"'


def sf(area):
    return f"{area:,.0f} SF"


def r05(x):
    """Round to the nearest half foot (layout module)."""
    return round(x * 2) / 2.0
