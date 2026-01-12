import traceback

import adsk.core

from .command import ensure_removed, wire_commands
from .config import load_config
from .constants import ADDIN_NAME, ADDIN_VERSION, CMD_ID, TOAST_ID
from .diagnostics import cleanup_legacy_debug_files, ensure_debug_file_exists
from .idle import start_idle_monitoring, stop_idle_monitoring
from .logging_utils import log
from .paths import addin_dir
from .state import STATE


def run(context):
    try:
        STATE.app = adsk.core.Application.get()
        STATE.ui = STATE.app.userInterface
        ensure_debug_file_exists({"event": "startup_begin", "addin_dir": addin_dir()})
        load_config()
        try:
            cleanup_legacy_debug_files()
        except Exception as exc:
            log(f"Legacy debug cleanup failed: {exc}")
        try:
            ensure_removed(STATE.ui, CMD_ID)
            wire_commands(STATE.ui)
        except Exception as exc:
            log(f"Command wiring failed: {exc}")
        try:
            start_idle_monitoring(STATE.app)
        except Exception as exc:
            log(f"Idle monitoring failed: {exc}")
    except Exception:
        ensure_debug_file_exists(
            {
                "event": "startup_error",
                "addin_dir": addin_dir(),
                "traceback": traceback.format_exc(),
            }
        )
        if STATE.ui:
            STATE.ui.messageBox(
                f"{ADDIN_NAME} v{ADDIN_VERSION}\n\nInit failed:\n\n{traceback.format_exc()}"
            )


def stop(context):
    try:
        ui = adsk.core.Application.get().userInterface
        stop_idle_monitoring(adsk.core.Application.get())
        ensure_removed(ui, CMD_ID)
        pal = ui.palettes.itemById(TOAST_ID)
        if pal:
            try:
                pal.deleteMe()
            except Exception:
                pass
    except Exception:
        pass
