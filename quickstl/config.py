import json
import os
import re

import adsk.core

from .constants import QUALITY_CHOICES, SLICER_CHOICES
from .dialogs import pick_folder_dialog
from .logging_utils import log
from .paths import config_path
from .state import STATE


def load_config() -> None:
    try:
        with open(config_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            for key in STATE.config:
                if key in data:
                    if isinstance(STATE.config[key], dict) and isinstance(data[key], dict):
                        STATE.config[key].update(data[key])
                    else:
                        STATE.config[key] = data[key]
            if "per_doc_folders" not in STATE.config or not isinstance(
                STATE.config["per_doc_folders"], dict
            ):
                STATE.config["per_doc_folders"] = {}
            if "clicks_saved" not in STATE.config or not isinstance(
                STATE.config["clicks_saved"], int
            ):
                STATE.config["clicks_saved"] = 0
            if "auto_close_after_export" not in STATE.config or not isinstance(
                STATE.config["auto_close_after_export"], bool
            ):
                STATE.config["auto_close_after_export"] = True
            if (
                "quality" not in STATE.config
                or STATE.config["quality"] not in QUALITY_CHOICES
            ):
                STATE.config["quality"] = "Legacy"
            for name in SLICER_CHOICES:
                STATE.config["slicer"]["paths"].setdefault(name, "")
    except Exception:
        pass


def save_config() -> None:
    try:
        with open(config_path(), "w", encoding="utf-8") as handle:
            json.dump(STATE.config, handle, indent=2)
    except Exception:
        pass


def current_doc_key() -> str:
    try:
        app = adsk.core.Application.get()
        doc = app.activeDocument if app else None
        if doc:
            try:
                df = doc.dataFile
                if df and getattr(df, "id", None):
                    return f"datafile:{df.id}"
            except Exception:
                pass
            nm = getattr(doc, "name", None)
            if nm:
                return f"docname:{nm}"
    except Exception:
        pass
    return "global"


def get_doc_folder() -> str:
    key = current_doc_key()
    folder = STATE.config.get("per_doc_folders", {}).get(key, "").strip()
    if folder:
        return folder
    return (STATE.config.get("export_dir") or "").strip()


def set_doc_folder(folder: str) -> None:
    key = current_doc_key()
    STATE.config.setdefault("per_doc_folders", {})[key] = folder
    STATE.config["export_dir"] = folder
    save_config()


def safe_filename(name: str) -> str:
    if not name:
        name = "export"
    illegal = '<>:"/\\|?*'
    cleaned = "".join(c for c in name if c not in illegal).rstrip(" .") or "export"
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update({f"COM{i}" for i in range(1, 10)})
    reserved.update({f"LPT{i}" for i in range(1, 10)})
    if cleaned.upper() in reserved:
        cleaned = f"_{cleaned}"
    cleaned = re.sub(r":\d+$", "", cleaned)
    return cleaned


def resolve_export_dir(maybe_override: str = "") -> str:
    path = (maybe_override or get_doc_folder() or "").strip()
    if path:
        return path
    chosen = pick_folder_dialog("Choose export folder for this document (remembered)")
    if not chosen:
        raise RuntimeError("Export cancelled (no folder chosen).")
    set_doc_folder(chosen)
    return chosen


def add_clicks_saved(count: int, inputs: adsk.core.CommandInputs = None) -> None:
    try:
        STATE.config["clicks_saved"] = int(STATE.config.get("clicks_saved", 0)) + int(
            count
        )
    except Exception:
        STATE.config["clicks_saved"] = int(count)
    save_config()
    if inputs:
        from .ui_helpers import find_input

        tb = adsk.core.TextBoxCommandInput.cast(find_input(inputs, "clicksSavedText"))
        if tb:
            tb.text = f"Clicks saved: {STATE.config.get('clicks_saved', 0)}"
