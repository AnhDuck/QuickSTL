import time
from typing import Any, Optional

import adsk.core

from .constants import ADDIN_NAME, IDLE_LOG_INTERVAL_S, IDLE_TIMEOUT_S, TOAST_ID
from .diagnostics import write_idle_diag
from .logging_utils import log
from .state import STATE


def push_idle_event(event: str, details: Optional[dict] = None) -> None:
    payload = {
        "ts": time.monotonic(),
        "event": event,
        "details": details or {},
    }
    STATE.idle_debug_events.append(payload)
    if len(STATE.idle_debug_events) > 25:
        STATE.idle_debug_events = STATE.idle_debug_events[-25:]


def record_activity(reason: str = "", log_reset: bool = False) -> None:
    now = time.monotonic()
    STATE.last_activity_ts = now
    STATE.last_activity_reason = reason
    STATE.idle_last_elapsed_s = 0.0
    push_idle_event("activity", {"reason": reason})
    if log_reset:
        log(f"Idle timer reset ({reason}). Timeout={STATE.idle_timeout_s:.0f}s")
        write_idle_diag("idle_reset", {"reason": reason})


def mark_command_active(reason: str = "command_created") -> None:
    STATE.idle_active = True
    record_activity(reason, log_reset=True)
    push_idle_event("command_active", {"reason": reason})
    write_idle_diag("command_active", {"reason": reason})


def mark_command_inactive(reason: str = "command_destroy") -> None:
    STATE.idle_active = False
    STATE.last_activity_reason = reason
    push_idle_event("command_inactive", {"reason": reason})
    write_idle_diag("command_inactive", {"reason": reason})


def close_quickstl_ui(reason: str, idle_elapsed: float) -> None:
    push_idle_event("auto_close_start", {"reason": reason, "idle_elapsed": idle_elapsed})
    write_idle_diag(
        "auto_close_start",
        {"reason": reason, "idle_elapsed": idle_elapsed},
    )
    log(
        f"Auto-closing {ADDIN_NAME} after {idle_elapsed:.1f}s idle "
        f"({reason}). Timeout={STATE.idle_timeout_s:.0f}s"
    )
    try:
        cmd = STATE.active_command
        if cmd:
            try:
                if getattr(cmd, "isActive", True):
                    cmd.terminate()
            except Exception as exc:
                log(f"Idle terminate failed: {exc}")
                write_idle_diag("auto_close_error", {"stage": "terminate", "error": str(exc)})
    except Exception as exc:
        log(f"Idle command close error: {exc}")
        write_idle_diag("auto_close_error", {"stage": "command", "error": str(exc)})

    try:
        pal = STATE.ui.palettes.itemById(TOAST_ID) if STATE.ui else None
        if pal:
            pal.isVisible = False
            pal.deleteMe()
    except Exception as exc:
        log(f"Idle toast close error: {exc}")
        write_idle_diag("auto_close_error", {"stage": "toast", "error": str(exc)})

    STATE.active_command = None
    STATE.idle_active = False
    write_idle_diag("auto_close_complete", {"reason": reason, "idle_elapsed": idle_elapsed})


class IdleCloseHandler(adsk.core.IdleEventHandler):
    def notify(self, args: Any) -> None:
        try:
            if not STATE.idle_active:
                return
            now = time.monotonic()
            last = STATE.last_activity_ts or now
            idle_elapsed = max(0.0, now - last)
            STATE.idle_last_elapsed_s = idle_elapsed
            if idle_elapsed >= STATE.idle_timeout_s:
                close_quickstl_ui("idle_timeout", idle_elapsed)
                return
            if (now - STATE.last_idle_log_ts) >= STATE.idle_log_interval_s:
                push_idle_event("idle_check", {"idle_elapsed": idle_elapsed})
                log(
                    f"Idle check: {idle_elapsed:.1f}s idle "
                    f"(timeout={STATE.idle_timeout_s:.0f}s)."
                )
                write_idle_diag(
                    "idle_check",
                    {"idle_elapsed": idle_elapsed},
                )
                STATE.last_idle_log_ts = now
        except Exception as exc:
            log(f"Idle handler error: {exc}")
            write_idle_diag("idle_error", {"error": str(exc)})


def start_idle_monitoring(app: adsk.core.Application) -> None:
    if not app:
        return
    if STATE.idle_handler:
        return
    handler = IdleCloseHandler()
    app.idle.add(handler)
    STATE.handlers.append(handler)
    STATE.idle_handler = handler
    STATE.last_idle_log_ts = 0.0
    STATE.idle_log_interval_s = IDLE_LOG_INTERVAL_S
    STATE.idle_timeout_s = IDLE_TIMEOUT_S
    push_idle_event("idle_monitor_start", {})
    write_idle_diag("idle_monitor_start", {})


def stop_idle_monitoring(app: adsk.core.Application) -> None:
    if not app:
        return
    try:
        for handler in list(STATE.handlers):
            if isinstance(handler, IdleCloseHandler):
                try:
                    app.idle.remove(handler)
                except Exception:
                    pass
    except Exception:
        pass
    STATE.idle_active = False
    STATE.active_command = None
    STATE.idle_handler = None
    push_idle_event("idle_monitor_stop", {})
    write_idle_diag("idle_monitor_stop", {})
