import copy

from .constants import DEFAULT_CONFIG


class AddinState:
    def __init__(self):
        self.app = None
        self.ui = None
        self.handlers = []
        self.busy = False
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        self.command = None
        self.idle_monitor = None


STATE = AddinState()
