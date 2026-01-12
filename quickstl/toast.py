import os
from pathlib import Path

import adsk.core

from .constants import ADDIN_NAME, ADDIN_VERSION, TOAST_H, TOAST_ID, TOAST_MS, TOAST_TITLE, TOAST_W
from .logging_utils import log
from .paths import resource_path, toast_html_path, toast_json_path
from .state import STATE


def screen_size():
    try:
        import ctypes

        user32 = ctypes.windll.user32
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return 1920, 1080


def open_path(path: str):
    if not path:
        return
    try:
        os.startfile(path)
    except Exception as exc:
        log(f"Open path failed: {exc}")


class ToastActionHandler(adsk.core.HTMLEventHandler):
    def notify(self, args: adsk.core.HTMLEventArgs):
        try:
            action = args.action or ""
            data = (args.data or "").strip().strip('"').strip("'")
            if action == "openFolder":
                open_path(data)
            elif action in ("closeToast", "autoClose"):
                pal = STATE.ui.palettes.itemById(TOAST_ID)
                if pal:
                    pal.isVisible = False
                    pal.deleteMe()
            elif action == "previewError":
                log(f"Preview error: {data}")
        except Exception as exc:
            log(f"HTML event handler error: {exc}")


def write_toast_json(fname: str, folder: str, overwrote: bool, fullpath: str):
    payload = {
        "version": ADDIN_VERSION,
        "title": TOAST_TITLE,
        "name": fname,
        "folder": folder,
        "fileUrl": Path(fullpath).resolve().as_uri(),
        "overwrote": bool(overwrote),
        "toastMs": TOAST_MS,
        "width": TOAST_W,
        "height": TOAST_H,
    }
    os.makedirs(resource_path(), exist_ok=True)
    with open(toast_json_path(), "w", encoding="utf-8") as handle:
        import json

        json.dump(payload, handle, ensure_ascii=False)


def show_toast(folder: str, fname: str, overwrote: bool, fullpath: str):
    html_path = toast_html_path()
    if not os.path.isfile(html_path):
        STATE.ui.messageBox(
            "Quick STL toast HTML missing.\n\nExpected:\n"
            + html_path
            + "\n\nPlace quickstl_toast.html there (and three.min.js in resources/preview).",
            f"{ADDIN_NAME} v{ADDIN_VERSION}",
        )
        log(f"Missing toast HTML at: {html_path}")
        return

    write_toast_json(fname, folder, overwrote, fullpath)
    if not os.path.isfile(toast_json_path()):
        STATE.ui.messageBox(
            "Toast payload JSON not found — export succeeded but UI payload was not written.",
            f"{ADDIN_NAME} v{ADDIN_VERSION}",
        )
        log(f"Missing toast JSON at: {toast_json_path()}")
        return

    pal = STATE.ui.palettes.itemById(TOAST_ID)
    if pal:
        try:
            pal.deleteMe()
        except Exception:
            pass

    html_url = Path(html_path).resolve().as_uri()
    pal = STATE.ui.palettes.add(
        TOAST_ID,
        f"{TOAST_TITLE} — Quick STL v{ADDIN_VERSION}",
        html_url,
        True,
        False,
        False,
        TOAST_W,
        TOAST_H,
        True,
    )
    try:
        pal.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateFloating
        pal.isAlwaysOnTop = True
        sw, sh = screen_size()
        x = max(0, int(sw * (1.0 / 3.0) - TOAST_W / 2.0))
        y = max(0, int(sh * 0.5 - TOAST_H / 2.0))
        pal.setPosition(x, y)
    except Exception:
        pass

    on_html = ToastActionHandler()
    pal.incomingFromHTML.add(on_html)
    STATE.handlers.append(on_html)
