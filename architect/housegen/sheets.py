"""Printable sheets. One display list per sheet, written as SVG and as PDF.

Paper coordinates are inches from the bottom-left corner. Plan primitives
(model feet) are placed onto the paper by `place`.
"""
import base64
import datetime
import math
from xml.sax.saxutils import escape

from . import STAMP
from .mesh import roof_geometry
from .model import UNCONDITIONED
from .plan2d import LAYERS, plan_extent, plan_primitives, site_primitives
from .units import ft_in, sf

PT = 72.0
SCALES = [(0.5, "1/2\" = 1'-0\""), (0.375, "3/8\" = 1'-0\""), (0.25, "1/4\" = 1'-0\""),
          (0.1875, "3/16\" = 1'-0\""), (0.125, "1/8\" = 1'-0\""), (0.09375, "3/32\" = 1'-0\""),
          (0.0625, "1/16\" = 1'-0\"")]
SITE_SCALES = [(1 / 8.0, "1\" = 8'"), (1 / 10.0, "1\" = 10'"), (1 / 16.0, "1\" = 16'"), (1 / 20.0, "1\" = 20'"),
               (1 / 30.0, "1\" = 30'"), (1 / 40.0, "1\" = 40'"), (1 / 50.0, "1\" = 50'"), (1 / 100.0, "1\" = 100'")]
TB_W, MARGIN = 3.7, 0.4


def text_width(s, h, bold=False):
    return len(s) * h * (0.86 if bold else 0.78)


