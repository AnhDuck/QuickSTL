import os
import adsk.core

from .config import get_doc_folder, resolve_export_dir, save_config, set_doc_folder
from .constants import ADDIN_NAME, ADDIN_VERSION, CMD_ID, CMD_NAME, QUALITY_CHOICES, SLICER_CHOICES
from .diagnostics import append_debug_event
from .dialogs import pick_file_dialog, pick_folder_dialog
from .export import do_export_to_path, export_and_send, handle_export_error
from .logging_utils import log
from .paths import icon_folder
from .slicer import autodetect_slicer_path
from .state import STATE
from .toast import open_path
from .ui_helpers import find_input


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        cmd = args.command
        inputs = cmd.commandInputs
        try:
            cmd.okButtonText = "OK"
        except Exception:
            pass

        g1 = inputs.addGroupCommandInput("grpExport", "Export Destination")
        g1.isExpanded = True
        g1.isBordered = True
        g1c = g1.children

        current_folder = get_doc_folder()
        folder_disp = g1c.addStringValueInput("folderDisp", "Export Folder", current_folder)
        folder_disp.isReadOnly = True
        browse = g1c.addBoolValueInput("browseBtn", "Browse…", False, "", False)
        openfld = g1c.addBoolValueInput("openFolderBtn", "Open Folder", False, "", False)
        prefer = g1c.addBoolValueInput(
            "preferSel",
            "Prefer selection when available",
            True,
            "",
            STATE.config.get("prefer_selection", True),
        )
        note = g1c.addTextBoxCommandInput(
            "perDocNote",
            "",
            "This folder is remembered for this document.",
            1,
            True,
        )
        try:
            note.isFullWidth = True
        except Exception:
            pass

        q = STATE.config.get("quality", "Legacy")
        qdd = g1c.addDropDownCommandInput(
            "qualityDD", "Mesh Quality", adsk.core.DropDownStyles.TextListDropDownStyle
        )
        for name in QUALITY_CHOICES:
            qdd.listItems.add(name, name == q, "")

        g2 = inputs.addGroupCommandInput("grpSlicer", "Slicer")
        g2.isExpanded = True
        g2.isBordered = True
        g2c = g2.children
        drop = g2c.addDropDownCommandInput(
            "slicerChoice", "Slicer", adsk.core.DropDownStyles.TextListDropDownStyle
        )
        for slicer in SLICER_CHOICES:
            drop.listItems.add(
                slicer, slicer == STATE.config.get("slicer", {}).get("name", "OrcaSlicer"), ""
            )
        slicer_path = autodetect_slicer_path(
            STATE.config.get("slicer", {}).get("name", "OrcaSlicer")
        )
        if slicer_path:
            STATE.config["slicer"]["paths"][STATE.config["slicer"]["name"]] = slicer_path
            save_config()
        path_disp = g2c.addStringValueInput("slicerPath", "Slicer EXE", slicer_path)
        path_disp.isReadOnly = True
        browse_slicer = g2c.addBoolValueInput("browseSlicer", "Browse Slicer…", False, "", False)

        g3 = inputs.addGroupCommandInput("grpActions", "Actions")
        g3.isExpanded = True
        g3.isBordered = True
        g3c = g3.children
        send_btn = g3c.addBoolValueInput("sendBtn", "Send to slicer", False, "", False)
        export_btn = g3c.addBoolValueInput("exportBtn", "Export STL", False, "", False)
        auto_close = g3c.addBoolValueInput(
            "autoCloseAfterExport",
            "Auto-close after export/send",
            True,
            "",
            STATE.config.get("auto_close_after_export", True),
        )
        try:
            auto_close.isFullWidth = True
        except Exception:
            pass
        clicks_tb = g3c.addTextBoxCommandInput(
            "clicksSavedText",
            "",
            f"Clicks saved: {STATE.config.get('clicks_saved', 0)}",
            1,
            True,
        )
        try:
            clicks_tb.isFullWidth = True
        except Exception:
            pass
        diag_btn = g3c.addBoolValueInput("diagBtn", "Debug", False, "", False)

        try:
            folder_disp.tooltip = "This folder is saved for THIS document. Use “Browse…” to change."
            browse.tooltip = "Pick a new export folder. It is remembered for this document."
            openfld.tooltip = "Open the current export folder in File Explorer."
            prefer.tooltip = (
                "ON: if a body is selected, export that body; otherwise export the active component."
            )
            qdd.tooltip = (
                "Mesh tessellation quality:\n"
                "• Legacy: STL Only (same as Fusion 3D Print)\n"
                "• Low/…/Ultra: OBJ→STL with tighter tolerances"
            )
            drop.tooltip = 'Slicer to launch when you click "Send to slicer".'
            path_disp.tooltip = "Executable used to launch the slicer."
            browse_slicer.tooltip = "Pick the slicer executable (.exe)."
            export_btn.tooltip = "Export STL and show a success toast with live preview."
            send_btn.tooltip = "Export STL, then launch and focus the slicer. No toast unless it fails."
            auto_close.tooltip = "When enabled, close Quick STL after export/send."
            clicks_tb.tooltip = "Estimated clicks saved (assumes 5 per export or send)."
            diag_btn.tooltip = "Open debug.json (export history, errors)."
            cmd.tooltip = f"Quick STL v{ADDIN_VERSION} — OBJ→STL quality + debug info."
        except Exception:
            pass

        on_changed = CommandInputChangedHandler()
        cmd.inputChanged.add(on_changed)
        STATE.handlers.append(on_changed)
        on_exec = CommandExecuteHandler()
        cmd.execute.add(on_exec)
        STATE.handlers.append(on_exec)
        STATE.command = cmd
        on_destroy = CommandDestroyHandler()
        cmd.destroy.add(on_destroy)
        STATE.handlers.append(on_destroy)


