import json
import os

from .constants import ADDIN_VERSION
from .diagnostics import append_debug_event
from .paths import addin_dir


def manifest_path() -> str:
    return os.path.join(addin_dir(), "QuickSTL.manifest")


def sync_manifest_version() -> None:
    path = manifest_path()
    try:
        if not os.path.isfile(path):
            return
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return
        if data.get("version") == ADDIN_VERSION:
            return
        data["version"] = ADDIN_VERSION
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        append_debug_event("info", "Manifest version synced", {"version": ADDIN_VERSION})
    except Exception:
        pass
