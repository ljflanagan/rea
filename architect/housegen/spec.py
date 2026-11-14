"""Spec loading, defaults and the standing code baseline."""
import copy
import json
import re
from pathlib import Path

# Code baselines by jurisdiction. `to_confirm` lists what could not be verified
# against the adopted ordinance text and is printed in every report.
BASELINES = {
    "jefferson": {
        "id": "jefferson",
        "jurisdiction": "Jefferson County / City of Beaumont, Texas",
        "codes": ["2021 IRC", "2021 IPC", "2021 IECC", "2020 NEC", "ICC 600-2020"],
        "irc": "2021 IRC",
        "windstorm": "TDI / TWIA windstorm certification (WPI-8)",
        "windstorm_applies": "yes",
        "flood_basis": "bfe",
        "flood_freeboard_ft": 1.0,
        "notes": ["Finished floor at least 1 ft above base flood elevation where a BFE applies."],
        "to_confirm": [
            "Code editions are the owner's standing baseline. A local news report says Beaumont City Council "
            "adopted the 2021 I-codes, 2020 NEC and ICC 600-2020 on April 4, 2023; local amendments were not "
            "reviewed, and unincorporated Jefferson County may differ from the City of Beaumont.",
        ],
    },
    "harris": {
        "id": "harris",
        "jurisdiction": "Harris County, Texas (unincorporated)",
        "codes": ["2021 IRC (to confirm)", "2021 IECC (to confirm)", "2020 NEC (to confirm)"],
        "irc": "2021 IRC",
        "windstorm": "TDI / TWIA windstorm (WPI-8) only if the lot is in the designated area east of SH 146",
        "windstorm_applies": "check",
        "flood_basis": "500yr",
        "flood_freeboard_ft": 2.0,
        "notes": ["In the flood hazard area: finished floor 24 in. above the 0.2% (500-year) flood elevation "
                  "(to confirm)."],
        "to_confirm": [
            "Which residential code edition applies. Sources conflict on whether unincorporated Harris County "
            "enforces a residential building code of its own; state law points to the IRC edition in force in "
            "the county seat (Houston). The 2021 IRC screening values are used here as a placeholder.",
            "A lot inside a city (Houston, Pasadena, Katy, ...) follows that city's codes and amendments, not "
            "the county's. This baseline does not cover any city.",
            "The floodplain rule. 2017-2019 news reports of the county's post-Harvey regulations give the lowest "
            "floor as 24 in. above the 500-year flood elevation in the special flood hazard area; the current "
            "Regulations of Harris County for Flood Plain Management were not read.",
            "Whether the lot is in the TDI designated catastrophe area (the part of Harris County east of "
            "State Highway 146), which decides whether WPI-8 applies.",
            "Harris County also requires its own development permit, and detention or fill mitigation may apply.",
        ],
    },
}
BASELINE = BASELINES["jefferson"]          # the standing default

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
    "standards": {},
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
    over = raw.get("code") or {}
    jur = str(over.get("jurisdiction_id", "jefferson")).lower()
    if jur not in BASELINES:
        raise SpecError(f"code.jurisdiction_id '{jur}' is not known; available: {', '.join(BASELINES)}")
    spec["code"] = _merge(BASELINES[jur], {k: v for k, v in over.items() if k != "jurisdiction_id"})
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