class Canvas:
    """Display list in paper inches."""

    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def line(self, x1, y1, x2, y2, stroke="#000", width=0.5, dash=None):
        self.items.append(("line", x1, y1, x2, y2, stroke, width, dash))

    def path(self, rings, stroke="#000", width=0.5, fill=None, dash=None, closed=True):
        self.items.append(("path", rings, stroke, width, fill, dash, closed))

    def rect(self, x, y, w, h, **kw):
        self.path([[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]], **kw)

    def arc(self, cx, cy, r, a0, a1, stroke="#000", width=0.5):
        self.items.append(("arc", cx, cy, r, a0, a1, stroke, width))

    def text(self, x, y, s, h=0.1, anchor="middle", rot=0, bold=False, color="#111", valign="middle"):
        self.items.append(("text", x, y, s, h, anchor, rot, bold, color, valign))

    def image(self, x, y, w, h, path):
        self.items.append(("image", x, y, w, h, path))

    def paragraph(self, x, y, s, h, width, color="#111", bold=False, leading=1.75):
        """Left-aligned wrapped text starting at the top line y. Returns the next y."""
        words, line = s.split(), ""
        for wd in words:
            trial = (line + " " + wd).strip()
            if text_width(trial, h, bold) > width and line:
                self.text(x, y, line, h, "start", 0, bold, color); y -= h * leading
                line = wd
            else:
                line = trial
        if line:
            self.text(x, y, line, h, "start", 0, bold, color); y -= h * leading
        return y

    # ---- SVG -----------------------------------------------------------
    def to_svg(self, path):
        W, H = self.w * PT, self.h * PT
        Y = lambda y: H - y * PT
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
             f'width="{self.w}in" height="{self.h}in" viewBox="0 0 {W:.1f} {H:.1f}" '
             f'font-family="Helvetica, Arial, sans-serif">',
             f'<rect width="{W:.1f}" height="{H:.1f}" fill="#ffffff"/>']

        def st(stroke, width, dash, fill="none"):
            s = f'fill="{fill or "none"}"'
            if stroke and width:
                s += f' stroke="{stroke}" stroke-width="{width}"'
                if dash:
                    s += ' stroke-dasharray="' + ",".join(map(str, dash)) + '"'
            return s
        for it in self.items:
            k = it[0]
            if k == "line":
                _, x1, y1, x2, y2, stroke, width, dash = it
                o.append(f'<line x1="{x1 * PT:.2f}" y1="{Y(y1):.2f}" x2="{x2 * PT:.2f}" y2="{Y(y2):.2f}" '
                         f'{st(stroke, width, dash)} stroke-linecap="round"/>')
            elif k == "path":
                _, rings, stroke, width, fill, dash, closed = it
                d = ""
                for ring in rings:
                    d += "M" + " L".join(f"{x * PT:.2f},{Y(y):.2f}" for x, y in ring) + (" Z " if closed else " ")
                o.append(f'<path d="{d}" fill-rule="evenodd" {st(stroke, width, dash, fill)} stroke-linejoin="miter"/>')
            elif k == "arc":
                _, cx, cy, r, a0, a1, stroke, width = it
                p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
                p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
                large = 1 if (a1 - a0) > 180 else 0
                o.append(f'<path d="M{p0[0] * PT:.2f},{Y(p0[1]):.2f} A{r * PT:.2f},{r * PT:.2f} 0 {large} 0 '
                         f'{p1[0] * PT:.2f},{Y(p1[1]):.2f}" {st(stroke, width, None)}/>')
            elif k == "text":
                _, x, y, s, h, anchor, rot, bold, color, valign = it
                fs = h * 100
                dy = 0.36 * fs if valign == "middle" else 0
                tr = f' transform="rotate({-rot} {x * PT:.2f} {Y(y):.2f})"' if rot else ""
                o.append(f'<text x="{x * PT:.2f}" y="{Y(y) + dy:.2f}" font-size="{fs:.2f}" text-anchor="{anchor}" '
                         f'fill="{color}"{" font-weight=\"bold\"" if bold else ""}{tr}>{escape(s)}</text>')
            elif k == "image":
                _, x, y, w, h, p = it
                data = base64.b64encode(open(p, "rb").read()).decode()
                o.append(f'<image x="{x * PT:.2f}" y="{Y(y + h):.2f}" width="{w * PT:.2f}" height="{h * PT:.2f}" '
                         f'xlink:href="data:image/png;base64,{data}"/>')
        o.append("</svg>")
        with open(path, "w") as f:
            f.write("\n".join(o))

    # ---- PDF -----------------------------------------------------------
    def to_pdf(self, c):
        """Draw onto a reportlab canvas page."""
        from reportlab.lib.colors import HexColor
        c.setPageSize((self.w * PT, self.h * PT))
        for it in self.items:
            k = it[0]
            c.saveState()
            if k == "line":
                _, x1, y1, x2, y2, stroke, width, dash = it
                c.setStrokeColor(HexColor(stroke)); c.setLineWidth(width); c.setLineCap(1)
                if dash:
                    c.setDash(list(dash))
                c.line(x1 * PT, y1 * PT, x2 * PT, y2 * PT)
            elif k == "path":
                _, rings, stroke, width, fill, dash, closed = it
                p = c.beginPath()
                for ring in rings:
                    p.moveTo(ring[0][0] * PT, ring[0][1] * PT)
                    for x, y in ring[1:]:
                        p.lineTo(x * PT, y * PT)
                    if closed:
                        p.close()
                if stroke and width:
                    c.setStrokeColor(HexColor(stroke)); c.setLineWidth(width)
                    if dash:
                        c.setDash(list(dash))
                if fill:
                    c.setFillColor(HexColor(fill))
                c.drawPath(p, stroke=1 if (stroke and width) else 0, fill=1 if fill else 0, fillMode=0)
            elif k == "arc":
                _, cx, cy, r, a0, a1, stroke, width = it
                c.setStrokeColor(HexColor(stroke)); c.setLineWidth(width)
                c.arc((cx - r) * PT, (cy - r) * PT, (cx + r) * PT, (cy + r) * PT, a0, a1 - a0)
            elif k == "text":
                _, x, y, s, h, anchor, rot, bold, color, valign = it
                fs = h * 100
                c.setFillColor(HexColor(color))
                c.setFont("Helvetica-Bold" if bold else "Helvetica", fs)
                c.translate(x * PT, y * PT)
                if rot:
                    c.rotate(rot)
                dy = -0.36 * fs if valign == "middle" else 0
                s = s.replace("—", "-")
                {"middle": c.drawCentredString, "start": c.drawString, "end": c.drawRightString}[anchor](0, dy, s)
            elif k == "image":
                _, x, y, w, h, p = it
                c.drawImage(p, x * PT, y * PT, w * PT, h * PT)
            c.restoreState()
        c.showPage()


