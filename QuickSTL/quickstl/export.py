import os
import traceback

import adsk.core
import adsk.fusion

from .analysis import analyze_stl
from .config import add_clicks_saved, resolve_export_dir, safe_filename
from .constants import ADDIN_NAME, ADDIN_VERSION
from .diagnostics import snapshot_common, write_diag_file
from .logging_utils import log
from .obj_stl import export_via_obj_then_stl
from .slicer import autodetect_slicer_path, launch_slicer
from .state import STATE
from .toast import show_toast


def name_for_entity(entity) -> str:
    try:
        if isinstance(entity, adsk.fusion.BRepBody):
            base = entity.name or "export"
        elif isinstance(entity, adsk.fusion.Occurrence):
            base = entity.component.name or "export"
        elif isinstance(entity, adsk.fusion.Component):
            base = entity.name or "export"
        else:
            base = getattr(entity, "name", None) or "export"
    except Exception:
        base = "export"
    return base


def target_entity_and_name(design: adsk.fusion.Design):
    if STATE.config.get("prefer_selection", True):
        sels = STATE.ui.activeSelections
        if sels and sels.count > 0:
            ent = sels.item(0).entity
            if isinstance(
                ent,
                (adsk.fusion.BRepBody, adsk.fusion.Component, adsk.fusion.Occurrence),
            ):
                return ent, name_for_entity(ent)
    comp = design.activeComponent
    return comp, name_for_entity(comp)


def export_via_stl_legacy(design, entity, stl_fullpath: str) -> dict:
    """Legacy STL path: uses Fusion STL exporter (quality fixed in many builds)."""
    mgr = design.exportManager
    opts = mgr.createSTLExportOptions(entity, stl_fullpath)
    opts.isBinaryFormat = True
    try:
        opts.sendToPrintUtility = False
    except Exception:
        pass
    mgr.execute(opts)
    return {"mode": "Legacy", "target": "STL Only", "custom": {}}


def do_export_to_path(
    folder_override: str = "",
    skip_toast: bool = False,
    inputs: adsk.core.CommandInputs = None,
) -> str:
    if STATE.busy:
        return ""
    STATE.busy = True
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            raise RuntimeError("No active design.")

        export_dir = resolve_export_dir(folder_override)
        if not os.path.isdir(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        target, raw_name = target_entity_and_name(design)
        fname = safe_filename(raw_name) + ".stl"
        full = os.path.join(export_dir, fname)
        overwriting = os.path.exists(full)

        quality = STATE.config.get("quality", "Legacy")
        if quality == "Legacy":
            applied = export_via_stl_legacy(design, target, full)
            engine = "STL Only"
        else:
            applied = export_via_obj_then_stl(design, target, full, quality)
            engine = "OBJ→STL"

        if not os.path.exists(full):
            raise RuntimeError(f"Export failed (no file created):\n{full}")

        if not skip_toast:
            try:
                show_toast(export_dir, fname, overwriting, full)
            except Exception as exc:
                ui.messageBox(
                    f"✅ STL export successful. (Quick STL v{ADDIN_VERSION})\n\n"
                    f"Name: {fname}\n"
                    f"Folder:\n{export_dir}\n"
                    f"Overwrote existing file: {'Yes' if overwriting else 'No'}\n\n"
                    f"(Palette fallback due to: {exc})",
                    f"{ADDIN_NAME} v{ADDIN_VERSION}",
                )

        stl_info = analyze_stl(full)
        snap = snapshot_common("export", engine, applied, raw_name, full, stl_info)
        write_diag_file(snap, open_after=False)

        if inputs:
            add_clicks_saved(5, inputs)
        return full
    finally:
        STATE.busy = False


def export_and_send(
    folder_override: str = "", inputs: adsk.core.CommandInputs = None
) -> bool:
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active design.", f"{ADDIN_NAME} v{ADDIN_VERSION}")
        return False

    path = do_export_to_path(folder_override=folder_override, skip_toast=True, inputs=None)
    if not path:
        return False

    sconf = STATE.config.get("slicer", {})
    name = sconf.get("name") or "OrcaSlicer"
    exe = (sconf.get("paths") or {}).get(name, "")
    if not exe:
        exe = autodetect_slicer_path(name)
        if exe:
            STATE.config["slicer"]["paths"][name] = exe
            from .config import save_config

            save_config()

    launch_slicer(exe, path)

    stl_info = analyze_stl(path)
    applied = {
        "mode": STATE.config.get("quality", "Legacy"),
        "target": (
            "STL Only"
            if STATE.config.get("quality", "Legacy") == "Legacy"
            else "OBJ→STL"
        ),
        "custom": {},
    }
    snap = snapshot_common(
        "send",
        "STL Only"
        if STATE.config.get("quality", "Legacy") == "Legacy"
        else "OBJ→STL",
        applied,
        os.path.splitext(os.path.basename(path))[0],
        path,
        stl_info,
    )
    write_diag_file(snap, open_after=False)

    if inputs:
        add_clicks_saved(5, inputs)
    return True


def handle_export_error(action: str, error: Exception) -> None:
    log(f"{action} failed: {error}")
    STATE.ui.messageBox(
        f"❌ {action} failed.\n\n{error}\n\n{traceback.format_exc()}",
        f"{ADDIN_NAME} v{ADDIN_VERSION}",
    )
