"""glTF 2.0 binary (.glb) and Wavefront OBJ export of the element meshes.

Output is metres, Y up (the glTF convention): model (x, y, z) -> (x, z, -y).
"""
import json
import struct

import numpy as np

from . import STAMP
from .mesh import MATERIALS
from .units import FT_TO_M


def _xf(p):
    return (p[0] * FT_TO_M, p[2] * FT_TO_M, -p[1] * FT_TO_M)


def _arrays(el):
    pos, nrm = [], []
    for a, b_, c in el.triangles():
        A, B, C = (np.array(_xf(p)) for p in (a, b_, c))
        n = np.cross(B - A, C - A)
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            continue
        n = n / ln
        pos += [A, B, C]
        nrm += [n, n, n]
    return np.array(pos, dtype="<f4"), np.array(nrm, dtype="<f4")


def write_glb(elements, path, title):
    mats = list(MATERIALS)
    gltf = {
        "asset": {"version": "2.0", "generator": "housegen", "copyright": STAMP},
        "scene": 0,
        "scenes": [{"name": title, "nodes": [], "extras": {"notice": STAMP, "units": "metres"}}],
        "nodes": [], "meshes": [], "accessors": [], "bufferViews": [], "buffers": [],
        "materials": [],
    }
    for m in mats:
        r, g, b, a = MATERIALS[m]
        md = {"name": m, "doubleSided": True,
              "pbrMetallicRoughness": {"baseColorFactor": [r, g, b, a], "metallicFactor": 0.0,
                                       "roughnessFactor": 0.2 if m == "glass" else 0.9}}
        if a < 1:
            md["alphaMode"] = "BLEND"
        gltf["materials"].append(md)
    blob = bytearray()

    def view(arr, target):
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob.extend(arr.tobytes())
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": arr.nbytes, "target": target})
        return len(gltf["bufferViews"]) - 1

    for el in elements:
        pos, nrm = _arrays(el)
        if not len(pos):
            continue
        pa = len(gltf["accessors"])
        gltf["accessors"].append({"bufferView": view(pos, 34962), "componentType": 5126, "count": len(pos),
                                  "type": "VEC3", "min": pos.min(0).tolist(), "max": pos.max(0).tolist()})
        gltf["accessors"].append({"bufferView": view(nrm, 34962), "componentType": 5126, "count": len(nrm),
                                  "type": "VEC3"})
        gltf["meshes"].append({"name": el.name, "primitives": [{
            "attributes": {"POSITION": pa, "NORMAL": pa + 1}, "material": mats.index(el.material), "mode": 4}]})
        gltf["nodes"].append({"name": el.name, "mesh": len(gltf["meshes"]) - 1,
                              "extras": {"id": el.id, "category": el.category}})
        gltf["scenes"][0]["nodes"].append(len(gltf["nodes"]) - 1)
    while len(blob) % 4:
        blob.append(0)
    gltf["buffers"].append({"byteLength": len(blob)})
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack("<I4s", len(js), b"JSON")); f.write(js)
        f.write(struct.pack("<I4s", len(blob), b"BIN\0")); f.write(blob)
    return {"nodes": len(gltf["nodes"]), "triangles": sum(a["count"] for a in gltf["accessors"][::2]) // 3}


def write_obj(elements, path, title):
    mtl_path = str(path)[:-4] + ".mtl"
    with open(mtl_path, "w") as m:
        m.write(f"# {STAMP}\n")
        for name, (r, g, b, a) in MATERIALS.items():
            m.write(f"newmtl {name}\nKd {r:.3f} {g:.3f} {b:.3f}\nd {a:.2f}\n\n")
    with open(path, "w") as f:
        f.write(f"# {title}\n# {STAMP}\n# units: metres, Y up\n")
        f.write(f"mtllib {mtl_path.split('/')[-1]}\n")
        n = 1
        for el in elements:
            f.write(f"o {el.id}\nusemtl {el.material}\n")
            for poly in el.polys:
                for p in poly:
                    x, y, z = _xf(p)
                    f.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
                f.write("f " + " ".join(str(n + i) for i in range(len(poly))) + "\n")
                n += len(poly)