def place(cv, prims, scale, ox, oy, mx0, my0):
    """Draw model-space primitives at `scale` paper inches per foot."""
    X = lambda x: ox + (x - mx0) * scale
    Y = lambda y: oy + (y - my0) * scale
    for p in prims:
        _aci, _lt, stroke, width, dash, fill = LAYERS[p["layer"]]
        t = p["type"]
        if t == "region":
            cv.path([[(X(x), Y(y)) for x, y in ring] for ring in p["rings"]],
                    stroke=stroke, width=width, fill=fill)
        elif t == "line" and stroke:
            cv.line(X(p["a"][0]), Y(p["a"][1]), X(p["b"][0]), Y(p["b"][1]), stroke, width, dash)
        elif t == "poly" and stroke:
            cv.path([[(X(x), Y(y)) for x, y in p["pts"]]], stroke=stroke, width=width, dash=dash,
                    closed=p["closed"])
        elif t == "arc":
            cv.arc(X(p["c"][0]), Y(p["c"][1]), p["r"] * scale, p["a0"], p["a1"], stroke, width * 0.7)
        elif t == "text":
            cv.text(X(p["at"][0]), Y(p["at"][1]), p["text"], p["h"], "middle", p["rot"], p["bold"],
                    stroke or "#111")
        elif t == "dim":
            _dim(cv, p, X, Y, stroke, width)


def _dim(cv, p, X, Y, stroke, width):
    h = 0.085
    gap, over, tick = 0.06, 0.07, 0.05
    s = p["out"]
    if p["axis"] == "h":
        y = Y(p["pos"])
        xa, xb = X(p["a"][0]), X(p["b"][0])
        for x, q in ((xa, p["a"]), (xb, p["b"])):
            y_from = Y(q[1]) + s * gap
            if (y - y_from) * s > 0:
                cv.line(x, y_from, x, y + s * over, stroke, width * 0.7)
            cv.line(x - tick, y - tick, x + tick, y + tick, stroke, width * 2.2)
        cv.line(xa - over, y, xb + over, y, stroke, width)
        fits = text_width(p["text"], h) < abs(xb - xa) - 0.06
        cv.text((xa + xb) / 2, y + (0.085 if fits else -0.105), p["text"], h, "middle", 0, False, "#111")
    else:
        x = X(p["pos"])
        ya, yb = Y(p["a"][1]), Y(p["b"][1])
        for y, q in ((ya, p["a"]), (yb, p["b"])):
            x_from = X(q[0]) + s * gap
            if (x - x_from) * s > 0:
                cv.line(x_from, y, x + s * over, y, stroke, width * 0.7)
            cv.line(x - tick, y - tick, x + tick, y + tick, stroke, width * 2.2)
        cv.line(x, ya - over, x, yb + over, stroke, width)
        fits = text_width(p["text"], h) < abs(yb - ya) - 0.06
        cv.text(x - (0.085 if fits else -0.105), (ya + yb) / 2, p["text"], h, "middle", 90, False, "#111")


