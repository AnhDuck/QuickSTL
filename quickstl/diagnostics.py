import datetime
import json
import os

from .config import current_doc_key, get_doc_folder
from .constants import ADDIN_VERSION
from .paths import debug_path
from .state import STATE


def _timestamp() -> str:
    return datetime.datetime.now().isoformat()


def _base_payload() -> dict:
    return {
        "version": ADDIN_VERSION,
        "updated_at": _timestamp(),
        "events": [],
        "idle_monitor": {},
        "ui": {},
        "last_export": {},
    }


def load_debug_file() -> dict:
    try:
        if os.path.isfile(debug_path()):
            with open(debug_path(), "r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return _base_payload()


def write_debug_file(context: dict, open_after: bool = False) -> None:
    payload = context or _base_payload()
    payload["version"] = ADDIN_VERSION
    payload["updated_at"] = _timestamp()
    try:
        with open(debug_path(), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        if open_after:
            try:
                os.startfile(debug_path())
            except Exception:
                pass
    except Exception:
        pass


def update_debug_file(updater, open_after: bool = False) -> None:
    payload = load_debug_file()
    try:
        updated = updater(payload) if updater else payload
    except Exception:
        updated = payload
    write_debug_file(updated, open_after=open_after)


def append_debug_event(level: str, message: str, data: dict = None) -> None:
    def _update(payload: dict) -> dict:
        events = payload.get("events")
        if not isinstance(events, list):
            events = []
        events.append(
            {
                "timestamp": _timestamp(),
                "level": level,
                "message": message,
                "data": data or {},
            }
        )
        payload["events"] = events
        return payload

    update_debug_file(_update, open_after=False)


def update_idle_state(state: dict) -> None:
    def _update(payload: dict) -> dict:
        payload["idle_monitor"] = state or {}
        return payload

    update_debug_file(_update, open_after=False)


def update_ui_state(state: dict) -> None:
    def _update(payload: dict) -> dict:
        payload["ui"] = state or {}
        return payload

    update_debug_file(_update, open_after=False)


def record_export_snapshot(snapshot: dict) -> None:
    def _update(payload: dict) -> dict:
        payload["last_export"] = snapshot or {}
        return payload

    update_debug_file(_update, open_after=False)


def snapshot_common(
    action: str,
    engine: str,
    quality_applied: dict,
    target_name: str,
    fullpath: str,
    stl_info: dict,
) -> dict:
    return {
        "version": ADDIN_VERSION,
        "timestamp": _timestamp(),
        "action": action,
        "engine": engine,
        "quality": quality_applied.get("mode"),
        "quality_applied": quality_applied,
        "prefer_selection": bool(STATE.config.get("prefer_selection", True)),
        "doc_key": current_doc_key(),
        "export_folder": os.path.dirname(fullpath) if fullpath else get_doc_folder(),
        "file_name": os.path.basename(fullpath) if fullpath else "",
        "file_path": fullpath,
        "file_size_bytes": (stl_info or {}).get("fileSizeBytes"),
        "stl_is_binary": (stl_info or {}).get("isBinary"),
        "stl_triangles": (stl_info or {}).get("triangles"),
        "stl_vertices": (stl_info or {}).get("vertices"),
        "entity_name": target_name,
    }
