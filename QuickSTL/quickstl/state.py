import copy

from .constants import DEFAULT_CONFIG, IDLE_LOG_INTERVAL_S, IDLE_TIMEOUT_S


class AddinState:
    def __init__(self):
        self.app = None
        self.ui = None
        self.handlers = []
        self.busy = False
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        self.active_command = None
        self.idle_active = False
        self.idle_timeout_s = IDLE_TIMEOUT_S
        self.idle_log_interval_s = IDLE_LOG_INTERVAL_S
        self.last_activity_ts = None
        self.last_activity_reason = ""
        self.last_idle_log_ts = 0.0
        self.idle_last_elapsed_s = 0.0
        self.idle_handler = None
        self.idle_debug_events = []


STATE = AddinState()