def new_sheet(spec, number, title, scale_label):
    w, h = spec["sheet"]["size_in"]
    cv = Canvas(w, h)
    m = MARGIN
    cv.rect(m, m, w - 2 * m, h - 2 * m, stroke="#000", width=1.6)
    tx = w - m - TB_W
    cv.line(tx, m, tx, h - m, "#000", 1.2)
    x, y = tx + 0.2, h - m - 0.35
    inner = TB_W - 0.4
    y = cv.paragraph(x, y, spec["project"]["name"].upper(), 0.15, inner, bold=True)
    y -= 0.1
    lot = spec.get("lot") or {}
    pr = spec["program"]
    for ln in (f"{pr['beds']} bedroom / {pr['baths']:g} bath, target {pr['target_sqft']:,} sq ft",
               f"Lot {lot.get('width_ft', '?'):g} x {lot.get('depth_ft', '?'):g} ft",
               spec["code"]["jurisdiction"]):
        y = cv.paragraph(x, y, ln, 0.085, inner)
    y -= 0.12
    cv.line(tx, y, w - m, y, "#000", 0.6); y -= 0.25
    cv.text(x, y, "CODE BASELINE", 0.08, "start", bold=True); y -= 0.2
    y = cv.paragraph(x, y, ", ".join(spec["code"]["codes"]), 0.08, inner)
    y = cv.paragraph(x, y, spec["code"]["windstorm"], 0.08, inner)
    for n in spec["code"].get("notes", []):
        y = cv.paragraph(x, y, n, 0.08, inner)
    y -= 0.12
    cv.line(tx, y, w - m, y, "#000", 0.6)
    cv.meta_y = y - 0.25            # free space for sheet-specific notes
    cv.tb_x, cv.tb_inner = x, inner
    # stamp
    sy = m + 1.75
    cv.rect(tx + 0.12, sy, TB_W - 0.24, 1.45, stroke="#b00000", width=2.0, fill="#fff5f5")
    yy = sy + 1.2
    for ln, hh in (("CONCEPT", 0.2), ("NOT FOR CONSTRUCTION", 0.15)):
        cv.text(tx + TB_W / 2, yy, ln, hh, "middle", 0, True, "#b00000"); yy -= hh * 1.9
    yy -= 0.02
    for ln in ("requires validation by a licensed", "Texas architect/PE."):
        cv.text(tx + TB_W / 2, yy, ln, 0.1, "middle", 0, True, "#b00000"); yy -= 0.19
    # sheet id
    cv.line(tx, m + 1.6, w - m, m + 1.6, "#000", 0.6)
    cv.text(x, m + 1.3, title.upper(), 0.14, "start", bold=True)
    cv.text(x, m + 1.0, f"Scale: {scale_label}", 0.09, "start")
    cv.text(x, m + 0.78, f"Date: {spec.get('date') or datetime.date.today().isoformat()}", 0.09, "start")
    cv.text(x, m + 0.56, "Derived from model.json (single source model)", 0.07, "start", color="#555")
    cv.text(w - m - 0.2, m + 0.3, number, 0.3, "end", bold=True)
    cv.draw_area = (m + 0.3, m + 0.3, tx - 0.3, h - m - 0.3)
    return cv


def _fit(extent_fn, scales, area_w, area_h):
    for sc, label in scales:
        x0, y0, x1, y1 = extent_fn(sc)
        if (x1 - x0) * sc <= area_w and (y1 - y0) * sc <= area_h:
            return sc, label, (x0, y0, x1, y1)
    sc, label = scales[-1]
    return sc, label, extent_fn(sc)


def plan_sheet(b, spec, lid, number):
    """Returns (canvas, primitives, scale) so the DXF can reuse the primitives."""
    cv = new_sheet(spec, number, "", "")
    ax0, ay0, ax1, ay1 = cv.draw_area
    cache = {}

    def ext(sc):
        cache[sc] = plan_primitives(b, lid, sc)
        x0, y0, x1, y1 = plan_extent(cache[sc], sc)
        return x0 - 0.3 / sc, y0 - 0.3 / sc, x1 + 0.3 / sc, y1 + 0.3 / sc
    sc, label, (x0, y0, x1, y1) = _fit(ext, SCALES, ax1 - ax0, ay1 - ay0 - 0.9)
    prims = cache[sc]
    lv = b.level(lid)
    title = f"{lv.name} Plan" if len(b.levels) > 1 else "Floor Plan"
    cv = new_sheet(spec, number, title, label)
    pw, ph = (x1 - x0) * sc, (y1 - y0) * sc
    ox = ax0 + (ax1 - ax0 - pw) / 2
    oy = ay0 + 0.9 + (ay1 - ay0 - 0.9 - ph) / 2
    place(cv, prims, sc, ox, oy, x0, y0)
    cxm = (ax0 + ax1) / 2
    cv.text(cxm, oy - 0.25, title.upper(), 0.2, "middle", bold=True)
    cv.line(cxm - 2.2, oy - 0.42, cxm + 2.2, oy - 0.42, "#000", 1.0)
    cv.text(cxm, oy - 0.58, f"SCALE: {label}", 0.1)
    gx0, gy0, gx1, gy1 = b.gross_polygon(lid).bounds
    cv.text(ox + ((gx0 + gx1) / 2 - x0) * sc, oy + 0.12, "FRONT (STREET SIDE)", 0.085, color="#555")
    # notes in the title block
    y = cv.meta_y
    x, inner = cv.tb_x, cv.tb_inner
    cv.text(x, y, "AREAS", 0.08, "start", bold=True); y -= 0.2
    net = sum(r.area for r in b.rooms_on(lid) if r.kind not in UNCONDITIONED)
    for k, v in (("Living area (outside face of walls)", sf(b.conditioned_area(lid))),
                 ("Garage, porch, patio", sf(b.unconditioned_area(lid))),
                 ("Net area of conditioned rooms", sf(net)),
                 ("Target", sf(spec["program"]["target_sqft"]))):
        cv.text(x, y, k, 0.08, "start"); cv.text(x + inner, y, v, 0.08, "end", bold=True); y -= 0.17
    y -= 0.12
    cv.text(x, y, "PLAN NOTES", 0.08, "start", bold=True); y -= 0.2
    notes = ["Exterior dimensions are to the outside face of exterior walls and to the centerline of "
             "partitions and openings.",
             "Room sizes shown are clear dimensions between finished wall faces; areas are net.",
             "Opening tags read width then height in feet-inches: 3068 = 3'-0\" x 6'-8\".",
             f"Exterior walls {ft_in(spec['construction']['ext_wall_in'] / 12)} nominal, "
             f"partitions {ft_in(spec['construction']['int_wall_in'] / 12)}; "
             f"plate height {ft_in(lv.height)}.",
             "Dashed line is the roof edge above."]
    for n in notes:
        y = cv.paragraph(x, y, n, 0.072, inner, color="#333", leading=1.7) - 0.05
    return cv, prims, sc


