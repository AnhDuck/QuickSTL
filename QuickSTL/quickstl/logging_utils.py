from .diagnostics import append_debug_event


def log(message: str) -> None:
    append_debug_event("error", message)


def log_warning(message: str) -> None:
    append_debug_event("warning", message)