class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args: adsk.core.InputChangedEventArgs):
        try:
            ip = args.input
            inputs = args.inputs
            if ip.id == "browseBtn":
                chosen = pick_folder_dialog("Choose export folder (saved for this document)")
                if chosen:
                    fld = adsk.core.StringValueCommandInput.cast(
                        find_input(inputs, "folderDisp")
                    )
                    if fld:
                        fld.value = chosen
                    set_doc_folder(chosen)
                b = adsk.core.BoolValueCommandInput.cast(ip)
                if b:
                    b.value = False

            elif ip.id == "openFolderBtn":
                fld = adsk.core.StringValueCommandInput.cast(find_input(inputs, "folderDisp"))
                folder = fld.value.strip() if (fld and fld.value) else get_doc_folder()
                if not folder:
                    STATE.ui.messageBox(
                        "No export folder set yet.\n\nUse “Browse…” to choose one.",
                        f"{ADDIN_NAME} v{ADDIN_VERSION}",
                    )
                elif not os.path.isdir(folder):
                    STATE.ui.messageBox(
                        f"Export folder does not exist:\n{folder}\n\nUse “Browse…” to choose a current folder.",
                        f"{ADDIN_NAME} v{ADDIN_VERSION}",
                    )
                else:
                    open_path(folder)
                b = adsk.core.BoolValueCommandInput.cast(ip)
                if b:
                    b.value = False

            elif ip.id == "qualityDD":
                dd = adsk.core.DropDownCommandInput.cast(ip)
                if dd and dd.selectedItem:
                    STATE.config["quality"] = dd.selectedItem.name
                    save_config()

            elif ip.id == "slicerChoice":
                dd = adsk.core.DropDownCommandInput.cast(ip)
                if dd and dd.selectedItem:
                    name = dd.selectedItem.name
                    STATE.config["slicer"]["name"] = name
                    path = autodetect_slicer_path(name)
                    sp = adsk.core.StringValueCommandInput.cast(find_input(inputs, "slicerPath"))
                    if sp:
                        sp.value = path
                    STATE.config["slicer"]["paths"][name] = path
                    save_config()

            elif ip.id == "browseSlicer":
                dd = adsk.core.DropDownCommandInput.cast(find_input(inputs, "slicerChoice"))
                cur = (
                    dd.selectedItem.name
                    if dd and dd.selectedItem
                    else STATE.config["slicer"]["name"]
                )
                chosen = pick_file_dialog(f"Locate {cur} executable")
                if chosen:
                    sp = adsk.core.StringValueCommandInput.cast(
                        find_input(inputs, "slicerPath")
                    )
                    if sp:
                        sp.value = chosen
                    STATE.config["slicer"]["paths"][cur] = chosen
                    save_config()
                b = adsk.core.BoolValueCommandInput.cast(ip)
                if b:
                    b.value = False

            elif ip.id == "exportBtn":
                b = adsk.core.BoolValueCommandInput.cast(ip)
                if not b or not b.value:
                    return
                b.value = False
                try:
                    append_debug_event("info", "export_clicked", {})
                    fld = adsk.core.StringValueCommandInput.cast(
                        find_input(inputs, "folderDisp")
                    )
                    folder = fld.value.strip() if fld else ""
                    if not folder:
                        folder = resolve_export_dir("")
                        if fld:
                            fld.value = folder
                    set_doc_folder(folder)
                    do_export_to_path(
                        folder_override=folder, skip_toast=False, inputs=inputs
                    )
                    maybe_auto_close("export")
                except Exception as exc:
                    handle_export_error("Export STL", exc)

            elif ip.id == "sendBtn":
                b = adsk.core.BoolValueCommandInput.cast(ip)
                if not b or not b.value:
                    return
                b.value = False
                try:
                    append_debug_event("info", "send_clicked", {})
                    fld = adsk.core.StringValueCommandInput.cast(
                        find_input(inputs, "folderDisp")
                    )
                    folder = fld.value.strip() if fld else ""
                    if not folder:
                        folder = resolve_export_dir("")
                        if fld:
                            fld.value = folder
                    set_doc_folder(folder)
                    if export_and_send(folder_override=folder, inputs=inputs):
                        maybe_auto_close("send")
                except Exception as exc:
                    handle_export_error("Send to slicer", exc)

            elif ip.id == "autoCloseAfterExport":
                b = adsk.core.BoolValueCommandInput.cast(ip)
                if b:
                    STATE.config["auto_close_after_export"] = bool(b.value)
                    save_config()
                    append_debug_event(
                        "info",
                        "auto_close_setting_changed",
                        {"enabled": bool(b.value)},
                    )

            elif ip.id == "diagBtn":
                try:
                    from .paths import debug_path

                    path = debug_path()
                    if os.path.isfile(path):
                        os.startfile(path)
                    else:
                        STATE.ui.messageBox(
                            "No debug file found yet.\n\nExport once to generate debug.json.",
                            f"{ADDIN_NAME} v{ADDIN_VERSION}",
                        )
                except Exception as exc:
                    log(f"Debug open failed: {exc}")
                b = adsk.core.BoolValueCommandInput.cast(ip)
                if b:
                    b.value = False

        except Exception as exc:
            log(f"InputChanged error: {exc}")


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            inputs = args.command.commandInputs
            pref = adsk.core.BoolValueCommandInput.cast(find_input(inputs, "preferSel"))
            STATE.config["prefer_selection"] = bool(pref.value) if pref else True
            save_config()
            append_debug_event("ui", "command_executed", {})
        except Exception as exc:
            log(f"Execute (OK) error: {exc}")


