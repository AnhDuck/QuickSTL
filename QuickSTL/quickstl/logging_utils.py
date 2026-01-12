import datetime

from .constants import ADDIN_VERSION
from .paths import log_path


def log(message: str) -> None:
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path(), "a", encoding="utf-8") as handle:
            handle.write(f"[{ts}] v{ADDIN_VERSION} {message}\n")
    except Exception:
        pass
