import traceback

import adsk.core

from .command import ensure_removed, wire_commands
from .config import load_config
from .constants import ADDIN_NAME, ADDIN_VERSION, CMD_ID, TOAST_ID
from .state import STATE


def run(context):
    try:
        STATE.app = adsk.core.Application.get()
        STATE.ui = STATE.app.userInterface
        load_config()
        ensure_removed(STATE.ui, CMD_ID)
        wire_commands(STATE.ui)
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
    except Exception:
        pass
