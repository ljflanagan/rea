"""Software renderer (numpy z-buffer) for PNG views of the element meshes.

It draws exactly the triangles that go into the glTF, so a render is a
picture of the delivered 3D model, not a separate illustration.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import STAMP
from .mesh import MATERIALS

LIGHT = np.array([0.35, -0.55, 0.76])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
SKY = np.array([1.0, 1.0, 1.0])


def _font(size, bold=False):
    for name in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
                 ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _look(eye, target):
    f = np.array(target, float) - np.array(eye, float)
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0])
    if np.linalg.norm(r) < 1e-9:
        r = np.array([1.0, 0, 0])
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return r, u, f


def render(elements, path, eye, target, ortho=None, fov=38, size=(1600, 1000), ss=2,
           hide=(), caption=None, stamp=True):
    """ortho: None for perspective, else the view height in feet."""
    W, H = size[0] * ss, size[1] * ss
    r, u, f = _look(eye, target)
    eye = np.array(eye, float)
    tris, cols, alphas = [], [], []
    for el in elements:
        if el.category in hide or el.id in hide:
            continue
        c = MATERIALS[el.material]
        for t in el.triangles():
            tris.append(t); cols.append(c[:3]); alphas.append(c[3])
    T = np.array(tris, float)                      # n,3,3
    rel = T - eye
    cam = np.stack([rel @ r, rel @ u, rel @ f], axis=-1)
    if ortho:
        s = H / ortho
        sx = W / 2 + cam[..., 0] * s
        sy = H / 2 - cam[..., 1] * s
        depth = cam[..., 2]
    else:
        fl = (H / 2) / np.tan(np.radians(fov) / 2)
        z = np.maximum(cam[..., 2], 0.05)
        sx = W / 2 + cam[..., 0] / z * fl
        sy = H / 2 - cam[..., 1] / z * fl
        depth = cam[..., 2]
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = nrm / np.maximum(ln, 1e-12)
    toward = np.einsum("ij,ij->i", nrm, (eye - T.mean(1)) if not ortho else np.tile(-f, (len(T), 1)))
    nrm = np.where(toward[:, None] < 0, -nrm, nrm)          # two-sided shading
    light = LIGHT
    if ortho:                      # elevations: light from over the viewer's shoulder
        light = -f + np.array([0, 0, 0.6]) + 0.35 * r
        light = light / np.linalg.norm(light)
    shade = 0.42 + 0.58 * np.clip(nrm @ light, 0, 1)
    color = np.array(cols) * shade[:, None]

    zbuf = np.full((H, W), np.inf)
    img = np.tile(SKY, (H, W, 1)).astype(float)
    ids = np.full((H, W), -1, dtype=int)
    order = sorted(range(len(T)), key=lambda i: alphas[i] < 1)   # opaque first
    for i in order:
        if not ortho and (cam[i, :, 2] < 0.05).any():
            continue
        xs, ys, zs = sx[i], sy[i], depth[i]
        x0, x1 = int(max(np.floor(xs.min()), 0)), int(min(np.ceil(xs.max()), W - 1))
        y0, y1 = int(max(np.floor(ys.min()), 0)), int(min(np.ceil(ys.max()), H - 1))
        if x0 > x1 or y0 > y1:
            continue
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        b = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        c = 1 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        if ortho:
            zz = a * zs[0] + b * zs[1] + c * zs[2]
        else:
            zz = 1.0 / (a / zs[0] + b / zs[1] + c / zs[2])
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        hit = inside & (zz < sub - 1e-4)
        if not hit.any():
            continue
        si = img[y0:y1 + 1, x0:x1 + 1]
        if alphas[i] < 1:
            si[hit] = si[hit] * (1 - alphas[i]) + color[i] * alphas[i]
        else:
            si[hit] = color[i]
            sub[hit] = zz[hit]
            ids[y0:y1 + 1, x0:x1 + 1][hit] = i
    # linework: darken pixels where the surface or its orientation changes
    key = np.where(ids >= 0, ids, 0)
    nb = np.where((ids >= 0)[..., None], nrm[key], 0)
    zb = np.where(np.isfinite(zbuf), zbuf, 1e4)
    edge = np.zeros((H, W), bool)
    for ax in (0, 1):
        dn = np.abs(np.diff(nb, axis=ax)).sum(-1) > 0.35
        dz = np.abs(np.diff(zb, axis=ax)) > 0.02 * np.minimum(zb.take(range(zb.shape[ax] - 1), ax), 400) + 0.25
        e = dn | dz
        if ax == 0:
            edge[:-1] |= e; edge[1:] |= e
        else:
            edge[:, :-1] |= e; edge[:, 1:] |= e
    img[edge] *= 0.25
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype("uint8")).resize(size, Image.LANCZOS)
    d = ImageDraw.Draw(out)
    if caption:
        d.text((24, 18), caption, fill=(30, 30, 30), font=_font(26, True))
    if stamp:
        fnt = _font(17, True)
        tw = d.textlength(STAMP, font=fnt)
        x, y = (size[0] - tw) / 2, size[1] - 40
        d.rectangle([x - 12, y - 7, x + tw + 12, y + 27], fill=(255, 255, 255), outline=(190, 0, 0), width=2)
        d.text((x, y), STAMP, fill=(190, 0, 0), font=fnt)
    out.save(path)
    return path


def standard_views(b, elements, outdir):
    """Perspectives, a roof-off view, and four orthographic elevations."""
    g = b.footprint()
    x0, y0, x1, y1 = g.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    top = b.plate_height()
    R = max(x1 - x0, y1 - y0, top * 1.6)
    house = [e for e in elements if e.category != "site"]
    views = {}
    views["3d-front"] = render(elements, f"{outdir}/render-3d-front.png",
                               (cx - R * 0.95, cy - R * 1.45, top + R * 0.55), (cx, cy, top * 0.45),
                               caption="Front perspective (street side)")
    views["3d-rear"] = render(elements, f"{outdir}/render-3d-rear.png",
                              (cx + R * 0.95, cy + R * 1.45, top + R * 0.55), (cx, cy, top * 0.45),
                              caption="Rear perspective")
    views["3d-roof-off"] = render(elements, f"{outdir}/render-3d-roof-off.png",
                                  (cx - R * 0.25, cy - R * 1.0, top + R * 1.25), (cx, cy + R * 0.03, 0),
                                  hide=("roof", "GABLE"), caption="Roof removed: the plan in 3D")
    from .mesh import roof_geometry
    fag = b.site.floor_above_grade if b.site else 1.0
    zr = roof_geometry(b)["zr"]
    zc = (zr - fag) / 2
    w, h = 1400, 500
    for name, eye, tgt, span in (
            ("front", (cx, y0 - 200, zc), (cx, cy, zc), x1 - x0),
            ("rear", (cx, y1 + 200, zc), (cx, cy, zc), x1 - x0),
            ("left", (x0 - 200, cy, zc), (cx, cy, zc), y1 - y0),
            ("right", (x1 + 200, cy, zc), (cx, cy, zc), y1 - y0)):
        height = max((span + 10) * h / w, (zr + fag) * 1.55)
        views["elev-" + name] = render(house, f"{outdir}/render-elevation-{name}.png", eye, tgt,
                                       ortho=height, size=(w, h), caption=f"{name.title()} elevation")
    return views