class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            STATE.command = None
            append_debug_event("ui", "Command destroyed", {"command": CMD_ID})
        except Exception as exc:
            log(f"Command destroy error: {exc}")


def maybe_auto_close(reason: str) -> None:
    if not STATE.config.get("auto_close_after_export", True):
        append_debug_event("info", "auto_close_skipped", {"reason": reason})
        return
    if not STATE.command:
        append_debug_event("warning", "auto_close_missing_command", {"reason": reason})
        return
    try:
        append_debug_event("info", "auto_close_attempt", {"reason": reason})
        cmd = STATE.command
        if hasattr(cmd, "doTerminate"):
            cmd.doTerminate()
            append_debug_event("info", "auto_close_triggered", {"reason": reason})
            return
        if hasattr(cmd, "terminate"):
            cmd.terminate()
            append_debug_event("info", "auto_close_triggered", {"reason": reason})
            return
        ui = STATE.ui or adsk.core.Application.get().userInterface
        active_cmd = getattr(ui, "activeCommand", None)
        if active_cmd:
            if hasattr(active_cmd, "doTerminate"):
                active_cmd.doTerminate()
                append_debug_event("info", "auto_close_triggered", {"reason": reason})
                return
            if hasattr(active_cmd, "terminate"):
                active_cmd.terminate()
                append_debug_event("info", "auto_close_triggered", {"reason": reason})
                return
        append_debug_event("warning", "auto_close_no_method", {"reason": reason})
    except Exception as exc:
        append_debug_event(
            "error",
            "auto_close_failed",
            {"reason": reason, "error": str(exc)},
        )


def ensure_removed(ui: adsk.core.UserInterface, cid: str) -> None:
    try:
        ws = ui.workspaces.itemById("FusionSolidEnvironment")
        if ws:
            for i in range(ws.toolbarPanels.count):
                panel = ws.toolbarPanels.item(i)
                control = panel.controls.itemById(cid)
                if control:
                    control.deleteMe()
        cmd = ui.commandDefinitions.itemById(cid)
        if cmd:
            cmd.deleteMe()
    except Exception:
        pass


def ensure_command(defs: adsk.core.CommandDefinitions):
    cmd = defs.itemById(CMD_ID)
    if cmd:
        try:
            cmd.tooltip = f"Export STL (v{ADDIN_VERSION})"
        except Exception:
            pass
        return cmd
    res = icon_folder()
    if os.path.isdir(res):
        return defs.addButtonDefinition(
            CMD_ID, CMD_NAME, f"Export STL (v{ADDIN_VERSION})", res
        )
    return defs.addButtonDefinition(CMD_ID, CMD_NAME, f"Export STL (v{ADDIN_VERSION})")


def promote_in_panel(panel: adsk.core.ToolbarPanel, cmd_def: adsk.core.CommandDefinition):
    ctrl = panel.controls.itemById(CMD_ID)
    if not ctrl:
        ctrl = panel.controls.addCommand(cmd_def)
    try:
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True
    except Exception:
        pass


def promote_button_everywhere(ui: adsk.core.UserInterface):
    ws = ui.workspaces.itemById("FusionSolidEnvironment")
    if not ws:
        return
    panels = ws.toolbarPanels
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    for pid in ["SolidScriptsAddinsPanel", "ToolsAddinsPanel", "SolidUtilitiesPanel"]:
        try:
            panel = panels.itemById(pid)
            if panel:
                promote_in_panel(panel, cmd_def)
        except Exception:
            pass


def wire_commands(ui: adsk.core.UserInterface) -> None:
    for oid in ["quickstl_export_choose_cmd", "quickSTL.export.choose.cmd", "quickSTL.export.cmd"]:
        ensure_removed(ui, oid)
    defs = ui.commandDefinitions
    cmd_def = ensure_command(defs)
    on_created = CommandCreatedHandler()
    cmd_def.commandCreated.add(on_created)
    STATE.handlers.append(on_created)
    promote_button_everywhere(ui)
