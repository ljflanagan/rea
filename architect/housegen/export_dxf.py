"""DXF export of the plan primitives (the same list the printed sheet draws).

Model space, 1 unit = 1 inch, AIA-style layer names. Text and dimension
sizes are set for plotting at the sheet's scale. Written as DXF R2010.
"""
import ezdxf
from ezdxf import const
from ezdxf.enums import TextEntityAlignment

from . import STAMP
from .plan2d import LAYERS


def write_dxf(prims, path, scale, title, extra=()):
    """scale: paper inches per foot. extra: more primitives (site lines)."""
    k = 12.0                      # feet -> inches
    ann = 12.0 / scale            # paper inch -> model inches
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 1
    doc.header["$MEASUREMENT"] = 0
    doc.header["$LUNITS"] = 4     # architectural
    for name, (aci, lt, *_rest) in LAYERS.items():
        doc.layers.add(name, color=aci, linetype=lt if lt in doc.linetypes else "CONTINUOUS")
    doc.layers.get("A-AREA").dxf.plot = 0
    ds = doc.dimstyles.new("HOUSEGEN")
    for key, val in {"dimtxt": 0.085 * ann, "dimasz": 0.09 * ann, "dimtsz": 0.05 * ann, "dimexe": 0.07 * ann,
                     "dimexo": 0.06 * ann, "dimgap": 0.04 * ann, "dimtad": 1, "dimdle": 0.07 * ann,
                     "dimlunit": 4, "dimtih": 0, "dimtoh": 0}.items():
        ds.set_dxf_attrib(key, val)
    msp = doc.modelspace()
    P = lambda p: (p[0] * k, p[1] * k)
    ys = []
    for p in list(prims) + list(extra):
        layer = {"layer": p["layer"]}
        t = p["type"]
        if t == "region":
            h = msp.add_hatch(color=const.BYLAYER, dxfattribs=layer)
            for i, ring in enumerate(p["rings"]):
                pts = [P(q) for q in ring]
                h.paths.add_polyline_path(pts, is_closed=True,
                                          flags=const.BOUNDARY_PATH_EXTERNAL if i == 0 else const.BOUNDARY_PATH_DEFAULT)
                msp.add_lwpolyline(pts, close=True, dxfattribs=layer)
                ys += [q[1] for q in pts]
        elif t == "line":
            msp.add_line(P(p["a"]), P(p["b"]), dxfattribs=layer)
        elif t == "poly":
            msp.add_lwpolyline([P(q) for q in p["pts"]], close=p["closed"], dxfattribs=layer)
        elif t == "arc":
            msp.add_arc(P(p["c"]), p["r"] * k, p["a0"], p["a1"], dxfattribs=layer)
        elif t == "text":
            e = msp.add_text(p["text"], height=p["h"] * ann, rotation=p["rot"], dxfattribs=layer)
            e.set_placement(P(p["at"]), align=TextEntityAlignment.MIDDLE_CENTER)
        elif t == "dim":
            a, c = P(p["a"]), P(p["b"])
            if p["axis"] == "h":
                base, angle = (a[0], p["pos"] * k), 0
            else:
                base, angle = (p["pos"] * k, a[1]), 90
            d = msp.add_linear_dim(base=base, p1=a, p2=c, angle=angle, text=p["text"],
                                   dimstyle="HOUSEGEN", dxfattribs=layer)
            d.render()
            ys.append(base[1])
    xs = [q[0] for p in prims if p["type"] == "region" for ring in p["rings"] for q in ring]
    cx = (min(xs) + max(xs)) / 2 * k
    y = min(ys) - 0.9 * ann
    for txt, hgt, layer in ((title, 0.2, "A-ANNO-TTLB"), (STAMP, 0.13, "A-ANNO-NOTE")):
        e = msp.add_text(txt, height=hgt * ann, dxfattribs={"layer": layer})
        e.set_placement((cx, y), align=TextEntityAlignment.MIDDLE_CENTER)
        y -= 0.4 * ann
    doc.saveas(path)
    return path
