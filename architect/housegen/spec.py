"""Spec loading, defaults and the standing code baseline."""
import copy
import json
import re
from pathlib import Path

BASELINE = {
    "id": "jefferson-beaumont-tx",
    "jurisdiction": "Jefferson County / City of Beaumont, Texas",
    "codes": ["2021 IRC", "2021 IPC", "2021 IECC", "2020 NEC", "ICC 600-2020"],
    "windstorm": "TDI / TWIA windstorm certification (WPI-8)",
    "flood_freeboard_ft": 1.0,
    "notes": [
        "Finished floor at least 1 ft above base flood elevation where a BFE applies.",
    ],
}

DEFAULTS = {
    "project": {"name": None, "slug": None},
    "program": {"stories": 1},
    "preferences": {"template": "split_ranch", "primary_side": "left"},
    "construction": {"ext_wall_in": 6.0, "int_wall_in": 4.5, "ceiling_ft": 9.0},
    "roof": {"type": "hip", "pitch": 5, "overhang_ft": 1.0},
    "foundation": {"type": "slab-on-grade", "floor_above_grade_ft": 1.0},
    "budget": {},
    "sheet": {"size_in": [24, 18]},
    "assumptions": [],
}

REQUIRED = [
    ("program.target_sqft", "target conditioned square footage"),
    ("program.beds", "number of bedrooms"),
    ("program.baths", "number of bathrooms"),
    ("lot.width_ft", "lot width along the street"),
    ("lot.depth_ft", "lot depth"),
    ("lot.setbacks_ft.front", "front setback"),
    ("lot.setbacks_ft.side", "side setback"),
    ("lot.setbacks_ft.rear", "rear setback"),
]


class SpecError(Exception):
    """The spec is missing something the pipeline refuses to invent."""


def _get(d, path):
    for k in path.split("."):
        if not isinstance(d, dict) or k not in d or d[k] is None:
            return None
        d = d[k]
    return d


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_spec(path):
    text = Path(path).read_text()
    if str(path).endswith(".json"):
        raw = json.loads(text)
    else:
        import yaml
        raw = yaml.safe_load(text)
    return normalise(raw)


def normalise(raw):
    spec = _merge(DEFAULTS, raw)
    missing = [f"{p} ({why})" for p, why in REQUIRED if _get(spec, p) is None]
    if missing:
        raise SpecError("The spec does not say: " + "; ".join(missing)
                        + ". Ask the owner; do not invent these.")
    spec["code"] = _merge(BASELINE, raw.get("code") or {})
    pr = spec["program"]
    baths = pr["baths"]
    bath_s = str(int(baths)) if float(baths) == int(baths) else str(baths).replace(".", "p")
    place = spec["project"].get("slug") or "house"
    spec["folder"] = f"{int(pr['beds'])}bd{bath_s}ba-{int(round(pr['target_sqft']))}sqft-{_slug(place)}"
    if not spec["project"].get("name"):
        spec["project"]["name"] = (f"{int(pr['beds'])} Bed / {bath_s} Bath, "
                                   f"{int(pr['target_sqft']):,} SF Residence")
    return spec


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
