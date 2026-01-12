import adsk.core

from .state import STATE


def pick_folder_dialog(title: str) -> str:
    dlg = STATE.ui.createFolderDialog()
    dlg.title = title
    return dlg.folder if dlg.showDialog() == adsk.core.DialogResults.DialogOK else ""


def pick_file_dialog(title: str, filter_: str = "Executables (*.exe)") -> str:
    dlg = STATE.ui.createFileDialog()
    dlg.title = title
    dlg.filter = filter_
    if dlg.showOpen() == adsk.core.DialogResults.DialogOK:
        return dlg.filename
    return ""
