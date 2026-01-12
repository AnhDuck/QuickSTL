import os
import struct

from .logging_utils import log


def analyze_stl(stl_path: str) -> dict:
    info = {
        "isBinary": None,
        "triangles": None,
        "vertices": None,
        "fileSizeBytes": None,
    }
    try:
        size = os.path.getsize(stl_path)
        info["fileSizeBytes"] = size
        with open(stl_path, "rb") as handle:
            data = handle.read()
        if len(data) >= 84:
            tri = struct.unpack("<I", data[80:84])[0]
            expected = 84 + 50 * tri
            if expected == len(data) and tri > 0:
                info["isBinary"] = True
                info["triangles"] = tri
                info["vertices"] = tri * 3
                return info
        try:
            txt = data.decode("utf-8", errors="ignore")
            tri = txt.count("\nfacet ") + txt.count("\rfacet ")
            if tri == 0:
                tri = txt.count("facet ")
            info["isBinary"] = False
            info["triangles"] = tri if tri > 0 else None
            info["vertices"] = tri * 3 if tri > 0 else None
        except Exception:
            pass
    except Exception as exc:
        log(f"STL analyze failed: {exc}")
    return info
