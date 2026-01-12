import os
import subprocess
import time
from pathlib import Path

from .logging_utils import log
from .state import STATE


def candidate_paths_for(name: str):
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    lad = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    candidates = {
        "OrcaSlicer": [
            rf"{pf}\OrcaSlicer\OrcaSlicer.exe",
            rf"{lad}\Programs\OrcaSlicer\OrcaSlicer.exe",
        ],
        "SuperSlicer": [
            rf"{pf}\SuperSlicer\SuperSlicer.exe",
            rf"{pf86}\SuperSlicer\SuperSlicer.exe",
        ],
        "Bambu Studio": [
            rf"{pf}\Bambu Studio\Bambu Studio.exe",
            rf"{pf}\BambuStudio\BambuStudio.exe",
            rf"{lad}\Programs\BambuStudio\BambuStudio.exe",
        ],
    }
    return candidates.get(name, [])


def autodetect_slicer_path(name: str) -> str:
    saved = (STATE.config.get("slicer", {}).get("paths", {}) or {}).get(name, "")
    if saved and os.path.isfile(saved):
        return saved
    for path in candidate_paths_for(name):
        if path and os.path.isfile(path):
            return path
    return saved or ""


def launch_slicer(exe: str, stl_path: str) -> None:
    if not os.path.isfile(exe):
        raise RuntimeError(f"Slicer executable not found:\n{exe}")
    if not os.path.isfile(stl_path):
        raise RuntimeError(f"STL not found:\n{stl_path}")
    proc = subprocess.Popen([exe, stl_path], creationflags=0x00000008)
    try:
        import ctypes
        import ctypes.wintypes as wt

        user32 = ctypes.windll.user32
        hwnd_type = wt.HWND
        lresult = wt.LPARAM
        enum_proc = ctypes.WINFUNCTYPE(wt.BOOL, hwnd_type, lresult)
        handles = []

        def enum_cb(hwnd, l_param):
            if user32.IsWindowVisible(hwnd) and user32.IsIconic(hwnd) == 0:
                _pid = wt.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(_pid))
                if _pid.value == proc.pid:
                    handles.append(hwnd)
            return True

        deadline = time.time() + 6.0
        while time.time() < deadline and not handles:
            user32.EnumWindows(enum_proc(enum_cb), 0)
            if handles:
                break
            time.sleep(0.2)
        if handles:
            sw_restore = 9
            user32.ShowWindow(handles[0], sw_restore)
            user32.SetForegroundWindow(handles[0])
    except Exception as exc:
        log(f"Focus slicer error: {exc}")
