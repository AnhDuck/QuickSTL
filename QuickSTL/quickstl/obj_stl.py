import math
import struct
import os
import tempfile
import time

from .constants import ADDIN_VERSION
from .quality import apply_obj_quality


def write_binary_stl(stl_path: str, triangles) -> None:
    """
    triangles: iterable of (nx,ny,nz, (x1,y1,z1), (x2,y2,z2), (x3,y3,z3)) in millimeters.
    """
    tri_list = list(triangles)
    tri_count = len(tri_list)

    with open(stl_path, "wb") as handle:
        header = f"QuickSTL v{ADDIN_VERSION} OBJ->STL".encode("ascii", errors="ignore")
        if len(header) > 80:
            header = header[:80]
        else:
            header = header + b" " * (80 - len(header))
        handle.write(header)
        handle.write(tri_count.to_bytes(4, "little"))
        for nx, ny, nz, v1, v2, v3 in tri_list:
            handle.write(struct.pack("<3f", float(nx), float(ny), float(nz)))
            handle.write(struct.pack("<3f", float(v1[0]), float(v1[1]), float(v1[2])))
            handle.write(struct.pack("<3f", float(v2[0]), float(v2[1]), float(v2[2])))
            handle.write(struct.pack("<3f", float(v3[0]), float(v3[1]), float(v3[2])))
            handle.write(struct.pack("<H", 0))


def triangulate_face(indices):
    """Fan triangulation for polygon faces: returns triples of vertex indices (0-based)."""
    tris = []
    if len(indices) < 3:
        return tris
    for i in range(1, len(indices) - 1):
        tris.append((indices[0], indices[i], indices[i + 1]))
    return tris


def compute_normal(a, b, c):
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c
    ux, uy, uz = (bx - ax, by - ay, bz - az)
    vx, vy, vz = (cx - ax, cy - ay, cz - az)
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length <= 1e-20:
        return (0.0, 0.0, 0.0)
    return (nx / length, ny / length, nz / length)


def export_via_obj_then_stl(design, entity, stl_fullpath: str, quality: str) -> dict:
    """Use Fusion's OBJ exporter with quality controls, then convert OBJ→Binary STL."""
    mgr = design.exportManager
    tmp_dir = tempfile.gettempdir()
    tmp_obj = os.path.join(tmp_dir, f"quickstl_{int(time.time() * 1000)}.obj")

    opts = mgr.createOBJExportOptions(entity, tmp_obj)
    try:
        opts.sendToPrintUtility = False
    except Exception:
        pass
    applied = apply_obj_quality(opts, quality)
    mgr.execute(opts)

    vertices = []
    faces = []

    with open(tmp_obj, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("v "):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        x = float(parts[1])
                        y = float(parts[2])
                        z = float(parts[3])
                        vertices.append((x, y, z))
                    except Exception:
                        pass
            elif line.startswith("f "):
                parts = line.split()[1:]
                idxs = []
                for part in parts:
                    try:
                        v_idx = part.split("/")[0]
                        i = int(v_idx)
                        if i > 0:
                            i0 = i - 1
                        else:
                            i0 = len(vertices) + i
                        idxs.append(i0)
                    except Exception:
                        pass
                if len(idxs) >= 3:
                    faces.append(idxs)

    scale = 10.0
    v_mm = [(vx * scale, vy * scale, vz * scale) for (vx, vy, vz) in vertices]

    triangles = []
    for face in faces:
        for i1, i2, i3 in triangulate_face(face):
            try:
                a = v_mm[i1]
                b = v_mm[i2]
                c = v_mm[i3]
            except Exception:
                continue
            nx, ny, nz = compute_normal(a, b, c)
            triangles.append((nx, ny, nz, a, b, c))

    write_binary_stl(stl_fullpath, triangles)

    try:
        os.remove(tmp_obj)
    except Exception:
        pass

    applied["custom"]["triangles_written"] = len(triangles)
    return applied
