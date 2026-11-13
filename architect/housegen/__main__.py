"""python3 -m housegen design specs/<spec>.yaml [--out houses]"""
import argparse
import sys
from pathlib import Path

from .model import ModelError
from .pipeline import design
from .spec import SpecError, load_spec
from .templates import TemplateError


def main():
    ap = argparse.ArgumentParser(prog="housegen")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("design", help="spec -> plan, 3D model, validation report")
    d.add_argument("spec")
    d.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "houses"))
    g = sub.add_parser("budget", help="sale price -> construction budget and house size")
    g.add_argument("--lot", type=float, required=True, help="lot cost in dollars")
    g.add_argument("--prices", type=float, nargs="+", default=[140000, 170000, 200000, 225000, 250000])
    g.add_argument("--costs", type=float, nargs="+", default=[100, 115, 130, 150],
                   help="construction cost per sq ft of living area to tabulate")
    a = ap.parse_args()
    if a.cmd == "budget":
        from .budget import print_table
        print_table(a.prices, a.lot, a.costs)
        return
    try:
        spec = load_spec(a.spec)
        _b, report, _out = design(spec, a.out)
    except SpecError as e:
        sys.exit(f"SPEC INCOMPLETE: {e}")
    except TemplateError as e:
        sys.exit(f"NO TEMPLATE FITS: {e}")
    except ModelError as e:
        sys.exit(f"MODEL ERROR: {e}")
    sys.exit(1 if report["counts"]["FAIL"] else 0)


main()
