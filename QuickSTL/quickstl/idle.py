import datetime

import adsk.core

from .constants import ADDIN_NAME, ADDIN_VERSION, IDLE_TIMEOUT_S
from .diagnostics import append_debug_event, update_idle_state, update_ui_state
from .logging_utils import log
from .ui_helpers import find_input


class IdleEventHandler(adsk.core.IdleEventHandler):
    def __init__(self, monitor):
        super().__init__()
        self._monitor = monitor

    def notify(self, args: adsk.core.IdleEventArgs):
        self._monitor.tick()


class IdleMonitor:
    def __init__(self, timeout_s: int = IDLE_TIMEOUT_S):
        self.timeout_s = timeout_s
        self.started_at = None
        self.last_interaction = None
        self.auto_close_triggered = False
        self.command = None
        self.inputs = None
        self.active = False
        self._idle_handler = None
        self._last_remaining = None

    def start(self, command: adsk.core.Command, inputs: adsk.core.CommandInputs):
        now = datetime.datetime.now()
        self.command = command
        self.inputs = inputs
        self.started_at = now
        self.last_interaction = now
        self.auto_close_triggered = False
        self.active = True
        self._last_remaining = None
        update_ui_state({"command_visible": True, "last_event": "command_opened"})
        append_debug_event(
            "ui",
            "Command opened",
            {"name": ADDIN_NAME, "version": ADDIN_VERSION},
        )
        self._ensure_idle_handler()
        self._push_state(force=True)
        self._update_countdown(self.timeout_s)

    def stop(self, reason: str = ""):
        if not self.active:
            return
        self.active = False
        self.command = None
        self.inputs = None
        update_ui_state({"command_visible": False, "last_event": reason or "command_closed"})
        append_debug_event(
            "ui",
            "Command closed",
            {"reason": reason or "command_closed"},
        )
        try:
            app = adsk.core.Application.get()
            if self._idle_handler:
                app.idle.remove(self._idle_handler)
        except Exception:
            pass

    def record_interaction(self, source: str, detail: str = ""):
        if not self.active:
            return
        self.last_interaction = datetime.datetime.now()
        self._last_remaining = None
        self._update_countdown(self.timeout_s)

    def tick(self):
        if not self.active:
            return
        now = datetime.datetime.now()
        elapsed = (now - self.last_interaction).total_seconds()
        remaining = max(0, int(self.timeout_s - elapsed))
        if remaining != self._last_remaining:
            self._update_countdown(remaining)
            self._push_state(remaining)
        if remaining <= 0 and not self.auto_close_triggered:
            self.auto_close_triggered = True
            self._push_state(remaining)
            self._auto_close()

    def _ensure_idle_handler(self):
        try:
            app = adsk.core.Application.get()
            if not self._idle_handler:
                self._idle_handler = IdleEventHandler(self)
                app.idle.add(self._idle_handler)
        except Exception as exc:
            log(f"Idle handler setup failed: {exc}")

    def _update_countdown(self, remaining: int):
        self._last_remaining = remaining
        if not self.inputs:
            return
        try:
            timer_input = adsk.core.TextBoxCommandInput.cast(
                find_input(self.inputs, "idleCountdown")
            )
            if timer_input:
                timer_input.text = f"{remaining}s"
        except Exception:
            pass

    def _push_state(self, remaining: int = None, force: bool = False):
        if remaining is None:
            remaining = max(
                0,
                int(self.timeout_s - (datetime.datetime.now() - self.last_interaction).total_seconds()),
            )
        if not force and remaining == self._last_remaining:
            return
        update_idle_state(
            {
                "timer_started": self.started_at.isoformat() if self.started_at else "",
                "last_interaction": self.last_interaction.isoformat()
                if self.last_interaction
                else "",
                "timeout_seconds": self.timeout_s,
                "seconds_remaining": remaining,
                "auto_close_triggered": self.auto_close_triggered,
            }
        )

    def _auto_close(self):
        append_debug_event(
            "warning",
            "Idle timeout reached",
            {"timeout_seconds": self.timeout_s},
        )
        closed = False
        try:
            if self.command:
                try:
                    self.command.terminate()
                    closed = True
                    return
                except Exception:
                    pass
                try:
                    self.command.doTerminate()
                    closed = True
                    return
                except Exception:
                    pass
            ui = adsk.core.Application.get().userInterface
            active_cmd = getattr(ui, "activeCommand", None)
            if active_cmd:
                try:
                    active_cmd.terminate()
                    closed = True
                    return
                except Exception:
                    pass
        except Exception as exc:
            log(f"Idle auto-close failed: {exc}")
        if not closed:
            self.stop("idle_timeout")
