def log(message: str) -> None:
    from .diagnostics import append_debug_event

    append_debug_event("error", message)


def log_warning(message: str) -> None:
    from .diagnostics import append_debug_event

    append_debug_event("warning", message)
