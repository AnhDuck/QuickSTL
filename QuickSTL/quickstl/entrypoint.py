import traceback

import adsk.core

from .command import ensure_removed, wire_commands
from .config import load_config
from .constants import ADDIN_NAME, ADDIN_VERSION, CMD_ID, TOAST_ID
from .diagnostics import append_debug_event, update_ui_state
from .state import STATE
from .versioning import sync_manifest_version


def run(context):
    try:
        STATE.app = adsk.core.Application.get()
        STATE.ui = STATE.app.userInterface
        load_config()
        sync_manifest_version()
        ensure_removed(STATE.ui, CMD_ID)
        wire_commands(STATE.ui)
        update_ui_state({"command_visible": False, "last_event": "addin_started"})
        append_debug_event(
            "info",
            "Add-in started",
            {"version": ADDIN_VERSION},
        )
    except Exception:
        if STATE.ui:
            STATE.ui.messageBox(
                f"{ADDIN_NAME} v{ADDIN_VERSION}\n\nInit failed:\n\n{traceback.format_exc()}"
            )


def stop(context):
    try:
        ui = adsk.core.Application.get().userInterface
        ensure_removed(ui, CMD_ID)
        pal = ui.palettes.itemById(TOAST_ID)
        if pal:
            try:
                pal.deleteMe()
            except Exception:
                pass
        if STATE.idle_monitor:
            STATE.idle_monitor.stop("addin_stopped")
            STATE.idle_monitor = None
        update_ui_state({"command_visible": False, "last_event": "addin_stopped"})
        append_debug_event("info", "Add-in stopped", {"version": ADDIN_VERSION})
    except Exception:
        pass