def site_sheet(b, spec, report, number="A-001"):
    cv0 = new_sheet(spec, number, "", "")
    ax0, ay0, ax1, ay1 = cv0.draw_area
    site_w = (ax1 - ax0) * 0.42
    cache = {}

    def ext(sc):
        cache[sc] = site_primitives(b, sc)
        x0, y0, x1, y1 = plan_extent(cache[sc], sc)
        return x0 - 0.35 / sc, y0 - 0.35 / sc, x1 + 0.35 / sc, y1 + 0.35 / sc
    sc, label, (x0, y0, x1, y1) = _fit(ext, SITE_SCALES, site_w, ay1 - ay0 - 0.9)
    cv = new_sheet(spec, number, "Site Plan and Schedules", label)
    pw, ph = (x1 - x0) * sc, (y1 - y0) * sc
    ox = ax0 + (site_w - pw) / 2
    oy = ay0 + 0.9 + (ay1 - ay0 - 0.9 - ph) / 2
    place(cv, cache[sc], sc, ox, oy, x0, y0)
    cxm = ax0 + site_w / 2
    cv.text(cxm, ay0 + 0.62, "SITE PLAN", 0.2, "middle", bold=True)
    cv.line(cxm - 1.6, ay0 + 0.45, cxm + 1.6, ay0 + 0.45, "#000", 1.0)
    cv.text(cxm, ay0 + 0.29, f"SCALE: {label}", 0.1)

    # schedules, right of the site plan
    x = ax0 + site_w + 0.5
    colw = ax1 - x
    y = ay1 - 0.15
    cv.text(x, y, "ROOM SCHEDULE", 0.13, "start", bold=True); y -= 0.3
    half = colw * 0.47
    cols = [(0, "Room", "start"), (half * 0.62, "Net area", "end"), (half, "Clear size", "end")]
    rooms = sorted(b.rooms, key=lambda r: -r.area)
    per = math.ceil(len(rooms) / 2)
    y_top = y
    for ci in range(2):
        cx0 = x + ci * (half + colw * 0.06)
        y = y_top
        for off, hd, an in cols:
            cv.text(cx0 + off, y, hd, 0.08, an, bold=True, color="#555")
        y -= 0.1
        cv.line(cx0, y, cx0 + half, y, "#000", 0.6); y -= 0.17
        for r in rooms[ci * per:(ci + 1) * per]:
            cv.text(cx0, y, r.name, 0.085, "start")
            cv.text(cx0 + half * 0.62, y, sf(r.area), 0.085, "end")
            cv.text(cx0 + half, y, f"{ft_in(r.clear[0], 1)} x {ft_in(r.clear[1], 1)}", 0.085, "end")
            y -= 0.19
    y = y_top - 0.27 - per * 0.19 - 0.1
    cv.line(x, y, x + colw, y, "#000", 0.6); y -= 0.2
    s = report["summary"]
    rows = [("Net area of conditioned rooms", sf(s["net_area"])),
            ("Garage, porch and patio (not living area)", sf(s["unconditioned_area"])),
            ("Living area (outside face of walls)", sf(s["gross_area"])),
            ("Target", f"{sf(s['target'])}   ({s['delta_pct']:+.1f}%)")]
    for k, v in rows:
        cv.text(x, y, k, 0.09, "start"); cv.text(x + colw, y, v, 0.09, "end", bold=True); y -= 0.2
    y -= 0.2
    cv.text(x, y, "SITE DATA", 0.13, "start", bold=True); y -= 0.3
    for k, v in report["site_rows"]:
        cv.text(x, y, k, 0.09, "start"); cv.text(x + colw, y, v, 0.09, "end", bold=True); y -= 0.2
    y -= 0.2
    cv.text(x, y, "VALIDATION SUMMARY", 0.13, "start", bold=True); y -= 0.3
    c = report["counts"]
    cv.text(x, y, f"{c['PASS']} pass    {c['WARN']} warnings    {c['FAIL']} failures    "
            f"{c['INFO']} items for the design professional", 0.09, "start"); y -= 0.26
    for chk in [k for k in report["checks"] if k["status"] in ("FAIL", "WARN")][:9]:
        col = "#b00000" if chk["status"] == "FAIL" else "#8a5a00"
        cv.text(x, y, chk["status"], 0.075, "start", bold=True, color=col)
        y = cv.paragraph(x + 0.5, y, chk["message"], 0.075, colw - 0.5, color="#222", leading=1.65) - 0.05
    y -= 0.15
    if spec.get("assumptions") and y > ay0 + 1.2:
        cv.text(x, y, "ASSUMPTIONS TO CONFIRM", 0.13, "start", bold=True); y -= 0.28
        for a in spec["assumptions"]:
            if y < ay0 + 0.3:
                break
            y = cv.paragraph(x, y, "- " + a, 0.075, colw, color="#222", leading=1.65) - 0.05
    cv.text(x, ay0 + 0.05, "See validation-report.md for every check and its code reference.", 0.07, "start",
            color="#555")
    return cv


