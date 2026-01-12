import time

import adsk.core

from .constants import ADDIN_NAME, IDLE_LOG_INTERVAL_S, IDLE_TIMEOUT_S, TOAST_ID
from .logging_utils import log
from .state import STATE


def record_activity(reason: str = "", log_reset: bool = False) -> None:
    now = time.monotonic()
    STATE.last_activity_ts = now
    STATE.last_activity_reason = reason
    STATE.idle_last_elapsed_s = 0.0
    if log_reset:
        log(
            f"Idle timer reset ({reason}). Timeout={STATE.idle_timeout_s:.0f}s"
        )


def mark_command_active(reason: str = "command_created") -> None:
    STATE.idle_active = True
    record_activity(reason, log_reset=True)


def mark_command_inactive(reason: str = "command_destroy") -> None:
    STATE.idle_active = False
    STATE.last_activity_reason = reason


def close_quickstl_ui(reason: str, idle_elapsed: float) -> None:
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
    except Exception as exc:
        log(f"Idle command close error: {exc}")

    try:
        pal = STATE.ui.palettes.itemById(TOAST_ID) if STATE.ui else None
        if pal:
            pal.isVisible = False
            pal.deleteMe()
    except Exception as exc:
        log(f"Idle toast close error: {exc}")

    STATE.active_command = None
    STATE.idle_active = False


class IdleCloseHandler(adsk.core.IdleEventHandler):
    def notify(self, args: adsk.core.IdleEventArgs) -> None:
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
                log(
                    f"Idle check: {idle_elapsed:.1f}s idle "
                    f"(timeout={STATE.idle_timeout_s:.0f}s)."
                )
                STATE.last_idle_log_ts = now
        except Exception as exc:
            log(f"Idle handler error: {exc}")


def start_idle_monitoring(app: adsk.core.Application) -> None:
    if not app:
        return
    handler = IdleCloseHandler()
    app.idle.add(handler)
    STATE.handlers.append(handler)
    STATE.last_idle_log_ts = 0.0
    STATE.idle_log_interval_s = IDLE_LOG_INTERVAL_S
    STATE.idle_timeout_s = IDLE_TIMEOUT_S


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
