import datetime
import json
import os
from typing import Optional

from .config import current_doc_key, get_doc_folder
from .constants import ADDIN_VERSION
from .logging_utils import log
from .paths import diag_path
from .state import STATE


def write_diag_file(context: dict, open_after: bool = False) -> None:
    try:
        with open(diag_path(), "w", encoding="utf-8") as handle:
            json.dump(context, handle, indent=2)
        if open_after:
            try:
                os.startfile(diag_path())
            except Exception as exc:
                log(f"Open diag file failed: {exc}")
    except Exception as exc:
        log(f"Write diag failed: {exc}")


def snapshot_idle_state() -> dict:
    return {
        "idle_active": STATE.idle_active,
        "idle_timeout_s": STATE.idle_timeout_s,
        "idle_log_interval_s": STATE.idle_log_interval_s,
        "last_activity_ts": STATE.last_activity_ts,
        "last_activity_reason": STATE.last_activity_reason,
        "last_idle_log_ts": STATE.last_idle_log_ts,
        "idle_last_elapsed_s": STATE.idle_last_elapsed_s,
        "active_command_set": STATE.active_command is not None,
        "idle_debug_events": list(STATE.idle_debug_events),
    }


def write_idle_diag(event: str, details: Optional[dict] = None) -> None:
    payload = {
        "version": ADDIN_VERSION,
        "timestamp": datetime.datetime.now().isoformat(),
        "event": event,
        "details": details or {},
        "idle_state": snapshot_idle_state(),
    }
    write_diag_file(payload, open_after=False)


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
        "timestamp": datetime.datetime.now().isoformat(),
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