def views_sheet(b, spec, views, number="A-201"):
    cv = new_sheet(spec, number, "3D Views and Elevations", "Not to scale")
    ax0, ay0, ax1, ay1 = cv.draw_area
    gap = 0.25
    w = (ax1 - ax0 - gap) / 2
    hp = w * 1000 / 1600
    he = w * 500 / 1400
    total = hp + 2 * he + 2 * gap
    y = ay1 - (ay1 - ay0 - total) / 2 - hp
    for i, k in enumerate(("3d-front", "3d-roof-off")):
        cv.image(ax0 + i * (w + gap), y, w, hp, views[k])
        cv.rect(ax0 + i * (w + gap), y, w, hp, stroke="#888", width=0.5)
    for row, pair in enumerate((("elev-front", "elev-rear"), ("elev-left", "elev-right"))):
        y -= he + gap
        for i, k in enumerate(pair):
            cv.image(ax0 + i * (w + gap), y, w, he, views[k])
            cv.rect(ax0 + i * (w + gap), y, w, he, stroke="#888", width=0.5)
    yy = cv.meta_y
    rg = roof_geometry(b)
    cv.text(cv.tb_x, yy, "MODEL NOTES", 0.08, "start", bold=True); yy -= 0.2
    for n in (f"{b.roof.type.title()} roof, {b.roof.pitch:g}:12 pitch, {ft_in(b.roof.overhang)} overhang; "
              f"ridge {ft_in(rg['zr'])} above finished floor.",
              "All views are renders of model.glb; they are not separate drawings.",
              "Elevations are orthographic and undimensioned.",
              "Finishes, trim, fixtures and structure are not modelled."):
        yy = cv.paragraph(cv.tb_x, yy, n, 0.072, cv.tb_inner, color="#333", leading=1.7) - 0.05
    return cv


def write_sheets(sheets, outdir):
    """sheets: list of (file stem, canvas). Writes one SVG each and a combined PDF."""
    from reportlab.pdfgen import canvas as rl
    paths = []
    pdf = rl.Canvas(f"{outdir}/sheets.pdf")
    pdf.setTitle("Concept sheets"); pdf.setSubject(STAMP)
    for stem, cv in sheets:
        cv.to_svg(f"{outdir}/{stem}.svg")
        cv.to_pdf(pdf)
        paths.append(f"{outdir}/{stem}.svg")
    pdf.save()
    return paths
